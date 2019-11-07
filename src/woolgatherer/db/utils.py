"""
DB utilities
"""
import json
from uuid import UUID
from functools import partial
from datetime import datetime
from typing import Any, Dict, Tuple
import hashlib
from importlib.util import find_spec

try:
    from psycopg2 import IntegrityError  # pylint: disable=unused-import
except ImportError:
    from sqlite3 import IntegrityError


def has_postgres() -> bool:
    """ Whether to use postgres """
    return find_spec("psycopg2") is not None


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
