# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Hashing and verification of passwords (argon2), and rules for new passwords.

Hashes from ddserver<=0.3 (sha512_crypt) still work, but get replaced
by argon2 after the next successful verification.
"""

import logging
from string import digits, punctuation

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

log = logging.getLogger(__name__)

LEGACY_PREFIX = "$6$"

MIN_DIFFERENT_CHARACTERS = 5
# Shorter usernames are part of too many passwords by chance.
MIN_USERNAME_MATCH = 3
# Also found in reverse order and repeated, and starting anywhere.
SEQUENCES = (
    "abcdefghijklmnopqrstuvwxyz",
    "0123456789",
    "qwertzuiop",
    "qwertyuiop",
    "asdfghjkl",
    "yxcvbnm",
    "zxcvbnm",
)
# In lowercase and without digits or punctuation at the end.
COMMON_PASSWORDS = frozenset(
    {
        "admin",
        "administrator",
        "changeme",
        "ddserver",
        "default",
        "dragon",
        "dyndns",
        "fritzbox",
        "geheim",
        "hallo",
        "iloveyou",
        "internet",
        "letmein",
        "login",
        "master",
        "monkey",
        "password",
        "passwort",
        "router",
        "secret",
        "sommer",
        "summer",
        "test",
        "testtest",
        "welcome",
        "willkommen",
        "winter",
    }
)

_hasher = PasswordHasher()


class PasswordError(Exception):
    """A password is too simple."""


def hash_password(password: str) -> str:
    """Return a new hash for a given password."""
    return _hasher.hash(password)


def check_password(
    password: str, min_length: int, username: str = "", email: str = ""
) -> None:
    """Raise `PasswordError` if `password` is too simple to be set as a new password.

    Existing passwords are not affected, this is only about setting one.
    """
    if len(password) < min_length:
        raise PasswordError(f"The password must have at least {min_length} characters")

    lowered = password.lower()

    if len(set(lowered)) < MIN_DIFFERENT_CHARACTERS:
        raise PasswordError(
            "The password must have at least "
            f"{MIN_DIFFERENT_CHARACTERS} different characters"
        )

    if any(lowered in row * 3 or lowered in row[::-1] * 3 for row in SEQUENCES):
        raise PasswordError("The password must not be a simple sequence of characters")

    # `password123!` is no better than `password`.
    if lowered.rstrip(digits + punctuation) in COMMON_PASSWORDS:
        raise PasswordError("This password is too common")

    if len(username) >= MIN_USERNAME_MATCH and username.lower() in lowered:
        raise PasswordError("The password must not contain your username")

    if email and lowered == email.lower():
        raise PasswordError("The password must not be your email address")


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
