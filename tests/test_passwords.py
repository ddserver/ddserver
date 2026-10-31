# SPDX-License-Identifier: AGPL-3.0-or-later

import pytest
from argon2 import PasswordHasher

from ddserver.passwords import hash_password, needs_rehash, verify_password


def test_correct_password_matches():
    password_hash = hash_password("secret")

    assert verify_password("secret", password_hash)


def test_wrong_password_does_not_match():
    password_hash = hash_password("secret")

    assert not verify_password("wrong", password_hash)


def test_same_password_gives_different_hashes():
    # Every hash gets its own random salt.
    assert hash_password("secret") != hash_password("secret")


@pytest.mark.parametrize(
    "password_hash",
    [
        None,
        "",
        "not a hash",
        "$6$rounds=5000$salt$hash",  # sha512_crypt from ddserver 0.3
    ],
)
def test_missing_or_unknown_hash_does_not_match(password_hash):
    assert not verify_password("secret", password_hash)


def test_new_hash_needs_no_rehash():
    assert not needs_rehash(hash_password("secret"))


def test_hash_with_other_parameters_needs_rehash():
    old_hash = PasswordHasher(time_cost=1).hash("secret")

    assert verify_password("secret", old_hash)
    assert needs_rehash(old_hash)
