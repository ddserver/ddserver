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
from ddserver.pages.session import authorized_admin
from ddserver.validation.schemas import *



@route('/admin/inactiveUsers')
@authorized_admin
def inactive_users_display():
  ''' display a list of users that are waiting for account activation
  '''
  session = request.environ.get('beaker.session')

  with db.cursor() as cur:
    cur.execute('''
      SELECT *
      FROM users
      WHERE `active` = 0
    ''')
    users = cur.fetchall()

  template = templates.get_template('inactive.html')
  return template.render(session = session,
                         users = users)



@route('/admin/activateUser', method = 'POST')
@authorized_admin
@validated(ActivateUserSchema, '/admin/inactiveUsers')
def user_activate():
  ''' activate a users account
  '''
  session = request.environ.get('beaker.session')

  with db.cursor() as cur:
    cur.execute('''
      UPDATE users
      SET `active` = 1
      WHERE `id` = %(user_id)s
    ''', { 'user_id': request.POST.get('uid') })

  session['msg'] = ('success', 'Ok, done.')



@route('/admin/deleteUser', method = 'POST')
@authorized_admin
@validated(DeleteUserSchema, '/admin/inactiveUsers')
def user_delete():
  ''' activate a users account
  '''
  session = request.environ.get('beaker.session')

  with db.cursor() as cur:
    cur.execute('''
      DELETE FROM users
      WHERE `id` = %(user_id)s
    ''', { 'user_id': request.POST.get('uid') })

  session['msg'] = ('success', 'Ok, done.')

