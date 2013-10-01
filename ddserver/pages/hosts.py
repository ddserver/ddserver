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

from ddserver import templates
from ddserver.config import config




@route('/hosts')
def hosts_display(db):
  ''' display the users hostnames and a form for adding new ones.
  '''
  session = request.environ.get('beaker.session')

  if 'username' not in session:
    redirect('/')

  db.execute('SELECT * FROM hosts WHERE user_id = %s', (session['userid'],))
  rows = db.fetchall()

  template = templates.get_template('hosts.html')
  return template.render(session = session,
                         hosts = rows,
                         origin = config.dns['suffix'],
                         max_hostnames = config.dns['max_hosts'])



@route('/hosts', method = 'POST')
def hosts_delete(db):
  ''' delete a hostname.
  '''
  session = request.environ.get('beaker.session')

  if 'username' not in session:
    redirect('/')

  hostid = request.POST.get('hostid', '')

  if hostid != '':
    result = db.execute('DELETE FROM hosts WHERE id = %s AND user_id = %s',
                        (hostid, session['userid'],))

    if result == 1:
      session['msg'] = ('success', 'Ok, done.')

    else:
      session['msg'] = ('error', 'Error executing the requested action.')

  else:
    session['msg'] = ('error', 'No Host-ID specified.')

  session.save()
  redirect('/hosts')



@route('/hosts/add', method = 'POST')
def hosts_add(db):
  ''' add a new hostname
  '''
  session = request.environ.get('beaker.session')

  if 'username' not in session:
    redirect('/')

  hostname = request.POST.get('hostname', '')
  address = request.POST.get('address', '')

  db.execute('SELECT COUNT(hostname) AS count FROM hosts WHERE user_id = %s',
                 (session['userid'],))
  result = db.fetchone()

  if result['count'] < int(config.dns.max_hosts):
    if hostname != '':
      db.execute('SELECT hostname FROM hosts WHERE hostname = %s', (hostname,))

      if len(hostname) < 256:
        if db.fetchone() == None:
          result = db.execute('INSERT INTO hosts SET hostname = %s, address = %s, user_id = %s',
                              (hostname, address, session['userid'],))

          if result == 1:
            session['msg'] = ('success', 'Ok, done.')

          else:
            session['msg'] = ('error', 'Error executing the requested action.')

        else:
          session['msg'] = ('error', 'This hostname already exists.')

      else:
        session['msg'] = ('error', 'Hostname can be max. 255 characters long.')

    else:
      session['msg'] = ('error', 'No hostname specified.')

  else:
    session['msg'] = ('error', 'You already have %s hostnames defined.' % config.limits['max_hostnames'])

  session.save()
  redirect('/hosts')
