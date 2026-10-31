# SPDX-License-Identifier: AGPL-3.0-or-later
"""The Flask application."""

from flask import Flask

from ddserver import db
from ddserver.config import Config
from ddserver.web import public


def create_app(config: Config) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = config.web.secret_key

    engine = db.make_engine(config.database.url)
    db.check_schema(engine)
    db.init_app(app, engine)

    app.register_blueprint(public.blueprint)

    return app
