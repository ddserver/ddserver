# SPDX-License-Identifier: AGPL-3.0-or-later
"""
The update protocol (dyndns2).

Clients authenticate with their username and the password of the host,
as there is one password per host. Commit to DB is done by the caller.
"""

import enum
import logging
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from ddserver.db import utcnow
from ddserver.hosts import HostError, normalize_ipv4, normalize_ipv6
from ddserver.models import Host, User, UserStatus, Zone
from ddserver.passwords import hash_password, needs_rehash, verify_password

log = logging.getLogger(__name__)


class ResponseCode(enum.StrEnum):
    GOOD = "good"
    NOCHG = "nochg"
    NOHOST = "nohost"
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


def update(
    session: Session, username: str, password: str, hostname: str, address: str
) -> Response:
    """Set `address` for `hostname`, if `password` is the password of this host."""
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

    return _set_address(host, address)


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


def _set_address(host: Host, address: str) -> Response:
    """Store `address` as the IPv4 or IPv6 address of `host`."""
    field = "ipv6" if ":" in address else "ipv4"

    try:
        address = (
            normalize_ipv6(address) if field == "ipv6" else normalize_ipv4(address)
        )
    except HostError:
        return Response(ResponseCode.BADAGENT)

    # An empty address has nothing to set. The address cannot be guessed,
    # this is up to the caller, who knows the address of the client.
    if address is None:
        return Response(ResponseCode.BADAGENT)

    if getattr(host, field) == address:
        return Response(ResponseCode.NOCHG, address)

    setattr(host, field, address)
    host.updated = utcnow()

    return Response(ResponseCode.GOOD, address, host)
