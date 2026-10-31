# SPDX-License-Identifier: AGPL-3.0-or-later
"""The account page of the logged-in user."""

from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from ddserver import users
from ddserver.db import get_session
from ddserver.web.auth import log_in, login_required

blueprint = Blueprint("account", __name__, url_prefix="/account")


@blueprint.get("")
@login_required
def index():
    return render_template(
        "account.html", password_min_length=users.PASSWORD_MIN_LENGTH
    )


@blueprint.post("/password")
@login_required
def change_password():
    new_password = request.form.get("new_password", "")

    if new_password != request.form.get("new_password_repeat", ""):
        flash("The new passwords do not match.", "danger")
        return redirect(url_for("account.index"))

    try:
        users.change_password(
            g.user, request.form.get("current_password", ""), new_password
        )
    except users.UserError as e:
        flash(f"{e}.", "danger")
        return redirect(url_for("account.index"))

    get_session().commit()

    # The password hash has changed, which ends all sessions: keep this one.
    log_in(g.user)
    flash("Your password has been changed.", "success")

    return redirect(url_for("account.index"))


@blueprint.post("/delete")
@login_required
def delete():
    db_session = get_session()

    try:
        users.delete_user(db_session, g.user)
    except users.UserError as e:
        flash(f"{e}.", "danger")
        return redirect(url_for("account.index"))

    db_session.commit()
    session.clear()
    flash("Your account has been deleted.", "success")

    return redirect(url_for("public.index"))
