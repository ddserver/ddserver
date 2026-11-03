# SPDX-License-Identifier: AGPL-3.0-or-later
"""The Flask application."""

from flask import Flask
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix

from ddserver import db
from ddserver.config import Config
from ddserver.web import account, admin, auth, hosts, nic, public


def create_app(config: Config) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = config.web.secret_key
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    # Only send the session cookie over HTTPS, if ddserver is reached that way.
    app.config["SESSION_COOKIE_SECURE"] = config.web.base_url.startswith("https://")
    app.extensions["ddserver.config"] = config

    # Behind a reverse proxy, take the client address, scheme and host name from the
    # `X-Forwarded-*` headers of the proxy. Without a proxy, anyone could send them.
    if config.web.proxies:
        n = config.web.proxies
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=n, x_proto=n, x_host=n)

    # allow templates to access password_min_length
    @app.context_processor
    def password_min_length() -> dict[str, int]:
        config = app.extensions["ddserver.config"]
        return {"password_min_length": config.passwords.min_length}

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
