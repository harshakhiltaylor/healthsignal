import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from alembic import context
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import settings
from db.session import Base
import db.models  # noqa — ensure models are registered

config = context.config
# Do NOT use set_main_option here — % in the URL breaks configparser interpolation.
# Instead we pass the URL directly to the engine factory below.

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline():
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online():
    from sqlalchemy.ext.asyncio import create_async_engine
    connectable = create_async_engine(
        settings.database_url,
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
