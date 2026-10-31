# SPDX-License-Identifier: AGPL-3.0-or-later


def test_user_list_needs_login(client):
    response = client.get("/admin/users")

    assert response.status_code == 302
    assert response.headers["Location"] == "/"


def test_user_list_is_forbidden_for_users(client, add_user, login):
    add_user()
    login(client)

    assert client.get("/admin/users").status_code == 403


def test_user_list(client, add_user, login):
    add_user("root", admin=True)
    add_user("john")
    login(client, "root")

    page = client.get("/admin/users").data

    assert b"root@example.org" in page
    assert b"john@example.org" in page


def test_users_menu_is_only_shown_to_admins(app, client, add_user, login):
    add_user("root", admin=True)
    add_user("john")
    other_browser = app.test_client()
    login(client, "root")
    login(other_browser, "john")

    assert b'href="/admin/users"' in client.get("/").data
    assert b'href="/admin/users"' not in other_browser.get("/").data
