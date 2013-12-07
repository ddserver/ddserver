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

from ddserver.utils.deps import extend, require

from ddserver.interface.user import authorized

from ddserver.interface import validation
from ddserver.interface.validation import validate

from passlib.apps import custom_app_context as pwd



@extend('ddserver.config:ConfigDeclaration')
def config_auth(config_decl):
  with config_decl.declare('dns') as s:
    s('max_hosts',
       conv = int,
       default = 5)



@route('/user/hosts', method = 'GET')
@authorized()
@require(db = 'ddserver.db:Database',
         templates = 'ddserver.interface.template:TemplateManager')
def get_hosts_display(user,
                      db,
                      templates):
  ''' Display the users hostnames and a form for adding new ones. '''

  with db.cursor() as cur:
    # Get all available suffixes
    cur.execute('''
        SELECT *
        FROM `suffixes`
    ''')
    suffixes = cur.fetchall()

    # Get hosts of the user
    cur.execute('''
        SELECT
          `host`.`id` AS `id`,
          `host`.`hostname` AS `hostname`,
          `suffix`.`name` AS `suffix`,
          `host`.`address` AS `address`,
          `host`.`updated` AS `updated`
        FROM `hosts` AS `host`
        LEFT JOIN `suffixes` AS `suffix`
          ON ( `suffix`.`id` = `host`.`suffix_id` )
        WHERE `user_id` = %(user_id)s
    ''', {'user_id': user.id})
    hosts = cur.fetchall()

  return templates['hosts.html'](hosts = hosts,
                                 suffixes = suffixes)



@route('/user/hosts/add', method = 'POST')
@authorized()
@validate('/user/hosts',
          hostname = validation.UniqueHostname(),
          suffix = validation.Int(not_empty = True),
          address = validation.IPAddress(),
          password = validation.SecurePassword(min = 8),
          password_confirm = validation.String(),
          chained_validators = [validation.FieldsMatch('password', 'password_confirm')])
@require(db = 'ddserver.db:Database',
         config = 'ddserver.config:Config',
         messages = 'ddserver.interface.message:MessageManager')
def post_hosts_add(user,
                   data,
                   db,
                   config,
                   messages):
  ''' Add a new hostname. '''

  # We do net check passed suffix, as mysql will tell us later on

  encrypted_password = pwd.encrypt(data.password)

  with db.cursor() as cur:
    cur.execute('''
      SELECT *
      FROM `hosts`
      WHERE `user_id` = %(user_id)s
    ''', {'user_id': user.id})

    if cur.rowcount >= config.dns.max_hosts:
      messages.error('Maximum number of hosts reached')
      bottle.redirect('/user/hosts')

    cur.execute('''
      INSERT
      INTO `hosts`
      SET `hostname` = %(hostname)s,
          `address` = %(address)s,
          `password` = %(password)s,
          `user_id` = %(user_id)s,
          `suffix_id` = %(suffix_id)s
    ''', {'hostname': data.hostname,
          'address': data.address,
          'password': encrypted_password,
          'user_id' : user.id,
          'suffix_id': data.suffix})

  messages.success('Ok, done.')

  bottle.redirect('/user/hosts')



@route('/user/hosts/delete', method = 'POST')
@authorized()
@validate('/user/hosts',
          host_id = validation.Int(not_empty = True))
@require(db = 'ddserver.db:Database',
         messages = 'ddserver.interface.message:MessageManager')
def post_hosts_delete(user,
                      data,
                      db,
                      messages):
  ''' Delete a hostname. '''

  # We do not check the host id for existence and belonging as we only delete
  # host of the user

  with db.cursor() as cur:
    cur.execute('''
        DELETE
        FROM hosts
        WHERE id = %(host_id)s
          AND user_id = %(user_id)s
    ''', {'host_id': data.host_id,
          'user_id': user.id})

  messages.success('Ok, done.')

  bottle.redirect('/user/hosts')
