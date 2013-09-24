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

from passlib.apps import custom_app_context as pwd

from bottle import route, request, redirect, static_file

from ddserver.config import Config
from ddserver import templates



@route('/static/<path:path>')
def callback(path):
  ''' provides a route to static files (css, images)
  '''
  return static_file(path, os.path.join(os.getcwd(), 'web'))



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



@route('/')
def index():
  ''' display the index page
  '''
  session = request.environ.get('beaker.session')

  return templates.get_template('index.html').render(session = session)



@route('/account')
def account_display(db):
  ''' display account information.
  '''
  session = request.environ.get('beaker.session')

  if 'username' not in session:
    redirect('/')

  db.execute('SELECT * FROM users WHERE username = %s', (session['username'],))
  row = db.fetchone()

  return templates.get_template('account.html').render(session = session,
                                                       data = row)



@route('/account', method = 'POST')
def account_edit(db):
  ''' display account information.
  '''
  session = request.environ.get('beaker.session')

  if 'username' not in session:
    redirect('/')

  email = request.POST.get('email', '')
  pass1 = request.POST.get('password1', '')
  pass2 = request.POST.get('password2', '')

  # email address may not be empty
  if email != '':
    db.execute('UPDATE users SET email = %s WHERE id = %s',
               (email, session['userid'],))
    session['msg'] = 'Ok, done.'

    # if a password was entered, is long enough and matches the retype
    # field, it gets encrypted and updated in mysql
    if pass1 == pass2:
      if pass1 != '':
        if len(pass1) >= int(Config().limits['passwd_min_chars']):
          newpass = pwd.encrypt(pass1)
          db.execute('UPDATE users SET password = %s WHERE id = %s',
                     (newpass, session['userid'],))
          session['msg'] = 'Ok, done.'

        else:
          session['msg'] = 'The password you entered is to short (use at least %s characters).' % Config().limits['passwd_min_chars']

    else:
      session['msg'] = 'The passwords you entered do not match.'

  else:
    session['msg'] = 'The email address can not be empty.'

  session.save()
  redirect('/account')



@route('/account/delete', method = 'POST')
def account_delete(db):
  ''' display account information.
  '''
  session = request.environ.get('beaker.session')

  if 'username' not in session:
    redirect('/')

  db.execute('DELETE FROM users WHERE id = %s LIMIT 1', (session['userid'],))
  session['msg'] = 'Ok. Bye bye.'

  logout()



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
                         origin = Config().dns['origin'],
                         max_hostnames = Config().limits['max_hostnames'])



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
      session['msg'] = 'Ok, done.'

    else:
      session['msg'] = 'Error executing the requested action.'

  else:
    session['msg'] = 'No Host-ID specified.'

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

  # validate ip address
  if address != '':
    try:
      formencode.validators.IPAddress().to_python(address)
    except formencode.Invalid, e:
      session['msg'] = e
      session.save()
      redirect('/hosts')

  # validate hostname
  try:
    validators.Hostname().to_python(hostname)
  except formencode.Invalid, e:
    session['msg'] = e
    session.save()
    redirect('/hosts')


  db.execute('SELECT COUNT(hostname) AS count FROM hosts WHERE user_id = %s',
                 (session['userid'],))
  result = db.fetchone()

  if result['count'] < int(Config().limits['max_hostnames']):
    if hostname != '':
      db.execute('SELECT hostname FROM hosts WHERE hostname = %s', (hostname,))

      if len(hostname) < 256:
        if db.fetchone() == None:
          result = db.execute('INSERT INTO hosts SET hostname = %s, address = %s, user_id = %s',
                              (hostname, address, session['userid'],))

          if result == 1:
            session['msg'] = 'Ok, done.'

          else:
            session['msg'] = 'Error executing the requested action.'

        else:
          session['msg'] = 'This hostname already exists.'

      else:
        session['msg'] = 'Hostname can be max. 255 characters long.'

    else:
      session['msg'] = 'No hostname specified.'

  else:
    session['msg'] = 'You already have %s hostnames defined.' % Config().limits['max_hostnames']

  session.save()
  redirect('/hosts')
