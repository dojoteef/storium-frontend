"""
DB utilities
"""
import json
from typing import Any, Dict, Tuple, Union
import hashlib
from importlib.util import find_spec


def has_postgres() -> bool:
    """ Whether to use postgres """
    return find_spec("psycopg2") is not None


def normalized_json_str(json_obj: Dict[str, Any]) -> str:
    """
    Normalize a JSON object by sorting it and removing any extraneous space.
    """
    return json.dumps(
        json_obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )


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
