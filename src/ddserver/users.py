# SPDX-License-Identifier: AGPL-3.0-or-later
"""
User management.

Add, update, delete, list or authenticate users. Commit to DB is done by the caller.
"""

import functools
import re
import secrets

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ddserver import hosts
from ddserver.models import User, UserStatus
from ddserver.passwords import (
    PASSWORD_MIN_LENGTH,
    hash_password,
    needs_rehash,
    verify_password,
)

USERNAME_PATTERN = re.compile(r"[a-z0-9][a-z0-9._-]{0,31}")
EMAIL_PATTERN = re.compile(r"[^@\s]+@[^@\s]+")
HOST_LIMIT_PATTERN = re.compile(r"[0-9]{1,6}")


class UserError(Exception):
    """User can not be created or changed."""


def normalize_username(username: str) -> str:
    """Return `username` in lowercase, raise `UserError` on invalid `username`."""
    username = username.strip().lower()

    if not USERNAME_PATTERN.fullmatch(username):
        raise UserError(
            "invalid username: use up to 32 letters, digits, '.', '_' or '-', "
            "starting with a letter or a digit"
        )

    return username


def normalize_email(email: str) -> str:
    """Return `email` in lowercase, raise `UserError` if `email` is invalid."""
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


def parse_host_limit(value: str) -> int | None:
    """Return the `User.host_limit` for a number, 'default' or 'unlimited'.

    Raises `UserError` for anything else. An empty value means 'default'.
    """
    value = value.strip().lower()

    if value in ("", "default"):
        return None

    if value == "unlimited":
        return hosts.HOST_LIMIT_UNLIMITED

    if not HOST_LIMIT_PATTERN.fullmatch(value):
        raise UserError(
            "Invalid host limit: use a number up to 999999, 'default' or 'unlimited'"
        )

    return int(value)


def format_host_limit(user: User) -> str:
    """Return the host limit of `user` the way `parse_host_limit` reads it."""
    if user.host_limit is None:
        return "default"

    if user.host_limit >= hosts.HOST_LIMIT_UNLIMITED:
        return "unlimited"

    return str(user.host_limit)


def get_user(session: Session, username: str) -> User:
    """Return the user with this `username`, raise `UserError` if there is none."""
    username = username.strip().lower()
    user = session.scalar(select(User).where(User.username == username))

    if user is None:
        raise UserError(f"There is no user {username}")

    return user


def delete_user(session: Session, user: User) -> None:
    """Delete a user, unless it is the last admin."""
    _check_not_last_admin(session, user)
    hosts.delete_hosts_of_user(session, user)
    session.delete(user)


def set_admin(session: Session, user: User, admin: bool) -> None:
    """Grant or revoke the admin role. Never remove the last admin."""
    if not admin:
        _check_not_last_admin(session, user)

    user.admin = admin


def authenticate(session: Session, username: str, password: str) -> User | None:
    """Return the active user with these credentials, otherwise `None`.

    Replaces an outdated password hash, so the caller has to commit.
    """
    username = username.strip().lower()
    user = session.scalar(select(User).where(User.username == username))

    # Always verify a hash, even if there is none to check against.
    # Otherwise, the response time would reveal which usernames exist.
    password_hash = user.password if user and user.password else _dummy_hash()
    verified = verify_password(password, password_hash)

    if user is None or not verified or user.status != UserStatus.ACTIVE:
        return None

    if needs_rehash(password_hash):
        user.password = hash_password(password)

    return user


def change_password(user: User, current_password: str, new_password: str) -> None:
    """Replace the password of a user, who has to know the current one."""
    if not verify_password(current_password, user.password):
        raise UserError("The current password is not correct")

    if len(new_password) < PASSWORD_MIN_LENGTH:
        raise UserError(
            f"The new password must have at least {PASSWORD_MIN_LENGTH} characters"
        )

    user.password = hash_password(new_password)


def _check_not_last_admin(session: Session, user: User) -> None:
    """Raise `UserError` if `user` is the only admin who is able to log in."""
    if not user.admin or user.status != UserStatus.ACTIVE:
        return

    admins = session.scalar(
        select(func.count())
        .select_from(User)
        .where(User.admin, User.status == UserStatus.ACTIVE)
    )

    if admins == 1:
        raise UserError(f"{user.username} is the last admin")


@functools.cache
def _dummy_hash() -> str:
    """Return a hash that no password matches (created on first use)."""
    return hash_password(secrets.token_hex(32))
