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


import jinja2
import smtplib

from ddserver.utils.deps import export, extend, require



@extend('ddserver.config:ConfigDeclaration')
def config_email(config_decl):
  with config_decl.declare('smtp') as s:
    s('host',
      conv = str,
      default = 'localhost')
    s('port',
      conv = int,
      default = 25)

  with config_decl.declare('contact') as s:
    s('name',
      conv = str,
      default = 'Your Administrator')
    s('email',
      conv = str)

  with config_decl.declare('wsgi') as s:
    s('protocol',
      conv = str,
      default = 'http://')

  with config_decl.declare('wsgi') as s:
    s('basename',
      conv = str,
      default = 'localhost:8080')



@export()
class EmailManager(object):
  def __init__(self):
    self.__environment = jinja2.Environment(loader = jinja2.PackageLoader('ddserver.resources',
                                                                          'email'))


  @require(config = 'ddserver.config:Config')
  def __send(self,
             key,
             rcpt,
             config,
             **kwargs):
    ''' Sends a mail.

        @param key: the name of the template used for the mail
        @param rcpt: the recipient mail address
        @param **kwargs: all remaining arguments are passed to the template
    '''

    # Load the template
    template = self.__environment.get_template(key)

    # Open SMTP connection
    smtp = smtplib.SMTP(host = config.smtp.host,
                        port = config.smtp.port)

    # Send mail
    smtp.sendmail(config.contact.email,
                  [rcpt],
                  template.render(rcpt = rcpt,
                                  config = config,
                                  **kwargs))

    # Close SMTP connection
    smtp.quit()


  def to_user(self,
              key,
              user,
              **kwargs):
    self.__send(key = key,
                rcpt = user.email,
                user = user,
                **kwargs)


  @require(config = 'ddserver.config:Config')
  def to_admin(self,
               key,
               config,
               **kwargs):
    self.__send(key = key,
                rcpt = config.contact.email,
                **kwargs)
