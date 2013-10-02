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

from bottle import route, request, redirect

import formencode

from ddserver.db import database as db
from ddserver import templates
from ddserver.config import config
from ddserver.pages.session import authorized
from ddserver.validation.schemas import *



@route('/hosts')
@authorized
def hosts_display():
  ''' display the users hostnames and a form for adding new ones.
  '''
  session = request.environ.get('beaker.session')

  with db.cursor() as cur:
    cur.execute('''
        SELECT *
        FROM hosts
        WHERE user_id = %(user_id)s
    ''', {'user_id': session['userid']})
    hosts = cur.fetchall()

  template = templates.get_template('hosts.html')
  return template.render(session = session,
                         hosts = hosts,
                         origin = config.dns_suffix,
                         max_hostnames = config.dns_max_hosts)



@route('/hosts', method = 'POST')
@authorized
@validated(DelHostnameSchema, '/hosts')
def hosts_delete():
  ''' delete a hostname.
  '''
  session = request.environ.get('beaker.session')

  with db.cursor() as cur:
    cur.execute('''
        DELETE
        FROM hosts
        WHERE id = %(host_id)s
    ''', {'host_id': request.POST.get('hostid')})

  session['msg'] = ('success', 'Ok, done.')



@route('/hosts/add', method = 'POST')
@authorized
@validated(AddHostnameSchema, '/hosts')
def hosts_add():
  ''' add a new hostname
  '''
  session = request.environ.get('beaker.session')

  with db.cursor() as cur:
    cur.execute('''
      INSERT INTO `hosts`
      SET `hostname` = %(hostname)s,
          `address` = %(address)s,
          `user_id` = %(user_id)s
    ''', {'hostname': request.POST.get('hostname'),
          'address': request.POST.get('address'),
          'user_id' : session['userid']})

  session['msg'] = ('success', 'Ok, done.')
