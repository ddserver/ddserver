# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Publishing to the DNS server: RFC 2136 updates, signed with TSIG.

The database is the source of truth, so this happens after the commit. A failure
never reaches the client (decision 0003): it is logged, and repaired with
`ddserver dns sync --all`.
"""

import logging
from typing import NamedTuple

import dns.query
import dns.rcode
import dns.tsig
import dns.update

from ddserver.config import DnsConfig
from ddserver.models import Host

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

    Replacing RRsets gives the same result however often it is sent.
    """
    update = _new_update(config, host.zone.name)

    for rdtype, address in (("A", host.ipv4), ("AAAA", host.ipv6)):
        if address:
            update.replace(host.name, config.ttl, rdtype, address)
        else:
            update.delete(host.name, rdtype)

    return update


def build_delete(config: DnsConfig, host: HostName) -> dns.update.UpdateMessage:
    """Return the update which removes the records of `host`.

    Only `A` and `AAAA`, as ddserver does not touch anything else.
    """
    update = _new_update(config, host.zone)
    update.delete(host.name, "A")
    update.delete(host.name, "AAAA")

    return update


def publish_host(config: DnsConfig, host: Host) -> bool:
    """Send the records of `host`. Returns `False` if this failed."""
    return _try_send(
        config, str(HostName(host.name, host.zone.name)), build_update, host
    )


def delete_records(config: DnsConfig, hosts: list[HostName]) -> bool:
    """Remove the records of deleted `hosts`. Returns `False` if any of this failed."""
    results = [_try_send(config, str(h), build_delete, h) for h in hosts]

    return all(results)


def _try_send(config: DnsConfig, name: str, build, host: Host | HostName) -> bool:
    if not config.server:
        return True

    # Anything may go wrong here, also with the configured key. It must not turn a
    # stored change into an error for the client.
    try:
        _send(config, build(config, host))
    except Exception:
        log.exception("DNS update of %s failed", name)
        return False

    return True


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
