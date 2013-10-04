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

from passlib.apps import custom_app_context as pwd

from bottle import route, request

from ddserver.db import database as db
from ddserver import templates
from ddserver.config import config
from ddserver.pages.session import authorized, logout
from ddserver.validation.schemas import *



@route('/account')
@authorized
def account_display():
  ''' display account information.
  '''
  session = request.environ.get('beaker.session')

  with db.cursor() as cur:
    cur.execute('''
      SELECT *
      FROM users
      WHERE username = %(username)s
    ''', {'username' : session['username']})
    row = cur.fetchone()

  return templates.get_template('account.html').render(session = session,
                                                       data = row)



@route('/account', method = 'POST')
@authorized
@validated(UpdateUserSchema, '/account')
def account_edit():
  ''' display account information.
  '''
  session = request.environ.get('beaker.session')

  with db.cursor() as cur:
    cur.execute('''
      UPDATE users
      SET email = %(email)s
      WHERE id = %(id)s
    ''', {'email': request.POST.get('email'),
          'id': session['userid']})

  session['msg'] = ('success', 'Ok, done.')


@route('/account/password', method = 'POST')
@authorized
@validated(UpdatePasswordSchema, '/account')
def password_edit():
  ''' update the users password
  '''
  session = request.environ.get('beaker.session')

  encrypted_password = pwd.encrypt(request.POST.get('password'))

  with db.cursor() as cur:
    cur.execute('''
      UPDATE users
      SET password = %(newpass)s
      WHERE id = %(id)s
    ''', {'newpass' : encrypted_password,
          'id': session['userid']})

  session['msg'] = ('success', 'Ok, done.')



@route('/account/delete', method = 'POST')
@authorized
def account_delete():
  ''' delete the users account
  '''
  session = request.environ.get('beaker.session')

  with db.cursor() as cur:
    cur.execute('''
      DELETE
      FROM users
      WHERE id = %(id)s
      LIMIT 1
    ''', {'id' : session['userid']})

  session['msg'] = ('success', 'Ok. Bye bye.')

  logout()

