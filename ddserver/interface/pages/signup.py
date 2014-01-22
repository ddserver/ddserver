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

from ddserver.utils.deps import require, extend

from ddserver.interface.user import authorized_by_code

from ddserver.interface import validation
from ddserver.interface.validation import validate

from ddserver.interface.captcha import captcha_check

from passlib.apps import custom_app_context as pwd



@extend('ddserver.config:ConfigDeclaration')
def config_signup(config_decl):
  with config_decl.declare('signup') as s:
    s('enabled',
      conv = bool,
      default = True)
    s('allowed_maildomains',
      conv = str,
      default = 'any')
    s('notify_admin',
      conv = bool,
      default = True)



@route('/signup', method = 'GET')
@require(config = 'ddserver.config:Config',
         templates = 'ddserver.interface.template:TemplateManager',
         messages = 'ddserver.interface.message:MessageManager',
         session = 'ddserver.interface.session:SessionManager')
def get_signup(config,
               templates,
               messages,
               session):
  ''' Display the sign up page. '''

  if config.signup.enabled:
    if not session.username:
      return templates['signup.html']()

    else:
      messages.error('You can not signup for an account while you are logged in.')
      bottle.redirect('/')

  else:
    return templates['nosignup.html']()



@route('/signup', method = 'POST')
@captcha_check('/signup')
@validate('/signup',
          username = validation.UniqueUsername(),
          email = validation.Email())
@require(db = 'ddserver.db:Database',
         users = 'ddserver.interface.user:UserManager',
         emails = 'ddserver.mail:EmailManager',
         config = 'ddserver.config:Config',
         messages = 'ddserver.interface.message:MessageManager')
def post_signup(data,
                db,
                users,
                emails,
                config,
                messages):
  ''' Create a new user account. '''

  if not config.signup.enabled:
    messages.error('User registration is currently disabled. Sorry.')
    bottle.redirect('/')

  # Get domain part of email
  email_domain = data.email.split('@', 1)[1]

  with db.cursor() as cur:
    cur.execute('''
      INSERT
      INTO users
      SET `username` = %(username)s,
          `email` = %(email)s,
          `admin` = 0,
          `active` = 0,
          `created` = CURRENT_TIMESTAMP
    ''', {'username': data.username,
          'email': data.email})

  # Check if the user can be activated directly
  if (config.signup.allowed_maildomains == 'any' or
      email_domain in config.signup.allowed_maildomains):
    # Generate auth code
    users.generate_authcode(data.username)

    # Get user record
    user = users[data.username]

    # Send out activation mail
    try:
      emails.to_user('signup_activate.mail',
                     user = user)

    except:
      # Failed to send activation email.
      # We reset the authcode in this case, so an admin can send
      # a new one after fixing email issues
      with db.cursor() as cur:
        cur.execute('''
            UPDATE users
            SET `authcode` = %(authcode)s
            WHERE `username` = %(username)s
        ''', {'authcode': None,
              'username': data.username})

      messages.error('Failed to send activation email. Please contact an administrator at %s' %
                     config.contact.email)

    else:
      messages.success('Your account has been created. You should receive an activation email in some minutes.')

  else:
    # Get user record
    user = users[data.username]

    messages.success('Your account has been created and will be reviewed by an administrator.')

  # Notify the admin about the new account
  if config.signup.notify_admin:
    try:
      emails.to_admin('signup_notify.mail',
                      user = user)

    except:
      messages.error('Failed to notify the administrator. Please contact %s' %
                     config.contact.email)

  bottle.redirect('/')



@route('/signup/activate', method = 'GET')
@require(templates = 'ddserver.interface.template:TemplateManager')
def get_signup_activate(templates):
  ''' Displays the activation form. '''

  return templates['activate.html'](username = bottle.request.query.username,
                                    authcode = bottle.request.query.authcode)



@route('/signup/activate', method = 'POST')
@authorized_by_code()
@validate(password = validation.SecurePassword(min = 8),
          password_confirm = validation.String(),
          chained_validators = [validation.FieldsMatch('password', 'password_confirm')])
@require(db = 'ddserver.db:Database',
         messages = 'ddserver.interface.message:MessageManager')
def post_signup_activate(user,
                         data,
                         db,
                         messages):
  ''' Activates an account. '''

  encrypted_password = pwd.encrypt(data.password)

  with db.cursor() as cur:
    cur.execute('''
        UPDATE users
        SET `active` = 1,
            `password` = %(password)s,
            `authcode` = NULL
        WHERE `id` = %(user_id)s
    ''', {'password': encrypted_password,
          'user_id': user.id})

  messages.success('Your account is active now. Please login.')

  bottle.redirect('/')



@route('/signup/cancel', method = 'POST')
@authorized_by_code()
@validate(username = validation.String(),
          authcode = validation.String())
@require(db = 'ddserver.db:Database',
         messages = 'ddserver.interface.message:MessageManager')
def post_signup_cancel(user,
                       data,
                       db,
                       messages):
  ''' Cancels a sign up. '''

  with db.cursor() as cur:
    cur.execute('''
        DELETE
        FROM users
        WHERE `id` = %(user_id)s
    ''', { 'user_id': user.id})

  messages.success('Signup cancelled. Your account has been removed.')

  bottle.redirect('/')
