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

import argparse



# Define a argument parser
parser = argparse.ArgumentParser()
parser.add_argument('-v', '--verbose',
                    const = True,
                    default = False,
                    action = 'store_const',
                    dest = 'verbose',
                    help = 'show more verbose messages')
parser.add_argument('-c', '--config',
                    type = file,
                    dest = 'config',
                    default = '/etc/ddserver.conf',
                    help = 'path to the config file to load')

parser_dns = parser.add_argument_group(title = 'DNS options')
parser_dns.add_argument('--dns-suffix',
                        dest = 'dns_suffix',
                        type = str,
                        metavar = 'SUFFIX',
                        help = 'the dynamic domain suffix to remove from update requests')
parser_dns.add_argument('--dns-max-hosts',
                        dest = 'dns_max_hosts',
                        type = str,
                        metavar = 'MAX_HOSTS',
                        help = 'the maximum number of hosts per user')

parser_wsgi = parser.add_argument_group(title = 'WSGI options')
parser_wsgi.add_argument('--wsgi-standalone',
                         dest = 'wsgi_standalone',
                         const = True,
                         action = 'store_const',
                         help = 'run in stand-alone mode')
parser_wsgi.add_argument('--wsgi-host',
                         dest = 'wsgi_host',
                         type = str,
                         default = 'localhost',
                         metavar = 'HOST',
                         help = 'the WSGI host to listen on')
parser_wsgi.add_argument('--wsgi-port',
                         dest = 'wsgi_port',
                         type = int,
                         default = '8080',
                         metavar = 'PORT',
                         help = 'the WSGI port to listen on')

parser_db = parser.add_argument_group(title = 'Database options')
parser_db.add_argument('--db-host',
                       dest = 'database_host',
                       type = str,
                       metavar = 'DB_HOST',
                       help = 'the database host to connect to')
parser_db.add_argument('--db-port',
                       dest = 'database_port',
                       type = int,
                       default = '3306',
                       metavar = 'DB_PORT',
                       help = 'the database port to connect to')
parser_db.add_argument('--db-name',
                       dest = 'database_name',
                       type = str,
                       default = 'ddserver',
                       metavar = 'DB_HOST',
                       help = 'the database name to connect to')
parser_db.add_argument('--db-user',
                       dest = 'database_username',
                       type = str,
                       default = 'ddserver',
                       metavar = 'DB_USER',
                       help = 'the database username to connect with')
parser_db.add_argument('--db-pass',
                       dest = 'database_password',
                       type = str,
                       metavar = 'DB_PASS',
                       help = 'the database password to connect with')

parser_auth = parser.add_argument_group(title = 'Authentication options')
parser_auth.add_argument('--auth-passwd-min-chars',
                         dest = 'auth_passwd_min_chars',
                         type = int,
                         default = '8',
                         metavar = 'AUTH_PASSWD_MIN_CHARS',
                         help = 'the minimal number of password characters')



class Config(object):
  ''' Allows to read configuration values in form Config.section.key
      from the configuration file.
  '''

  def __init__(self):
    # Parse the command line arguments
    self.__args = parser.parse_args()

    # Create the config store
    self.__parser = SafeConfigParser()

    # Apply the default values
    for key in vars(self.__args).iterkeys():
      value = parser.get_default(key)

      # Skip unset values
      if value is None:
        continue

      # Split key in section and option
      if not '_' in key:
        section, option = 'general', key

      else:
        section, option = key.split('_', 1)

      # Ensure section exists
      if section not in self.__parser.sections():
        self.__parser.add_section(section)

      # Update the value
      self.__parser.set(section, option, str(value))

    # Load the config file
    if self.__args.config:
      self.__parser.read(self.__args.config)

    # Apply the config from the command line
    for key, value in vars(self.__args).iteritems():
      # Skip unset values
      if value is None:
        continue

      # Split key in section and option
      if not '_' in key:
        section, option = 'general', key

      else:
        section, option = key.split('_', 1)

      # Ensure section exists
      if section not in self.__parser.sections():
        self.__parser.add_section(section)

      # Update the value
      self.__parser.set(section, option, str(value))


  def __getitem__(self,
                  section):
    parser = self.__parser

    class SectionWrapper():
      def __init__(self):
        pass

      def __getitem__(self, option):
        if not parser.has_section(section) or \
           not parser.has_option(section, option):
          return None

        return parser.get(section, option)

      def __getattr__(self, option):
        return self[option]

      def __iter__(self):
        return iter(parser.items(section))

    return SectionWrapper()

  def __getattr__(self, option):
    return self[option]


  def has_section(self,
                  section):
    return self.__parser.has_section(section)


  def get(self,
          section,
          option):
    return self.__parser.get(section, option)



config = Config()
