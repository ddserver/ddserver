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

import re
import bottle

from recaptcha.client import captcha

import formencode

from formencode.validators import (FancyValidator,
                                   FieldsMatch,  # @UnusedImport: for exporting
                                   Email,  # @UnusedImport: for exporting
                                   IPAddress,  # @UnusedImport: for exporting
                                   String,  # @UnusedImport: for exporting
                                   Int)  # @UnusedImport: for exporting

from ddserver.utils.deps import require



def validate(__on_error__ = '/',
             **kwargs):
  ''' Input validation wrapper that builds a validation schema.

      The given **kwargs are used to create a validation schema. Each post field
      is mapped against the key of the schema and validated using the keys
      validator.

      The special parameter '__on_error__' is used as a redirect target if the
      validation fails.

      If the validation was successful, the POST parameters are transformed into
      arguments with the same name and passed to the wrapped function.

      @param __on_error__: the redirect target used if tha valiadtion fails
      @param **kwargs: a mapping of names and validators
  '''

  # Build schema class
  Schema = type('Schema',
                (formencode.Schema,),
                kwargs)

  # Value container
  class Values(object):
    def __init__(self, values):
      self.__dict__.update(values)

  def wrapper(func):
    @require(messages = 'ddserver.interface.message:MessageManager')
    def wrapped(messages, *args, **kwargs):
      validator = Schema()

      try:
        # Validate the POST values using the schema
        data = validator().to_python({k : bottle.request.POST.get(k)
                                      for k
                                      in bottle.request.POST})

        func(*args,
             data = Values(data),
             **kwargs)

      except formencode.Invalid, e:
        for msg in e.error_dict.itervalues():
          messages.error(msg)

      bottle.redirect(__on_error__)

    return wrapped
  return wrapper



class ValidHostname(FancyValidator):
  ''' Check for valid hostname. '''

  messages = {
    'too_short': 'Hostname can not be empty',
    'too_long': 'Hostname can not exceed 63 characters',
    'non_letter': 'Hostname can only consist of a-z, 0-9, -, .',
    'invalid_start': 'Hostnames must start with an aplhanumeric character'
  }

  letter_regex = re.compile(r'[a-z0-9\-\.]+')

  def validate_python(self,
                      value,
                      state):
    if len(value) < 1:
      raise formencode.Invalid(self.message("too_short",
                                            value),
                               value,
                               state)

    if len(value) > 63:
      raise formencode.Invalid(self.message("too_long",
                                            value),
                               value,
                               state)

    if not self.letter_regex.match(value):
      raise formencode.Invalid(self.message('non_letter',
                                            value),
                               value,
                               state)

    if value[0] == '-' or value[0] == '.':
      raise formencode.Invalid(self.message('invalid_start',
                                            value),
                               value,
                               state)



class UniqueHostname(ValidHostname):
  ''' Check whether the hostname entered is unique. '''

  messages = {
    'not_uniq': 'This hostname already exists.'
  }

  @require(db = 'ddserver.db:Database')
  def validate_python(self,
                      value,
                      state,
                      db):
    ValidHostname.validate_python(self, value, state)

    with db.cursor() as cur:
      cur.execute('''
          SELECT hostname
          FROM hosts
          WHERE hostname = %(hostname)s
      ''', {'hostname': value})
      result = cur.fetchone()

    if result != None:
      raise formencode.Invalid(self.message('not_uniq',
                                            value),
                               value,
                               state)



class ValidUsername(FancyValidator):
  ''' Check whether a valid username was entered. '''

  messages = {
    'too_short': 'Username can not be empty',
    'too_long': 'Username can not exceed 30 characters.',
    'non_letter': 'Username can only consist of a-z, 0-9, -, .',
  }

  letter_regex = re.compile(r'[a-z0-9\-\.]+')

  def validate_python(self, value, state):
    if len(value) < 1:
      raise formencode.Invalid(self.message('too_short',
                                            value),
                               value,
                               state)

    if len(value) > 255:
      raise formencode.Invalid(self.message('too_long',
                                            value),
                               value,
                               state)

    if not self.letter_regex.match(value):
      raise formencode.Invalid(self.message('non_letter',
                                            value),
                               value,
                               state)



class UniqueUsername(ValidUsername):
  ''' Check whether the username entered is unique. '''

  messages = {
    'not_uniq': 'This username already exists.'
  }

  @require(users = 'ddserver.interface.user:UserManager')
  def validate_python(self,
                      value,
                      state,
                      users):
    ValidUsername.validate_python(self, value, state)

    user = users[value]

    if user:
      raise formencode.Invalid(self.message('not_uniq',
                                            value),
                               value,
                               state)


class ExistendUsername(ValidUsername):
  messages = {
    'not_existend': 'This username does not exist.'
  }


  @require(users = 'ddserver.interface.user:UserManager')
  def validate_python(self,
                      value,
                      state,
                      users):
    ValidUsername.validate_python(self, value, state)

    user = users[value]

    if not user:
      raise formencode.Invalid(self.message('not_existend',
                                            value),
                               value,
                               state)



class SecurePassword(FancyValidator):
  ''' Check whether the password entered is a good password. '''

  messages = {
    'too_short': 'Password must be at least %(min_chars)s characters long'
  }

  @require(config = 'ddserver.config:Config')
  def validate_python(self,
                      value,
                      state,
                      config):
    min_chars = config.auth.password_min_chars
    if len(value) < min_chars:
      raise formencode.Invalid(self.message('too_short',
                                            value,
                                            min_chars = min_chars),
                               value,
                               state)



class ValidCaptcha(FancyValidator):
  ''' Validate the recaptcha from the login form. '''

  messages = {
    'invalid': 'Captcha invalid'
  }

  challenge = response = None

  __unpackargs__ = ('challenge', 'response')

  @require(config = 'ddserver.config:Config')
  def validate_python(self, field_dict, state, config):
    response = captcha.submit(
      field_dict[self.challenge],
      field_dict[self.response],
      config.recaptcha_private_key,
      bottle.request.remote_addr
    )

    if not response.is_valid:
      raise formencode.Invalid(self.message('invalid', field_dict), field_dict, state)



class ValidSuffix(FancyValidator):
  ''' Check for valid suffix. '''

  # TODO: validate hostname, tld, at least one dot, ...

  messages = {
    'too_short': 'Suffix can not be empty',
    'too_long': 'Suffix can not exceed 255 characters',
    'non_letter': 'Suffix can only consist of a-z, 0-9, -, .'
  }

  letter_regex = re.compile(r'[a-z0-9\-\.]+')

  def validate_python(self,
                      value,
                      state):
    if len(value) < 1:
      raise formencode.Invalid(self.message("too_short",
                                            value),
                               value,
                               state)

    if len(value) > self.max:
      raise formencode.Invalid(self.message("too_long",
                                            value),
                               value,
                               state)

    if not self.letter_regex.match(value):
      raise formencode.Invalid(self.message('non_letter',
                                            value),
                               value,
                               state)



class UniqueSuffix(ValidSuffix):
  ''' Check whether the entered entered is unique. '''

  messages = {
    'not_uniq': 'This suffix already exists.'
  }

  @require(db = 'ddserver.db:Database')
  def validate_python(self,
                      value,
                      state,
                      db):
    ValidSuffix.validate_python(self, value, state)

    with db.cursor() as cur:
      cur.execute('''
          SELECT name
          FROM suffixes
          WHERE name = %(suffixname)s
      ''', {'suffixname': value})
      result = cur.fetchone()

    if result != None:
      raise formencode.Invalid(self.message('not_uniq',
                                            value),
                               value,
                               state)

