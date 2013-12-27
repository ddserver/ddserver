'''
Copyright 2013 Dustin Frisch<fooker@lab.sh>

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

import contextlib
import threading

import MySQLdb.cursors

from ddserver.utils.deps import extend, export, require



@extend('ddserver.config:ConfigDeclaration')
def config_db(config_decl):
  with config_decl.declare('db') as s:
    s('host',
      conv = str,
      default = 'localhost')
    s('port',
      conv = int,
      default = 3306)
    s('name',
      conv = str,
      default = 'ddserver')
    s('username',
      conv = str,
      default = 'ddserver')
    s('password',
      conv = str)



@export(config = 'ddserver.config:Config')
class Database(object):

  def __init__(self,
               config):
    self.__connection = MySQLdb.connect(host = config.db.host,
                                       port = config.db.port,
                                       user = config.db.username,
                                       passwd = config.db.password,
                                       db = config.db.name,
                                       cursorclass = MySQLdb.cursors.DictCursor)


  def __del__(self):
    self.__connection.close()


  @contextlib.contextmanager
  def cursor(self):
    cursor = self.__connection.cursor()

    try:
      yield cursor

    except:
      self.__connection.rollback()
      raise

    else:
      self.__connection.commit()

    finally:
      cursor.close()
