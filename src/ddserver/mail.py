# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Send plain text mail from the templates in `templates/mail`.
"""

import logging
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formatdate, make_msgid, parseaddr

from jinja2 import Environment, PackageLoader, StrictUndefined

from ddserver.config import MailConfig

log = logging.getLogger(__name__)

TIMEOUT = 10

# Use our own templates here, not the ones we use with Flask.
_templates = Environment(
    loader=PackageLoader("ddserver", "templates/mail"),
    autoescape=False,
    undefined=StrictUndefined,
)


def send(
    config: MailConfig, to: str, subject: str, template: str, **values: str
) -> bool:
    """Send `template`, filled with `values`, to `to`. Return `False` on error."""
    if not config.sender:
        log.error("no mail to %s sent: mail.sender is not configured", to)
        return False

    try:
        _send_smtp(config, _build(config, to, subject, template, values))
    except Exception:
        log.exception("sending mail to %s failed", to)
        return False

    return True


def _build(
    config: MailConfig, to: str, subject: str, template: str, values: dict[str, str]
) -> EmailMessage:
    message = EmailMessage()
    message["From"] = config.sender
    message["To"] = to
    message["Subject"] = subject
    message["Date"] = formatdate(usegmt=True)
    message["Message-ID"] = make_msgid(
        domain=parseaddr(config.sender)[1].rpartition("@")[2]
    )
    message.set_content(_templates.get_template(template).render(values))

    return message


def _send_smtp(config: MailConfig, message: EmailMessage) -> None:
    # Without this context, `smtplib` does not check the certificate of the server.
    context = ssl.create_default_context()

    if config.security == "tls":
        smtp = smtplib.SMTP_SSL(
            config.host, config.port, timeout=TIMEOUT, context=context
        )
    else:
        smtp = smtplib.SMTP(config.host, config.port, timeout=TIMEOUT)

    with smtp:
        if config.security == "starttls":
            smtp.starttls(context=context)

        if config.username:
            smtp.login(config.username, config.password)

        smtp.send_message(message)
