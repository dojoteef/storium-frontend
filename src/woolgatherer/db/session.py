"""
Encapsulate SQLAlchemy sessions
"""
import databases

from woolgatherer.utils.settings import Settings

__all__ = ["get_db", "open_connection_pool", "close_connection_pool"]


database: databases.Database = databases.Database(Settings.dsn)


async def get_db():
    """
    A generator which yields a database. It can be used as a dependency for routes.
    """
    try:
        transaction = await database.transaction()
        yield database
    except:  # pylint: disable=bare-except
        await transaction.rollback()
    finally:
        await transaction.commit()


async def open_connection_pool():
    """ Initialize the db connection pool """
    await database.connect()


async def close_connection_pool():
    """ Close the db connection pool """
    await database.disconnect()
