"""
Cross driver wrapper for SQLAlchemy db types
"""
import json
import uuid
import datetime
from enum import Enum
from typing import Any, Dict, Mapping, Union
import sqlalchemy as sa
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID, JSONB as _JSONB
from sqlalchemy.dialects.sqlite import JSON as _JSON

from pydantic import BaseModel, Json
from woolgatherer.db.utils import has_postgres

JSON = _JSONB if has_postgres() else _JSON
ModelMetaClass = type(BaseModel)


class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Uses PostgreSQL's UUID type, otherwise uses
    CHAR(32), storing as stringified hex values.

    Taken from the SQLAlchemy docs
    https://docs.sqlalchemy.org/en/13/core/custom_types.html?highlight=guid#backend-agnostic-guid-type
    """

    impl = CHAR

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(UUID())

        return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value

        if dialect.name == "postgresql":
            return str(value)

        if not isinstance(value, uuid.UUID):
            return "%.32x" % uuid.UUID(value).int

        # hexstring
        return "%.32x" % value.int

    def process_result_value(self, value, dialect):
        if value is None:
            return value

        if not isinstance(value, uuid.UUID):
            value = uuid.UUID(value)

        return value

    def process_literal_param(self, value, dialect):
        raise NotImplementedError()


# Mapping from python type to SQLAlchemy type
TypeMapping: Dict[type, sa.types.TypeEngine] = {
    str: sa.String,
    int: sa.Integer,
    bool: sa.Boolean,
    float: sa.Float,
    bytes: sa.Binary,
    bytearray: sa.Binary,
    Enum: sa.Enum,
    Json: JSON,
    uuid.UUID: GUID,
    BaseModel: JSON,
    datetime.date: sa.Date,
    datetime.time: sa.Time,
    datetime.datetime: sa.DateTime,
}

# Define a total ordering for sqlalchemy types, such that if a column could be
# specified by either type, it chooses the most best type based on this
# ordering.
TypeOrder: Dict[sa.types.TypeEngine, int] = {
    sa.Integer: 7,
    sa.Float: 6,
    sa.Boolean: 5,
    sa.Binary: 5,
    sa.String: 4,
    sa.Enum: 3,
    JSON: 3,
    GUID: 2,
    sa.Date: 2,
    sa.Time: 2,
    sa.DateTime: 1,
}


def get_sa_type(from_type: type):
    """ Compute the SQLAlchemy type from the passed in type """
    base_type = from_type
    origin = getattr(from_type, "__origin__", None)
    if origin:
        # Need to do different processing if the type is wrapped in a special typing
        # annotation, e.g. Union, Dict, etc.
        if origin is Union:
            union_args = set(getattr(from_type, "__args__"))
            union_args.discard(type(None))

            if len(union_args) == 1:
                base_type = union_args.pop()
            else:
                union_args.discard(Json)
                union_args.discard(Dict[str, Any])
                if all(issubclass(t, BaseModel) for t in union_args):
                    base_type = Json
                    union_args.clear()

            if union_args:
                raise AttributeError("Unsupported annotation type!")
        elif issubclass(origin, Mapping):
            mapping_args = getattr(from_type, "__args__")
            if not issubclass(mapping_args[0], str):
                raise AttributeError("Mapping key must be a string!")
            base_type = Json
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
    for type_ in base_type.__mro__:
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
        sa_type = sa.Enum(from_type)

    return sa_type


def to_db_type(obj: Any) -> Any:
    """ Convert an object to a type acceptable by the database """
    if isinstance(obj, BaseModel):
        return json.loads(obj.json())

    if isinstance(obj, datetime.datetime):
        return obj.isoformat(" ")

    if isinstance(obj, (datetime.date, datetime.time)):
        return obj.isoformat()

    return obj


def from_db_type(cls: type, obj: Any) -> Any:
    """ Convert an object to a type acceptable by the database """
    if type(cls) is ModelMetaClass:  # pylint:disable=unidiomatic-typecheck
        if isinstance(obj, str):
            return cls(**json.loads(obj))

    return obj
