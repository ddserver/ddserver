# SPDX-License-Identifier: AGPL-3.0-or-later

from pathlib import Path

import click
from sqlalchemy.orm import Session

from ddserver import db, dns, hosts, mail, users, zones
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


@main.group()
def user():
    """Manage users."""


@user.command(name="add")
@click.argument("username")
@click.argument("email")
@click.option("--admin", is_flag=True, help="Grant admin rights.")
@click.pass_obj
def user_add(config, username: str, email: str, admin: bool):
    """Create an activated user."""
    password = click.prompt("Password", hide_input=True, confirmation_prompt=True)

    with _session(config) as session:
        try:
            new_user = users.create_user(session, username, email, password, admin)
        except users.UserError as e:
            raise click.ClickException(str(e)) from e

        session.commit()
        click.echo(f"User {new_user.username} created.")


@user.command(name="list")
@click.pass_obj
def user_list(config):
    """List all users."""
    with _session(config) as session:
        rows = [
            (
                u.username,
                u.email,
                "yes" if u.admin else "",
                users.format_host_limit(u),
                u.status.value,
                f"{u.created:%Y-%m-%d}",
            )
            for u in users.list_users(session)
        ]

    _print_table(("USERNAME", "EMAIL", "ADMIN", "LIMIT", "STATUS", "CREATED"), rows)


@user.command(name="delete")
@click.argument("username")
@click.option("--yes", is_flag=True, help="Do not ask for confirmation.")
@click.pass_obj
def user_delete(config, username: str, yes: bool):
    """Delete a user."""
    with _session(config) as session:
        try:
            existing_user = users.get_user(session, username)

            if not yes:
                click.confirm(
                    f"Delete user {existing_user.username} and all their hostnames?",
                    abort=True,
                )

            username = existing_user.username
            deleted = users.delete_user(session, existing_user)
        except users.UserError as e:
            raise click.ClickException(str(e)) from e

        session.commit()
        dns.delete_records(session, config.dns, deleted)
        click.echo(f"User {username} deleted.")


@user.command(name="grant-admin")
@click.argument("username")
@click.pass_obj
def user_grant_admin(config, username: str):
    """Grant the admin role to a user."""
    _set_admin(config, username, True)


@user.command(name="revoke-admin")
@click.argument("username")
@click.pass_obj
def user_revoke_admin(config, username: str):
    """Revoke the admin role from a user."""
    _set_admin(config, username, False)


@user.command(name="host-limit")
@click.argument("username")
@click.argument("limit")
@click.pass_obj
def user_host_limit(config, username: str, limit: str):
    """Set the number of hostnames of a user.

    LIMIT is a number, 'default' or 'unlimited'.
    """
    with _session(config) as session:
        try:
            existing_user = users.get_user(session, username)
            existing_user.host_limit = users.parse_host_limit(limit)
        except users.UserError as e:
            raise click.ClickException(str(e)) from e

        session.commit()
        new_limit = users.format_host_limit(existing_user)
        click.echo(f"Host limit of {existing_user.username}: {new_limit}.")


def _set_admin(config, username: str, admin: bool) -> None:
    with _session(config) as session:
        try:
            existing_user = users.get_user(session, username)
            users.set_admin(session, existing_user, admin)
        except users.UserError as e:
            raise click.ClickException(str(e)) from e

        session.commit()
        state = "now" if admin else "no longer"
        click.echo(f"User {existing_user.username} is {state} an admin.")


@main.group()
def zone():
    """Manage zones."""


@zone.command(name="add")
@click.argument("name")
@click.pass_obj
def zone_add(config, name: str):
    """Add a zone."""
    with _session(config) as session:
        try:
            new_zone = zones.create_zone(session, name)
        except zones.ZoneError as e:
            raise click.ClickException(str(e)) from e

        session.commit()
        click.echo(f"Zone {new_zone.name} added.")


@zone.command(name="list")
@click.pass_obj
def zone_list(config):
    """List all zones."""
    with _session(config) as session:
        rows = [(z.name, f"{z.created:%Y-%m-%d}") for z in zones.list_zones(session)]

    _print_table(("NAME", "CREATED"), rows)


@zone.command(name="delete")
@click.argument("name")
@click.option("--yes", is_flag=True, help="Do not ask for confirmation.")
@click.pass_obj
def zone_delete(config, name: str, yes: bool):
    """Delete a zone."""
    with _session(config) as session:
        try:
            existing_zone = zones.get_zone(session, name)
        except zones.ZoneError as e:
            raise click.ClickException(str(e)) from e

        if not yes:
            count = hosts.count_hosts_by_zone(session).get(existing_zone.id, 0)
            click.confirm(
                f"Delete zone {existing_zone.name} with {count} hostname(s)?",
                abort=True,
            )

        zone_name = existing_zone.name
        deleted = zones.delete_zone(session, existing_zone)
        session.commit()
        dns.delete_records(session, config.dns, deleted)
        click.echo(f"Zone {zone_name} deleted.")


@main.group(name="dns")
def dns_group():
    """Publish to the DNS server."""


@dns_group.command()
@click.option("--all", "all_hosts", is_flag=True, help="Publish every host.")
@click.pass_obj
def sync(config, all_hosts: bool):
    """Publish what has not reached the DNS server yet."""
    if not config.dns.server:
        raise click.ClickException("dns.server: no DNS server configured")

    with _session(config) as session:
        selected = (
            hosts.all_hosts(session) if all_hosts else hosts.unpublished_hosts(session)
        )
        results = [dns.publish_host(session, config.dns, host) for host in selected]

        deletions = hosts.pending_deletions(session)
        dns.delete_records(session, config.dns, deletions)
        remaining = len(hosts.pending_deletions(session))

    click.echo(f"{sum(results)} of {len(results)} hosts published.")
    click.echo(f"{len(deletions) - remaining} of {len(deletions)} deletions done.")

    if not all(results) or remaining:
        raise click.ClickException("some changes did not reach DNS, see the log")


@main.group(name="mail")
def mail_group():
    """Send mail."""


@mail_group.command(name="test")
@click.argument("address")
@click.pass_obj
def mail_test(config, address: str):
    """Send a test mail to the given address."""
    if not mail.send(config.mail, address, "ddserver test mail", "test.txt"):
        raise click.ClickException("sending the mail failed, see the log")

    click.echo(f"Test mail to {address} sent.")


def _session(config) -> Session:
    """Open a database session for a command."""
    engine = db.make_engine(config.database.url)

    try:
        db.check_schema(engine)
    except db.SchemaError as e:
        raise click.ClickException(str(e)) from e

    return Session(engine)


def _print_table(headers: tuple[str, ...], rows: list[tuple[str, ...]]) -> None:
    """Output a formatted table."""
    widths = [
        max(len(value) for value in column)
        for column in zip(headers, *rows, strict=True)
    ]

    for row in (headers, *rows):
        click.echo(
            "  ".join(f"{v:<{w}}" for v, w in zip(row, widths, strict=True)).rstrip()
        )
