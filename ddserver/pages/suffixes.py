'''
Copyright 2013 Sven Reissmann <sven@0x80.io>

This file is part of ddserver.

ddserver is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published
by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.

ddserver is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with ddserver.  If not, see <http://www.gnu.org/licenses/>.
'''

from bottle import route, request, redirect

import formencode

from ddserver.db import database as db
from ddserver import templates
from ddserver.config import config
from ddserver.pages.session import authorized_admin
from ddserver.validation.schemas import *



@route('/admin/suffixes')
@authorized_admin
def suffixes_display():
  ''' display a list of suffixes and a form to add new ones
  '''
  session = request.environ.get('beaker.session')

  with db.cursor() as cur:
    cur.execute('''
        SELECT *
        FROM suffixes
        WHERE 1 = 1
    ''')
    suffixes = cur.fetchall()

  template = templates.get_template('suffixes.html')
  return template.render(session = session,
                         suffixes = suffixes)



@route('/admin/suffixes', method = 'POST')
@authorized_admin
@validated(DelSuffixSchema, '/admin/suffixes')
def suffix_delete():
  ''' delete a suffix
  '''
  session = request.environ.get('beaker.session')

  with db.cursor() as cur:
    cur.execute('''
        DELETE
        FROM suffixes
        WHERE id = %(suffix_id)s
    ''', {'suffix_id': request.POST.get('suffixid')})

  session['msg'] = ('success', 'Ok, done.')



@route('/admin/suffixes/add', method = 'POST')
@authorized_admin
@validated(AddSuffixSchema, '/admin/suffixes')
def suffix_add():
  ''' add a new suffix
  '''
  session = request.environ.get('beaker.session')

  with db.cursor() as cur:
    cur.execute('''
      INSERT INTO `suffixes`
      SET `name` = %(suffixname)s
    ''', {'suffixname': request.POST.get('suffixname')})

  session['msg'] = ('success', 'Ok, done.')
