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
  logging.basicConfig(level = logging.DEBUG if config.general.verbose else logging.INFO)

  # Ensure the suffix has a leading dot
  if config.dns.suffix and not config.dns.suffix.startswith('.'):
      config.dns.suffix = '.%s' % config.dns.suffix

  # Get the bottle application
  app = bottle.app()

  # Connect to the database
  database = bottle_mysql.MySQLPlugin(dbhost = config.database.host,
                                      dbport = int(config.database.port),
                                      dbname = config.database.name,
                                      dbuser = config.database.username,
                                      dbpass = config.database.password,
                                      autocommit = True)
  app.install(database)

  app = SessionMiddleware(app, {'session.cookie_expires': True})

  # Start web server and run it
  if config.general.verbose:
      bottle.debug(True)

  if config.wsgi.standalone:
      bottle.run(app = app,
                 host = config.wsgi.host,
                 port = config.wsgi.port,
                 debug = config.general.verbose)



if __name__ == '__main__':
    main()
