# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Hashing and verification of passwords (argon2).

Hashes from ddserver<=0.3 (sha512_crypt) still work, but get replaced
by argon2 after the next successful verification.
"""

import logging

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

log = logging.getLogger(__name__)

LEGACY_PREFIX = "$6$"

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

    if password_hash.startswith(LEGACY_PREFIX):
        return _verify_legacy(password, password_hash)

    try:
        return _hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False
    except InvalidHashError:
        log.warning("unsupported password hash format: %.10s...", password_hash)
        return False


def needs_rehash(password_hash: str) -> bool:
    """Return whether a password rehash should take place after successful login."""
    return password_hash.startswith(LEGACY_PREFIX) or _hasher.check_needs_rehash(
        password_hash
    )


def _verify_legacy(password: str, password_hash: str) -> bool:
    # Support ddserver 0.2 and 0.3-dev password hashed (sha512_crypt)
    # Imported here, as new installations have no such hashes.
    try:
        from passlib.hash import sha512_crypt
    except ImportError:
        log.warning(
            "passlib import failed. unable to verify ddserver<=0.3 password hashes."
        )
        return False

    try:
        return sha512_crypt.verify(password, password_hash)
    except ValueError:
        log.warning("unsupported password hash format: %.10s...", password_hash)
        return False
