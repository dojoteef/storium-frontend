"""
The base class for all SQLAlchemy models
"""
from typing import Any, Dict, Tuple, Set

import sqlalchemy as sa
from pydantic import BaseConfig, BaseModel

from woolgatherer.db.types import TypeMapping, TypeOrder
from woolgatherer.models.utils import Field


__all__ = ["DBBaseModel"]


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

    __metadata__: sa.MetaData = sa.MetaData()

    id: int = Field(1, primary_key=True, autoincrement=True)

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        columns = []
        for field in cls.__fields__.values():
            kwargs: Dict[str, Any] = {}
            if field.has_alias:
                kwargs["key"] = field.alias

            if field.default is not Ellipsis:
                kwargs["default"] = field.default

            if not field.allow_none:
                kwargs["nullable"] = False

            extra = field.schema.extra
            for source_field, target_field in ExtraFieldMappings.items():
                if source_field in extra:
                    kwargs[target_field] = extra[source_field]

            sa_types: Set[sa.types.TypeEngine] = set()
            for _type in field.type_.__mro__:
                if _type in TypeMapping:
                    sa_types.add(TypeMapping[_type])

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

        tablename = cls.__name__.lower()
        setattr(cls, "__tablename__", tablename)
        setattr(
            cls, "__table__", sa.Table(tablename, DBBaseModel.__metadata__, *columns)
        )

    class Config(BaseConfig):
        """ Configure the pydantic model """

        orm_mode: bool = True
        keep_untouched: Tuple[type, ...] = (sa.MetaData,)
