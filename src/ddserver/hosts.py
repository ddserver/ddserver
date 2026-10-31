# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Host management.

Add, change, delete or list hosts. Commit to DB is done by the caller.
"""

import ipaddress
import re

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ddserver.config import HostsConfig
from ddserver.db import utcnow
from ddserver.models import Host, User, Zone
from ddserver.passwords import PASSWORD_MIN_LENGTH, hash_password

HOSTNAME_PATTERN = re.compile(r"[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?")
FQDN_MAX_LENGTH = 253
DESCRIPTION_MAX_LENGTH = 255
HOST_LIMIT_UNLIMITED = 1_000_000
_DEFAULT_CONFIG = HostsConfig()


class HostError(Exception):
    """Host can not be created or changed."""


def normalize_hostname(name: str) -> str:
    """Return `name` in lowercase, raise `HostError` if it is no valid hostname."""
    name = name.strip().lower()

    if not HOSTNAME_PATTERN.fullmatch(name):
        raise HostError(
            "Invalid hostname: use up to 63 letters, digits or '-', "
            "starting and ending with a letter or a digit"
        )

    return name


def normalize_ipv4(address: str) -> str | None:
    """Return `address` in its canonical form, `None` if it is empty."""
    address = address.strip()

    if not address:
        return None

    try:
        return str(ipaddress.IPv4Address(address))
    except ValueError as e:
        raise HostError(f"Invalid IPv4 address: {address}") from e


def normalize_ipv6(address: str) -> str | None:
    """Return `address` in its canonical form, `None` if it is empty."""
    address = address.strip()

    if not address:
        return None

    try:
        ipv6 = ipaddress.IPv6Address(address)
    except ValueError as e:
        raise HostError(f"Invalid IPv6 address: {address}") from e

    # A scope like `%eth0` only has a meaning on the machine it comes from.
    if ipv6.scope_id is not None:
        raise HostError(f"Invalid IPv6 address: {address}")

    return str(ipv6)


def normalize_description(description: str) -> str | None:
    """Return `description` as a single line, `None` if it is empty."""
    description = " ".join(description.split())

    if len(description) > DESCRIPTION_MAX_LENGTH:
        raise HostError(
            f"The description can have at most {DESCRIPTION_MAX_LENGTH} characters"
        )

    return description or None


def create_host(
    session: Session,
    user: User,
    zone: Zone,
    name: str,
    password: str,
    ipv4: str = "",
    ipv6: str = "",
    description: str = "",
    config: HostsConfig = _DEFAULT_CONFIG,
) -> Host:
    """Add a new host for `user`, within the limits of `config`."""
    limit = host_limit(user, config)
    count = session.scalar(
        select(func.count()).select_from(Host).where(Host.user_id == user.id)
    )

    if count >= limit:
        raise HostError(f"You have reached your limit of {limit} hostnames")

    name = normalize_hostname(name)
    ipv4 = normalize_ipv4(ipv4)
    ipv6 = normalize_ipv6(ipv6)
    description = normalize_description(description)

    if name in {reserved_name.lower() for reserved_name in config.reserved}:
        raise HostError(f"The hostname {name} is reserved")

    if len(f"{name}.{zone.name}") > FQDN_MAX_LENGTH:
        raise HostError(f"The hostname {name} is too long for this zone")

    _check_password(password)

    existing = select(Host).where(Host.zone_id == zone.id, Host.name == name)
    if session.scalar(existing):
        raise HostError(f"The hostname {name}.{zone.name} already exists")

    host = Host(
        user=user,
        zone=zone,
        name=name,
        password=hash_password(password),
        ipv4=ipv4,
        ipv6=ipv6,
        description=description,
        updated=utcnow() if ipv4 or ipv6 else None,
    )
    session.add(host)

    return host


def update_host(host: Host, ipv4: str, ipv6: str, description: str) -> None:
    """Change the addresses and the description of `host`."""
    ipv4 = normalize_ipv4(ipv4)
    ipv6 = normalize_ipv6(ipv6)
    host.description = normalize_description(description)

    if (ipv4, ipv6) != (host.ipv4, host.ipv6):
        host.ipv4 = ipv4
        host.ipv6 = ipv6
        host.updated = utcnow()


def set_host_password(host: Host, password: str) -> None:
    """Replace the password of `host`."""
    _check_password(password)
    host.password = hash_password(password)


def host_limit(user: User, config: HostsConfig) -> int:
    """Return how many hosts `user` can have."""
    return config.default_limit if user.host_limit is None else user.host_limit


def get_host(session: Session, user: User, host_id: int) -> Host | None:
    """Return the host with `host_id`, if it belongs to `user`."""
    return session.scalar(
        select(Host).where(Host.id == host_id, Host.user_id == user.id)
    )


def list_hosts(session: Session, user: User) -> list[Host]:
    """Return the hosts of `user`, ordered by zone and name."""
    return list(
        session.scalars(
            select(Host)
            .join(Host.zone)
            .where(Host.user_id == user.id)
            .order_by(Zone.name, Host.name)
        )
    )


def count_hosts_by_zone(session: Session) -> dict[int, int]:
    """Return the number of hosts per zone id, without zones that have no hosts."""
    rows = session.execute(select(Host.zone_id, func.count()).group_by(Host.zone_id))

    return {zone_id: count for zone_id, count in rows}


def delete_host(session: Session, host: Host) -> None:
    """Delete `host`. All deletions of hosts go through this function."""
    session.delete(host)


def delete_hosts_of_user(session: Session, user: User) -> None:
    """Delete all hosts of `user`."""
    for host in session.scalars(select(Host).where(Host.user_id == user.id)):
        delete_host(session, host)


def delete_hosts_of_zone(session: Session, zone: Zone) -> None:
    """Delete all hosts in `zone`."""
    for host in session.scalars(select(Host).where(Host.zone_id == zone.id)):
        delete_host(session, host)


def _check_password(password: str) -> None:
    if len(password) < PASSWORD_MIN_LENGTH:
        raise HostError(
            f"The password must have at least {PASSWORD_MIN_LENGTH} characters"
        )
