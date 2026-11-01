# SPDX-License-Identifier: AGPL-3.0-or-later
"""
The update protocol (dyndns2).

Clients authenticate with their username and the password of the host,
as there is one password per host. Commit to DB is done by the caller.
"""

import enum
import ipaddress
import logging
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from ddserver.db import utcnow
from ddserver.hosts import HostError, normalize_ipv4, normalize_ipv6
from ddserver.models import Host, User, UserStatus, Zone
from ddserver.passwords import hash_password, needs_rehash, verify_password

log = logging.getLogger(__name__)

# Limit of the original Dyn service
MAX_HOSTNAMES = 20


class ResponseCode(enum.StrEnum):
    GOOD = "good"
    NOCHG = "nochg"
    NOHOST = "nohost"
    NUMHOST = "numhost"
    BADAUTH = "badauth"
    BADAGENT = "badagent"
    SERVER_ERROR = "911"


@dataclass(frozen=True)
class Response:
    """The answer to a client: `good 192.0.2.1`, `badauth`, ..."""

    code: ResponseCode
    address: str | None = None
    # The host with the new address, for publishing it after the commit.
    changed: Host | None = field(default=None, compare=False)

    def __str__(self) -> str:
        return f"{self.code} {self.address}" if self.address else str(self.code)


def update_many(
    session: Session, username: str, password: str, hostnames: str, myip: str
) -> list[Response]:
    """Update each host in the comma-separated `hostnames`.

    Returns one response per host, in the same order. Each host is handled on its
    own, so with different passwords only some of them are updated.
    """
    names = hostnames.split(",")

    if len(names) > MAX_HOSTNAMES:
        return [Response(ResponseCode.NUMHOST)]

    return [update(session, username, password, name, myip) for name in names]


def update(
    session: Session, username: str, password: str, hostname: str, myip: str
) -> Response:
    """Set the addresses in `myip` for `hostname`, if `password` is its password.

    `myip` is an IPv4 or an IPv6 address, or one of each separated by a comma. An
    update for only one of the addresses does not change the other (if set).
    """
    if not username or not password:
        return Response(ResponseCode.BADAUTH)

    host = _find_host(session, username, hostname)

    # An unknown user is not told apart from an unknown host, as otherwise clients
    # could find out which usernames exist.
    if host is None:
        return Response(ResponseCode.NOHOST)

    if not verify_password(password, host.password):
        log.warning("wrong password for host %s.%s", host.name, host.zone.name)
        return Response(ResponseCode.BADAUTH)

    if host.user.status != UserStatus.ACTIVE:
        return Response(ResponseCode.BADAUTH)

    if needs_rehash(host.password):
        host.password = hash_password(password)

    return _set_addresses(host, myip)


def _find_host(session: Session, username: str, hostname: str) -> Host | None:
    """Return the host with the full name `hostname`, if it belongs to `username`."""
    name, _, zone = hostname.strip().lower().removesuffix(".").partition(".")

    return session.scalar(
        select(Host)
        .join(Host.zone)
        .join(Host.user)
        .where(
            User.username == username.strip().lower(),
            Host.name == name,
            Zone.name == zone,
        )
    )


def _set_addresses(host: Host, myip: str) -> Response:
    """Store the addresses in `myip`. Nothing is stored if any address is invalid."""
    try:
        addresses = _parse_addresses(myip)
    except HostError:
        return Response(ResponseCode.BADAGENT)

    text = ",".join(addresses.values())

    if all(getattr(host, attr) == value for attr, value in addresses.items()):
        return Response(ResponseCode.NOCHG, text)

    for attr, value in addresses.items():
        setattr(host, attr, value)

    host.updated = utcnow()

    return Response(ResponseCode.GOOD, text, host)


def _parse_addresses(myip: str) -> dict[str, str]:
    """Return the addresses in `myip` by attribute of `Host`.

    Raise `HostError` for an invalid address or two of the same protocol.
    """
    # Routers fill in both placeholders, and leave one empty without that protocol.
    entries = [entry for entry in myip.split(",") if entry.strip()]

    # Without any address, there is nothing to set. The address cannot be guessed,
    # this is up to the caller, who knows the address of the client.
    if not entries:
        raise HostError(f"Invalid address: {myip}")

    addresses = {}

    for entry in entries:
        attr, value = parse_address(entry)

        if attr in addresses:
            raise HostError(f"Invalid address: {myip}")

        addresses[attr] = value

    return addresses


def parse_address(address: str) -> tuple[str, str]:
    """Return the attribute of `Host` for `address`, and its canonical form."""
    if ":" not in address:
        return "ipv4", normalize_ipv4(address)

    ipv6 = normalize_ipv6(address)
    mapped = ipaddress.IPv6Address(ipv6).ipv4_mapped

    # Servers listening on both protocols see IPv4 clients in this form.
    return ("ipv4", str(mapped)) if mapped else ("ipv6", ipv6)
