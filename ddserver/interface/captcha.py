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

import bottle

from require import extend, require

from ddserver.config import parse_bool



@extend('ddserver.config:ConfigDeclaration')
def config_captcha(config_decl):
  with config_decl.declare('captcha') as s:
    s('enabled',
      conv = parse_bool,
      default = False)
    s('recaptcha_public_key',
      conv = str,
      default = '')
    s('recaptcha_private_key',
      conv = str,
      default = '')



def captcha_check(__on_error__):
  ''' Checks if the captcha challenge and response in the request are matching.

      The challenge and response values are extracted from the POST data and
      passed to the recaptcha API.

      @param __on_error__: The target to redirect if the check failed
  '''

  def wrapper(func):
    @require(config = 'ddserver.config:Config',
             users = 'ddserver.interface.user:UserManager',
             messages = 'ddserver.interface.message:MessageManager')
    def wrapped(config,
                users,
                messages,
                *args,
                **kwargs):
      if config.captcha.enabled:
        from recaptcha.client import captcha

        challenge = bottle.request.POST.pop('recaptcha_challenge_field', None)
        response = bottle.request.POST.pop('recaptcha_response_field', None)

        if challenge is None or response is None:
          messages.error('Captcha values are missing')
          bottle.redirect('/')

        result = captcha.submit(challenge,
                                response,
                                config.captcha.recaptcha_private_key,
                                bottle.request.remote_addr)

        if not result.is_valid:
          messages.error('Captcha invalid')
          bottle.redirect(__on_error__)

      # Call the wrapped function
      return func(*args,
                  **kwargs)

    return wrapped
  return wrapper
