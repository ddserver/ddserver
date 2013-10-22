'''
Copyright 2013 Sven Reissmann <sven@0x80.io>

This file is part of ddserver.

ddserver is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

ddserver is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with ddserver. If not, see <http://www.gnu.org/licenses/>.
'''

from bottle import route, request, redirect

from ddserver.db import database as db
from ddserver import templates
from ddserver.pages.session import authorized_admin
from ddserver.validation.schemas import *
from ddserver.mail import Email



@route('/admin/users/<mode>')
@authorized_admin
def users_display(mode = 'all'):
  ''' display a list of users that are waiting for account activation
  '''
  session = request.environ.get('beaker.session')

  if mode == 'admins':
      where = 'WHERE `admin` = 1'

  elif mode == 'inactive':
      where = 'WHERE `active` = 0'

  else:
      where = 'WHERE 1 = 1'

  with db.cursor() as cur:
    cur.execute('''
        SELECT *
        FROM users
    ''' + where)
    users = cur.fetchall()

  template = templates.get_template('users.html')
  return template.render(session = session,
                         users = users,
                         mode = mode)



@route('/admin/users/activate', method = 'POST')
@authorized_admin
@validated(AdminActivateUserSchema, '/admin/users/all')
def user_activate():
  ''' activate a users account
  '''
  session = request.environ.get('beaker.session')

  email = Email(username = request.POST.get('username'))
  email.account_activation()

  session['msg'] = ('success', 'Ok, done.')



@route('/admin/users/delete', method = 'POST')
@authorized_admin
@validated(IsUserSchema, '/admin/users/all')
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



@route('/admin/users/makeAdmin', method = 'POST')
@authorized_admin
@validated(IsUserSchema, '/admin/users/all')
def user_mkadmin():
  ''' activate a users account
  '''
  session = request.environ.get('beaker.session')

  with db.cursor() as cur:
    cur.execute('''
      UPDATE users
      SET `admin` = 1
      WHERE `id` = %(user_id)s
    ''', { 'user_id': request.POST.get('uid') })

  session['msg'] = ('success', 'Ok, done.')



@route('/admin/users/removeAdmin', method = 'POST')
@authorized_admin
@validated(IsUserSchema, '/admin/users/all')
def user_rmadmin():
  ''' activate a users account
  '''
  session = request.environ.get('beaker.session')

  with db.cursor() as cur:
    cur.execute('''
      UPDATE users
      SET `admin` = 0
      WHERE `id` = %(user_id)s
    ''', { 'user_id': request.POST.get('uid') })

  session['msg'] = ('success', 'Ok, done.')



@route('/admin/adduser')
@authorized_admin
def adduser_form():
  ''' form for adding a new user
  '''
  session = request.environ.get('beaker.session')

  template = templates.get_template('adduser.html')
  return template.render(session = session)


@route('/admin/adduser', method = 'POST')
@authorized_admin
@validated(AdminCreateUserSchema, '/admin/adduser')
def adduser():
  ''' add a new user
  '''
  session = request.environ.get('beaker.session')

  username = request.POST.get('username')
  email_address = request.POST.get('email')

  with db.cursor() as cur:
    cur.execute('''
      INSERT
      INTO users
      SET `username` = %(username)s,
          `email` = %(email)s,
          `admin` = 0,
          `active` = 0,
          `created` = CURRENT_TIMESTAMP
    ''', {'username': username,
          'email': email_address})

    email = Email(username = username)
    email.account_activation()

    session['msg'] = ('success', 'Account created. The user will get an activation email.')

