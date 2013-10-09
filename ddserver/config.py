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



# Define a argument arg_parser



class Config(object):
  ''' Parses command line arguments and a config file.

      Tthe command line arguments defined will be parsed. If a config file is
      specified in the arguments, it will be read and mixed up with the command
      line arguments by overwriting the defaults but net the specified values.

      The transformation between the values in the config file and the arguments
      uses the following pattern:
        For the general section, the key is used. For every other section, the
        section name is combined with the value name separated with an
        underscore. If the name contains any score, it is replaced with an
        underscore (see 'argparse' 'dest' transformation rules).
  '''

  arg_parser = argparse.ArgumentParser()
  arg_parser.add_argument('-v', '--verbose',
                          const = True,
                          default = False,
                          action = 'store_const',
                          dest = 'verbose',
                          help = 'show more verbose messages')
  arg_parser.add_argument('-c', '--config',
                          type = file,
                          metavar = 'FILE',
                          dest = 'config',
                          help = 'path to the config file to load')

  arg_parser_dns = arg_parser.add_argument_group(title = 'DNS options')
  arg_parser_dns.add_argument('--dns-max-hosts',
                              dest = 'dns_max_hosts',
                              type = str,
                              metavar = 'N',
                              help = 'the maximum number of hosts per user')

  arg_parser_wsgi = arg_parser.add_argument_group(title = 'WSGI options')
  arg_parser_wsgi.add_argument('--wsgi-standalone',
                               dest = 'wsgi_standalone',
                               const = True,
                               action = 'store_const',
                               help = 'run in stand-alone mode')
  arg_parser_wsgi.add_argument('--wsgi-host',
                               dest = 'wsgi_host',
                               type = str,
                               default = 'localhost',
                               metavar = 'HOST',
                               help = 'the WSGI host to listen on')
  arg_parser_wsgi.add_argument('--wsgi-port',
                               dest = 'wsgi_port',
                               type = int,
                               default = '8080',
                               metavar = 'PORT',
                               help = 'the WSGI port to listen on')

  arg_parser_db = arg_parser.add_argument_group(title = 'Database options')
  arg_parser_db.add_argument('--db-host',
                             dest = 'database_host',
                             type = str,
                             default = '127.0.0.1',
                             metavar = 'HOST',
                             help = 'the database host to connect to')
  arg_parser_db.add_argument('--db-port',
                             dest = 'database_port',
                             type = int,
                             default = '3306',
                             metavar = 'PORT',
                             help = 'the database port to connect to')
  arg_parser_db.add_argument('--db-name',
                             dest = 'database_name',
                             type = str,
                             default = 'ddserver',
                             metavar = 'HOST',
                             help = 'the database name to connect to')
  arg_parser_db.add_argument('--db-user',
                             dest = 'database_username',
                             type = str,
                             default = 'ddserver',
                             metavar = 'USER',
                             help = 'the database username to connect with')
  arg_parser_db.add_argument('--db-pass',
                             dest = 'database_password',
                             type = str,
                             metavar = 'PASS',
                             help = 'the database password to connect with')

  arg_parser_auth = arg_parser.add_argument_group(title = 'Authentication options')
  arg_parser_auth.add_argument('--auth-passwd-min-chars',
                               dest = 'auth_passwd_min_chars',
                               type = int,
                               default = '8',
                               metavar = 'N',
                               help = 'the minimal number of password characters')


  @staticmethod
  def conf_to_arg(section, key):
    if section == 'general':
      return key.replace('-', '_')

    else:
      return '%s_%s' % (section, key.replace('-', '_'))


  def __init__(self):
    # Parse the command line arguments
    args, _ = Config.arg_parser.parse_known_args()

    # Create the config parser and load config file
    conf_parser = SafeConfigParser()
    if args.config:
      conf_parser.readfp(args.config)

    # Update defaults using the values from config file
    for section in conf_parser.sections():
      Config.arg_parser.set_defaults(**{Config.conf_to_arg(section, key) : value
                                        for key, value
                                        in conf_parser.items(section)})

    # Parse remaining arguments using new parser
    Config.arg_parser.parse_args(namespace = self)


config = Config()
