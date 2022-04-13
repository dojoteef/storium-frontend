"""
The base class for all SQLAlchemy models
"""
from typing import (
    Any,
    ClassVar,
    Dict,
    List,
    Mapping,
    Tuple,
    Set,
    Sequence,
    Optional,
    Union,
    Type,
    TypeVar,
    TYPE_CHECKING,
)

import sqlalchemy as sa
from sqlalchemy.schema import Constraint
from sqlalchemy.sql.expression import select, and_
from databases import Database
from pydantic import BaseConfig, BaseModel, Field, Json

from woolgatherer.db import types
from woolgatherer.errors import InvalidOperationError
from woolgatherer.utils import snake_case


__all__ = ["DBBaseModel"]


if TYPE_CHECKING:
    DBModel = TypeVar("DBModel", bound="DBBaseModel")


_ExtraFieldMappings: Dict[str, str] = {
    "index": "index",
    "unique": "unique",
    "nullable": "nullable",
    "primary_key": "primary_key",
    "autoincrement": "autoincrement",
    "server_default": "server_default",
    "description": "doc",
}


class DBModelMetaClass(types.ModelMetaClass):  # type: ignore
    """ The meta class for the DB base model """

    def __new__(  # type: ignore
        mcs: type,
        name: str,
        bases: Tuple[type, ...],
        namespace: Dict[str, Any],
        constraints: Sequence[Constraint] = tuple(),  # pylint:disable=unused-argument
    ) -> type:
        new_type = super().__new__(mcs, name, bases, namespace)  # type: ignore
        table = getattr(new_type, "__table__", None)
        if table is not None:
            for constraint in constraints:
                table.append_constraint(constraint)

        return new_type


class DBBaseModel(BaseModel, metaclass=DBModelMetaClass):
    """ The base DB model """

    __table__: sa.Table
    __metadata__: sa.MetaData = sa.MetaData()
    __slots__ = ('_modified',)

    # What if any fields have been updated after creation. This allows db update to only
    # set newly changed values.
    _modified: Dict[str, bool]

    id: Optional[int] = Field(..., primary_key=True, autoincrement=True)


    @classmethod
    def __init_subclass__(cls, constraints: Sequence[Constraint] = tuple()) -> None:
        super().__init_subclass__()

        bases: List[type] = []
        for base in cls.__bases__:
            if base is DBBaseModel:
                bases.append(BaseModel)
            else:
                bases.append(base)

        columns = []
        for field in cls.__fields__.values():
            foriegn_key = None
            kwargs: Dict[str, Any] = {}
            if field.has_alias:
                kwargs["key"] = field.alias

            if field.default is not Ellipsis:
                kwargs["default"] = field.default

            if not field.allow_none:
                kwargs["nullable"] = False

            if field.field_info:
                extra = field.field_info.extra
                for source_field, target_field in _ExtraFieldMappings.items():
                    if source_field in extra:
                        kwargs[target_field] = extra[source_field]

                if "foriegn_key" in extra:
                    foriegn_key = extra["foriegn_key"]

            args = [field.name, types.get_sa_type(field.type_)]
            if foriegn_key:
                args.append(foriegn_key)

            columns.append(sa.Column(*args, **kwargs))

        cls.__table__ = sa.Table(
            snake_case(cls.__name__), DBBaseModel.__metadata__, *columns, *constraints
        )

    class Config(BaseConfig):
        """ Configure the pydantic model """

        keep_untouched: Tuple[type, ...] = (sa.MetaData,)

    def __new__(cls: Type['DBBaseModel'], **kwargs) -> 'DBBaseModel':
        self = super().__new__(cls)
        object.__setattr__(self, "_modified", {})

        return self

    def __setattr__(self, key: str, value: Any):
        """ Set an attribute """
        super().__setattr__(key, value)
        self._modified[key] = True

    def db_dict(
        self,
        *,
        include: Optional[Union[str, Set[str]]] = None,
        exclude: Optional[Union[str, Set[str]]] = None,
        defaults: bool = False,
        modified_only: bool = False
    ):
        """
        Collect the fields that have been set on the model, optionally including
        defaults if specified.
        """
        if isinstance(include, str):
            include = {include}

        if isinstance(exclude, str):
            exclude = {exclude}

        include = include or set()
        exclude = exclude or set()

        fields_set: Set[str] = set(self.__fields_set__)
        include = fields_set.intersection(include) if include else fields_set
        include = include.difference(exclude)

        values = {}
        for name, field in type(self).__dict__["__fields__"].items():
            if modified_only and not name in self._modified:
                continue

            if name in include:
                values[name] = getattr(self, name)
            elif (
                defaults
                and name not in exclude
                and not field.allow_none
                and field.default is not Ellipsis
            ):
                values[name] = (
                    field.default() if callable(field.default) else field.default
                )

        return {k: types.to_db_type(v) for k, v in values.items()}

    async def insert(
        self,
        db: Database,
        *,
        include_columns: Optional[Union[str, Set[str]]] = None,
        exclude_columns: Optional[Union[str, Set[str]]] = None,
    ):
        """
        Insert the current model into the db. Make sure to only insert values that have
        actually been set, or defaults if provided.
        """
        await db.execute(
            query=type(self).__table__.insert(
                values=self.db_dict(
                    include=include_columns, exclude=exclude_columns, defaults=True
                )
            )
        )
        self._modified.clear()

    async def delete(self, db: Database, *, where: Optional[Dict[str, Any]] = None):
        """
        Delete the current model from the db. Either and id or a where clause must be provided.
        """
        table = type(self).__table__
        query = table.delete()

        if where:
            clauses = tuple(table.columns[c] == v for c, v in where.items())
            query = query.where(and_(*clauses))
        elif self.id is not None:
            query = query.where(table.columns["id"] == self.id)
        else:
            raise InvalidOperationError(
                f"Cowardly refusing to delete all {type(self).__name__}"
            )

        await db.execute(query=query)
        self._modified.clear()

    async def update(
        self,
        db: Database,
        *,
        include_columns: Optional[Union[str, Set[str]]] = None,
        exclude_columns: Optional[Union[str, Set[str]]] = None,
        where: Optional[Dict[str, Any]] = None,
        modified_only: bool = True
    ):
        """
        Update the model the db. Make sure to only update values that have
        actually been set, or defaults if provided.
        """
        table = type(self).__table__
        query = table.update(
            values=self.db_dict(
                include=include_columns,
                exclude=exclude_columns,
                modified_only=modified_only,
            )
        )

        if where:
            clauses = tuple(table.columns[c] == v for c, v in where.items())
            query = query.where(and_(*clauses))
        elif self.id is not None:
            query = query.where(table.columns["id"] == self.id)
        else:
            raise InvalidOperationError(
                f"Cowardly refusing to update all {type(self).__name__}"
            )

        await db.execute(query=query)
        self._modified.clear()

    @classmethod
    def _select_query(
        cls: Type["DBModel"],
        columns: Optional[Union[str, Sequence[str]]] = None,
        where: Optional[Dict[str, Any]] = None,
    ) -> Optional["DBModel"]:
        """ Generate a select statement for the type """
        table = cls.__table__
        if columns:
            if isinstance(columns, str):
                columns = (columns,)

            columns = tuple(table.columns[c] for c in columns)
            query = select(columns=columns)
        else:
            # Explicitly select all columns rather than empty `table.select()`, otherwise
            # the databases package will return "raw" results, i.e. string result rather than
            # converting to python types
            query = select(columns=tuple(table.columns.values()))

        if where:
            clauses = tuple(table.columns[c] == v for c, v in where.items())
            query = query.where(and_(*clauses))

        return query

    @classmethod
    def db_construct(cls: Type["DBModel"], result) -> "DBModel":
        """ Construct an object of the class from a query result """
        return cls.construct(
            set(result.keys()),
            **{
                k: types.from_db_type(cls.__fields__[k].type_, v)
                for k, v in result.items()
            },
        )

    @classmethod
    async def select(
        cls: Type["DBModel"],
        db: Database,
        columns: Optional[Union[str, Sequence[str]]] = None,
        where: Optional[Dict[str, Any]] = None,
    ) -> Optional["DBModel"]:
        """ Generate a select statement for the type """
        result = await db.fetch_one(
            query=cls._select_query(columns=columns, where=where)
        )
        return cls.db_construct(result) if result else None

    @classmethod
    async def select_all(
        cls: Type["DBModel"],
        db: Database,
        columns: Optional[Union[str, Sequence[str]]] = None,
        where: Optional[Dict[str, Any]] = None,
    ) -> List["DBModel"]:
        """ Generate a select statement for the type """
        results = await db.fetch_all(
            query=cls._select_query(columns=columns, where=where)
        )
        return [cls.db_construct(result) for result in results]
