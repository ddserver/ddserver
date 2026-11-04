# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Publishing to the DNS server: RFC 2136 updates, signed with TSIG.

The database is the source of truth, so this happens after the commit. A failure
never reaches the client, but gets logged and stored. The ddserver db and dns can
be synced later, using the cli - this is not exactly what the dyndns2 protocol
says, but it prevents clients from sending updates again and again, while the dns
server is not available.
"""

import logging
from typing import NamedTuple

import dns.query
import dns.rcode
import dns.tsig
import dns.update
from sqlalchemy import delete
from sqlalchemy.orm import Session

from ddserver.config import DnsConfig
from ddserver.models import DnsDeletion, Host

log = logging.getLogger(__name__)

TIMEOUT = 5


class DnsError(Exception):
    """The DNS server refused an update."""


class HostName(NamedTuple):
    """The name of a host, which remains known after the host has been deleted."""

    name: str
    zone: str

    def __str__(self) -> str:
        return f"{self.name}.{self.zone}"


def build_update(config: DnsConfig, host: Host) -> dns.update.UpdateMessage:
    """Return the update which makes DNS match `host`.

    Replacing RRsets gives the same result however often it is sent. Without the
    wildcard option, the wildcard records are deleted: they may be left from the time
    it was on.
    """
    update = _new_update(config, host.zone.name)
    wildcard = f"*.{host.name}"

    for rdtype, address in (("A", host.ipv4), ("AAAA", host.ipv6)):
        if address:
            update.replace(host.name, config.ttl, rdtype, address)
        else:
            update.delete(host.name, rdtype)

        if address and host.wildcard:
            update.replace(wildcard, config.ttl, rdtype, address)
        else:
            update.delete(wildcard, rdtype)

    return update


def build_delete(config: DnsConfig, host: HostName) -> dns.update.UpdateMessage:
    """Return the update which removes the records of `host`.

    Only `A` and `AAAA`, as ddserver does not touch anything else. Also those of the
    wildcard, which is not known any more after the host has been deleted.
    """
    update = _new_update(config, host.zone)

    for name in (host.name, f"*.{host.name}"):
        update.delete(name, "A")
        update.delete(name, "AAAA")

    return update


def publish_host(session: Session, config: DnsConfig, host: Host) -> bool:
    """Send the records of `host` and store the outcome. Returns `False` if this failed.

    Unlike other functions this commits, as it runs after the commit of the change.
    """
    if not config.server:
        return True

    revision = host.revision
    name = str(HostName(host.name, host.zone.name))
    error = _try_send(config, name, build_update, host)

    host.dns_error = error

    if error is None:
        host.published_revision = revision

    _store_outcome(session, name)

    return error is None


def delete_records(session: Session, config: DnsConfig, hosts: list[HostName]) -> bool:
    """Remove the records of deleted `hosts`. Return `False` if any record failed.

    What failed stays in `DnsDeletion` for the next sync. Commits like `publish_host`.
    """
    if not config.server:
        return True

    deleted = True

    for host in hosts:
        name = str(host)

        if _try_send(config, name, build_delete, host) is None:
            session.execute(delete(DnsDeletion).where(DnsDeletion.fqdn == name))
            _store_outcome(session, name)
        else:
            deleted = False

    return deleted


def _store_outcome(session: Session, name: str) -> None:
    # Without the outcome, the sync only does the same work again.
    try:
        session.commit()
    except Exception:
        log.exception("storing the DNS status of %s failed", name)
        session.rollback()


def _try_send(config: DnsConfig, name: str, build, host: Host | HostName) -> str | None:
    """Send an update, and return the error if it failed."""
    # Anything may go wrong here, also with the configured key. It must not turn a
    # stored change into an error for the client.
    try:
        _send(config, build(config, host))
    except Exception as e:
        log.exception("DNS update of %s failed", name)
        return str(e) or type(e).__name__

    return None


def _new_update(config: DnsConfig, zone: str) -> dns.update.UpdateMessage:
    update = dns.update.UpdateMessage(zone)
    update.use_tsig(
        dns.tsig.Key(config.key_name, config.key_secret, config.key_algorithm)
    )

    return update


def _send(config: DnsConfig, update: dns.update.UpdateMessage) -> None:
    response = dns.query.tcp(update, config.server, timeout=TIMEOUT, port=config.port)

    if response.rcode() != dns.rcode.NOERROR:
        raise DnsError(dns.rcode.to_text(response.rcode()))
