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
Session = sessionmaker(autoflush=False, autocommit=False, bind=engine)
