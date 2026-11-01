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

from ddserver import dns, hosts, mail
from ddserver import users as user_management
from ddserver import zones as zone_management
from ddserver.config import DnsConfig
from ddserver.db import get_session
from ddserver.models import Base, Host, User, Zone
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


@blueprint.get("/users/add")
@admin_required
def add_user():
    return render_template("adduser.html")


@blueprint.post("/users/add")
@admin_required
def add_user_post():
    db_session = get_session()
    username = request.form.get("username", "")
    email = request.form.get("email", "")

    try:
        user = user_management.create_invited_user(db_session, username, email)
    except user_management.UserError as e:
        flash(f"{e}.", "danger")
        return render_template("adduser.html", username=username, email=email)

    db_session.commit()

    if _send_activation_mail(user):
        flash(f"User {user.username} has been added.", "success")
    else:
        flash(
            f"User {user.username} has been added, "
            "but the activation mail could not be sent.",
            "warning",
        )

    return redirect(url_for("admin.users"))


@blueprint.get("/users/<int:user_id>")
@admin_required
def user_hosts(user_id: int):
    db_session = get_session()
    user = _get_or_404(User, user_id)

    return render_template(
        "admin_hosts.html",
        heading=f"User: {user.username}",
        hosts=hosts.list_hosts(db_session, user),
        back="user",
    )


@blueprint.post("/users/<int:user_id>/delete")
@admin_required
def delete_user(user_id: int):
    db_session = get_session()
    user = _get_other_user(user_id)
    username = user.username

    deleted = user_management.delete_user(db_session, user)
    db_session.commit()
    dns.delete_records(db_session, _dns_config(), deleted)
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
    user = _get_or_404(User, user_id)

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


@blueprint.get("/zones/<int:zone_id>")
@admin_required
def zone_hosts(zone_id: int):
    db_session = get_session()
    zone = _get_or_404(Zone, zone_id)

    return render_template(
        "admin_hosts.html",
        heading=f"Zone: {zone.name}",
        hosts=hosts.list_hosts_of_zone(db_session, zone),
        back="zone",
    )


@blueprint.post("/zones/<int:zone_id>/delete")
@admin_required
def delete_zone(zone_id: int):
    db_session = get_session()
    zone = _get_or_404(Zone, zone_id)
    name = zone.name

    deleted = zone_management.delete_zone(db_session, zone)
    db_session.commit()
    dns.delete_records(db_session, _dns_config(), deleted)
    flash(f"Zone {name} has been deleted.", "success")

    return redirect(url_for("admin.zones"))


@blueprint.post("/hosts/<int:host_id>/delete")
@admin_required
def delete_host(host_id: int):
    db_session = get_session()
    host = _get_or_404(Host, host_id)

    # `back` only selects one of our own pages, it is never used as a URL.
    if request.args.get("back") == "user":
        back = url_for("admin.user_hosts", user_id=host.user_id)
    else:
        back = url_for("admin.zone_hosts", zone_id=host.zone_id)

    deleted = hosts.delete_host(db_session, host)
    db_session.commit()
    dns.delete_records(db_session, _dns_config(), [deleted])
    flash(f"Hostname {deleted} has been deleted.", "success")

    return redirect(back)


def _send_activation_mail(user: User) -> bool:
    config = current_app.extensions["ddserver.config"]
    token = user_management.activation_token(config.web.secret_key, user)

    return mail.send(
        config.mail,
        user.email,
        "Activate your ddserver account",
        "activation.txt",
        username=user.username,
        url=url_for("auth.activate", token=token, _external=True),
        days=str(user_management.ACTIVATION_DAYS),
    )


def _dns_config() -> DnsConfig:
    return current_app.extensions["ddserver.config"].dns


def _get_or_404[T: Base](model: type[T], object_id: int) -> T:
    """Return the object with `object_id`, otherwise answer `404 Not Found`."""
    found = get_session().get(model, object_id)

    if found is None:
        abort(404)

    return found


def _get_other_user(user_id: int) -> User:
    """Return a user to act on, which cannot be the admin who is logged in.

    Admins can neither remove their own role nor lock themselves out from this page:
    the next page would be forbidden. They delete themselves on the account page.
    """
    user = _get_or_404(User, user_id)

    if user.id == g.user.id:
        abort(403)

    return user
