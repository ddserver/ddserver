# SPDX-License-Identifier: AGPL-3.0-or-later
"""The hostnames of a user."""

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

from ddserver import dns, hosts, zones
from ddserver.config import DnsConfig, HostsConfig
from ddserver.db import get_session
from ddserver.models import Host, Zone
from ddserver.passwords import PASSWORD_MIN_LENGTH
from ddserver.web.auth import login_required

blueprint = Blueprint("hosts", __name__, url_prefix="/hosts")


@blueprint.get("")
@login_required
def index():
    return render_template("hosts.html", hosts=hosts.list_hosts(get_session(), g.user))


@blueprint.get("/add")
@login_required
def add():
    return _render_add_form()


@blueprint.post("/add")
@login_required
def add_post():
    db_session = get_session()
    form = request.form
    zone = db_session.get(Zone, form.get("zone", 0, type=int))

    if zone is None:
        flash("Please select a zone.", "danger")
        return _render_add_form()

    if form.get("password", "") != form.get("password_repeat", ""):
        flash("The passwords do not match.", "danger")
        return _render_add_form()

    try:
        host = hosts.create_host(
            db_session,
            g.user,
            zone,
            form.get("name", ""),
            form.get("password", ""),
            ipv4=form.get("ipv4", ""),
            ipv6=form.get("ipv6", ""),
            description=form.get("description", ""),
            config=_config(),
        )
    except hosts.HostError as e:
        flash(f"{e}.", "danger")
        return _render_add_form()

    db_session.commit()
    dns.publish_host(_dns_config(), host)
    flash(f"Hostname {host.name}.{zone.name} has been added.", "success")

    return redirect(url_for("hosts.index"))


@blueprint.get("/<int:host_id>")
@login_required
def details(host_id: int):
    return _render_details(_get_own_host(host_id))


@blueprint.post("/<int:host_id>")
@login_required
def update(host_id: int):
    host = _get_own_host(host_id)
    form = request.form

    try:
        addresses_changed = hosts.update_host(
            host,
            form.get("ipv4", ""),
            form.get("ipv6", ""),
            form.get("description", ""),
        )
    except hosts.HostError as e:
        flash(f"{e}.", "danger")
        return _render_details(host)

    get_session().commit()

    if addresses_changed:
        dns.publish_host(_dns_config(), host)

    flash("The hostname has been updated.", "success")

    return redirect(url_for("hosts.details", host_id=host.id))


@blueprint.post("/<int:host_id>/password")
@login_required
def change_password(host_id: int):
    host = _get_own_host(host_id)
    password = request.form.get("password", "")

    if password != request.form.get("password_repeat", ""):
        flash("The passwords do not match.", "danger")
        return _render_details(host)

    try:
        hosts.set_host_password(host, password)
    except hosts.HostError as e:
        flash(f"{e}.", "danger")
        return _render_details(host)

    get_session().commit()
    flash("The host password has been changed.", "success")

    return redirect(url_for("hosts.details", host_id=host.id))


@blueprint.post("/<int:host_id>/delete")
@login_required
def delete(host_id: int):
    db_session = get_session()
    host = _get_own_host(host_id)
    deleted = hosts.delete_host(db_session, host)
    db_session.commit()
    dns.delete_records(_dns_config(), [deleted])
    flash(f"Hostname {deleted} has been deleted.", "success")

    return redirect(url_for("hosts.index"))


def _config() -> HostsConfig:
    return current_app.extensions["ddserver.config"].hosts


def _dns_config() -> DnsConfig:
    return current_app.extensions["ddserver.config"].dns


def _get_own_host(host_id: int) -> Host:
    """Return a host of the logged-in user, others get `404 Not Found`.

    Not `403`, as this would reveal which hosts exist.
    """
    host = hosts.get_host(get_session(), g.user, host_id)

    if host is None:
        abort(404)

    return host


def _render_details(host: Host):
    """Show the page of `host`, keeping what was entered in the form."""
    return render_template(
        "host.html",
        host=host,
        form=request.form,
        password_min_length=PASSWORD_MIN_LENGTH,
    )


def _render_add_form():
    """Show the form again with what was entered, as long pages are tedious to redo."""
    return render_template(
        "addhost.html",
        zones=zones.list_zones(get_session()),
        form=request.form,
        host_limit=hosts.host_limit(g.user, _config()),
        unlimited=hosts.HOST_LIMIT_UNLIMITED,
        password_min_length=PASSWORD_MIN_LENGTH,
    )
