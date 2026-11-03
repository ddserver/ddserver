# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Load and validate the config file.

The configuration is written in TOML. Its structure is described by the dataclasses
below: every section is a dataclass, every option a field. A field without a
default value is required.
"""

import dataclasses
import tomllib
import typing
from dataclasses import dataclass
from pathlib import Path

DEFAULT_PATH = Path("/etc/ddserver/ddserver.toml")


class ConfigError(Exception):
    """The configuration file cannot be read or is invalid."""


@dataclass(frozen=True)
class WebConfig:
    secret_key: str
    # Public address of ddserver, for links in mails.
    base_url: str
    # Number of reverse proxies in front of ddserver,
    # whose `X-Forwarded-*` headers are trusted.
    proxies: int = 0

    def __post_init__(self):
        if not self.base_url.startswith(("http://", "https://")):
            raise ConfigError("web.base_url: expected http:// or https://")

        if self.proxies < 0:
            raise ConfigError("web.proxies: expected 0 or more")


@dataclass(frozen=True)
class DatabaseConfig:
    # A relative SQLite path is relative to the current working directory.
    url: str = "sqlite:///ddserver.db"


@dataclass(frozen=True)
class PasswordConfig:
    # Minimum length of new passwords for users and hosts.
    min_length: int = 10

    def __post_init__(self):
        if self.min_length < 1:
            raise ConfigError("passwords.min_length: expected at least 1")


@dataclass(frozen=True)
class HostsConfig:
    # Names which users cannot register.
    reserved: tuple[str, ...] = ()
    # Number of hosts per user, unless an admin sets another limit for that user.
    default_limit: int = 5


@dataclass(frozen=True)
class DnsConfig:
    # Address of the primary DNS server. Without one, nothing is published.
    server: str = ""
    port: int = 53
    key_name: str = ""
    key_secret: str = ""
    key_algorithm: str = "hmac-sha256"
    ttl: int = 60


@dataclass(frozen=True)
class MailConfig:
    # Address in the `From` header. Without one, no mail can be sent.
    sender: str = ""
    host: str = "localhost"
    port: int = 587
    # `starttls`, `tls` or `none`.
    security: str = "starttls"
    # Without a username, no login is attempted.
    username: str = ""
    password: str = ""

    def __post_init__(self):
        # A typo must not end up as mail without encryption.
        if self.security not in ("starttls", "tls", "none"):
            raise ConfigError("mail.security: expected starttls, tls or none")


@dataclass(frozen=True)
class Config:
    web: WebConfig
    database: DatabaseConfig
    passwords: PasswordConfig
    hosts: HostsConfig
    dns: DnsConfig
    mail: MailConfig


def load_config(path: Path) -> Config:
    """Read the configuration file at `path` and return it as a `Config`.

    Raises `ConfigError` with a message naming the offending option if the file
    cannot be read, is not valid TOML or does not match the expected structure.
    """
    try:
        with path.open("rb") as file:
            data = tomllib.load(file)

    except OSError as e:
        raise ConfigError(f"{path}: cannot read file: {e.strerror}") from e

    except tomllib.TOMLDecodeError as e:
        raise ConfigError(f"{path}: invalid TOML: {e}") from e

    return _build(Config, data, prefix="")


def _build(cls, data: dict, prefix: str):
    """Create an instance of the dataclass `cls` from the TOML table `data`.

    prefix: the dotted name of the table (e.g. "web"), used in error messages.
    """
    fields = {field.name: field for field in dataclasses.fields(cls)}
    types = typing.get_type_hints(cls)

    for key in data.keys() - fields.keys():
        kind = "option" if prefix else "section"
        raise ConfigError(f"{_name(prefix, key)}: unknown {kind}")

    values = {}
    for name, field in fields.items():
        if name in data:
            values[name] = _convert(types[name], data[name], _name(prefix, name))

        elif dataclasses.is_dataclass(types[name]):
            # A missing section is treated as empty, so that its own defaults apply
            # and missing required options are reported by name.
            values[name] = _build(types[name], {}, _name(prefix, name))

        elif field.default is dataclasses.MISSING:
            raise ConfigError(f"{_name(prefix, name)}: missing required value")

    return cls(**values)


def _convert(expected: type, value, name: str):
    """Check that `value` has the expected type, and return it."""
    if dataclasses.is_dataclass(expected):
        if not isinstance(value, dict):
            raise ConfigError(f"{name}: expected a section, got a value")

        return _build(expected, value, name)

    if expected in (str, int, bool):
        if type(value) is not expected:
            raise ConfigError(
                f"{name}: expected {expected.__name__}, got {type(value).__name__}"
            )

        return value

    if expected == tuple[str, ...]:
        if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
            raise ConfigError(f"{name}: expected a list of strings")

        return tuple(value)

    raise TypeError(f"unsupported type in configuration declaration: {expected!r}")


def _name(prefix: str, key: str) -> str:
    return f"{prefix}.{key}" if prefix else key
