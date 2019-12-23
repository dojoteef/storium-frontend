"""
The base class for all SQLAlchemy models
"""
from typing import (
    Any,
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

            # Need to do different processing if the type is wrapped in a special typing
            # annotation, e.g. Union, Dict, etc.
            base_type_: type = field.type_
            origin = getattr(field.type_, "__origin__", None)
            if origin:
                if origin is Union:
                    union_args = set(getattr(field.type_, "__args__"))
                    union_args.discard(type(None))

                    if len(union_args) == 1:
                        base_type_ = union_args.pop()
                    else:
                        union_args.discard(Json)
                        union_args.discard(Dict[str, Any])
                        if all(issubclass(t, BaseModel) for t in union_args):
                            base_type_ = Json
                            union_args.clear()

                    if union_args:
                        raise AttributeError("Unsupported annotation type!")
                elif issubclass(origin, Mapping):
                    mapping_args = getattr(field.type_, "__args__")
                    if not issubclass(mapping_args[0], str):
                        raise AttributeError("Mapping key must be a string!")
                    base_type_ = Json
                else:
                    # Technically, PostgreSQL supports an array (which could be
                    # specified as a List or Tuple), but only that database does. Since
                    # I want this to also work with SQLite, supporting lists is not an
                    # option.
                    raise AttributeError(
                        "Only Optional, Union, Dict annotations currently supported!"
                    )

            # Now convert the detected types into SQLAlchemy types
            sa_types: Set[sa.types.TypeEngine] = set()
            for type_ in base_type_.__mro__:
                if type_ in types.TypeMapping:
                    sa_types.add(types.TypeMapping[type_])

            if not sa_types:
                raise AttributeError(
                    f"{field.name} must be convertible to sqlalchemy type!"
                )

            sa_type: sa.types.TypeEngine = sorted(
                list(sa_types), key=lambda t: types.TypeOrder[t]
            )[0]

            if sa_type is sa.Enum:
                sa_type = sa.Enum(field.type_)

            args = [field.name, sa_type]
            if foriegn_key:
                args.append(foriegn_key)

            columns.append(sa.Column(*args, **kwargs))

        cls.__table__ = sa.Table(
            snake_case(cls.__name__), DBBaseModel.__metadata__, *columns, *constraints
        )

    class Config(BaseConfig):
        """ Configure the pydantic model """

        keep_untouched: Tuple[type, ...] = (sa.MetaData,)

    def db_dict(
        self,
        *,
        include: Optional[Union[str, Set[str]]] = None,
        exclude: Optional[Union[str, Set[str]]] = None,
        defaults: bool = False,
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

    async def update(
        self,
        db: Database,
        *,
        include_columns: Optional[Union[str, Set[str]]] = None,
        exclude_columns: Optional[Union[str, Set[str]]] = None,
        where: Optional[Dict[str, Any]] = None,
    ):
        """
        Insert the current model into the db. Make sure to only insert values that have
        actually been set, or defaults if provided.
        """
        table = type(self).__table__
        query = table.update(
            values=self.db_dict(include=include_columns, exclude=exclude_columns)
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

    @classmethod
    def _select_query(
        cls: Type["DBModel"],
        columns: Optional[Union[str, Sequence[str]]] = None,
        where: Optional[Dict[str, Any]] = None,
    ) -> Optional["DBModel"]:
        """ Generate an insert statement for the type """
        table = cls.__table__
        if columns:
            if isinstance(columns, str):
                columns = (columns,)

            columns = tuple(table.columns[c] for c in columns)
            query = select(columns=columns)
        else:
            query = table.select()

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
        """ Generate an insert statement for the type """
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
        """ Generate an insert statement for the type """
        results = await db.fetch_all(
            query=cls._select_query(columns=columns, where=where)
        )
        return [cls.db_construct(result) for result in results]
