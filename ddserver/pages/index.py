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

from bottle import route, request, static_file

from ddserver.db import database as db
from ddserver.config import config
from ddserver import templates

from ddserver.mail import Email
from ddserver.validation.schemas import *


@route('/static/<path:path>')
def static(path):
  ''' provides a route to static files (css, images)
  '''
  return static_file(path, os.path.join(os.getcwd(), 'resources', 'web'))



@route('/')
def index():
  ''' display the index page
  '''
  session = request.environ.get('beaker.session')

  template = templates.get_template('index.html')
  return template.render(session = session,
                         config = config)


#
# signup
#

@route('/signup')
def signup():
  ''' display the index page
  '''
  session = request.environ.get('beaker.session')

  if config.auth_enable_registration == '1':
    template = templates.get_template('signup.html')
  else:
    template = templates.get_template('nosignup.html')

  return template.render(session = session,
                         config = config,
                         recaptcha_enabled = config.recaptcha_enabled,
                         recaptcha_public_key = config.recaptcha_public_key)



@route('/signup', method = 'POST')
@validated(SignupSchema, '/signup')
def account_create():
  ''' create a new user account
  '''
  session = request.environ.get('beaker.session')

  username = request.POST.get('username')
  email_address = request.POST.get('email')
  email_domain = email_address.split("@")

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

  if (config.auth_allowed_maildomains == 'any' or
      email_domain[1] in config.auth_allowed_maildomains):
    email = Email(username = username)
    email.account_activation()

    session['msg'] = ('success', 'Your account has been created. You should receive an activation email in some minutes.')

  else:
    session['msg'] = ('success', 'Your account has been created, but is inactive at the moment.')

  # notify admin
  if config.auth_notify_admin:
    email.notify_admin()


@route('/signup/activate/<username>/<authcode>')
def activate_form(username,
             authcode):
  session = request.environ.get('beaker.session')

  template = templates.get_template('activate.html')
  return template.render(session = session,
                         recaptcha_enabled = config.recaptcha_enabled,
                         recaptcha_public_key = config.recaptcha_public_key,
                         username = username,
                         authcode = authcode)


@route('/signup/activate', method = 'POST')
@validated(ActivateAccountSchema, '/')
def activate():
  session = request.environ.get('beaker.session')

  encrypted_password = pwd.encrypt(request.POST.get('password'))

  with db.cursor() as cur:
    cur.execute('''
      UPDATE users
      SET `active` = 1,
          `password` = %(encrypted_password)s
      WHERE `username` = %(username)s
    ''', {'encrypted_password': encrypted_password,
          'username': request.POST.get('username') })

  session['msg'] = ('success', 'Your account is active now. Please login.')



@route('/signup/cancel', method = 'POST')
@validated(CancelActivateAccountSchema, '/')
def signup_cancel():
  session = request.environ.get('beaker.session')

  with db.cursor() as cur:
    cur.execute('''
      DELETE
      FROM users
      WHERE `username` = %(username)s
    ''', { 'username': request.POST.get('username') })

  session['msg'] = ('success', 'Signup cancelled. Your account has been removed.')




#
# password recovery
#

@route('/lostpass')
def lostpass():
  session = request.environ.get('beaker.session')

  template = templates.get_template('lostpass.html')
  return template.render(session = session,
                         recaptcha_enabled = config.recaptcha_enabled,
                         recaptcha_public_key = config.recaptcha_public_key)


@route('/lostpass', method = 'POST')
@validated(LostPasswordSchema, '/')
def lostpass_sendmail():
  session = request.environ.get('beaker.session')

  email = Email(username = request.POST.get('username'))
  email.password_reminder()

  session['msg'] = ('success', 'Password recovery email has been sent.')


@route('/lostpass/recover/<username>/<authcode>', method = 'GET')
def lostpass_setnew_form(username,
                         authcode):
  session = request.environ.get('beaker.session')

  template = templates.get_template('resetpass.html')
  return template.render(session = session,
                         recaptcha_enabled = config.recaptcha_enabled,
                         recaptcha_public_key = config.recaptcha_public_key,
                         username = username,
                         authcode = authcode)


@route('/lostpass/setnew', method = 'POST')
@validated(ResetPasswordSchema, '/')
def lostpass_setnew():
  session = request.environ.get('beaker.session')

  encrypted_password = pwd.encrypt(request.POST.get('password'))

  with db.cursor() as cur:
    cur.execute('''
      UPDATE users
      SET `password` = %(encrypted_password)s,
          `authcode` = 0
      WHERE `username` = %(username)s
    ''', {'encrypted_password': encrypted_password,
          'username': request.POST.get('username')})

  session['msg'] = ('success', 'Your new password has been set.')


@route('/lostpass/cancel', method = 'POST')
@validated(ResetPasswordCancelSchema, '/')
def lostpass_cancel():
  session = request.environ.get('beaker.session')

  with db.cursor() as cur:
    cur.execute('''
      UPDATE users
      SET `authcode` = 0
      WHERE `username` = %(username)s
    ''', {'username': request.POST.get('username')})

  session['msg'] = ('success', 'Your password reset request has been cancelled.')

