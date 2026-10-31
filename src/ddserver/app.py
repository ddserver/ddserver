# SPDX-License-Identifier: AGPL-3.0-or-later
"""The Flask application."""

from flask import Flask
from flask_wtf.csrf import CSRFProtect

from ddserver import db
from ddserver.config import Config
from ddserver.web import account, admin, auth, hosts, nic, public


def create_app(config: Config) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = config.web.secret_key
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.extensions["ddserver.config"] = config

    CSRFProtect(app)

    engine = db.make_engine(config.database.url)
    db.check_schema(engine)
    db.init_app(app, engine)

    app.register_blueprint(public.blueprint)
    app.register_blueprint(auth.blueprint)
    app.register_blueprint(hosts.blueprint)
    app.register_blueprint(account.blueprint)
    app.register_blueprint(admin.blueprint)
    app.register_blueprint(nic.blueprint)

    return app
