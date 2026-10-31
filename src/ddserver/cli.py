# SPDX-License-Identifier: AGPL-3.0-or-later

from pathlib import Path

import click

from ddserver import db
from ddserver.app import create_app
from ddserver.config import DEFAULT_PATH, ConfigError, load_config


@click.group()
@click.option(
    "--config",
    "config_path",
    type=click.Path(path_type=Path, dir_okay=False),
    envvar="DDSERVER_CONFIG",
    default=DEFAULT_PATH,
    show_default=True,
    help="Configuration file (or set DDSERVER_CONFIG).",
)
@click.pass_context
def main(ctx: click.Context, config_path: Path):
    """ddserver - a server-side application for dynamic DNS."""
    try:
        ctx.obj = load_config(config_path)
    except ConfigError as e:
        raise click.ClickException(str(e)) from e


@main.command()
@click.option(
    "--host",
    default="127.0.0.1",
    show_default=True,
    help="Address to listen on.",
)
@click.option(
    "--port",
    default=8080,
    show_default=True,
    help="Port to listen on.",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug mode and automatic reloading.",
)
@click.pass_obj
def run(config, host: str, port: int, debug: bool):
    """Run the dev webserver."""
    try:
        app = create_app(config)
    except db.SchemaError as e:
        raise click.ClickException(str(e)) from e

    app.run(host=host, port=port, debug=debug)


@main.group(name="db")
def database():
    """Manage the database."""


@database.command()
@click.pass_obj
def upgrade(config):
    """Create the database or upgrade it to the current schema."""
    db.upgrade(db.make_engine(config.database.url))
    click.echo("The database schema is up to date.")


@database.command()
@click.option("-m", "--message", required=True, help="Short description.")
@click.pass_obj
def revision(config, message: str):
    """Create a draft migration from model changes (for developers)."""
    db.revision(db.make_engine(config.database.url), message)
