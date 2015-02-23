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



@route('/admin/suffixes/list', method = 'GET')
@authorized_admin()
@require(db = 'ddserver.db:Database',
         templates = 'ddserver.interface.template:TemplateManager')
def get_suffix_list(user,
                    db,
                    templates):
  ''' Display a list of available suffixes (zones) '''

  with db.cursor() as cur:
    cur.execute('''
      SELECT `suffixes`.*, COUNT(`hosts`.`id`) AS count
        FROM `suffixes`
      LEFT JOIN `hosts`
        ON `suffixes`.`id` = `hosts`.`suffix_id`
      GROUP BY `suffixes`.`id`
    ''')
    suffixes = cur.fetchall()

  return templates['suffixes.html'](suffixes = suffixes)



@route('/admin/suffixes/add', method = 'GET')
@authorized_admin()
@require(db = 'ddserver.db:Database',
         config = 'ddserver.config:Config',
         templates = 'ddserver.interface.template:TemplateManager')
def get_suffix_add(user,
                   db,
                   config,
                   templates):
  '''  Display a form for adding new suffixes (zones) '''

  return templates['addsuffix.html']()



@route('/admin/suffixes/add', method = 'POST')
@authorized_admin()
@validate('/admin/suffixes/add',
          suffix_name = validation.ValidSuffix(min = 1, max = 255))
@require(db = 'ddserver.db:Database',
         messages = 'ddserver.interface.message:MessageManager')
def post_suffix_add(user,
                    data,
                    db,
                    messages):
  ''' Add a new suffix. '''

  with db.cursor() as cur:
    cur.execute('''
      SELECT *
      FROM `suffixes`
      WHERE `name` = %(name)s
    ''', {'name': data.suffix_name})

    if cur.rowcount > 0:
      messages.error('Suffix with same name already exists')
      bottle.redirect('/admin/suffixes/add')

    cur.execute('''
      INSERT
      INTO `suffixes`
      SET `name` = %(name)s
    ''', {'name': data.suffix_name})

  messages.success('Ok, done.')

  bottle.redirect('/admin/suffixes/list')



@route('/admin/suffixes/delete', method = 'POST')
@authorized_admin()
@validate('/admin/suffixes/list',
          suffix_id = validation.Int(not_empty = True))
@require(db = 'ddserver.db:Database',
         messages = 'ddserver.interface.message:MessageManager')
def post_suffix_delete(user,
                       data,
                       db,
                       messages):
  ''' Delete a suffix. '''

  with db.cursor() as cur:
    cur.execute('''
      DELETE
      FROM `suffixes`
      WHERE id = %(suffix_id)s
    ''', {'suffix_id': data.suffix_id})

  messages.success('Ok, done.')

  bottle.redirect('/admin/suffixes/list')


@route('/admin/suffix/<suffix_id>', method = 'GET')
@authorized_admin()
@require(db = 'ddserver.db:Database',
         templates = 'ddserver.interface.template:TemplateManager')
def get_suffix_hostnames(user,
                         db,
                         templates,
                         suffix_id):
  ''' Display a list of hostnames for a given suffixes. '''

  with db.cursor() as cur:
    cur.execute('''
      SELECT `suffixes`.`name` AS suffixname
        FROM `suffixes`
      WHERE `suffixes`.`id` = %(suffix_id)s
    ''', {'suffix_id': suffix_id})
    suffixname = cur.fetchone()

    cur.execute('''
      SELECT `users`.`username` AS username,
             `hosts`.*
        FROM `suffixes`
      RIGHT JOIN `hosts`
        ON `suffixes`.`id` = `hosts`.`suffix_id`
      RIGHT JOIN `users`
        ON `hosts`.`user_id` = `users`.`id`
      WHERE `suffixes`.`id` = %(suffix_id)s
    ''', {'suffix_id': suffix_id})
    hostlist = cur.fetchall()

  return templates['suffix_hosts.html'](suffix = suffixname,
                                        hostlist = hostlist)




@route('/admin/suffix/deleteHost', method = 'POST')
@authorized_admin()
@validate('/admin/suffixes/list',
          host_id = validation.Int(not_empty = True))
@require(db = 'ddserver.db:Database',
         messages = 'ddserver.interface.message:MessageManager')
def post_hosts_delete(user,
                      data,
                      db,
                      messages):
  ''' Delete a hostname administratively. '''

  with db.cursor() as cur:
    cur.execute('''
        DELETE
        FROM hosts
        WHERE id = %(host_id)s
    ''', {'host_id': data.host_id})

  messages.success('Ok, done.')

  bottle.redirect('/admin/suffixes/list')



@route('/admin/suffix/disableHost', method = 'POST')
@authorized_admin()
@validate('/admin/suffixes/list',
          host_id = validation.Int(not_empty = True),
          reason = validation.String(max = 1000))
@require(db = 'ddserver.db:Database',
         messages = 'ddserver.interface.message:MessageManager')
def post_host_disable(user,
                      data,
                      db,
                      messages):
  """ Disable a hostname administratively.
  """

  with db.cursor() as cur:
    cur.execute('''
        UPDATE hosts
           SET `abuse` = %(reason)s
         WHERE `id` = %(host_id)s
    ''', {'host_id': data.host_id,
          'reason': data.reason.replace('\n', '').replace('\r', '')})

  messages.success('Ok, done.')

  bottle.redirect('/admin/suffixes/list')



@route('/admin/suffix/enableHost', method = 'POST')
@authorized_admin()
@validate('/admin/suffixes/list',
          host_id = validation.Int(not_empty = True))
@require(db = 'ddserver.db:Database',
         messages = 'ddserver.interface.message:MessageManager')
def post_host_disable(user,
                      data,
                      db,
                      messages):
  """ Enable a hostname administratively.
  """

  with db.cursor() as cur:
    cur.execute('''
        UPDATE hosts
           SET `abuse` = NULL
         WHERE `id` = %(host_id)s
    ''', {'host_id': data.host_id})

  messages.success('Ok, done.')

  bottle.redirect('/admin/suffixes/list')