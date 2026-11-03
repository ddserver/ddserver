# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Host management.

Add, change, delete or list hosts. Commit to DB is done by the caller.
"""

import ipaddress
import re

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from ddserver.config import HostsConfig, PasswordConfig
from ddserver.db import utcnow
from ddserver.dns import HostName
from ddserver.models import DnsDeletion, Host, User, Zone
from ddserver.passwords import PasswordError, check_password, hash_password

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
    password_min_length: int = PasswordConfig.min_length,
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

    _check_password(user, password, password_min_length)

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

    # Publishing the new host replaces the records anyway.
    session.execute(
        delete(DnsDeletion).where(DnsDeletion.fqdn == f"{name}.{zone.name}")
    )

    return host


def update_host(host: Host, ipv4: str, ipv6: str, description: str) -> bool:
    """Change `host`. Returns whether its addresses have changed."""
    ipv4 = normalize_ipv4(ipv4)
    ipv6 = normalize_ipv6(ipv6)
    host.description = normalize_description(description)

    if (ipv4, ipv6) == (host.ipv4, host.ipv6):
        return False

    host.ipv4 = ipv4
    host.ipv6 = ipv6
    record_address_change(host)

    return True


def record_address_change(host: Host) -> None:
    """Note that the addresses of `host` have changed, and have to be published."""
    host.updated = utcnow()
    host.revision += 1


def set_host_password(host: Host, password: str, min_length: int) -> None:
    """Replace the password of `host`."""
    _check_password(host.user, password, min_length)
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


def list_hosts_of_zone(session: Session, zone: Zone) -> list[Host]:
    """Return the hosts in `zone`, ordered by name."""
    return list(
        session.scalars(select(Host).where(Host.zone_id == zone.id).order_by(Host.name))
    )


def count_hosts_by_zone(session: Session) -> dict[int, int]:
    """Return the number of hosts per zone id, without zones that have no hosts."""
    rows = session.execute(select(Host.zone_id, func.count()).group_by(Host.zone_id))

    return {zone_id: count for zone_id, count in rows}


def all_hosts(session: Session) -> list[Host]:
    """Return all hosts."""
    return list(session.scalars(select(Host)))


def unpublished_hosts(session: Session) -> list[Host]:
    """Return the hosts whose latest change has not reached DNS."""
    return list(
        session.scalars(select(Host).where(Host.revision != Host.published_revision))
    )


def pending_deletions(session: Session) -> list[HostName]:
    """Return the deleted hosts whose records may still be in DNS."""
    fqdns = session.scalars(select(DnsDeletion.fqdn))

    return [HostName(*fqdn.split(".", 1)) for fqdn in fqdns]


def delete_host(session: Session, host: Host) -> HostName:
    """Delete `host`. All deletions of hosts go through this function.

    Returns its name, for removing the records after the commit. Until this has
    worked, the deletion stays in `DnsDeletion`.
    """
    name = HostName(host.name, host.zone.name)
    session.delete(host)
    session.add(DnsDeletion(fqdn=str(name)))

    return name


def delete_hosts_of_user(session: Session, user: User) -> list[HostName]:
    """Delete all hosts of `user`, and return their names."""
    hosts = session.scalars(select(Host).where(Host.user_id == user.id)).all()

    return [delete_host(session, host) for host in hosts]


def delete_hosts_of_zone(session: Session, zone: Zone) -> list[HostName]:
    """Delete all hosts in `zone`, and return their names."""
    hosts = session.scalars(select(Host).where(Host.zone_id == zone.id)).all()

    return [delete_host(session, host) for host in hosts]


def _check_password(user: User, password: str, min_length: int) -> None:
    try:
        check_password(password, min_length, user.username, user.email)
    except PasswordError as e:
        raise HostError(str(e)) from e
