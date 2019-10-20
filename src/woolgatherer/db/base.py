"""
The base class for all SQLAlchemy models
"""
from copy import deepcopy
from collections.abc import Sequence
from typing import (
    Any,
    Dict,
    List,
    Mapping,
    Tuple,
    Set,
    Optional,
    Union,
    Type,
    TypeVar,
    TYPE_CHECKING,
)

import sqlalchemy as sa
from sqlalchemy.sql.expression import select, and_
from databases import Database
from pydantic import BaseConfig, BaseModel

from woolgatherer.db.types import TypeMapping, TypeOrder
from woolgatherer.models.utils import Field


__all__ = ["DBBaseModel"]

if TYPE_CHECKING:
    DBModel = TypeVar("DBModel", bound="DBBaseModel")


ExtraFieldMappings: Dict[str, str] = {
    "index": "index",
    "unique": "unique",
    "primary_key": "primary_key",
    "autoincrement": "autoincrement",
    "server_default": "server_default",
    "description": "doc",
}


class DBBaseModel(BaseModel):
    """ The base DB model """

    __table__: sa.Table
    __orm_cls__: Type["BaseModel"]
    __metadata__: sa.MetaData = sa.MetaData()

    id: Optional[int] = Field(None, primary_key=True, autoincrement=True)

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        bases: List[type] = []
        for base in cls.__bases__:
            if base is DBBaseModel:
                bases.append(BaseModel)
            else:
                bases.append(base)

        _orm_dict = dict(cls.__dict__)
        _orm_dict["__fields__"] = deepcopy(_orm_dict["__fields__"])
        for field in _orm_dict["__fields__"].values():
            field.required = False

        cls.__orm_cls__ = type(f"{cls.__name__}Base", tuple(bases), _orm_dict)

        columns = []
        for field in cls.__fields__.values():
            kwargs: Dict[str, Any] = {}
            if field.has_alias:
                kwargs["key"] = field.alias

            if field.default is not Ellipsis:
                kwargs["default"] = field.default

            if not field.allow_none:
                kwargs["nullable"] = False

            if field.schema:
                extra = field.schema.extra
                for source_field, target_field in ExtraFieldMappings.items():
                    if source_field in extra:
                        kwargs[target_field] = extra[source_field]

            # Need to do different processing if the type is wrapped in a special typing
            # annotation, e.g. Union, Dict, etc.
            base_type_: type = field.type_
            origin = getattr(field.type_, "__origin__", None)
            if origin:
                if origin is Union:
                    union_args = set(getattr(field.type_, "__args__"))
                    if len(union_args) == 1:
                        pass
                    elif (
                        len(union_args) == 2
                        and type(None)  # pylint:disable = unidiomatic-typecheck
                        in union_args
                    ):
                        kwargs["nullable"] = True
                        union_args.remove(type(None))
                        base_type_ = union_args.pop()
                    else:
                        raise AttributeError(
                            "Only Union[<type>] & Union[<type>, None] supported!"
                        )
                elif issubclass(origin, Mapping):
                    mapping_args = getattr(field.type_, "__args__")
                    if not issubclass(mapping_args[0], str):
                        raise AttributeError("Mapping key must be a string!")
                    base_type_ = dict
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
                if type_ in TypeMapping:
                    sa_types.add(TypeMapping[type_])

            if not sa_types:
                raise AttributeError(
                    f"{field.name} must be convertible to sqlalchemy type!"
                )

            sa_type: sa.types.TypeEngine = sorted(
                list(sa_types), key=lambda t: TypeOrder[t]
            )[0]

            if sa_type is sa.Enum:
                sa_type = sa.Enum(field.type_)

            columns.append(sa.Column(field.name, sa_type, **kwargs))

        cls.__table__ = sa.Table(
            cls.__name__.lower(), DBBaseModel.__metadata__, *columns
        )

    class Config(BaseConfig):
        """ Configure the pydantic model """

        orm_mode: bool = True
        keep_untouched: Tuple[type, ...] = (sa.MetaData,)

    @classmethod
    def from_orm(cls: Type["DBModel"], obj: Any) -> Any:
        """
        Overload the baseclass from_orm to use our special base class which
        removes required for all fields
        """
        return cls.__orm_cls__.from_orm(obj)

    async def insert(self, db: Database):
        """ Insert the current model into the db """
        await db.execute(query=type(self).__table__.insert(), values=self.dict())

    @classmethod
    async def select(
        cls: Type["DBModel"],
        db: Database,
        columns: Optional[Union[str, Sequence]] = None,
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
            clause = and_(*clauses)
            query = query.where(clause)

        result = await db.fetch_one(query=query)
        return cls.from_orm(dict(result)) if result else None
