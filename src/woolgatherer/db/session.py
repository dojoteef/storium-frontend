"""
Encapsulate SQLAlchemy sessions
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from woolgatherer.utils.settings import Settings
from woolgatherer.db.utils import normalized_json_str


engine = create_engine(
    Settings.dsn, pool_pre_ping=True, json_serializer=normalized_json_str
)
_session = sessionmaker(autoflush=False, autocommit=False, bind=engine)


def get_db():
    """
    A generator which yields a database. It can be used as a dependency for routes.
    """
    try:
        db = _session()
        yield db
    finally:
        db.close()
