# SPDX-License-Identifier: AGPL-3.0-or-later

import re

from conftest import PASSWORD
from sqlalchemy import select

from ddserver.db import get_session
from ddserver.models import User, UserStatus


def _change_user(app, **values):
    with app.app_context():
        session = get_session()
        user = session.scalars(select(User)).one()

        for name, value in values.items():
            setattr(user, name, value)

        session.commit()


def test_start_page_shows_login_form(client):
    assert b'action="/login"' in client.get("/").data


def test_login(client, add_user, login):
    add_user()

    page = login(client).data

    assert b'action="/logout"' in page
    assert b'action="/login"' not in page


def test_login_wrong_password(client, add_user, login):
    add_user()

    page = login(client, password="wrong").data

    assert b"Wrong username or password" in page
    assert b'action="/login"' in page


def test_login_unknown_user_gives_same_message(client, login):
    assert b"Wrong username or password" in login(client, username="nobody").data


def test_login_inactive_user(app, client, add_user, login):
    add_user()
    _change_user(app, status=UserStatus.ACTIVATION)

    assert b"Wrong username or password" in login(client).data


def test_logout(client, add_user, login):
    add_user()
    login(client)

    page = client.post("/logout", follow_redirects=True).data

    assert b'action="/login"' in page
    assert client.get("/account").status_code == 302


def test_logout_needs_post(client):
    assert client.get("/logout").status_code == 405


def test_session_ends_when_user_becomes_inactive(app, client, add_user, login):
    add_user()
    login(client)

    _change_user(app, status=UserStatus.ACTIVATION)

    assert client.get("/account").status_code == 302


def test_session_ends_when_user_is_deleted(app, client, add_user, login):
    add_user()
    login(client)

    with app.app_context():
        session = get_session()
        session.delete(session.scalars(select(User)).one())
        session.commit()

    assert client.get("/account").status_code == 302


def test_post_without_csrf_token_is_refused(app, client, add_user):
    add_user()
    app.config["WTF_CSRF_ENABLED"] = True

    response = client.post("/login", data={"username": "john", "password": PASSWORD})

    assert response.status_code == 302
    assert b"session has expired" in client.get("/").data
    assert client.get("/account").status_code == 302


def test_post_with_csrf_token_from_login_form(app, client, add_user):
    add_user()
    app.config["WTF_CSRF_ENABLED"] = True

    page = client.get("/").get_data(as_text=True)
    token = re.search(r'name="csrf_token" value="([^"]+)"', page)[1]

    client.post(
        "/login",
        data={"username": "john", "password": PASSWORD, "csrf_token": token},
    )

    assert client.get("/account").status_code == 200


def test_session_cookie_settings(client, add_user):
    add_user()

    response = client.post("/login", data={"username": "john", "password": PASSWORD})
    cookie = response.headers["Set-Cookie"]

    assert "HttpOnly" in cookie
    assert "SameSite=Lax" in cookie
