# SPDX-License-Identifier: AGPL-3.0-or-later

import pytest
from sqlalchemy import select

from ddserver.db import get_session
from ddserver.hosts import HOST_LIMIT_UNLIMITED
from ddserver.models import Host, User
from ddserver.passwords import verify_password
from ddserver.zones import create_zone

PASSWORD = "host password"


def _names(app) -> list[str]:
    with app.app_context():
        return [host.name for host in get_session().scalars(select(Host))]


@pytest.fixture
def zone_id(app) -> int:
    with app.app_context():
        session = get_session()
        zone = create_zone(session, "dyn.example.org")
        session.commit()

        return zone.id


@pytest.fixture
def user_client(client, add_user, login):
    """A browser logged in as the normal user `john`."""
    add_user()
    login(client)

    return client


@pytest.fixture
def add_host(user_client, zone_id):
    """Return a function which submits the form to add a host."""

    def add_host(client=user_client, **values):
        data = {
            "name": "myhost",
            "zone": zone_id,
            "password": PASSWORD,
            "password_repeat": PASSWORD,
            **values,
        }

        return client.post("/hosts/add", data=data, follow_redirects=True)

    return add_host


def test_add_host(app, add_host):
    page = add_host(ipv4="192.0.2.1", ipv6="2001:db8::1", description="router").data

    assert b"Hostname myhost.dyn.example.org has been added" in page
    assert b"myhost" in page
    assert b"192.0.2.1" in page
    assert b"2001:db8::1" in page
    assert b'title="router"' in page
    assert _names(app) == ["myhost"]


def test_add_reserved_host(app, add_host):
    assert b"The hostname www is reserved." in add_host(name="www").data
    assert _names(app) == []


def test_add_duplicate_host(app, add_host):
    add_host()

    assert b"myhost.dyn.example.org already exists." in add_host().data
    assert _names(app) == ["myhost"]


def test_add_host_unknown_zone(app, add_host):
    assert b"Please select a zone" in add_host(zone=999).data
    assert _names(app) == []


def test_add_host_invalid_zone(app, add_host):
    assert b"Please select a zone" in add_host(zone="x").data
    assert _names(app) == []


def test_host_list_shows_only_own_hosts(app, add_host, add_user, login):
    add_host()
    add_user("anna")
    other_browser = app.test_client()
    login(other_browser, "anna")

    assert b"myhost" not in other_browser.get("/hosts").data


def test_admin_delete_user_with_hosts(app, add_host, add_user, login):
    add_host()
    add_user("root", admin=True)
    admin_browser = app.test_client()
    login(admin_browser, "root")

    with app.app_context():
        user_id = get_session().scalars(select(Host)).one().user_id

    response = admin_browser.post(f"/admin/users/{user_id}/delete")

    assert response.status_code == 302
    assert _names(app) == []


def test_delete_own_account_with_hosts(app, user_client, add_host):
    add_host()

    assert user_client.post("/account/delete").status_code == 302
    assert _names(app) == []


def test_zone_page_shows_host_count_and_deletes_hosts(
    app, add_host, zone_id, add_user, login
):
    add_host()
    add_user("root", admin=True)
    admin_browser = app.test_client()
    login(admin_browser, "root")

    page = admin_browser.get("/admin/zones").get_data(as_text=True)
    assert "<td>1</td>" in page
    assert "1 hostname</strong>" in page

    response = admin_browser.post(f"/admin/zones/{zone_id}/delete")

    assert response.status_code == 302
    assert _names(app) == []


def _host_id(app, name: str = "myhost") -> int:
    with app.app_context():
        return get_session().scalar(select(Host.id).where(Host.name == name))


def _host(app) -> tuple:
    with app.app_context():
        host = get_session().scalars(select(Host)).one()
        return host.ipv4, host.ipv6, host.description, host.password


def test_update_host(app, add_host, user_client):
    add_host()
    url = f"/hosts/{_host_id(app)}"

    page = user_client.post(
        url,
        data={"ipv4": "192.0.2.1", "ipv6": "2001:db8::1", "description": "router"},
        follow_redirects=True,
    ).data

    assert b"The hostname has been updated" in page
    assert _host(app)[:3] == ("192.0.2.1", "2001:db8::1", "router")


def test_delete_host(app, add_host, user_client):
    add_host(name="a")
    add_host(name="b")
    url = f"/hosts/{_host_id(app, 'a')}/delete"

    page = user_client.post(url, follow_redirects=True).data

    assert b"Hostname a.dyn.example.org has been deleted" in page
    assert _names(app) == ["b"]


def test_delete_unknown_host(user_client):
    assert user_client.post("/hosts/999/delete").status_code == 404


def test_cannot_delete_host_of_other_user(app, add_host, add_user, login):
    add_host()
    add_user("anna")
    other_browser = app.test_client()
    login(other_browser, "anna")

    response = other_browser.post(f"/hosts/{_host_id(app)}/delete")

    assert response.status_code == 404
    assert _names(app) == ["myhost"]
