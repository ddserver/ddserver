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

import os

from bottle import route, request, static_file

from ddserver import templates



@route('/static/<path:path>')
def static(path):
  ''' provides a route to static files (css, images)
  '''
  return static_file(path, os.path.join(os.getcwd(), 'resources', 'web'))



@route('/')
def index():
  ''' display the index page
  '''
  session = request.environ.get('beaker.session')

  return templates.get_template('index.html').render(session = session)







