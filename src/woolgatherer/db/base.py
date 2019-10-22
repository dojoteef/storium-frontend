"""
The base class for all SQLAlchemy models
"""
import sys
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
from sqlalchemy.engine import RowProxy
from databases import Database
from pydantic import BaseConfig, BaseModel, Json
from pydantic import fields

from woolgatherer.db.types import TypeMapping, TypeOrder
from woolgatherer.models.utils import Field


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


class Namespace(object):
    """
    Simple object for storing attributes. Based on the Namespace from argparse. Pydantic
    only support attributes, rather than a dict, when using from_orm, so we need to
    convert the dict to an object with attributes.  Implements equality by attribute
    names and values.
    """

    def __init__(self, row: RowProxy):
        for key, value in row.items():
            setattr(self, key, value)

    def __eq__(self, other):
        if not isinstance(other, Namespace):
            return NotImplemented
        return vars(self) == vars(other)

    def __contains__(self, key):
        return key in self.__dict__


class DBBaseModel(BaseModel):
    """ The base DB model """

    __table__: sa.Table
    __orm_cls__: Type["BaseModel"]
    __metadata__: sa.MetaData = sa.MetaData()

    id: Optional[int] = Field(..., primary_key=True, autoincrement=True)

    @classmethod
    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        bases: List[type] = []
        for base in cls.__bases__:
            if base is DBBaseModel:
                bases.append(BaseModel)
            else:
                bases.append(base)

        _orm_fields: Dict[str, fields.Field] = {}
        for name, field in cls.__dict__["__fields__"].items():
            _orm_fields[name] = fields.Field(
                name=field.name,
                type_=field.type_,
                class_validators=field.class_validators,
                model_config=field.model_config,
                default=field.default,
                required=False,
                alias=field.alias,
                schema=field.schema,
            )

        _orm_name = f"{cls.__name__}Base"
        _orm_dict = dict(cls.__dict__)
        _orm_dict["__fields__"] = _orm_fields

        _orm_cls = type(_orm_name, tuple(bases), _orm_dict)
        _module = sys.modules[cls.__module__]
        setattr(_module, _orm_name, _orm_cls)
        cls.__orm_cls__ = _orm_cls

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
                for source_field, target_field in _ExtraFieldMappings.items():
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
                    elif (
                        len(union_args) == 2
                        and Json in union_args
                        and Dict[str, Any] in union_args
                    ):
                        base_type_ = Json
                    else:
                        raise AttributeError(
                            "Only Union[<type>] & Union[<type>, None] supported!"
                        )
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
        Overload the baseclass from_orm to use our special base class which removes
        required for all fields
        """
        return cls.__orm_cls__.from_orm(obj)

    async def insert(self, db: Database):
        """
        Insert the current model into the db. Make sure to only insert values that have
        actually been set, or defaults if provided.
        """
        values = {}
        for name, field in type(self).__dict__["__fields__"].items():
            if (
                name
                in self.__fields_set__  # pylint:disable=unsupported-membership-test
            ):
                values[name] = getattr(self, name)
            elif not field.allow_none and field.default is not Ellipsis:
                values[name] = field.default

        await db.execute(query=type(self).__table__.insert(values=values))

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
            query = query.where(and_(*clauses))

        result = await db.fetch_one(query=query)
        return cls.from_orm(Namespace(result)) if result else None
