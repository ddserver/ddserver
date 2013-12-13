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

from ddserver.web import route

from ddserver.utils.deps import require

from ddserver.interface.user import authorized_by_code

from ddserver.interface import validation
from ddserver.interface.validation import validate

from ddserver.interface.captcha import captcha_check

from passlib.apps import custom_app_context as pwd



@route('/lostpass', method = 'GET')
@require(config = 'ddserver.config:Config',
         templates = 'ddserver.interface.template:TemplateManager')
def get_lostpass(config,
                 templates):
  return templates['lostpass.html']()



@route('/lostpass', method = 'POST')
@captcha_check('/lostpass')
@validate(username = validation.ExistendUsername())
@require(users = 'ddserver.interface.user:UserManager',
         emails = 'ddserver.mail:EmailManager',
         messages = 'ddserver.interface.message:MessageManager')
def post_lostpass(data,
                  users,
                  emails,
                  messages):
  # Generate a authcode for the user
  users.generate_authcode(data.username)

  # Fetch user info
  user = users[data.username]

  emails.to_user('lostpasswd.mail',
                 user = user)

  messages.success('Password recovery email has been sent.')

  bottle.redirect('/')



@route('/lostpass/recover', method = 'GET')
@require(templates = 'ddserver.interface.template:TemplateManager')
def get_lostpass_setnew(templates):
  username = bottle.request.query.username
  authcode = bottle.request.query.authcode

  return templates['resetpass.html'](username = username,
                                     authcode = authcode)



@route('/lostpass/setnew', method = 'POST')
@authorized_by_code()
@validate(password = validation.SecurePassword(min = 8),
          password_confirm = validation.String(),
          chained_validators = [validation.FieldsMatch('password', 'password_confirm')])
@require(db = 'ddserver.db:Database',
         messages = 'ddserver.interface.message:MessageManager')
def post_lostpass_setnew(user,
                         data,
                         db,
                         messages):
  encrypted_password = pwd.encrypt(data.password)

  with db.cursor() as cur:
    cur.execute('''
        UPDATE `users`
        SET `password` = %(encrypted_password)s,
            `authcode` = NULL
        WHERE `id` = %(user_id)s
    ''', {'encrypted_password': encrypted_password,
          'user_id': user.id})

  messages.success('Your new password has been set.')

  bottle.redirect('/')



@route('/lostpass/cancel', method = 'POST')
@authorized_by_code()
@require(db = 'ddserver.db:Database',
         messages = 'ddserver.interface.message:MessageManager')
def post_lostpass_cancel(user,
                         db,
                         messages):
  with db.cursor() as cur:
    cur.execute('''
        UPDATE `users`
        SET `authcode` = NULL
        WHERE `id` = %(user_id)s
    ''', {'user_id': user.id})

  messages.success('Your password reset request has been cancelled.')

  bottle.redirect('/')
