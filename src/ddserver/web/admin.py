# SPDX-License-Identifier: AGPL-3.0-or-later
"""Pages for administrators."""

from flask import Blueprint, render_template

from ddserver.db import get_session
from ddserver.users import list_users
from ddserver.web.auth import admin_required

blueprint = Blueprint("admin", __name__, url_prefix="/admin")


@blueprint.get("/users")
@admin_required
def users():
    return render_template("users.html", users=list_users(get_session()))
