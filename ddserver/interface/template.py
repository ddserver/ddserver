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

from ddserver.utils.deps import export, extend, require

import functools
import jinja2



@export()
class TemplateManager(object):
  def __init__(self):
    self.__environment = jinja2.Environment(loader = jinja2.PackageLoader('ddserver.resources',
                                                                          'templates'))

    self.__globals = {}


  def __getitem__(self, key):
    ''' Returns a template render function for the requested template.

        @param key: the name of the template
    '''

    # Generate the globals and get the template from the environment
    template = self.__environment.get_template(key)

    c = self.__globals['config']()

    # Return the render function of the template
    return functools.partial(template.render, **{name : func()
                                                 for name, func
                                                 in self.__globals.iteritems()})


  @property
  def globals(self):
    ''' The registered globals to inject in each template.

        All values of this dict must be functions returning the global.
    '''

    return self.__globals



@extend('ddserver.interface.template:TemplateManager')
def template_config(templates):
  @require(config = 'ddserver.config:Config')
  def __(config):
    return config

  templates.globals['config'] = __
