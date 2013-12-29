'''
Copyright 2013 Dustin Frisch <fooker@lab.sh>

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

import uuid
import bottle
import functools
import collections

from passlib.apps import custom_app_context as pwd

from ddserver.utils.deps import export, extend, require



@export()
class UserManager(object):
  User = collections.namedtuple('User', ['id',
                                         'username',
                                         'password',
                                         'email',
                                         'admin',
                                         'active',
                                         'created',
                                         'authcode',
                                         'maxhosts'])


  @require(db = 'ddserver.db:Database')
  def __getitem__(self,
                  key,
                  db):
    ''' Returns the user record for the given username.

        @param key: the username

        @return: the user record or None if no such user exists
    '''

    with db.cursor() as cur:
      cur.execute('''
          SELECT *
          FROM users
          WHERE username = %(username)s
      ''', {'username': key})
      row = cur.fetchone()

      if row:
        return self.User(**row)


  @require(session = 'ddserver.interface.session:SessionManager',
           messages = 'ddserver.interface.message:MessageManager')
  def login(self,
            session,
            messages,
            username,
            password):
    ''' Tries to authenticate the session.

        @param username: the name of the user to authenticate
        @param password: the password for the user
    '''

    user = self[username]

    if not user or not pwd.verify(password, user.password):
      messages.error('The username or password you entered was incorrect.')

      return False

    elif not user.active:
      messages.error('This account has not yet been activated.')

      return False

    else:
      session.username = username
      session.save()

    messages.success('Welcome, %s' % username)

    return True



  @require(session = 'ddserver.interface.session:SessionManager',
           messages = 'ddserver.interface.message:MessageManager')
  def logout(self,
             session,
             messages):
    ''' Deauthenticates the session. '''

    session.username = None
    session.save()

    messages.success('Good bye.')


  @require(db = 'ddserver.db:Database')
  def generate_authcode(self, username, db):
    # Make a new auth code
    authcode = uuid.uuid4()

    # Update the auth code for the user
    with db.cursor() as cur:
      cur.execute('''
          UPDATE users
          SET `authcode` = %(authcode)s
          WHERE `username` = %(username)s
      ''', {'authcode': authcode,
            'username': username})

    return authcode


  @property
  @require(session = 'ddserver.interface.session:SessionManager')
  def authorized(self, session):
    if session.username:
      return self[session.username]



def authorized(admin = False):
  ''' Checks if the session is authorized.

      @param admin: If set to True, the session must be authorized by a user
                    which has the admin flag set in her account
  '''

  def wrapper(func):
    @require(users = 'ddserver.interface.user:UserManager',
             messages = 'ddserver.interface.message:MessageManager')
    def wrapped(users,
                messages,
                *args,
                **kwargs):
      user = users.authorized

      if not user or (admin and not user.admin):
        messages.error('You are not authorized to display this page!')
        bottle.redirect('/')

      # Inject the user in the wrapped function
      return func(*args,
                  user = user,
                  **kwargs)

    return wrapped
  return wrapper


authorized_admin = functools.partial(authorized, True)



def authorized_by_code():
  ''' Checks if a valid username and authcode is passed. '''

  def wrapper(func):
    @require(users = 'ddserver.interface.user:UserManager',
             messages = 'ddserver.interface.message:MessageManager')
    def wrapped(users,
                messages,
                *args,
                **kwargs):
      if (bottle.request.query.username == "" or
         bottle.request.query.authcode == ""):
        messages.error('You have to provide username and authcode!')
        bottle.redirect('/')

      username = bottle.request.query.username
      authcode = bottle.request.query.authcode

      user = users[username]

      if user.authcode != authcode:
        messages.error('The auth code you provided was invalid!')
        bottle.redirect('/')

      # Inject the user in the wrapped function
      return func(*args,
                  user = user,
                  **kwargs)

    return wrapped
  return wrapper



@extend('ddserver.interface.template:TemplateManager')
def template_auth(templates):
  @require(users = 'ddserver.interface.user:UserManager')
  def __(users):
    return users.authorized

  templates.globals['user'] = __
