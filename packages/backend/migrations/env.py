import asyncio
from logging.config import fileConfig
from typing import Any, Literal

import alembic_postgresql_enum  # type: ignore[import-untyped] # noqa
import sqlalchemy_utils
from alembic import context
from alembic.autogenerate.api import AutogenContext
from alembic.operations.ops import MigrationScript
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from alembic.script.revision import _GetRevArg
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from wallstr.conf import settings
from wallstr.models.all import *  # noqa
from wallstr.models.base import BaseModel

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = BaseModel.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.get_secret_value())


def process_revision_directives(
    context: MigrationContext, revision: _GetRevArg, directives: list[MigrationScript]
) -> None:
    migration_script = directives[0]
    config = context.config
    if not config:
        return
    head_revision = ScriptDirectory.from_config(config).get_current_head()

    if head_revision is None:
        rev_id = 1
    else:
        last_rev_id = int(head_revision.lstrip("0"))
        rev_id = last_rev_id + 1
    migration_script.rev_id = f"{rev_id:04d}"


# https://github.com/kvesteri/sqlalchemy-utils/issues/129#issuecommentLiteral082
def render_item(
    type_: str, obj: Any, autogen_context: AutogenContext
) -> str | Literal[False]:
    if type_ == "type" and isinstance(obj, sqlalchemy_utils.types.PasswordType):
        max_length = obj.calculate_max_length()
        return f"sa.LargeBinary(length={max_length})"

    return False


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        render_item=render_item,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        process_revision_directives=process_revision_directives,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_item=render_item,
        process_revision_directives=process_revision_directives,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
