# SPDX-License-Identifier: AGPL-3.0-or-later
"""Sign-up: new users choose a username and get an activation mail."""

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)

from ddserver import mail, users
from ddserver.config import SignupConfig
from ddserver.db import get_session
from ddserver.models import User, UserStatus
from ddserver.web.auth import honeypot_filled, mail_url, send_activation_mail

blueprint = Blueprint("signup", __name__)


@blueprint.before_request
def check_signup_open():
    if _config().mode == "closed":
        abort(404)

    if g.user:
        return redirect(url_for("public.index"))


@blueprint.get("/signup")
def signup():
    return _render_form()


@blueprint.post("/signup")
def signup_post():
    db_session = get_session()
    username = request.form.get("username", "")
    email = request.form.get("email", "")

    # Spam protection.
    # A bot gets the answer for a successful sign-up, but nothing is stored or sent.
    if honeypot_filled():
        _flash_signed_up()
        return redirect(url_for("public.index"))

    if not users.email_domain_allowed(email, _config()):
        flash("Please use an email address from one of the listed domains.", "danger")
        return _render_form(username, email)

    try:
        # The username first: otherwise, the answer for a taken username would tell
        # whether the email address has an account.
        users.check_username_available(db_session, username)
        existing = users.get_user_by_email(db_session, email)

        if existing is None:
            _sign_up(username, email)
        else:
            _send_to_existing_user(existing)

    except users.UserError as e:
        flash(f"{e}.", "danger")
        return _render_form(username, email)

    # The same answer for a known email address, as this must not reveal who has an
    # account. The mail tells the owner of the address what to do.
    _flash_signed_up()

    return redirect(url_for("public.index"))


def _flash_signed_up() -> None:
    if _config().approval:
        flash(
            "Thank you for signing up. An admin will review your request, then you "
            "will get a mail with a link to activate your account.",
            "success",
        )
    else:
        flash(
            "We have sent a mail to your email address. Please follow the link in it "
            "to activate your account.",
            "success",
        )


def _sign_up(username: str, email: str) -> None:
    db_session = get_session()
    approval = _config().approval
    user = users.create_invited_user(db_session, username, email, approval)
    db_session.commit()

    if not approval:
        send_activation_mail(user)

    if _config().notify_admins:
        _notify_admins(user)


def _notify_admins(user: User) -> None:
    config = current_app.extensions["ddserver.config"]

    if user.status == UserStatus.APPROVAL:
        template = "signup_approval.txt"
    else:
        template = "signup_notification.txt"

    for admin in users.list_admins(get_session()):
        mail.send(
            config.mail,
            admin.email,
            f"New ddserver sign-up: {user.username}",
            template,
            username=user.username,
            email=user.email,
            url=mail_url("admin.users"),
        )


def _config() -> SignupConfig:
    return current_app.extensions["ddserver.config"].signup


def _render_form(username: str = "", email: str = ""):
    config = _config()
    domains = config.domains if config.mode == "restricted" else ()

    return render_template(
        "signup.html", username=username, email=email, signup_domains=domains
    )


def _send_to_existing_user(user: User) -> None:
    # Still waiting for an admin: the mail follows with the approval.
    if user.status == UserStatus.APPROVAL:
        return

    # The mail names the existing username, as it may differ from the one entered.
    if user.status == UserStatus.ACTIVATION:
        send_activation_mail(user, "activation_pending.txt")
        return

    config = current_app.extensions["ddserver.config"]
    mail.send(
        config.mail,
        user.email,
        "Your ddserver account",
        "account_exists.txt",
        username=user.username,
        url=mail_url("auth.lostpass"),
    )
