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

from require import require

from ddserver.web import route

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
  """ Display a list of users. Depending on the mode, show all users,
      only show admins, or only show accounts that are awaiting activation.
  """

  if mode == 'admins':
      where = 'WHERE `admin` = 1'

  elif mode == 'inactive':
      where = 'WHERE `active` = 0'

  else:
      where = 'WHERE 1 = 1'

  with db.cursor() as cur:
    cur.execute('''
        SELECT *
        FROM `users`
    ''' + where)
    users = cur.fetchall()

  return templates['users.html'](users = users,
                                 user = user,
                                 mode = mode)


@route('/admin/user/<userid>/hosts')
@authorized_admin()
@require(db = 'ddserver.db:Database',
         templates = 'ddserver.interface.template:TemplateManager')
def get_user_hosts(user,
                   userid,
                   db,
                   templates):
  """ Display a list of a users hostnames.
  """

  with db.cursor() as cur:
    cur.execute('''
        SELECT `hosts`.*,
               `suffixes`.`name` AS suffix,
               `users`.`username` AS username
        FROM `hosts`
        RIGHT JOIN `suffixes`
          ON `suffixes`.`id` = `hosts`.`suffix_id`
        RIGHT JOIN `users`
          ON `hosts`.`user_id` = `users`.`id`
        WHERE `user_id` = %(userid)s
    ''', {'userid': int(userid)})
    hosts = cur.fetchall()

  return templates['userhosts.html'](hosts = hosts,
                                     user = user)


@route('/admin/users/add', method = 'GET')
@authorized_admin()
@require(templates = 'ddserver.interface.template:TemplateManager')
def get_user_add(user,
                 templates):
  ''' Adds a new user. '''
  return templates['adduser.html']()



@route('/admin/users/add', method = 'POST')
@authorized_admin()
@validate('/admin/users/add',
          username = validation.UniqueUsername(max = 255),
          email = validation.Email())
@require(db = 'ddserver.db:Database',
         users = 'ddserver.interface.user:UserManager',
         emails = 'ddserver.mail:EmailManager',
         messages = 'ddserver.interface.message:MessageManager')
def post_user_add(user,
                  data,
                  db,
                  users,
                  emails,
                  messages):
  ''' Manually add a new user. '''

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

    messages.error('Failed to send activation email.')

  else:
    messages.success('Account created. The user will get an activation email.')

  bottle.redirect('/admin/users/all')



@route('/admin/users/activate', method = 'POST')
@authorized_admin()
@validate('/admin/users/all',
          username = validation.ValidUsername(min = 1, max = 255))
@require(db = 'ddserver.db:Database',
         users = 'ddserver.interface.user:UserManager',
         config = 'ddserver.config:Config',
         emails = 'ddserver.mail:EmailManager',
         messages = 'ddserver.interface.message:MessageManager')
def post_users_activate(user,
                        data,
                        db,
                        users,
                        config,
                        emails,
                        messages):
  ''' Activate a users account. '''

  users.generate_authcode(data.username)
  user = users[data.username]

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

    messages.error('Failed to send the activation email.')

  else:
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

  bottle.redirect('/admin/users/all')



@route('/admin/users/updateMaxhosts', method = 'POST')
@authorized_admin()
@validate('/admin/users/all',
          max_hosts = validation.Int(not_empty = True,
                                     min = -2),
          user_id = validation.Int(not_empty = True))
@require(db = 'ddserver.db:Database',
         messages = 'ddserver.interface.message:MessageManager')
def post_user_updatemaxhosts(user,
                             data,
                             db,
                             messages):
  ''' Update the maximum allowed hostnames of a user . '''

  if data.max_hosts == -2:
    data.max_hosts = None

  with db.cursor() as cur:
    cur.execute('''
        UPDATE `users`
        SET `maxhosts` = %(max_hosts)s
        WHERE `id` = %(user_id)s
    ''', {'max_hosts': data.max_hosts,
          'user_id': data.user_id})

  messages.success('Ok, done.')

  bottle.redirect('/admin/users/all')

