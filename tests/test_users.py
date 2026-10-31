# SPDX-License-Identifier: AGPL-3.0-or-later

import pytest
from argon2 import PasswordHasher
from sqlalchemy import select

from ddserver.models import User, UserStatus
from ddserver.passwords import needs_rehash, verify_password
from ddserver.users import UserError, authenticate, change_password, create_user


def test_create_user(session):
    create_user(session, "john", "john.doe@example.org", "secret")
    session.commit()

    user = session.scalars(select(User)).one()
    assert user.username == "john"
    assert user.email == "john.doe@example.org"
    assert verify_password("secret", user.password)
    assert user.status == UserStatus.ACTIVE
    assert not user.admin


def test_create_admin(session):
    user = create_user(session, "john", "john.doe@example.org", "secret", admin=True)

    assert user.admin


def test_username_and_email_normalized(session):
    user = create_user(session, " John ", " John.Doe@Example.ORG ", "secret")

    assert user.username == "john"
    assert user.email == "john.doe@example.org"


@pytest.mark.parametrize("username", ["john", "j0hn", "j.o_h-n", "a" * 32])
def test_valid_username(session, username):
    assert create_user(session, username, "john.doe@example.org", "secret")


@pytest.mark.parametrize(
    "username", ["", "-john", ".john", "jo:hn", "jo hn", "jöhn", "a" * 33]
)
def test_invalid_username(session, username):
    with pytest.raises(UserError, match="invalid username"):
        create_user(session, username, "john.doe@example.org", "secret")


def test_duplicate_username(session):
    create_user(session, "john", "john.doe@example.org", "secret")

    with pytest.raises(UserError, match="already taken"):
        create_user(session, "John", "john@example.org", "secret")


@pytest.mark.parametrize(
    "email",
    ["", "john", "john@", "@example.org", "john@@example.org", "jo hn@example.org"],
)
def test_invalid_email(session, email):
    with pytest.raises(UserError, match="invalid email address"):
        create_user(session, "john", email, "secret")


def test_duplicate_email(session):
    create_user(session, "john", "john.doe@example.org", "secret")

    with pytest.raises(UserError, match="already in use"):
        create_user(session, "jd", "John.Doe@example.org", "secret")


def test_authenticate(session):
    user = create_user(session, "john", "john.doe@example.org", "secret")
    session.commit()

    assert authenticate(session, "john", "secret") is user


def test_authenticate_normalizes_username(session):
    user = create_user(session, "john", "john.doe@example.org", "secret")
    session.commit()

    assert authenticate(session, " John ", "secret") is user


def test_authenticate_wrong_password(session):
    create_user(session, "john", "john.doe@example.org", "secret")
    session.commit()

    assert authenticate(session, "john", "wrong") is None


def test_authenticate_unknown_user(session):
    assert authenticate(session, "john", "secret") is None


@pytest.mark.parametrize("status", [UserStatus.APPROVAL, UserStatus.ACTIVATION])
def test_authenticate_inactive_user(session, status):
    user = create_user(session, "john", "john.doe@example.org", "secret")
    user.status = status
    session.commit()

    assert authenticate(session, "john", "secret") is None


def test_authenticate_user_without_password(session):
    user = create_user(session, "john", "john.doe@example.org", "secret")
    user.password = None
    session.commit()

    assert authenticate(session, "john", "") is None


def test_authenticate_replaces_outdated_hash(session):
    user = create_user(session, "john", "john.doe@example.org", "secret")
    user.password = PasswordHasher(time_cost=1).hash("secret")
    session.commit()

    assert authenticate(session, "john", "secret") is user
    assert not needs_rehash(user.password)
    assert verify_password("secret", user.password)


def test_change_password(session):
    user = create_user(session, "john", "john.doe@example.org", "secret")

    change_password(user, "secret", "a new password")

    assert verify_password("a new password", user.password)
    assert not verify_password("secret", user.password)


def test_change_password_needs_current_password(session):
    user = create_user(session, "john", "john.doe@example.org", "secret")

    with pytest.raises(UserError, match="current password"):
        change_password(user, "wrong", "a new password")

    assert verify_password("secret", user.password)


def test_new_password_too_short(session):
    user = create_user(session, "john", "john.doe@example.org", "secret")

    with pytest.raises(UserError, match="at least 8 characters"):
        change_password(user, "secret", "short")

    assert verify_password("secret", user.password)
