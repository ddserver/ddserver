# SPDX-License-Identifier: AGPL-3.0-or-later

from sqlalchemy import select

from ddserver.models import User, UserStatus
from ddserver.passwords import verify_password
from ddserver.users import create_user


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

