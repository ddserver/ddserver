# SPDX-License-Identifier: AGPL-3.0-or-later
"""
The entry point for a WSGI server, e.g. `gunicorn ddserver.wsgi:app`.

The configuration file is taken from `DDSERVER_CONFIG`, like the CLI does, or from
the default path.
"""

import os
from pathlib import Path

from ddserver.app import create_app
from ddserver.config import DEFAULT_PATH, load_config

app = create_app(load_config(Path(os.environ.get("DDSERVER_CONFIG", DEFAULT_PATH))))
