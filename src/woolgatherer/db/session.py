"""
Encapsulate SQLAlchemy sessions
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from woolgatherer.utils.settings import Settings


engine = create_engine(Settings.dsn, pool_pre_ping=True)
Session = sessionmaker(autoflush=False, autocommit=False, bind=engine)
