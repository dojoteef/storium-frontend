"""
DB utilities
"""
import os
import json
import hashlib
from uuid import UUID
from functools import partial
from datetime import datetime
from typing import Any, Dict, Tuple
from importlib.util import find_spec

import aiofiles

try:
    from asyncpg.exceptions import (  # pylint: disable=unused-import
        IntegrityConstraintViolationError as IntegrityError,
    )
except ImportError:
    from sqlite3 import IntegrityError  # pylint: disable=unused-import


def has_postgres() -> bool:
    """ Whether to use postgres """
    return find_spec("asyncpg") is not None


async def load_query(filename: str) -> str:
    """
    Load the query from the file and return it
    """
    dialect = "postgres" if has_postgres() else "sqlite"
    async with aiofiles.open(os.path.join("sql", dialect, filename), "rt") as sql:
        return await sql.read()


class JSONEncoder(json.JSONEncoder):
    """ A custom JSON encoder which handles datetime objects """

    def default(self, o):  # pylint:disable=method-hidden
        """ Overloaded to support datetime objects """
        if isinstance(o, datetime):
            return o.isoformat(" ")

        return super().default(o)


json_dumps = partial(json.dumps, cls=JSONEncoder, separators=(",", ":"))


def normalized_json_str(json_obj: Dict[str, Any]) -> str:
    """
    Normalize a JSON object by sorting it and removing any extraneous space.
    """
    return json_dumps(json_obj, sort_keys=True, ensure_ascii=False)


def json_hash(json_obj: Dict[str, Any]) -> Tuple[str, str]:
    """
    Generate a consistent hash for a given JSON object. We need this in order
    to have a consistent hash that we can compute for JSON in the database when
    checking for equality. For example, while PostgreSQL has support for unique
    constraints on JSONB columns, it has a size limit which we will definitely
    go over!
    """
    hasher = hashlib.md5()
    json_str = normalized_json_str(json_obj)
    hasher.update(json_str.encode("utf-8"))
    return json_str, hasher.hexdigest()


def uuid_str(uuid: UUID):
    """ Return the UUID as a string """
    return str(uuid).replace("-", "")
