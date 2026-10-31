# SPDX-License-Identifier: AGPL-3.0-or-later
"""Database models: one class per table."""

import enum
from datetime import datetime

from sqlalchemy import Enum
from sqlalchemy.orm import Mapped, mapped_column

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
