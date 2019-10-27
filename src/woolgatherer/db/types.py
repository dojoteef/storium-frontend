"""
Cross driver wrapper for SQLAlchemy db types
"""
import json
import uuid
import datetime
from enum import Enum
from typing import Any, Dict
import sqlalchemy as sa
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID

from pydantic import BaseModel, Json
from woolgatherer.db.utils import has_postgres

# pylint: disable=ungrouped-imports
if has_postgres():
    from sqlalchemy.dialects.postgresql import JSONB as _JSON
else:
    from sqlalchemy.dialects.sqlite import JSON as _JSON
# pylint: enable=ungrouped-imports

JSON = _JSON


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
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % uuid.UUID(value).int
            else:
                # hexstring
                return "%.32x" % value.int

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                value = uuid.UUID(value)
            return value


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


def to_db_type(obj: Any) -> Any:
    """ Convert an object to a type acceptable by the database """
    if isinstance(obj, BaseModel):
        return obj.json()
    elif isinstance(obj, datetime.datetime):
        return obj.isoformat(" ")
    elif isinstance(obj, datetime.date) or isinstance(obj, datetime.time):
        return obj.isoformat()
    else:
        return obj


def from_db_type(cls: type, obj: Any) -> Any:
    """ Convert an object to a type acceptable by the database """
    if issubclass(cls, BaseModel):
        if isinstance(obj, str):
            return cls(**json.loads(obj))

    return obj
