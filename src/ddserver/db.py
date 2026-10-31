# SPDX-License-Identifier: AGPL-3.0-or-later
"""
The Database (SQLAlchemy).

Create an engine, which holds the DB connection, once at startup.
Each request then uses its own session, which gets created on first use by the
get_session() method and closed automatically when the request ends. Changes
have to be committed with session.commit().
"""

from datetime import UTC, datetime

import alembic.command
import alembic.config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from flask import Flask, current_app, g
from sqlalchemy import (
    Connection,
    DateTime,
    Engine,
    MetaData,
    TypeDecorator,
    create_engine,
    event,
)
from sqlalchemy.orm import DeclarativeBase, Session


class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


class UTCDateTime(TypeDecorator):
    """A timestamp, stored in UTC and returned as datetime with timezone UTC.

    SQLite cannot store timezones, so we store the value without one.
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return None

        if value.tzinfo is None:
            raise ValueError("timestamps must have a timezone")

        return value.astimezone(UTC).replace(tzinfo=None)

    def process_result_value(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return None

        return value.replace(tzinfo=UTC)


def utcnow() -> datetime:
    """Return the current time in UTC (for `UTCDateTime` columns)."""
    return datetime.now(UTC)


def make_engine(url: str) -> Engine:
    """Create the engine."""
    engine = create_engine(url)
    event.listen(engine, "connect", _enable_sqlite_foreign_keys)

    return engine


def _enable_sqlite_foreign_keys(connection, connection_record):
    """Enable foreign keys."""
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.close()


def init_app(app: Flask, engine: Engine) -> None:
    """Make `engine` available to `get_session()` within `app`."""
    app.extensions["ddserver.db"] = engine
    app.teardown_appcontext(_close_session)


def get_session() -> Session:
    """Return the session of the current request (creates it on first use)."""
    if "db_session" not in g:
        g.db_session = Session(current_app.extensions["ddserver.db"])

    return g.db_session


def _close_session(exception: BaseException | None) -> None:
    """Close the db session."""
    session = g.pop("db_session", None)

    if session is not None:
        session.close()


class SchemaError(Exception):
    """The database schema does not match the version of ddserver."""


def check_schema(engine: Engine) -> None:
    """Raise `SchemaError` if the database is not at the latest migration."""
    script = ScriptDirectory.from_config(_alembic_config())

    with engine.connect() as connection:
        current = MigrationContext.configure(connection).get_current_heads()

    if set(current) != set(script.get_heads()):
        raise SchemaError("the database schema is outdated, run `ddserver db upgrade`")


def upgrade(engine: Engine) -> None:
    """Apply all missing migrations to the database."""
    with engine.begin() as connection:
        alembic.command.upgrade(_alembic_config(connection), "head")


def revision(engine: Engine, message: str) -> None:
    """Create a draft migration from the differences between models and database."""
    with engine.begin() as connection:
        config = _alembic_config(connection)

        # Format the new migration file with ruff (a development dependency).
        config.set_section_option("post_write_hooks", "hooks", "ruff")
        config.set_section_option("post_write_hooks", "ruff.type", "module")
        config.set_section_option("post_write_hooks", "ruff.module", "ruff")
        config.set_section_option(
            "post_write_hooks", "ruff.options", "format REVISION_SCRIPT_FILENAME"
        )

        alembic.command.revision(config, message=message, autogenerate=True)


def _alembic_config(connection: Connection | None = None) -> alembic.config.Config:
    # Configure Alembic in code instead of an `alembic.ini` file. The connection
    # is picked up by `migrations/env.py`.
    config = alembic.config.Config()
    config.set_main_option("script_location", "ddserver:migrations")
    config.attributes["connection"] = connection

    return config
