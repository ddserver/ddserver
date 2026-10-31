# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Login, logout and access control.

The session is a cookie signed by Flask. It holds the id of the logged-in user and a
fingerprint of the password hash, so changing a password ends all other sessions of
that user. The logged-in user of the current request is available as `g.user`.
"""

import functools
import hashlib

from flask import (
    Blueprint,
    abort,
    flash,
    g,
    redirect,
    request,
    session,
    url_for,
)
from flask_wtf.csrf import CSRFError

from ddserver import users
from ddserver.db import get_session
from ddserver.models import User, UserStatus

blueprint = Blueprint("auth", __name__)


def log_in(user: User) -> None:
    """Start a new session for `user`, replacing everything in the current one."""
    session.clear()
    session["user_id"] = user.id
    session["fingerprint"] = _fingerprint(user)


def _fingerprint(user: User) -> str:
    return hashlib.sha256((user.password or "").encode()).hexdigest()


def login_required(view):
    """Send visitors who are not logged in to the start page."""

    @functools.wraps(view)
    def wrapper(*args, **kwargs):
        if g.user is None:
            flash("Please log in first.", "warning")
            return redirect(url_for("public.index"))

        return view(*args, **kwargs)

    return wrapper


def admin_required(view):
    """Allow only admins: others get `403 Forbidden`."""

    @functools.wraps(view)
    @login_required
    def wrapper(*args, **kwargs):
        if not g.user.admin:
            abort(403)

        return view(*args, **kwargs)

    return wrapper


@blueprint.before_app_request
def load_user():
    """Set `g.user` and end sessions which are not valid anymore."""
    g.user = None

    user_id = session.get("user_id")
    if user_id is None:
        return

    user = get_session().get(User, user_id)

    if (
        user is None
        or user.status != UserStatus.ACTIVE
        or session.get("fingerprint") != _fingerprint(user)
    ):
        session.clear()
        return

    g.user = user


@blueprint.app_errorhandler(CSRFError)
def csrf_error(error: CSRFError):
    # Usually a form which was open for too long, as CSRF tokens expire.
    flash("Your session has expired, please try again.", "warning")
    return redirect(url_for("public.index"))


@blueprint.post("/login")
def login():
    db_session = get_session()
    user = users.authenticate(
        db_session,
        request.form.get("username", ""),
        request.form.get("password", ""),
    )

    if user is None:
        flash("Wrong username or password.", "danger")
        return redirect(url_for("public.index"))

    db_session.commit()
    log_in(user)

    return redirect(url_for("public.index"))


@blueprint.post("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")

    return redirect(url_for("public.index"))
