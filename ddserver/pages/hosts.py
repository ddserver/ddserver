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

from ddserver.db import database as db
from ddserver import templates
from ddserver.config import config
from ddserver.pages.session import authorized




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
    rows = cur.fetchall()

  template = templates.get_template('hosts.html')
  return template.render(session = session,
                         hosts = rows,
                         origin = config.dns_suffix,
                         max_hostnames = config.dns_max_hosts)



@route('/hosts', method = 'POST')
@authorized
def hosts_delete():
  ''' delete a hostname.
  '''
  session = request.environ.get('beaker.session')

  hostid = request.POST.get('hostid', '')

  if hostid != '':
    with db.cursor() as cur:
      result = cur.execute('''
          DELETE
          FROM hosts
          WHERE id = %(id)s
            AND user_id = %(user_id)s
      ''', {'id': hostid,
            'user_id': session['userid']})

    if result == 1:
      session['msg'] = ('success', 'Ok, done.')

    else:
      session['msg'] = ('error', 'Error executing the requested action.')

  else:
    session['msg'] = ('error', 'No Host-ID specified.')

  session.save()
  redirect('/hosts')



@route('/hosts/add', method = 'POST')
@authorized
def hosts_add():
  ''' add a new hostname
  '''
  session = request.environ.get('beaker.session')

  hostname = request.POST.get('hostname', '')
  address = request.POST.get('address', '')

  with db.cursor() as cur:
    cur.execute('''
        SELECT COUNT(hostname) AS count
        FROM hosts
        WHERE user_id = %(user_id)s
    ''', {'user_id' : session['userid']})
    result = cur.fetchone()

    if result['count'] < int(config.dns_max_hosts):
      if hostname != '':
        cur.execute('SELECT hostname FROM hosts WHERE hostname = %s', (hostname,))

        if result['count'] < int(config.dns_max_hosts):
          if hostname != '':
            cur.execute('SELECT hostname FROM hosts WHERE hostname = %s', (hostname,))

            if result == 1:
              session['msg'] = ('success', 'Ok, done.')

            if result == 1:
              session['msg'] = ('success', 'Ok, done.')

          else:
            session['msg'] = ('error', 'This hostname already exists.')

        else:
          session['msg'] = ('error', 'Hostname can be max. 255 characters long.')

      else:
        session['msg'] = ('error', 'No hostname specified.')

    else:
      session['msg'] = ('error', 'You already have %s hostnames defined.' % config.dns_max_hosts)

  session.save()
  redirect('/hosts')
