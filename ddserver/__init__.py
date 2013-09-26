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

import bottle

from jinja2 import Environment, PackageLoader



templates = Environment(loader = PackageLoader('web', 'templates'))


def getmsg():
  session = bottle.request.environ.get('beaker.session')
  if 'msg' in session:
    msg = session['msg']
    del session['msg']
    session.save()
    return msg

templates.globals['getmsg'] = getmsg
