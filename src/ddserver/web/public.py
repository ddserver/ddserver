# SPDX-License-Identifier: AGPL-3.0-or-later

from flask import Blueprint, render_template

blueprint = Blueprint("public", __name__)


@blueprint.get("/")
def index():
    return render_template("index.html")
