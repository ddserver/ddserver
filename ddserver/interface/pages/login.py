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

from ddserver.interface.user import authorized_by_code, authorized

from ddserver.interface import validation
from ddserver.interface.validation import validate



@route('/_auth/login', method = 'POST')
@validate('/',
          username = validation.ValidUsername(min = 1, max = 255),
          password = validation.String())
@require(users = 'ddserver.interface.user:UserManager')
def post_login(data,
               users):
  ''' Handles user authentication. '''

  users.login(username = data.username,
              password = data.password)

  return {
          'success': 'true',
          'message': 'Authenticated as ' + username + '.'
          }


@route('/_auth/logout', method = 'GET')
@require(users = 'ddserver.interface.user:UserManager')
def get_logout(users):
  ''' Handles user logout. '''

  users.logout()

  return {
          'success': 'true',
          'message': 'Logged out.'
          }


@route('/api/v1/profile', method='GET')
@authorized()
def get_login_status():
  return {'test': 'success'}

