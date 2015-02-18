"""
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
"""

import os

import bottle

from ddserver.web import route

from ddserver.interface.user import authorized

from require import require, extend



@extend('ddserver.config:ConfigDeclaration')
def config_wsgi(config_decl):
  with config_decl.declare('wsgi') as s:
    s('static_files',
      conv = str,
      default = '/usr/share/ddserver/static')



@route('/static/<path:path>', method = 'GET')
@require(config = 'ddserver.config:Config')
def get_static(path,
               config):
  """ Provides a route to static files (like css, images, etc).
  """

  return bottle.static_file(path,
                            root = config.wsgi.static_files)



@route('/', method = 'GET')
@require(db = 'ddserver.db:Database',
         templates = 'ddserver.interface.template:TemplateManager',
         session = 'ddserver.interface.session:SessionManager')
def get_index(db,
              templates,
              session):
  """ Display the index page.
  """

  if session.username:
    motd = None
    if os.path.isfile('/etc/ddserver/motd'):
      motd = open('/etc/ddserver/motd').read()

    (users, zones, hosts, userhosts) = get_statistics()

    return templates['index.html'](users = users,
                                   zones = zones,
                                   hosts = hosts,
                                   userhosts = userhosts,
                                   current_ip = bottle.request.remote_addr,
                                   motd = motd)

  else:
    return templates['index.html']()



@require(db = 'ddserver.db:Database')
@authorized()
def get_statistics(user,
                   db):
  """ collect some statistics, which will be displayed on the index page
  """
  with db.cursor() as cur:
    cur.execute('''
      SELECT COUNT(`id`) AS count
      FROM `users`
    ''')
    users = cur.fetchone()

    cur.execute('''
      SELECT COUNT(`id`) AS count
      FROM `suffixes`
    ''')
    zones = cur.fetchone()

    cur.execute('''
      SELECT COUNT(`id`) AS count
      FROM `hosts`
    ''')
    hosts = cur.fetchone()


    cur.execute('''
      SELECT COUNT(`id`) AS count
      FROM `hosts`
      WHERE `user_id` = %(user_id)s
    ''', {'user_id': user.id })
    userhosts = cur.fetchone()

    return (users, zones, hosts, userhosts)
