# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fixtures shared by all tests (found by pytest automatically)."""

import pytest
from sqlalchemy.orm import Session

import ddserver.models  # noqa: F401 (defines the tables in Base.metadata)
from ddserver import db
from ddserver.app import create_app
from ddserver.config import Config, DatabaseConfig, WebConfig
from ddserver.db import Base, get_session, make_engine
from ddserver.users import create_user

PASSWORD = "correct horse"


@pytest.fixture
def session():
    """A session on a new, empty in-memory SQLite database."""
    engine = make_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    engine.dispose()


@pytest.fixture
def app(tmp_path):
    """The application with a new database, created by the real migrations.

    CSRF protection is off, as tests would otherwise have to send a token with each
    request. `test_web_auth.py` covers it.
    """
    config = Config(
        web=WebConfig(secret_key="test"),
        database=DatabaseConfig(url=f"sqlite:///{tmp_path / 'test.db'}"),
    )
    db.upgrade(make_engine(config.database.url))

    app = create_app(config)
    app.config["WTF_CSRF_ENABLED"] = False

    return app


@pytest.fixture
def client(app):
    """A browser (keeps cookies) that is not logged in."""
    return app.test_client()


@pytest.fixture
def add_user(app):
    """Return a function which adds an active user with the password `PASSWORD`."""

    def add_user(username: str = "john", admin: bool = False) -> None:
        with app.app_context():
            session = get_session()
            email = f"{username}@example.org"
            create_user(session, username, email, PASSWORD, admin)
            session.commit()

    return add_user


@pytest.fixture
def login():
    """Return a function which logs in a test client."""

    def login(client, username: str = "john", password: str = PASSWORD):
        return client.post(
            "/login",
            data={"username": username, "password": password},
            follow_redirects=True,
        )

    return login
