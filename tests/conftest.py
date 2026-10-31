# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fixtures shared by all tests (found by pytest automatically)."""

import pytest
from sqlalchemy.orm import Session

import ddserver.models  # noqa: F401 (defines the tables in Base.metadata)
from ddserver.db import Base, make_engine

PASSWORD = "correct horse"


@pytest.fixture
def session():
    """A session on a new, empty in-memory SQLite database."""
    engine = make_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    engine.dispose()
