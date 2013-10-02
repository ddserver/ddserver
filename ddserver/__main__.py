'''
Copyright 2013 Dustin Frisch<fooker@lab.sh>

This file is part of ddserver.

ddserver is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published
by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.

ddserver is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with ddserver.  If not, see <http://www.gnu.org/licenses/>.
'''

from beaker.middleware import SessionMiddleware

import bottle
import bottle_mysql

import logging

from ddserver.config import config
from ddserver.db import database

from ddserver.pages import *
from ddserver.pages.index import *
from ddserver.pages.session import *
from ddserver.pages.account import *
from ddserver.pages.hosts import *
from ddserver.pages.nic import *



# Create a logger
logger = logging.getLogger('ddserver')



def main():
  # Initialize logging
  logging.basicConfig(level = logging.DEBUG if config.verbose else logging.INFO)

  # Ensure the suffix has a leading dot
  if config.dns_suffix and not config.dns_suffix.startswith('.'):
      config.dns_suffix = '.%s' % config.dns_suffix

  # Connect to the database
  database.setup(dbhost = config.database_host,
                 dbport = int(config.database_port),
                 dbname = config.database_name,
                 dbuser = config.database_username,
                 dbpass = config.database_password)

  # Get the bottle application
  app = bottle.app()
  app = SessionMiddleware(app, {'session.cookie_expires': True})

  # Start web server and run it
  if config.verbose:
      bottle.debug(True)

  if config.wsgi_standalone:
      bottle.run(app = app,
                 host = config.wsgi_host,
                 port = config.wsgi_port,
                 debug = config.verbose)



if __name__ == '__main__':
    main()
