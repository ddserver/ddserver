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

from ddserver.interface.user import authorized_admin

from ddserver.interface import validation
from ddserver.interface.validation import validate



@route('/admin/users/<mode>')
@authorized_admin()
@require(db = 'ddserver.db:Database',
         templates = 'ddserver.interface.template:TemplateManager')
def get_users(user,
              db,
              templates,
              mode = 'all'):
  ''' Display a list of users that are waiting for account activation. '''

  if mode == 'admins':
      where = 'WHERE `admin` = 1'

  elif mode == 'inactive':
      where = 'WHERE `active` = NULL'

  else:
      where = 'WHERE 1 = 1'

  with db.cursor() as cur:
    cur.execute('''
        SELECT *
        FROM `users`
    ''' + where)
    users = cur.fetchall()

  return templates['users.html'](users = users,
                                 mode = mode)



# @route('/admin/users/add', method = 'GET')
# @authorized_admin()
# @require(templates = 'ddserver.interface.template:TemplateManager')
# def get_user_add(templates):
#   ''' Adds a new user. '''
#
#   return templates['adduser.html']()
#
#
#
# @route('/admin/users/add', method = 'POST')
# @authorized_admin()
# @validate('/admin/users/add',
#           username = validators.UniqueUsername(),
#           email = validators.Email())
# @require(db = 'ddserver.db:Database',
#          users = 'ddserver.interface.user:UserManager',
#          emails = 'ddserver.email:EmailManager',
#          messages = 'ddserver.interface.message:MessageManager')
# def post_user_add(username,
#                   email,
#                   db,
#                   users,
#                   emails,
#                   messages):
#   ''' Adds a new user. '''
#
#   with db.cursor() as cur:
#     cur.execute('''
#       INSERT
#       INTO users
#       SET `username` = %(username)s,
#           `email` = %(email)s,
#           `admin` = 0,
#           `active` = 0,
#           `created` = CURRENT_TIMESTAMP
#     ''', {'username': username,
#           'email': email})
#
#   users.generate_authcode(username)
#   user = users[username]
#
#   emails.to_user('signup_activate.mail',
#                  user = user)
#
#   messages.success('Account created. The user will get an activation email.')
#
#   bottle.redirect('/admin/users/all')



@route('/admin/users/activate', method = 'POST')
@authorized_admin()
@validate('/admin/users/all',
          username = validation.ValidUsername(min = 1, max = 255))
@require(db = 'ddserver.db:Database',
         users = 'ddserver.interface.user:UserManager',
         emails = 'ddserver.email:EmailManager',
         messages = 'ddserver.interface.message:MessageManager')
def post_users_activate(user,
                        data,
                        db,
                        users,
                        emails,
                        messages):
  ''' Activate a users account. '''

  users.generate_authcode(data.username)
  user = users[data.user_name]

  emails.to_user('signup_activate.mail',
                 user = user)

  messages.success('Ok, done.')

  bottle.redirect('/admin/users/all')



@route('/admin/users/delete', method = 'POST')
@authorized_admin()
@validate('/admin/users/all',
          user_id = validation.Int(not_empty = True))
@require(db = 'ddserver.db:Database',
         messages = 'ddserver.interface.message:MessageManager')
def post_users_delete(user,
                      data,
                      db,
                      messages):
  ''' Delete a users account. '''

  with db.cursor() as cur:
    cur.execute('''
        DELETE
        FROM `users`
        WHERE `id` = %(user_id)s
    ''', { 'user_id': data.user_id})

  messages.success('Ok, done.')

  bottle.redirect('/admin/users/all')



@route('/admin/users/mkadmin', method = 'POST')
@authorized_admin()
@validate('/admin/users/all',
          user_id = validation.Int(not_empty = True))
@require(db = 'ddserver.db:Database',
         messages = 'ddserver.interface.message:MessageManager')
def post_user_mkadmin(user,
                      data,
                      db,
                      messages):
  ''' Makes a users an administrator. '''

  with db.cursor() as cur:
    cur.execute('''
        UPDATE `users`
        SET `admin` = 1
        WHERE `id` = %(user_id)s
    ''', { 'user_id': data.user_id})

  messages.success('Ok, done.')

  bottle.redirect('/admin/users/all')



@route('/admin/users/rmadmin', method = 'POST')
@authorized_admin()
@validate('/admin/users/all',
          user_id = validation.Int(not_empty = True))
@require(db = 'ddserver.db:Database',
         messages = 'ddserver.interface.message:MessageManager')
def post_user_rmadmin(user,
                      data,
                      db,
                      messages):
  ''' Makes a users account a unprivileged user. '''

  with db.cursor() as cur:
    cur.execute('''
        UPDATE `users`
        SET `admin` = NULL
        WHERE `id` = %(user_id)s
    ''', { 'user_id': data.user_id})

  messages.success('Ok, done.')

  bottle.redirect('/admin/users/admin')

