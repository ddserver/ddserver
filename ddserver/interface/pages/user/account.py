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

import bottle

from require import extend, require

from ddserver.web import route

from ddserver.interface.user import authorized, verify_yubikey_otp

from ddserver.interface import validation
from ddserver.interface.validation import validate

from passlib.apps import custom_app_context as pwd



@extend('ddserver.config:ConfigDeclaration')
def config_auth(config_decl):
  with config_decl.declare('auth') as s:
    s('password_min_chars',
       conv = int,
       default = 8)



@route('/user/account', method = 'GET')
@authorized()
@require(template = 'ddserver.interface.template:TemplateManager')
def get_account(user,
                template):
  ''' Display account information. '''

  return template['account.html'](data = user)



@route('/user/account', method = 'POST')
@authorized()
@validate('/user/account',
          email = validation.Email())
@require(db = 'ddserver.db:Database',
         messages = 'ddserver.interface.message:MessageManager')
def post_account_edit(user,
                      data,
                      db,
                      messages):
  ''' Display account information. '''

  with db.cursor() as cur:
    cur.execute('''
        UPDATE `users`
        SET `email` = %(email)s
        WHERE `id` = %(id)s
    ''', {'email': data.email,
          'id': user.id})

  messages.success('Ok, done.')

  bottle.redirect('/user/account')



@route('/user/account/password', method = 'POST')
@authorized()
@validate('/user/account',
          password = validation.SecurePassword(min = 8),
          password_confirm = validation.String(),
          chained_validators = [validation.FieldsMatch('password', 'password_confirm')])
@require(db = 'ddserver.db:Database',
         messages = 'ddserver.interface.message:MessageManager')
def post_account_password(user,
                          data,
                          db,
                          messages):
  ''' Update the users password. '''

  encrypted_password = pwd.encrypt(data.password)

  with db.cursor() as cur:
    cur.execute('''
        UPDATE `users`
        SET `password` = %(newpass)s
        WHERE `id` = %(id)s
    ''', {'newpass' : encrypted_password,
          'id': user.id})

  messages.success('Ok, done.')

  bottle.redirect('/user/account')



@route('/user/account/delete', method = 'POST')
@authorized()
@require(db = 'ddserver.db:Database',
         auth = 'ddserver.interface.user:UserManager',
         messages = 'ddserver.interface.message:MessageManager')
def post_account_delete(user,
                        db,
                        auth,
                        messages):
  ''' Delete the users account. '''

  with db.cursor() as cur:
    cur.execute('''
        DELETE
        FROM users
        WHERE id = %(id)s
    ''', {'id': user.id})

  auth.logout()

  bottle.redirect('/')



@route('/user/account/yubikey/enable', method = 'POST')
@authorized()
@validate('/user/account',
          yubico_id = validation.Int(),
          yubico_key = validation.String())
@require(db = 'ddserver.db:Database',
         messages = 'ddserver.interface.message:MessageManager')
def post_account_yubico_enable(user,
                               data,
                               db,
                               messages):
  """ Enable Yubikey OTP
  """

  with db.cursor() as cur:
    cur.execute('''
        UPDATE `users`
        SET `yubico_id` = %(yubico_id)s,
            `yubico_key` = %(yubico_key)s
        WHERE `id` = %(id)s
    ''', {'yubico_id' : data.yubico_id,
          'yubico_key' : data.yubico_key,
          'id': user.id})

  messages.success('Ok, done.')

  bottle.redirect('/user/account')



@route('/user/account/yubikey/disable', method = 'POST')
@authorized()
@require(db = 'ddserver.db:Database',
         messages = 'ddserver.interface.message:MessageManager')
def post_account_yubico_disable(user,
                                db,
                                messages):
  """ Disable Yubikey OTP
  """

  with db.cursor() as cur:
    cur.execute('''
        UPDATE `users`
        SET `yubico_id` = NULL,
            `yubico_key` = NULL
        WHERE `id` = %(id)s
    ''', {'id': user.id})

  messages.success('Ok, done.')

  bottle.redirect('/user/account')



@route('/user/account/yubikey/test', method = 'POST')
@authorized()
@validate('/user/account',
          yubikey_otp = validation.String())
@require(db = 'ddserver.db:Database',
         messages = 'ddserver.interface.message:MessageManager')
def post_account_yubico_test(user,
                             db,
                             messages,
                             data):
  """ Test Yubikey OTP
  """

  result = verify_yubikey_otp(username = user.username,
                              yubikey_otp = data.yubikey_otp)
  if result:
    messages.success('Congratulation, your Yubikey works.')
  else:
    messages.error('Error validating your Yubikey OTP.')

  bottle.redirect('/user/account')
