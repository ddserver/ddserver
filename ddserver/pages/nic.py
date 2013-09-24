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

import logging
import functools

from bottle import route, request

from passlib.apps import custom_app_context as pwd

from ddserver.config import config



# See http://www.noip.com/integrate for further protocol specification



# Create a logger
logger = logging.getLogger('ddserver')



# The Response code
class Response(object):
    __slots__ = ['name',
                 'value']


    def __init__(self, name, value):
        self.name = name
        self.value = value


    def __str__(self):
        if self.value:
            return '%s %s' % (self.name, self.value)

        else:
            return '%s' % (self.name)

    __repr__ = __str__



# Existing response codes
resp_good = functools.partial(Response, 'good')
resp_nochg = functools.partial(Response, 'nochg')
resp_nohost = functools.partial(Response, 'nohost', None)
resp_badauth = functools.partial(Response, 'badauth', None)
resp_badagent = functools.partial(Response, 'badagent', None)
resp_not_donator = functools.partial(Response, '!donator', None)
resp_abuse = functools.partial(Response, 'abuse', None)
resp_911 = functools.partial(Response, '911', None)



def update(db, username, password, hostnames, address):
    # Check if we get some credentials
    if not request.auth:
        logger.warning('Missing credentials')
        return resp_badauth()

    # Try to get user ID from database
    db.execute('''
        SELECT `id`, `password`
        FROM `users`
        WHERE `username` = %(username)s
    ''', {'username': username})
    user = db.fetchone()

    # Check if we have a valid user
    if not user or not pwd.verify(password, user['password']):
        logger.warning('Mismatching credentials')
        return resp_badauth()

    logger.debug('Fund user in DB: %s', user)

    # The specification allows to give multiple hosts separated by comma
    responses = []
    for hostname in hostnames:
        # Check if the hostname has suffix and strip it off
        if hostname.endswith(config.dns.suffix):
            hostname = hostname[:-len(config.dns.suffix)]

        logger.debug('Fetching host entry for %s', hostname)

        # Get the host entry for the current hostname from the database
        db.execute('''
            SELECT `id`, `address`
            FROM `hosts`
            WHERE `user_id` = %(user_id)s
              AND `hostname` = %(hostname)s
        ''', {'user_id': user['id'],
              'hostname': hostname})
        host = db.fetchone()

        # Check if we got a host entry for the queried hostname
        if not host:
            logger.debug('No such host entry found')

            responses.append(resp_nohost())
            continue

        # Check if the address has changed
        if host['address'] == address:
            logger.debug('No address has not changed: %s', address)

            responses.append(resp_nochg(value = address))
            continue

        # Update the host entry
        db.execute('''
            UPDATE `hosts`
            SET `address` = %(address)s,
                `updated` = CURRENT_TIMESTAMP
            WHERE `id` = %(id)s
        ''', {'id': host['id'],
              'address': address})

        logger.debug('Host entry updated')

        responses.append(resp_good(value = address))

    return responses



@route('/nic/ip')
def get_ip():
    # Return the client's IP
    return request.remote_addr



@route('/nic/update')
def get_update(db):
    # Extract the hostnames separated by comma, the new IP address and the
    # deletion flag from the query
    hostnames = request.query.get('hostname', None).split(',')
    address = request.query.get('myip', None)
    offline = request.query.get('offline', 'NO') == 'YES'

    # Fetch the the credentials from HTTP header
    username, password = request.auth

    # Clear the address if the offline flag is set
    if offline:
        address = None

    logger.debug('Update request for %s as %s', hostnames, address)

    # Call the update function
    try:
        responses = update(db = db,
                           username = username,
                           password = password,
                           hostnames = hostnames,
                           address = address)

    except:
        responses = resp_911()

    # Blow up responses if we got a single response
    if isinstance(responses, Response):
        responses = [responses] * len(hostnames)

    logger.debug('Update responses: %s', responses)

    # Return responses as string
    return '\n'.join(str(response)
                     for response
                     in responses)
