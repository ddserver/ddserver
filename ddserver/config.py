'''
Copyright 2013 Dustin Frisch <fooker@lab.sh>

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

from ConfigParser import SafeConfigParser



class Config(object):
  ''' Allows to read configuration values in form Config().section['key']
      from the configuration file config/settings.conf
  '''
  __instance = None


  def __new__(cls, *args, **kwargs):
    if cls.__instance is None:
      cls.__instance = object.__new__(cls)
      cls.__instance.__init()

    return cls.__instance


  def __init(self):
    self.__parser = SafeConfigParser()
    self.__parser.read('config/settings.conf')


  def __getattr__(self,
                  section):
    parser = self.__parser

    class SectionWrapper():
      def __init__(self):
        pass

      def __getitem__(self, option):
        return parser.get(section, option)

      def __iter__(self):
        return iter(parser.items(section))

    return SectionWrapper()


  def has_section(self,
                  section):
    return self.__parser.has_section(section)


  def get(self,
          section,
          option):
    return self.__parser.get(section, option)
