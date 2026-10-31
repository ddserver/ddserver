# SPDX-License-Identifier: AGPL-3.0-or-later

import pytest
from sqlalchemy import select

from ddserver.db import get_session
from ddserver.models import Zone


def _zone_names(app) -> list[str]:
    with app.app_context():
        return [zone.name for zone in get_session().scalars(select(Zone))]


def _add_zone(client, name: str):
    return client.post("/admin/zones", data={"name": name}, follow_redirects=True)


@pytest.fixture
def admin_client(client, add_user, login):
    """A browser logged in as an admin."""
    add_user("root", admin=True)
    login(client, "root")

    return client


def test_add_zone(app, admin_client):
    page = _add_zone(admin_client, "dyn.example.org").data

    assert b"Zone dyn.example.org has been added" in page
    assert b"<td>dyn.example.org</td>" in page
    assert b"No zones configured" not in page
    assert _zone_names(app) == ["dyn.example.org"]


def test_add_zone_normalizes_name(app, admin_client):
    _add_zone(admin_client, " DYN.Example.ORG. ")

    assert _zone_names(app) == ["dyn.example.org"]


def test_add_invalid_zone(app, admin_client):
    page = _add_zone(admin_client, "org").data

    assert b"invalid zone name" in page
    assert _zone_names(app) == []


def test_add_duplicate_zone(app, admin_client):
    _add_zone(admin_client, "dyn.example.org")

    page = _add_zone(admin_client, "dyn.example.org").data

    assert b"The zone dyn.example.org already exists." in page
    assert _zone_names(app) == ["dyn.example.org"]


def test_add_zone_without_name(app, admin_client):
    assert admin_client.post("/admin/zones").status_code == 302
    assert _zone_names(app) == []


def _zone_id(app, name: str) -> int:
    with app.app_context():
        return get_session().scalar(select(Zone.id).where(Zone.name == name))


def test_delete_zone(app, admin_client):
    _add_zone(admin_client, "a.example.org")
    _add_zone(admin_client, "b.example.org")
    url = f"/admin/zones/{_zone_id(app, 'a.example.org')}/delete"

    page = admin_client.post(url, follow_redirects=True).data

    assert b"Zone a.example.org has been deleted" in page
    assert _zone_names(app) == ["b.example.org"]


def test_delete_unknown_zone(admin_client):
    assert admin_client.post("/admin/zones/999/delete").status_code == 404

