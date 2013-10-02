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

import re

from bottle import request

from formencode import validators
from formencode.api import Invalid

from ddserver.db import database as db
from ddserver.config import config



class ValidHostname(validators.FancyValidator):
  ''' check for valid hostname
  '''
  messages = {
    'too_short': 'Hostname can not be empty',
    'too_long': 'Hostname can not exceed 255 characters',
    'non_letter': 'Hostname can only consist of a-z, 0-9, -, .',
    'first_letter': 'Hostname must start and end with a letter',
    'last_letter': 'Hostname must start and end with a letter'
  }

  letter_regex = re.compile(r'[a-z0-9\-\.]')
  letter_range = range(97, 122)

  def validate_python(self, value, state):
    if len(value) < self.min:
      raise Invalid(self.message("too_short", state), value, state)

    if len(value) > self.max:
      raise Invalid(self.message("too_long", state), value, state)

    non_letters = self.letter_regex.sub('', value)
    if len(non_letters) != 0:
      raise Invalid(self.message('non_letter', value), value, state)

    print value[-1:]
    if int(value[0]) not in self.letter_range:
      raise Invalid(self.message('first_letter', value), value, state)

    print value[-1:]
    print int(value[-1:])
    if int(value[-1:]) not in self.letter_range:
      raise Invalid(self.message('last_letter', value), value, state)





class UniqueHostname(validators.FancyValidator):
  ''' check whether the hostname entered is unique
  '''
  messages = {
    'not_uniq': 'This hostname already exists.'
  }

  def validate_python(self, value, state):
    with db.cursor() as cur:
      cur.execute('''
          SELECT hostname
          FROM hosts
          WHERE hostname = %(hostname)s
      ''', {'hostname': value})
      result = cur.fetchone()

    if result != None:
      raise Invalid(self.message('not_uniq', value), value, state)



class MaxHostnames(validators.FancyValidator):
  ''' check whether a user has not hit the max number of hostnames he can have
  '''
  messages = {
    'max_hosts': 'You can only have %s hostnames' % config.dns_max_hosts
  }

  def validate_python(self, value, state):
    session = request.environ.get('beaker.session')

    with db.cursor() as cur:
      cur.execute('''
        SELECT COUNT(hostname) AS c
        FROM hosts
        WHERE user_id = %(user_id)s
      ''', {'user_id': session['userid']})
      result = cur.fetchone()

    if result['c'] >= int(config.dns_max_hosts):
      raise Invalid(self.message('max_hosts', value), value, state)



class HostnameOwner(validators.FancyValidator):
  ''' check whether the authenticated user owns a hostname
  '''
  messages = {
    'nonexistend': 'This hostname does not exist'
  }

  def validate_python(self, value, state):
    session = request.environ.get('beaker.session')

    with db.cursor() as cur:
      cur.execute('''
        SELECT id
        FROM hosts
        WHERE id = %(host_id)s
        AND user_id = %(user_id)s
      ''', {'host_id': value,
            'user_id': session['userid']})

      if len(cur.fetchone()) != 1:
        raise Invalid(self.message('nonexistend', value), value, state)



class ValidUsername(validators.FancyValidator):
  ''' check whether a valid username was entered
  '''
  messages = {
    'too_short': 'Username can not be empty',
    'too_long': 'Username can not exceed 30 characters.',
    'non_letter': 'Username can only consist of a-z, 0-9, -, .',
  }

  letter_regex = re.compile(r'[a-z0-9\-\.]')

  def _validate_python(self, value, state, db):
    if len(value) < self.min:
      raise Invalid(self.message('too_short', state))

    if len(value) > self.max:
      raise Invalid(self.message('too_long', state))

    non_letters = self.letter_regex.sub('', value)
    if len(non_letters) != 0:
      raise Invalid(self.message('non_letter', value), value, state)



class UniqueUsername(validators.FancyValidator):
  ''' check whether the username entered is unique
  '''
  messages = {
    'not_uniq': 'This username already exists.'
  }

  def validate_python(self, value, state):
    with db.cursor() as cur:
      cur.execute('''
          SELECT username
          FROM users
          WHERE username = %(username)s
      ''', {'username': value})

      if cur.fetchone() != None:
        raise Invalid(self.message('not_uniq', value), value, state)



class SecurePassword(validators.FancyValidator):
  ''' check whether the password entered is a good password
      @TODO
  '''
  messages = {
    'too_short': 'Password must be at least %s characters long' % config.auth_passwd_min_chars
  }

  def validate_python(self, value, state):
    if len(value) < int(config.auth_passwd_min_chars):
      raise Invalid(self.message('too_short', state), value, state)

