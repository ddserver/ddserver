# SPDX-License-Identifier: AGPL-3.0-or-later
"""
User management.

Add, update, delete, list or authenticate users. Commit to DB is done by the caller.
"""

import functools
import hashlib
import re
import secrets

from itsdangerous import BadSignature, URLSafeTimedSerializer
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ddserver import hosts
from ddserver.dns import HostName
from ddserver.models import User, UserStatus
from ddserver.passwords import (
    hash_password,
    needs_rehash,
    verify_password,
)

USERNAME_PATTERN = re.compile(r"[a-z0-9][a-z0-9._-]{0,31}")
EMAIL_PATTERN = re.compile(r"[^@\s]+@[^@\s]+")
HOST_LIMIT_PATTERN = re.compile(r"[0-9]{1,6}")

ACTIVATION_DAYS = 7
RESET_MINUTES = 60


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
    user = User(
        **_check_available(session, username, email),
        password=hash_password(password),
        admin=admin,
        status=UserStatus.ACTIVE,
    )
    session.add(user)

    return user


def create_invited_user(session: Session, username: str, email: str) -> User:
    """Add a new user, who sets a password through the link in the activation mail."""
    user = User(
        **_check_available(session, username, email),
        status=UserStatus.ACTIVATION,
    )
    session.add(user)

    return user


def activation_token(secret_key: str, user: User) -> str:
    """Return the signed token for the activation link of `user`.

    It holds the email address and not the id: SQLite may give the id of a deleted user
    to a new user, whose account would then be open to the link of the old one.
    """
    return _serializer(secret_key, "activation").dumps(user.email)


def user_to_activate(session: Session, secret_key: str, token: str) -> User | None:
    """Return the user of an activation `token`, otherwise `None`.

    Nothing is stored about the token, it is the status of the user which makes the
    link work only once.
    """
    try:
        email = _serializer(secret_key, "activation").loads(
            token, max_age=ACTIVATION_DAYS * 24 * 60 * 60
        )
    except BadSignature:
        return None

    return session.scalar(
        select(User).where(User.email == email, User.status == UserStatus.ACTIVATION)
    )


def activate(user: User, password: str, min_length: int) -> None:
    """Set the first password of `user`, which makes the account active."""
    user.password = _hash_new_password(password, min_length)
    user.status = UserStatus.ACTIVE


def find_user(session: Session, login: str) -> User | None:
    """Return the user with this username or email address, if there is one."""
    login = login.strip().lower()

    return session.scalar(
        select(User).where((User.username == login) | (User.email == login))
    )


def reset_token(secret_key: str, user: User) -> str:
    """Return the signed token for the password reset link of `user`."""
    return _serializer(secret_key, "reset").dumps(
        [user.email, password_fingerprint(user)]
    )


def user_to_reset(session: Session, secret_key: str, token: str) -> User | None:
    """Return the user of a password reset `token`, otherwise `None`.

    The token holds a fingerprint of the password, so it stops working as soon as the
    password changes. This makes the link work only once.
    """
    try:
        email, fingerprint = _serializer(secret_key, "reset").loads(
            token, max_age=RESET_MINUTES * 60
        )
    except BadSignature:
        return None

    user = session.scalar(
        select(User).where(User.email == email, User.status == UserStatus.ACTIVE)
    )

    if user is None or password_fingerprint(user) != fingerprint:
        return None

    return user


def reset_password(user: User, password: str, min_length: int) -> None:
    """Replace the password of a user, who proved their identity by a reset link."""
    user.password = _hash_new_password(password, min_length)


def password_fingerprint(user: User) -> str:
    """Return a value which changes with the password, and does not reveal its hash."""
    return hashlib.sha256((user.password or "").encode()).hexdigest()


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


def delete_user(session: Session, user: User) -> list[HostName]:
    """Delete a user, unless it is the last admin. Returns the names of the deleted hosts."""
    _check_not_last_admin(session, user)
    deleted = hosts.delete_hosts_of_user(session, user)
    session.delete(user)

    return deleted


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


def change_password(
    user: User, current_password: str, new_password: str, min_length: int
) -> None:
    """Replace the password of a user, who has to know the current one."""
    if not verify_password(current_password, user.password):
        raise UserError("The current password is not correct")

    user.password = _hash_new_password(new_password, min_length)


def _check_available(session: Session, username: str, email: str) -> dict[str, str]:
    """Return `username` and `email` as they get stored, if nobody else has them."""
    username = normalize_username(username)
    email = normalize_email(email)

    if session.scalar(select(User).where(User.username == username)):
        raise UserError(f"The username {username} is already taken")

    if session.scalar(select(User).where(User.email == email)):
        raise UserError(f"The email address {email} is already in use")

    return {"username": username, "email": email}


def _serializer(secret_key: str, purpose: str) -> URLSafeTimedSerializer:
    # The salt keeps tokens of different purposes apart, with the same key.
    return URLSafeTimedSerializer(secret_key, salt=purpose)


def _hash_new_password(password: str, min_length: int) -> str:
    if len(password) < min_length:
        raise UserError(f"The new password must have at least {min_length} characters")

    return hash_password(password)


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
