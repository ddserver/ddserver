# SPDX-License-Identifier: AGPL-3.0-or-later
"""The endpoints of the update protocol (dyndns2)."""

import logging

from flask import Blueprint, Response, current_app, request

from ddserver import dns, updater
from ddserver.db import get_session

log = logging.getLogger(__name__)

blueprint = Blueprint("nic", __name__, url_prefix="/nic")


@blueprint.get("/ip")
def ip():
    return _text(request.remote_addr)


@blueprint.get("/update")
def update():
    auth = request.authorization

    # Asks clients which do not send credentials on their first attempt to do so.
    if auth is None or auth.type != "basic":
        response = _text(updater.ResponseCode.BADAUTH, status=401)
        response.headers["WWW-Authenticate"] = 'Basic realm="ddserver"'
        return response

    try:
        results = updater.update_many(
            get_session(),
            auth.username or "",
            auth.password or "",
            request.args.get("hostname", ""),
            request.args.get("myip") or request.remote_addr,
        )
        get_session().commit()

        config = current_app.extensions["ddserver.config"]

        for result in results:
            if result.changed:
                dns.publish_host(config.dns, result.changed)

    except Exception:
        log.exception("update failed")
        return _text(updater.ResponseCode.SERVER_ERROR)

    return _text("\n".join(str(result) for result in results))


def _text(text: str, status: int = 200) -> Response:
    return Response(text, status, mimetype="text/plain")
