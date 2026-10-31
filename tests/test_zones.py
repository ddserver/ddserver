# SPDX-License-Identifier: AGPL-3.0-or-later

import pytest

from ddserver.zones import (
    ZoneError,
    create_zone,
    delete_zone,
    get_zone,
    list_zones,
)


def test_create_zone(session):
    create_zone(session, "dyn.example.org")
    session.commit()

    assert [zone.name for zone in list_zones(session)] == ["dyn.example.org"]


def test_zone_name_normalized(session):
    zone = create_zone(session, " DYN.Example.ORG. ")

    assert zone.name == "dyn.example.org"


@pytest.mark.parametrize(
    "name",
    [
        "example.org",
        "dyn.example.org",
        "my-zone.example.org",
        "xn--mnchen-3ya.example.org",
        "1.example.org",
        f"{'a' * 63}.example.org",
        ".".join(["a" * 61] * 4),  # 247 characters
    ],
)
def test_valid_zone_name(session, name):
    assert create_zone(session, name)


@pytest.mark.parametrize(
    "name",
    [
        "",
        ".",
        "org",
        ".example.org",
        "example..org",
        "example.org..",
        "-dyn.example.org",
        "dyn-.example.org",
        "dyn_1.example.org",
        "dyn example.org",
        "münchen.example.org",
        f"{'a' * 64}.example.org",
        ".".join(["a" * 63] * 4),  # 255 characters
    ],
)
def test_invalid_zone_name(session, name):
    with pytest.raises(ZoneError, match="invalid zone name"):
        create_zone(session, name)


def test_duplicate_zone(session):
    create_zone(session, "dyn.example.org")

    with pytest.raises(ZoneError, match="already exists"):
        create_zone(session, "DYN.example.org.")


def test_get_zone(session):
    zone = create_zone(session, "dyn.example.org")
    session.commit()

    assert get_zone(session, "DYN.example.org.") is zone


def test_get_unknown_zone(session):
    with pytest.raises(ZoneError, match=r"There is no zone dyn\.example\.org"):
        get_zone(session, "dyn.example.org")


def test_delete_zone(session):
    zone = create_zone(session, "dyn.example.org")
    session.commit()

    delete_zone(session, zone)
    session.commit()

    assert list_zones(session) == []
