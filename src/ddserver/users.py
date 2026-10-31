# SPDX-License-Identifier: AGPL-3.0-or-later
"""
User management.

Add, Update, or list users. Commit to DB is done by the caller.
"""

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from ddserver.models import User, UserStatus
from ddserver.passwords import hash_password

USERNAME_PATTERN = re.compile(r"[a-z0-9][a-z0-9._-]{0,31}")
EMAIL_PATTERN = re.compile(r"[^@\s]+@[^@\s]+")


class UserError(Exception):
    """User can not be created or changed."""


def normalize_username(username: str) -> str:
    """Return username in lowercase, raise UserError on invalid username."""
    username = username.strip().lower()

    if not USERNAME_PATTERN.fullmatch(username):
        raise UserError(
            "invalid username: use up to 32 letters, digits, '.', '_' or '-', "
            "starting with a letter or a digit"
        )

    return username


def normalize_email(email: str) -> str:
    """Return email in lowercase, raise UserError if email is invalid."""
    email = email.strip().lower()

    if not EMAIL_PATTERN.fullmatch(email):
        raise UserError("invalid email address")

    return email


def create_user(
    session: Session,
    username: str,
    email: str,
    password: str,
    admin: bool = False,
) -> User:
    """Add a new, activated user."""
    username = normalize_username(username)
    email = normalize_email(email)

    if session.scalar(select(User).where(User.username == username)):
        raise UserError(f"The username {username} is already taken")

    if session.scalar(select(User).where(User.email == email)):
        raise UserError(f"The email address {email} is already in use")

    user = User(
        username=username,
        email=email,
        password=hash_password(password),
        admin=admin,
        status=UserStatus.ACTIVE,
    )
    session.add(user)

    return user


def list_users(session: Session) -> list[User]:
    """Return all users, ordered by username."""
    return list(session.scalars(select(User).order_by(User.username)))
