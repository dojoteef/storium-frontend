"""
Cross driver wrapper for SQLAlchemy db types
"""
import datetime
from enum import Enum
from typing import Dict
import sqlalchemy as sa
from pydantic import Json
from woolgatherer.db.utils import has_postgres

if has_postgres():
    from sqlalchemy.dialects.postgresql import JSONB as _JSON
else:
    from sqlalchemy.dialects.sqlite import JSON as _JSON

JSON = _JSON

TypeMapping: Dict[type, sa.types.TypeEngine] = {
    str: sa.String,
    int: sa.Integer,
    bool: sa.Boolean,
    float: sa.Float,
    bytes: sa.Binary,
    bytearray: sa.Binary,
    Enum: sa.Enum,
    Json: JSON,
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
    sa.Date: 2,
    sa.Time: 2,
    sa.DateTime: 1,
}
