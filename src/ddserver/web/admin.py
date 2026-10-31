# SPDX-License-Identifier: AGPL-3.0-or-later
"""Pages for administrators."""

from flask import (
    Blueprint,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)

from ddserver import users as user_management
from ddserver.db import get_session
from ddserver.models import User
from ddserver.web.auth import admin_required

blueprint = Blueprint("admin", __name__, url_prefix="/admin")


@blueprint.get("/users")
@admin_required
def users():
    users = user_management.list_users(get_session())

    return render_template("users.html", users=users)


@blueprint.post("/users/<int:user_id>/delete")
@admin_required
def delete_user(user_id: int):
    db_session = get_session()
    user = _get_other_user(user_id)
    username = user.username

    user_management.delete_user(db_session, user)
    db_session.commit()
    flash(f"User {username} has been deleted.", "success")

    return redirect(url_for("admin.users"))


@blueprint.post("/users/<int:user_id>/admin")
@admin_required
def set_admin(user_id: int):
    db_session = get_session()
    user = _get_other_user(user_id)
    admin = request.form.get("admin") == "1"

    user_management.set_admin(db_session, user, admin)
    db_session.commit()

    if admin:
        flash(f"User {user.username} is now an admin.", "success")
    else:
        flash(f"User {user.username} is no longer an admin.", "success")

    return redirect(url_for("admin.users"))


def _get_other_user(user_id: int) -> User:
    """Return a user to act on, which cannot be the admin who is logged in.

    Admins can neither remove their own role nor lock themselves out from this page:
    the next page would be forbidden. They delete themselves on the account page.
    """
    user = get_session().get(User, user_id)

    if user is None:
        abort(404)

    if user.id == g.user.id:
        abort(403)

    return user
