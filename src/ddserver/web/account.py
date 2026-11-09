# SPDX-License-Identifier: AGPL-3.0-or-later
"""The account page of the logged-in user."""

from flask import (
    Blueprint,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from ddserver import dns, mail, users
from ddserver.db import get_session
from ddserver.web.auth import log_in, login_required, mail_url

blueprint = Blueprint("account", __name__, url_prefix="/account")


@blueprint.get("")
@login_required
def index():
    signup = current_app.extensions["ddserver.config"].signup
    domains = signup.domains if signup.mode == "restricted" else ()

    return render_template("account.html", signup_domains=domains)


@blueprint.post("/password")
@login_required
def change_password():
    new_password = request.form.get("new_password", "")

    if new_password != request.form.get("new_password_repeat", ""):
        flash("The new passwords do not match.", "danger")
        return redirect(url_for("account.index"))

    try:
        users.change_password(
            g.user,
            request.form.get("current_password", ""),
            new_password,
            current_app.extensions["ddserver.config"].passwords.min_length,
        )
    except users.UserError as e:
        flash(f"{e}.", "danger")
        return redirect(url_for("account.index"))

    get_session().commit()

    # The password hash has changed, which ends all sessions: keep this one.
    log_in(g.user)
    flash("Your password has been changed.", "success")

    return redirect(url_for("account.index"))


@blueprint.post("/email")
@login_required
def change_email():
    config = current_app.extensions["ddserver.config"]

    try:
        new_email = users.request_email_change(
            g.user,
            request.form.get("current_password", ""),
            request.form.get("email", ""),
            config.signup,
        )
    except users.UserError as e:
        flash(f"{e}.", "danger")
        return redirect(url_for("account.index"))

    token = users.email_change_token(config.web.secret_key, g.user, new_email)
    sent = mail.send(
        config.mail,
        new_email,
        "Confirm your new email address",
        "email_confirm.txt",
        username=g.user.username,
        url=mail_url("account.confirm_email", token=token),
        hours=str(users.EMAIL_CHANGE_HOURS),
    )

    if sent:
        flash(
            f"We have sent a mail to {new_email}. Your email address changes once you "
            "follow the link in it.",
            "success",
        )
    else:
        flash("The confirmation mail could not be sent.", "danger")

    return redirect(url_for("account.index"))


# No login needed: the link in the mail is enough, also in another browser.
@blueprint.get("/email/confirm")
def confirm_email():
    return render_template("email_confirm.html", token=request.args.get("token", ""))


@blueprint.post("/email/confirm")
def confirm_email_post():
    db_session = get_session()
    config = current_app.extensions["ddserver.config"]

    try:
        user, old_email = users.change_email(
            db_session, config.web.secret_key, request.form.get("token", "")
        )
    except users.UserError as e:
        flash(f"{e}.", "danger")
        return redirect(url_for("public.index"))

    db_session.commit()

    # In case this was not the user: the old address learns about it.
    mail.send(
        config.mail,
        old_email,
        "Your email address has been changed",
        "email_changed.txt",
        username=user.username,
        email=user.email,
    )
    flash(f"Your email address is now {user.email}.", "success")

    return redirect(url_for("public.index"))


@blueprint.post("/delete")
@login_required
def delete():
    db_session = get_session()

    try:
        deleted = users.delete_user(db_session, g.user)
    except users.UserError as e:
        flash(f"{e}.", "danger")
        return redirect(url_for("account.index"))

    db_session.commit()
    config = current_app.extensions["ddserver.config"]
    dns.delete_records(db_session, config.dns, deleted)
    session.clear()
    flash("Your account has been deleted.", "success")

    return redirect(url_for("public.index"))
