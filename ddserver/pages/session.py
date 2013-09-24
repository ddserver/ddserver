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



@route('/login', method = 'POST')
def login(db):
  ''' handles user authentication. redirects to index in any case.
  '''
  session = request.environ.get('beaker.session')

  username = request.POST.get('username', '')
  password = request.POST.get('password', '')

  db.execute('SELECT id, username, password FROM users WHERE username = %s',
             (username,))
  row = db.fetchone()

  if row and pwd.verify(password, row['password']):
    session['username'] = row['username']
    session['userid'] = row['id']
    session.save()

  redirect('/')



@route('/logout')
def logout():
  ''' handles user logout. redirects to index in any case.
  '''
  session = request.environ.get('beaker.session')

  del session['username']
  del session['userid']
  session.save()

  redirect('/')
