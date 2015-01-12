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

import enum
import collections

from require import export, require, extend



@export()
class MessageManager(object):
  class Level(enum.Enum):
    success = 'success'
    error = 'error'

  Message = collections.namedtuple('Message', ['level',
                                               'message'])


  def __init__(self):
    self.__messages = []


  @require(session = 'ddserver.interface.session:SessionManager')
  def __push(self, level, message, session):
    if not session.messages:
      session.messages = []

    session.messages.append(self.Message(level = level,
                                         message = message))
    session.save()


  def success(self, message):
    self.__push(self.Level.success, message)


  def error(self, message):
    self.__push(self.Level.error, message)


  @require(session = 'ddserver.interface.session:SessionManager')
  def popall(self, session):
    if not session.messages:
      return []

    messages = session.messages

    session.messages = []
    session.save()

    return messages



@extend('ddserver.interface.template:TemplateManager')
def template_message(template):
  @require(messages = 'ddserver.interface.message:MessageManager')
  def __(messages):
    return messages

  template.globals['messages'] = __
