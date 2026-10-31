# SPDX-License-Identifier: AGPL-3.0-or-later
"""Hashing and verification of passwords (argon2)."""

import logging

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

log = logging.getLogger(__name__)

PASSWORD_MIN_LENGTH = 8

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Return a new hash for a given password."""
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    """Check `password` against a stored `password_hash`.

    A missing hash (a user who has not set a password) never matches.
    """
    if password_hash is None:
        return False

    try:
        return _hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False
    except InvalidHashError:
        log.warning("unsupported password hash format: %.10s...", password_hash)
        return False


def needs_rehash(password_hash: str) -> bool:
    """Return whether a password rehash should take place after successful login."""
    return _hasher.check_needs_rehash(password_hash)
