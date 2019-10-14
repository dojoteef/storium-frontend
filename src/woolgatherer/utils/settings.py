"""
Encapsulate the configuration for woolgatherer
"""
from typing import Optional
from importlib.util import find_spec

from pydantic import BaseSettings, DSN, SecretStr


class _BasicSettings(BaseSettings):
    """ The basic app settings that don't require Postgres """

    db_driver: str = "sqlite"
    db_user: Optional[str] = None
    db_password: Optional[SecretStr] = None
    db_host: Optional[str] = None
    db_port: Optional[int] = None
    db_name: str = "woolgatherer.db"
    db_query: Optional[dict] = None
    dsn: DSN

    class Config(object):
        """ Additional configuration for the settings """

        prefix = "GW_"


class _Settings(_BasicSettings):
    """ The app settings """

    db_driver: str = "postgres+psycopg2"
    db_user: Optional[str] = "postgres"
    db_password: Optional[SecretStr] = None
    db_host: Optional[str] = "localhost"
    db_port: Optional[int] = 5432
    db_name: str = "woolgatherer"


# Forward declare Settings to make mypy happy
Settings: BaseSettings
if find_spec("psycopg2"):
    Settings = _Settings()
else:
    Settings = _BasicSettings()
