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

import bottle

import formencode

import validators

from ddserver.config import config



def validated(cls, target):
  ''' input validation wrapper that takes a validation schema and redirect url
      as parameters. the POST array gets validated, rewritten and returned. if
      validation errors occur, an error message specified by the validator is
      set and a redirect triggered.
  '''
  def wrapper(func):
    def wrapped(*args, **kwargs):
      session = bottle.request.environ.get('beaker.session')

      validator = cls()

      try:
        bottle.request.POST = validator().to_python({k : bottle.request.POST.get(k)
                                                     for k
                                                     in bottle.request.POST})

        func(*args, **kwargs)

      except formencode.Invalid, e:
        session['msg'] = ('error', e)

      session.save()
      bottle.redirect(target)


    return wrapped
  return wrapper



class AddHostnameSchema(formencode.Schema):
  ''' schema for validation of the form for adding a new hostname
  '''
  hostname = formencode.All(validators.ValidHostname(min = 1,
                                                     max = 255),
                            validators.UniqueHostname(),
                            validators.MaxHostnames())
  address = formencode.validators.IPAddress()



class DelHostnameSchema(formencode.Schema):
  ''' schema for validation of the delete action of a hostname
  '''
  hostid = formencode.All(formencode.validators.Int(not_empty = True),
                          validators.HostnameOwner())



class ActivateUserSchema(formencode.Schema):
  ''' schema for validation of the administrative user activation action
  '''
  uid = formencode.validators.Int(not_empty = True)



class DeleteUserSchema(formencode.Schema):
  ''' schema for validation of the administrative user delete action
  '''
  uid = formencode.validators.Int(not_empty = True)



class UpdateUserSchema(formencode.Schema):
  ''' schema for validation of the form for editing account information
  '''
  email = formencode.validators.Email()


class UpdatePasswordSchema(formencode.Schema):
  ''' schema for validation of the form for setting a new password
  '''
  password = validators.SecurePassword(min = 8)
  password_confirm = formencode.validators.String()
  chained_validators = [formencode.validators.FieldsMatch('password',
                                                          'password_confirm')]


class CreateUserSchema(formencode.Schema):
  ''' schema for validation of the form for creating a new account
  '''
  allow_extra_fields = True

  username = formencode.All(validators.ValidUsername(min = 1,
                                                     max = 255),
                            validators.UniqueUsername())

  email = formencode.validators.Email()

  password = validators.SecurePassword(min = 8)
  password_confirm = formencode.validators.String()


  chained_validators = [formencode.validators.FieldsMatch('password',
                                                          'password_confirm')]

  if config.recaptcha_enabled == '1':
    recaptcha_challenge_field = formencode.validators.String()
    recaptcha_response_field = formencode.validators.String()

    chained_validators.append(validators.ValidCaptcha('recaptcha_challenge_field',
                                                      'recaptcha_response_field'))


class LoginSchema(formencode.Schema):
  ''' schema for validation of the login form
  '''
  username = validators.ValidUsername(min = 1,
                                      max = 255)
  password = formencode.validators.String()
