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

from ddserver.interface.user import authorized

from ddserver.interface import validation
from ddserver.interface.validation import validate

from passlib.apps import custom_app_context as pwd
import formencode



@route('/user/host/<host_id>', method = 'GET')
@authorized()
@require(db = 'ddserver.db:Database',
         templates = 'ddserver.interface.template:TemplateManager',
         messages = 'ddserver.interface.message:MessageManager')
def get_host_display(user,
                     host_id,
                     db,
                     templates,
                     messages):
  ''' Display the users hostnames and a form for adding new ones. '''

  with db.cursor() as cur:
    # Get host details
    cur.execute('''
        SELECT
          `host`.`id` AS `id`,
          `host`.`hostname` AS `hostname`,
          `suffix`.`name` AS `suffix`,
          `host`.`address` AS `address`,
          `host`.`updated` AS `updated`,
          `host`.`description` AS `description`
        FROM `hosts` AS `host`
        LEFT JOIN `suffixes` AS `suffix`
          ON ( `suffix`.`id` = `host`.`suffix_id` )
        WHERE `host`.`id` = %(id)s
          AND `host`. `user_id` = %(user_id)s
    ''', {'id': host_id,
          'user_id': user.id})
    host = cur.fetchone()

  if host is None:
    messages.error('Hostname not found or no access!')
    bottle.redirect('/user/hosts/list')

  return templates['host.html'](host = host,
                                current_ip = bottle.request.remote_addr)



@route('/user/host/updateAddress', method = 'POST')
@authorized()
@validate('/user/hosts/list',
          host_id = formencode.validators.Int(),
          address = validation.IPAddress(),
          description = validation.String(max = 255))
@require(db = 'ddserver.db:Database',
         config = 'ddserver.config:Config',
         messages = 'ddserver.interface.message:MessageManager')
def post_host_update_address(user,
                             data,
                             db,
                             config,
                             messages):
  ''' Update the IP address and/or description of a hostname. '''

  with db.cursor() as cur:
    cur.execute('''
      UPDATE `hosts`
        SET  `address` = %(address)s,
             `description` = %(description)s
      WHERE  `id` = %(host_id)s
        AND  `user_id` = %(user_id)s
    ''', {'address': data.address,
          'description': data.description,
          'host_id': data.host_id,
          'user_id': user.id})

  messages.success('Ok, done.')

  bottle.redirect('/user/hosts/list')



@route('/user/host/updatePassword', method = 'POST')
@authorized()
@validate('/user/hosts/list',
          host_id = formencode.validators.Int(),
          password = validation.SecurePassword(min = 8),
          password_confirm = validation.String(),
          chained_validators = [validation.FieldsMatch('password', 'password_confirm')])
@require(db = 'ddserver.db:Database',
         config = 'ddserver.config:Config',
         messages = 'ddserver.interface.message:MessageManager')
def post_host_update_password(user,
                              data,
                              db,
                              config,
                              messages):
  ''' Update the password of a hostname. '''

  encrypted_password = pwd.encrypt(data.password)

  with db.cursor() as cur:
    cur.execute('''
      UPDATE `hosts`
        SET  `password` = %(password)s
      WHERE  `id` = %(host_id)s
        AND  `user_id` = %(user_id)s
    ''', {'password': encrypted_password,
          'host_id': data.host_id,
          'user_id': user.id})

  messages.success('Ok, done.')

  bottle.redirect('/user/hosts/list')
