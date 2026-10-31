# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Alembic environment: run by Alembic for every migration command.

The database connection is passed in by `ddserver.db` (see `_alembic_config()`),
so there is no `alembic.ini` and no separate database configuration.
"""

from alembic import context

import ddserver.models  # noqa: F401 (defines the tables in Base.metadata)
from ddserver.db import Base, UTCDateTime


def render_item(type_, obj, autogen_context):
    # Write our own column types as their plain SQLAlchemy equivalent into
    # migrations, so that migrations do not depend on code that may change later.
    if type_ == "type" and isinstance(obj, UTCDateTime):
        return "sa.DateTime()"

    return False


context.configure(
    connection=context.config.attributes["connection"],
    target_metadata=Base.metadata,
    # SQLite can hardly alter tables; batch mode recreates them instead.
    render_as_batch=True,
    render_item=render_item,
)

with context.begin_transaction():
    context.run_migrations()
