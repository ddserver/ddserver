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

import beaker.middleware

from ddserver.utils.deps import export, extend, require



@extend('ddserver.web:Middleware')
def middleware_session(middleware):
  return beaker.middleware.SessionMiddleware(middleware,
                                             {'session.cookie_expires': True})



@export()
class SessionManager(object):
  def __init__(self):
    pass


  @property
  def session(self):
    return bottle.request.environ.get('beaker.session')


  def __getattr__(self, key):
    try:
      return self.session[key]

    except KeyError:
      return None


  def __setattr__(self, key, value):
    self.session[key] = value


  def __delattr__(self, key):
    del self.session[key]


  def save(self):
    self.session.save()



@extend('ddserver.interface.template:TemplateManager')
def template_session(templates):
  @require(session = 'ddserver.interface.session:SessionManager')
  def __(session):
    return session

  templates.globals['session'] = __
