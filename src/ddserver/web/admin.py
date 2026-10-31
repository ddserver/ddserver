# SPDX-License-Identifier: AGPL-3.0-or-later
"""Pages for administrators."""

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

from ddserver import hosts
from ddserver import users as user_management
from ddserver import zones as zone_management
from ddserver.db import get_session
from ddserver.models import User, Zone
from ddserver.web.auth import admin_required

blueprint = Blueprint("admin", __name__, url_prefix="/admin")


@blueprint.get("/users")
@admin_required
def users():
    return render_template(
        "users.html",
        users=user_management.list_users(get_session()),
        format_host_limit=user_management.format_host_limit,
        default_limit=current_app.extensions["ddserver.config"].hosts.default_limit,
    )


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


@blueprint.post("/users/<int:user_id>/host-limit")
@admin_required
def set_host_limit(user_id: int):
    db_session = get_session()
    user = db_session.get(User, user_id)

    if user is None:
        abort(404)

    try:
        user.host_limit = user_management.parse_host_limit(
            request.form.get("host_limit", "")
        )
    except user_management.UserError as e:
        flash(f"{e}.", "danger")
        return redirect(url_for("admin.users"))

    db_session.commit()
    limit = user_management.format_host_limit(user)
    flash(f"Host limit of {user.username}: {limit}.", "success")

    return redirect(url_for("admin.users"))


@blueprint.get("/zones")
@admin_required
def zones():
    db_session = get_session()

    return render_template(
        "zones.html",
        zones=zone_management.list_zones(db_session),
        host_counts=hosts.count_hosts_by_zone(db_session),
    )


@blueprint.post("/zones")
@admin_required
def add_zone():
    db_session = get_session()

    try:
        zone = zone_management.create_zone(db_session, request.form.get("name", ""))
    except zone_management.ZoneError as e:
        flash(f"{e}.", "danger")
        return redirect(url_for("admin.zones"))

    db_session.commit()
    flash(f"Zone {zone.name} has been added.", "success")

    return redirect(url_for("admin.zones"))


@blueprint.post("/zones/<int:zone_id>/delete")
@admin_required
def delete_zone(zone_id: int):
    db_session = get_session()
    zone = db_session.get(Zone, zone_id)

    if zone is None:
        abort(404)

    name = zone.name

    zone_management.delete_zone(db_session, zone)
    db_session.commit()
    flash(f"Zone {name} has been deleted.", "success")

    return redirect(url_for("admin.zones"))


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
