# SPDX-License-Identifier: AGPL-3.0-or-later

from flask import Blueprint, current_app, g, render_template, request
from sqlalchemy import func, select

from ddserver import hosts
from ddserver.db import Base, get_session
from ddserver.models import Host, User, Zone

blueprint = Blueprint("public", __name__)


@blueprint.get("/")
def index():
    if not g.user:
        return render_template("index.html")

    config = current_app.extensions["ddserver.config"].hosts
    own_hosts = len(hosts.list_hosts(get_session(), g.user))
    host_count = _count(Host)

    return render_template(
        "index.html",
        current_ip=request.remote_addr,
        own_hosts=own_hosts,
        own_share=round(own_hosts / host_count * 100) if host_count else 0,
        host_limit=hosts.host_limit(g.user, config),
        unlimited=hosts.HOST_LIMIT_UNLIMITED,
        zone_count=_count(Zone),
        user_count=_count(User),
        host_count=host_count,
    )


def _count(model: type[Base]) -> int:
    return get_session().scalar(select(func.count()).select_from(model))
