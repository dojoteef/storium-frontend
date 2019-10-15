"""
Encapsulate the configuration for woolgatherer
"""
from typing import Optional

from pydantic import BaseSettings, DSN, SecretStr

from woolgatherer.db.utils import has_postgres


class _DevSettings(BaseSettings):
    """ The basic app settings that don't require Postgres """

    db_driver: str = "sqlite"
    db_user: Optional[str] = None
    db_password: Optional[SecretStr] = None
    db_host: Optional[str] = None
    db_port: Optional[int] = None
    db_name: str = "woolgatherer.db"
    db_query: Optional[dict] = {"check_same_thread": False}
    dsn: DSN = None

    class Config(object):
        """ Additional configuration for the settings """

        prefix = "GW_"


class _Settings(_DevSettings):
    """ The app settings """

    db_driver: str = "postgres+psycopg2"
    db_user: Optional[str] = "postgres"
    db_password: Optional[SecretStr] = None
    db_host: Optional[str] = "localhost"
    db_port: Optional[int] = 5432
    db_name: str = "woolgatherer"


# Forward declare Settings to make mypy happy
Settings: BaseSettings
if has_postgres():
    Settings = _Settings()
else:
    Settings = _DevSettings()
