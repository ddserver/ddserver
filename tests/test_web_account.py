# SPDX-License-Identifier: AGPL-3.0-or-later

from conftest import PASSWORD

NEW_PASSWORD = "a new password"


def _change_password(client, current=PASSWORD, new=NEW_PASSWORD, repeat=NEW_PASSWORD):
    return client.post(
        "/account/password",
        data={
            "current_password": current,
            "new_password": new,
            "new_password_repeat": repeat,
        },
        follow_redirects=True,
    )


def test_account_needs_login(client):
    response = client.get("/account")

    assert response.status_code == 302
    assert response.headers["Location"] == "/"


def test_change_password_needs_login(client):
    assert client.post("/account/password").status_code == 302


def test_account_shows_user(client, add_user, login):
    add_user()
    login(client)

    page = client.get("/account").data

    assert b'value="john"' in page
    assert b'value="john@example.org"' in page


def test_change_password(client, add_user, login):
    add_user()
    login(client)

    assert b"password has been changed" in _change_password(client).data
    assert client.get("/account").status_code == 200

    client.post("/logout")

    assert b"Wrong username or password" in login(client).data
    assert (
        b"Wrong username or password" not in login(client, password=NEW_PASSWORD).data
    )


def test_change_password_wrong_current_password(client, add_user, login):
    add_user()
    login(client)

    page = _change_password(client, current="wrong").data

    assert b"The current password is not correct." in page


def test_change_password_too_short(client, add_user, login):
    add_user()
    login(client)

    page = _change_password(client, new="short", repeat="short").data

    assert b"at least 8 characters." in page


def test_change_password_repeat_differs(client, add_user, login):
    add_user()
    login(client)

    assert b"do not match" in _change_password(client, repeat="different").data

    # The old password still works.
    client.post("/logout")
    assert b"Wrong username or password" not in login(client).data


def test_change_password_ends_other_sessions(app, client, add_user, login):
    add_user()
    other_browser = app.test_client()
    login(client)
    login(other_browser)

    _change_password(client)

    assert client.get("/account").status_code == 200
    assert other_browser.get("/account").status_code == 302
