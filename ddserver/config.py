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
arg_parser = argparse.ArgumentParser(add_help = False)
arg_parser.add_argument('-v', '--verbose',
                        const = True,
                        default = False,
                        action = 'store_const',
                        dest = 'verbose',
                        help = 'show more verbose messages')
arg_parser.add_argument('-c', '--config',
                        type = file,
                        dest = 'config',
#                         default = '/etc/ddserver.conf',
                        help = 'path to the config file to load')

arg_parser_dns = arg_parser.add_argument_group(title = 'DNS options')
arg_parser_dns.add_argument('--dns-suffix',
                            dest = 'dns_suffix',
                            type = str,
                            metavar = 'SUFFIX',
                            help = 'the dynamic domain suffix to remove from update requests')
arg_parser_dns.add_argument('--dns-max-hosts',
                            dest = 'dns_max_hosts',
                            type = str,
                            metavar = 'MAX_HOSTS',
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
                           metavar = 'DB_HOST',
                           help = 'the database host to connect to')
arg_parser_db.add_argument('--db-port',
                           dest = 'database_port',
                           type = int,
                           default = '3306',
                           metavar = 'DB_PORT',
                           help = 'the database port to connect to')
arg_parser_db.add_argument('--db-name',
                           dest = 'database_name',
                           type = str,
                           default = 'ddserver',
                           metavar = 'DB_HOST',
                           help = 'the database name to connect to')
arg_parser_db.add_argument('--db-user',
                           dest = 'database_username',
                           type = str,
                           default = 'ddserver',
                           metavar = 'DB_USER',
                           help = 'the database username to connect with')
arg_parser_db.add_argument('--db-pass',
                           dest = 'database_password',
                           type = str,
                           metavar = 'DB_PASS',
                           help = 'the database password to connect with')

arg_parser_auth = arg_parser.add_argument_group(title = 'Authentication options')
arg_parser_auth.add_argument('--auth-passwd-min-chars',
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
    args, remaining_args = arg_parser.parse_known_args(namespace = self)

    # Create the config parser and load config file
    conf_parser = SafeConfigParser()
    if args.config:
      conf_parser.read(args.config)

    # Update defaults from config file
    for section in conf_parser.sections():
      arg_parser.set_defaults({'%s_%s' % (section, key) : value
                               for key, value
                               in conf_parser.items(section)})

    # Parse remaining arguments using new parser
    arg_parser.parse_args(remaining_args, namespace = self)


config = Config()
