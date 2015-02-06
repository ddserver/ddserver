'''
Copyright 2013 Dustin Frisch<fooker@lab.sh>

This file is part of ddserver.

ddserver is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

ddserver is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with ddserver.  If not, see <http://www.gnu.org/licenses/>.
'''

import sys
import logging

from ddserver.utils.deps import extend, export

from ddserver.config import parse_bool



@extend('ddserver.config:ConfigDeclaration')
def config_logging(config_decl):
  with config_decl.declare('logging') as s:
    s('verbose',
      conv = parse_bool,
      default = False)
    s('file',
      conv = str,
      default = '/var/log/ddserver.log')


@export(config = 'ddserver.config:Config')
def Logger(config):
  logging.root.addHandler(logging.FileHandler(filename = config.logging.file))

  if config.logging.verbose:
    logging.root.addHandler(logging.StreamHandler(stream = sys.stderr))
    logging.root.setLevel(logging.DEBUG)

  return logging.getLogger('ddserver')
