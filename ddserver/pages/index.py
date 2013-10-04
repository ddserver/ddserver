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
  return template.render(session = session)



@route('/signup')
def signup():
  ''' display the index page
  '''
  session = request.environ.get('beaker.session')

  template = templates.get_template('signup.html')
  return template.render(session = session,
                         recaptcha_enabled = config.recaptcha_enabled,
                         recaptcha_public_key = config.recaptcha_public_key)



@route('/signup', method = 'POST')
@validated(CreateUserSchema, '/signup')
def account_create():
  ''' create a new user account
  '''
  session = request.environ.get('beaker.session')

  encrypted_password = pwd.encrypt(request.POST.get('password'))

  with db.cursor() as cur:
    cur.execute('''
      INSERT 
      INTO users
      SET `username` = %(username)s,
          `password` = %(password)s,
          `email` = %(email)s,
          `admin` = 0,
          `active` = 0,
          `created` = CURRENT_TIMESTAMP
    ''', {'username': request.POST.get('username'),
          'password': encrypted_password,
          'email': request.POST.get('email')})

  session['msg'] = ('success', 'Your account has been created, but is inactive at the moment. ')


