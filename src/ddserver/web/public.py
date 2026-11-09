# SPDX-License-Identifier: AGPL-3.0-or-later

import logging
from pathlib import Path

from flask import Blueprint, current_app, g, render_template, request
from sqlalchemy import func, select

from ddserver import hosts
from ddserver.db import Base, get_session
from ddserver.models import Host, User, Zone

log = logging.getLogger(__name__)

blueprint = Blueprint("public", __name__)


@blueprint.get("/")
def index():
    config = current_app.extensions["ddserver.config"]
    motd = _motd(config.motd.file) if g.user or config.motd.public else None

    if not g.user:
        return render_template("index.html", motd=motd)

    own_hosts = len(hosts.list_hosts(get_session(), g.user))
    host_count = _count(Host)

    return render_template(
        "index.html",
        motd=motd,
        current_ip=request.remote_addr,
        own_hosts=own_hosts,
        own_share=round(own_hosts / host_count * 100) if host_count else 0,
        host_limit=hosts.host_limit(g.user, config.hosts),
        unlimited=hosts.HOST_LIMIT_UNLIMITED,
        zone_count=_count(Zone),
        user_count=_count(User),
        host_count=host_count,
    )


def _motd(file: str) -> str | None:
    """Return the start page text from `file`. It is HTML, written by the admin."""
    if not file:
        return None

    try:
        text = Path(file).read_text()
    except FileNotFoundError:
        # Deleting the file is the way to remove the text.
        return None
    except (OSError, UnicodeDecodeError) as e:
        log.warning("cannot read motd file %s: %s", file, e)
        return None

    return text if text.strip() else None


def _count(model: type[Base]) -> int:
    return get_session().scalar(select(func.count()).select_from(model))
