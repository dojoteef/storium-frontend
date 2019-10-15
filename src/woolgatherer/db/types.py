"""
Cross driver wrapper for SQLAlchemy db types
"""
from woolgatherer.db.utils import has_postgres

if has_postgres():
    from sqlalchemy.dialects.postgresql import JSONB as _JSON
else:
    from sqlalchemy.dialects.sqlite import JSON as _JSON

JSON = _JSON
