# SPDX-License-Identifier: AGPL-3.0-or-later

from ddserver.passwords import hash_password, verify_password


def test_correct_password_matches():
    password_hash = hash_password("secret")

    assert verify_password("secret", password_hash)


def test_wrong_password_does_not_match():
    password_hash = hash_password("secret")

    assert not verify_password("wrong", password_hash)


def test_same_password_gives_different_hashes():
    # Every hash gets its own random salt.
    assert hash_password("secret") != hash_password("secret")

