# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Zone management.

Add, delete or list zones. Commit to DB is done by the caller.
"""

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from ddserver.models import Zone

ZONE_NAME_MAX_LENGTH = 253
_LABEL = r"[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?"
ZONE_NAME_PATTERN = re.compile(rf"({_LABEL}\.)+{_LABEL}")


class ZoneError(Exception):
    """Zone can not be created or found."""


def normalize_zone_name(name: str) -> str:
    """Return `name` in lowercase without a final dot, raise `ZoneError` if invalid."""
    name = name.strip().lower().removesuffix(".")

    if len(name) > ZONE_NAME_MAX_LENGTH or not ZONE_NAME_PATTERN.fullmatch(name):
        raise ZoneError(
            "invalid zone name: use a domain with at least one dot, like "
            f"'example.org', up to {ZONE_NAME_MAX_LENGTH} characters. Each part "
            "between the dots may have up to 63 letters, digits or '-', but must not "
            "start or end with '-'"
        )

    return name


def create_zone(session: Session, name: str) -> Zone:
    """Add a new zone."""
    name = normalize_zone_name(name)

    if session.scalar(select(Zone).where(Zone.name == name)):
        raise ZoneError(f"The zone {name} already exists")

    zone = Zone(name=name)
    session.add(zone)

    return zone


def list_zones(session: Session) -> list[Zone]:
    """Return all zones, ordered by name."""
    return list(session.scalars(select(Zone).order_by(Zone.name)))


def get_zone(session: Session, name: str) -> Zone:
    """Return the zone with this `name`, raise `ZoneError` if there is none."""
    name = name.strip().lower().removesuffix(".")
    zone = session.scalar(select(Zone).where(Zone.name == name))

    if zone is None:
        raise ZoneError(f"There is no zone {name}")

    return zone


def delete_zone(session: Session, zone: Zone) -> None:
    """Delete a zone."""
    session.delete(zone)
