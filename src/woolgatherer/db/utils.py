"""
DB utilities
"""
import json
import hashlib
from importlib.util import find_spec


def has_postgres() -> bool:
    """ Whether to use postgres """
    return find_spec("psycopg2") is not None


def normalized_json_str(json_obj: dict) -> str:
    """
    Normalize a JSON object by sorting it and removing any extraneous space. We need
    this in order to have a consistent hash that we can compute for JSON in the database
    when checking for equality. While PostgreSQL has support for unique constraints on
    JSONB columns, it has a size limit which we will definitely go over!
    """
    return json.dumps(
        json_obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")


def json_hash(json_obj: dict) -> str:
    """
    Generate a consistent hash for a given JSON object.
    """
    hasher = hashlib.md5()
    hasher.update(normalized_json_str(json_obj))
    return hasher.hexdigest()
