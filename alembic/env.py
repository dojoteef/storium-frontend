"""
Environment file for setting up alembic migrations
"""
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from woolgatherer.db_models.base import DBBaseModel
from woolgatherer.utils.settings import Settings

from alembic import context
import alembic_autogenerate_enums


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config  # pylint:disable=no-member

# Make sure to provide the appropriate data source name
config.set_main_option("sqlalchemy.url", Settings.dsn)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = DBBaseModel.__metadata__  # pylint:disable=no-member

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    context.configure(  # pylint:disable=no-member
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():  # pylint:disable=no-member
        context.run_migrations()  # pylint:disable=no-member


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(  # pylint:disable=no-member
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():  # pylint:disable=no-member
            context.run_migrations()  # pylint:disable=no-member


if context.is_offline_mode():  # pylint:disable=no-member
    run_migrations_offline()
else:
    run_migrations_online()
