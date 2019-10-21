"""
Encapsulate SQLAlchemy sessions
"""
try:
    from contextlib import asynccontextmanager
except ImportError:
    from async_generator import asynccontextmanager

import databases

from woolgatherer.utils.settings import Settings


_database: databases.Database = databases.Database(Settings.dsn)


async def open_connection_pool():
    """ Initialize the db connection pool """
    await _database.connect()


async def close_connection_pool():
    """ Close the db connection pool """
    await _database.disconnect()


async def get_db():
    """
    A generator which yields a database. It can be used as a dependency for routes.
    """
    try:
        transaction = await _database.transaction()
        yield _database
    except:  # pylint: disable=bare-except
        await transaction.rollback()
    finally:
        await transaction.commit()


get_async_db = asynccontextmanager(get_db)
