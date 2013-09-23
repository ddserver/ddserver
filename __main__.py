'''
Copyright 2013 Sven Reissmann <sven@0x80.io>

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

from ddserver.config import Config
from ddserver.pages import *



session_opts = {
    'session.cookie_expires': True
}


plugin = bottle_mysql.Plugin(dbhost = Config().database['hostname'],
                             dbuser = Config().database['username'],
                             dbpass = Config().database['password'],
                             dbname = Config().database['database'])

app = bottle.app()
app.install(plugin)

app = SessionMiddleware(app, session_opts)

bottle.run(app,
           host = Config().server['address'],
           port = Config().server['port'])

