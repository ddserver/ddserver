ddserver - A dynamic DNS service
================================

ddserver is a self-hosted dynamic DNS service. Users add hostnames in your DNS
zones and update their addresses with the dyndns2 protocol (routers, ddclient,
curl). ddserver publishes the changes to your DNS server by dynamic updates
(RFC 2136).


Features
--------

* Web interface for users and admins
* IPv4 and IPv6, optional wildcard per hostname
* A separate password per hostname
* Sign-up: open, restricted to mail domains, or closed; optional admin approval
* Any DNS server with TSIG-signed dynamic updates; failed updates are retried
* Command line for administration
* Import from ddserver 0.3


Documentation
-------------

* [Installation](docs/installation.md)
* [DNS server setup](docs/dns.md)
* [Update clients](docs/clients.md)


Development
-----------

Python 3.12 or newer, [uv](https://docs.astral.sh/uv/).

Clone this repository, and run the following.

```sh
cp ddserver.example.toml ddserver.toml   # set secret_key, base_url,
                                         # url = "sqlite:///ddserver.db"
uv run ddserver --config ddserver.toml db upgrade
uv run ddserver --config ddserver.toml user add --admin USERNAME EMAIL
uv run ddserver --config ddserver.toml run --debug
```

To run tests, you can do something like this:
```sh
uv run pytest
uv run --isolated --python X.YZ pytest
uv run ruff check
uv run ruff format
```


License
-------

ddserver is free software and can be redistributed and/or modified under the
terms of the GNU Affero General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your option) any
later version.

