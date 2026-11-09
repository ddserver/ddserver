# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Login, logout and access control.

The session is a cookie signed by Flask. It holds the id of the logged-in user and a
fingerprint of the password hash, so changing a password ends all other sessions of
that user. The logged-in user of the current request is available as `g.user`.
"""

import functools

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_wtf.csrf import CSRFError

from ddserver import mail, users
from ddserver.db import get_session
from ddserver.models import User, UserStatus

blueprint = Blueprint("auth", __name__)


def log_in(user: User) -> None:
    """Start a new session for `user`, replacing everything in the current one."""
    session.clear()
    session["user_id"] = user.id
    session["fingerprint"] = users.password_fingerprint(user)


def mail_url(endpoint: str, **values: str) -> str:
    """Return the full URL for a link in a mail.

    It comes from `web.base_url`, not from the request: whoever asks for a reset mail
    chooses the `Host` header, which would let them put their own site into the link.
    """
    base_url = current_app.extensions["ddserver.config"].web.base_url

    return base_url.rstrip("/") + url_for(endpoint, **values)


def send_activation_mail(user: User, template: str = "activation.txt") -> bool:
    """Send the link to choose a password to a user who is not activated yet."""
    config = current_app.extensions["ddserver.config"]
    token = users.activation_token(config.web.secret_key, user)

    return mail.send(
        config.mail,
        user.email,
        "Activate your ddserver account",
        template,
        username=user.username,
        url=mail_url("auth.activate", token=token),
        days=str(users.ACTIVATION_DAYS),
    )


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
        or session.get("fingerprint") != users.password_fingerprint(user)
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


@blueprint.get("/activate")
def activate():
    token = request.args.get("token", "")
    user = _user_to_activate(token)

    if user is None:
        return _invalid_activation_link()

    return render_template(
        "activate.html",
        user=user,
        token=token,
    )


@blueprint.post("/activate")
def activate_post():
    token = request.form.get("token", "")
    user = _user_to_activate(token)

    if user is None:
        return _invalid_activation_link()

    if not _store_new_password(users.activate, user):
        return redirect(url_for("auth.activate", token=token))

    flash("Your account has been activated, you can log in now.", "success")

    return redirect(url_for("public.index"))


@blueprint.get("/lostpass")
def lostpass():
    return render_template("lostpass.html")


@blueprint.post("/lostpass")
def lostpass_post():
    config = current_app.extensions["ddserver.config"]
    user = users.find_user(get_session(), request.form.get("login", ""))

    if user is not None and user.status == UserStatus.ACTIVE:
        token = users.reset_token(config.web.secret_key, user)
        mail.send(
            config.mail,
            user.email,
            "Reset your ddserver password",
            "reset.txt",
            username=user.username,
            url=mail_url("auth.reset", token=token),
            minutes=str(users.RESET_MINUTES),
        )

    # The same answer in any case, as this must not reveal who has an account.
    flash(
        "If this account exists, we have sent a link to reset the password to its "
        "email address.",
        "success",
    )

    return redirect(url_for("public.index"))


@blueprint.get("/lostpass/reset")
def reset():
    token = request.args.get("token", "")
    user = _user_to_reset(token)

    if user is None:
        return _invalid_reset_link()

    return render_template(
        "resetpass.html",
        user=user,
        token=token,
    )


@blueprint.post("/lostpass/reset")
def reset_post():
    token = request.form.get("token", "")
    user = _user_to_reset(token)

    if user is None:
        return _invalid_reset_link()

    if not _store_new_password(users.reset_password, user):
        return redirect(url_for("auth.reset", token=token))

    flash("Your password has been changed, you can log in now.", "success")

    return redirect(url_for("public.index"))


def _store_new_password(set_password, user: User) -> bool:
    """Apply the password of the form, or show what is wrong with it."""
    password = request.form.get("password", "")
    min_length = current_app.extensions["ddserver.config"].passwords.min_length

    if password != request.form.get("password_repeat", ""):
        flash("The passwords do not match.", "danger")
        return False

    try:
        set_password(user, password, min_length)
    except users.UserError as e:
        flash(f"{e}.", "danger")
        return False

    get_session().commit()

    return True


def _user_to_activate(token: str) -> User | None:
    config = current_app.extensions["ddserver.config"]

    return users.user_to_activate(get_session(), config.web.secret_key, token)


def _user_to_reset(token: str) -> User | None:
    config = current_app.extensions["ddserver.config"]

    return users.user_to_reset(get_session(), config.web.secret_key, token)


def _invalid_activation_link():
    flash(
        "This activation link is not valid, has already been used or has expired. "
        "Please contact an administrator.",
        "danger",
    )

    return redirect(url_for("public.index"))


def _invalid_reset_link():
    flash(
        "This link is not valid, has already been used or has expired. "
        "You can request a new one.",
        "danger",
    )

    return redirect(url_for("auth.lostpass"))
