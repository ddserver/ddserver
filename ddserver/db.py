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

import MySQLdb



class DatabaseManager(object):

  thread_local = threading.local()


  def __init__(self):
    pass


  def setup(self,
            dbhost,
            dbport,
            dbname,
            dbuser,
            dbpass):
    self.dbhost = dbhost
    self.dbport = dbport
    self.dbname = dbname
    self.dbuser = dbuser
    self.dbpass = dbpass


  @contextlib.contextmanager
  def cursor(self):
    if not hasattr(DatabaseManager.thread_local, 'db_connection'):
        setattr(DatabaseManager.thread_local, 'db_connection',
                MySQLdb.connect(self.dbhost,
                                self.dbuser,
                                self.dbpass,
                                self.dbname,
                                self.dbport,
                                cursorclass = MySQLdb.cursors.DictCursor))

    connection = getattr(DatabaseManager.thread_local, 'db_connection')

    cursor = connection.cursor()

    try:
      yield cursor

    except:
      connection.rollback()
      raise

    else:
      connection.commit()

    finally:
      cursor.close()



database = DatabaseManager()
