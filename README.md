ddserver - A dynamic DNS service
================================

About
-----

ddserver is a server-side application for dynamic DNS.

It allows you to specify hostnames (subdomains) inside a dynamic DNS zone, and
to update the IPv4 address of those hostnames using the dyndns2 update protocol
(http://www.noip.com/integrate). This enables you to access hosts with dynamic
IP addresses by a static domain name, even if the IP address changes.

License
-------

ddserver is free software and can be redistributed and/or modified under the
terms of the GNU Affero General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your option) any
later version.

Run & Test
----------

```
uv run ddserver --config ddserver.toml run
uv run --isolated --python X.YZ pytest 
```
