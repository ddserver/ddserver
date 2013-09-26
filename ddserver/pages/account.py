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

from ddserver import templates
from ddserver.config import config
from ddserver.pages.session import logout


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
        if len(pass1) >= int(config.limits['passwd_min_chars']):
          newpass = pwd.encrypt(pass1)
          db.execute('UPDATE users SET password = %s WHERE id = %s',
                     (newpass, session['userid'],))
          session['msg'] = ('success', 'Ok, done.')

        else:
          session['msg'] = ('error', 'The password you entered is to short (use at least %s characters).' % config.limits['passwd_min_chars'])

    else:
      session['msg'] = ('error', 'The passwords you entered do not match.')

  else:
    session['msg'] = ('error', 'The email address can not be empty.')

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
  session['msg'] = ('success', 'Ok. Bye bye.')

  logout()
