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

from bottle import route, request, redirect

from ddserver.db import database as db
from ddserver.validation.schemas import *



@route('/login', method = 'POST')
@validated(LoginSchema, '/')
def login():
  ''' handles user authentication. redirects to index in any case.
  '''
  session = request.environ.get('beaker.session')

  with db.cursor() as cur:
    cur.execute('''
      SELECT *
        FROM users 
       WHERE username = %(username)s
    ''', {'username': request.POST.get('username')})
    row = cur.fetchone()

  if row and pwd.verify(request.POST.get('password'), row['password']):
    if row['active'] == True:
      session['username'] = row['username']
      session['userid'] = row['id']
      session['admin'] = row['admin']
      session['msg'] = ('success', 'Welcome, %s' % row['username'])

    else:
      session['msg'] = ('error', 'This account has not yet been activated.')

  else:
    session['msg'] = ('error', 'Login incorrect.')



@route('/logout')
def logout():
  ''' handles user logout. redirects to index in any case.
  '''
  session = request.environ.get('beaker.session')

  del session['username']
  del session['userid']
  del session['admin']
  session.save()

  redirect('/')



def authorized(func):
  def __(*args, **kwargs):
    session = request.environ.get('beaker.session')

    if 'username' not in session:
      redirect('/')

    else:
      return func(*args, **kwargs)

  return __



def admin(func):
  def __(*args, **kwargs):
    session = request.environ.get('beaker.session')

    if 'admin' not in session or session['admin'] != True:
      session['msg'] = ('error', 'Sorry, you are no admin.')
      session.save()

      redirect('/')

    else:
      return func(*args, **kwargs)

  return __
