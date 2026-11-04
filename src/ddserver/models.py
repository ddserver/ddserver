# SPDX-License-Identifier: AGPL-3.0-or-later
"""Database models: one class per table."""

import enum
from datetime import datetime

from sqlalchemy import Enum, ForeignKey, UniqueConstraint, false
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ddserver.db import Base, UTCDateTime, utcnow


class UserStatus(enum.StrEnum):
    APPROVAL = "approval"
    ACTIVATION = "activation"
    ACTIVE = "active"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    email: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str | None]
    admin: Mapped[bool] = mapped_column(default=False)
    status: Mapped[UserStatus] = mapped_column(Enum(UserStatus, native_enum=False))
    host_limit: Mapped[int | None]
    created: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)


class Zone(Base):
    __tablename__ = "zones"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    created: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)


class Host(Base):
    __tablename__ = "hosts"
    __table_args__ = (UniqueConstraint("zone_id", "name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    # RESTRICT: hosts are deleted by `ddserver.hosts`, never by the database.
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    zone_id: Mapped[int] = mapped_column(ForeignKey("zones.id", ondelete="RESTRICT"))
    name: Mapped[str]
    password: Mapped[str]
    description: Mapped[str | None]
    ipv4: Mapped[str | None]
    ipv6: Mapped[str | None]
    # Also publish the addresses for `*.<name>.<zone>`.
    wildcard: Mapped[bool] = mapped_column(default=False, server_default=false())
    # A host has to be published as long as these two differ.
    revision: Mapped[int] = mapped_column(default=1, server_default="1")
    published_revision: Mapped[int] = mapped_column(default=0, server_default="0")
    dns_error: Mapped[str | None]
    updated: Mapped[datetime | None] = mapped_column(UTCDateTime)
    created: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

    # Not database columns: these load the related object on first access.
    user: Mapped[User] = relationship()
    zone: Mapped[Zone] = relationship()


class DnsDeletion(Base):
    """The records of a deleted host, as long as they may still be in DNS."""

    __tablename__ = "dns_deletions"

    id: Mapped[int] = mapped_column(primary_key=True)
    fqdn: Mapped[str] = mapped_column(unique=True)
    # The error of the last attempt to delete the records.
    error: Mapped[str | None]
    created: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
