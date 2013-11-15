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

import sys

from ddserver.utils.deps import require
from ddserver.utils.txtprot import (LexerDeclaration,
                                    FormatterDeclaration,
                                    MessageDeclaration,
                                    FieldDeclaration)



# See http://doc.powerdns.com/html/backends-detail.html#pipebackend for further
# protocol specification



# Declaration of the PowerDNS pipe protocol
lexer = LexerDeclaration(splitter = '\t',
                         messages = (MessageDeclaration('HELO',
                                                        FieldDeclaration('version', int)),

                                     MessageDeclaration('Q',
                                                        FieldDeclaration('qname', str),
                                                        FieldDeclaration('qclass', str),
                                                        FieldDeclaration('qtype', str),
                                                        FieldDeclaration('id', int),
                                                        FieldDeclaration('remote', str)),

                                     MessageDeclaration('AXFR',
                                                        FieldDeclaration('id', int)),

                                     MessageDeclaration('PING')))


formatter = FormatterDeclaration(splitter = '\t',
                                 messages = (MessageDeclaration('OK',
                                                                FieldDeclaration('banner', str)),

                                             MessageDeclaration('DATA',
                                                                FieldDeclaration('qname', str),
                                                                FieldDeclaration('qclass', str),
                                                                FieldDeclaration('qtype', str),
                                                                FieldDeclaration('ttl', str),
                                                                FieldDeclaration('id', int),
                                                                FieldDeclaration('content', str)),

                                             MessageDeclaration('LOG',
                                                                FieldDeclaration('message', str)),

                                             MessageDeclaration('END'),
                                             MessageDeclaration('FAIL')))



@require(logger = 'ddserver.utils.logger:Logger')
def receiver(logger):
  # Read lines from standard input
  for line in sys.stdin:
    # Lex the line
    message = lexer(line)

    if message is None:
      logger.error('Unknown tag: %s', line)
      continue

    logger.debug('Received message: %s', message)

    yield message



@require(db = 'ddserver.db:Database',
         logger = 'ddserver.utils.logger:Logger')
def handler(db, logger):
  messages = receiver()

  for message in messages:
    if message.tag == 'HELO':
      if message.version != 1:
        logger.error('Unappropriate ABI version: %s', message.version)
        yield formatter.FAIL()

      yield formatter.OK(banner = 'ddserver')

      break

    else:
      logger.error('Missing HELO before command: %s', message.tag)
      yield formatter.FAIL()

  for message in messages:
    if message.tag == 'HELO':
      logger.error('Duplicated HELO')
      yield formatter.FAIL()

    elif message.tag == 'Q':
      yield formatter.END()

    elif message.tag == 'AXFR':
      # We do not support transfer by now
      yield formatter.FAIL()

    elif message.tag == 'PING':
      # Ping does not require any data response
      yield formatter.END()

    else:
      logger.error('Unhandled message tag: %s', message)
      yield formatter.FAIL()



@require(logger = 'ddserver.utils.logger:Logger')
def run(logger):
  for message in handler():
    logger.debug('Responding message: %s', message)

    # Format the response
    line = formatter(message)

    # Send line to standard output
    sys.stdout.write(line + '\n')



def main():
  run()



if __name__ == '__main__':
    main()
