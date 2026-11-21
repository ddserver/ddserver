# DNS server setup

Starting with version 1.0.0, ddserver sends dynamic updates (RFC 2136, 
over TCP) signed with a TSIG key to the primary DNS server of each zone.
It only changes `A` and `AAAA` records of its hostnames and of their 
wildcards (`*.name`).

Tested with PowerDNS 5. Other servers work if they accept such updates; see
their documentation.

## PowerDNS

`pdns.conf`, then restart:

```ini
dnsupdate=yes
dnsupdate-require-tsig=yes
```

Add your zone(s) to PowerDNS, allow the IP address of ddserver (`/128` for IPv6) to send updates, and configure a TSIG key:

```sh
pdnsutil zone create dyn.example.org
pdnsutil metadata set dyn.example.org ALLOW-DNSUPDATE-FROM 192.0.2.10/32
pdnsutil tsigkey generate ddserver hmac-sha512
pdnsutil metadata add dyn.example.org TSIG-ALLOW-DNSUPDATE ddserver
```

The `pdnsutil tsigkey` command prints the base64 secret, which needs to be set in the ddserver.toml configuration file.

The zone needs NS records and a delegation in its parent zone, for example with
the name servers `ns1.example.org` and `ns2.example.org`:

```sh
pdnsutil rrset add dyn.example.org @ NS ns1.example.org. ns2.example.org.
```

The SOA serial increases with each update by itself.

Secondaries: a `NATIVE` zone relies on the replication of the database backend.
For AXFR, make the zone `PRIMARY`, set `primary=yes`, and
`pdnsutil metadata set dyn.example.org NOTIFY-DNSUPDATE 1`.

## ddserver

```toml
[dns]
server = "192.0.2.53"          # address of the primary, not a name
key_name = "ddserver"
key_secret = "<base64 secret>"
key_algorithm = "hmac-sha512"  # as generated, default is hmac-sha256
```

```sh
ddserver zone add dyn.example.org
```

## Check

Add a hostname in the web interface, then:

```sh
dig +short @192.0.2.53 myhost.dyn.example.org A
```

Admins see changes which have not reached DNS yet on the page *DNS*.
The timer retries them periodically; `ddserver dns sync` does it at once.

## Errors

In the log (`journalctl -u ddserver -u ddserver-dns-sync`) and on the page *DNS*:

- `REFUSED` – key not allowed for the zone, or address of ddserver not allowed.
- `NOTAUTH` – server not authoritative for the zone, or key unknown.
- `BADSIG`, `The TSIG signature fails to verify` – wrong secret or algorithm.
- `Connection refused`, timeout – wrong address or port; TCP port 53 must be
  reachable.
