# SPDX-License-Identifier: AGPL-3.0-or-later
"""The endpoints of the update protocol (dyndns2)."""

import logging

from flask import Blueprint, Response, request

from ddserver import updater
from ddserver.db import get_session

log = logging.getLogger(__name__)

blueprint = Blueprint("nic", __name__, url_prefix="/nic")


@blueprint.get("/ip")
def ip():
    return _text(request.remote_addr)


@blueprint.get("/update")
def update():
    auth = request.authorization

    try:
        result = updater.update(
            get_session(),
            auth.username or "",
            auth.password or "",
            request.args.get("hostname", ""),
            request.args.get("myip") or request.remote_addr,
        )
        get_session().commit()

    except Exception:
        log.exception("update failed")
        return _text(updater.ResponseCode.SERVER_ERROR)

    return _text(str(result))


def _text(text: str, status: int = 200) -> Response:
    return Response(text, status, mimetype="text/plain")
