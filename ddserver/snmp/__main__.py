"""
Copyright 2016 Sven Reissmann <sven@0x80.io>

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
"""

import sys, time, errno

from require import require

import snmp_passpersist as snmp
from pysnmp.hlapi import *


OID_BASE = '.1.3.6.1.4.1.40743.1'
MAX_RETRY = 3

pp = None

"""
 Map of ddserver MIB:

+--ddserver(1)
   |
   +--ddserverInfo(0)
   |  |
   |  +-- -R-- String    ddserverVersion(1)
   |  +-- -R-- String    ddserverServerName(2)
   |
   +--ddserverStats(1)
      |
      +-- -R-- Gauge     ddserverNumUsers(1)
      +-- -R-- Gauge     ddserverNumZones(2)
      +-- -R-- Gauge     ddserverNumHostnames(3)
      +-- -R-- Counter   ddserverNumRequests(4)
      +-- -R-- Counter   ddserverNumAnswers(5)
      +-- -R-- Counter   ddserverNumUpdateSuccess(6)
      +-- -R-- Counter   ddserverNumUpdateFailure(7)

"""


@require(db='ddserver.db:Database',
         config='ddserver.config:Config',
         logger='ddserver.utils.logger:Logger')
def update_data(db,
                config,
                logger):
    global pp

    # ddserverInfo
    pp.add_str('0.1.0', "version")
    pp.add_str('0.2.0', "baseurl")

    # ddserverStats
    try:
        with db.cursor() as cur:
            # ddserverNumUsers
            cur.execute('''
                SELECT count(`id`) AS `count`
                  FROM `users`
                 WHERE 1
            ''')
            users = cur.fetchone()
            pp.add_gau('1.1.0', users['count'])

            # ddserverNumZones
            cur.execute('''
                SELECT count(`id`) AS `count`
                  FROM `suffixes`
                 WHERE 1
            ''')
            zones = cur.fetchone()
            pp.add_gau('1.2.0', zones['count'])

            # ddserverNumHostnames
            cur.execute('''
                SELECT count(`id`) AS `count`
                  FROM `hosts`
                 WHERE 1
            ''')
            hostnames = cur.fetchone()
            pp.add_gau('1.3.0', hostnames['count'])

    except Exception as e:
        logger.warning("snmp: Database exception: %s: %s" % (e.__class__.__name__, e))


@require(logger='ddserver.utils.logger:Logger')
def main(logger):
    global pp

    retry_timestamp = int(time.time())
    retry_counter = MAX_RETRY

    while retry_counter > 0:
        try:
            pp = snmp.PassPersist(OID_BASE)

            pp.start(update_data, 300)

        except KeyboardInterrupt:
            print("Exiting on user request.")
            sys.exit(0)

        except IOError as e:
            if e.errno == errno.EPIPE:
                logger.info("snmp: Snmpd had close the pipe, exiting ...")
            else:
                logger.warning("snmp: Updater thread died: IOError: %s" % e)

        except Exception as e:
            logger.warning("snmp: Main thread as died: %s: %s" % (e.__class__.__name__, e))

        else:
            logger.warning("snmp: Updater thread as died: %s" % pp.error)

        logger.info("snmp: Restarting snmp connector in 10 sec ...")
        time.sleep(10)

        now = int(time.time())
        if (now - 3600) > retry_timestamp:  # If the previous error is older than 1H
            retry_counter = MAX_RETRY       # Reset the counter
        else:
            retry_counter -= 1              # Else countdown
        retry_timestamp = now

    logger.error("snmp: Too many retrys, abording ... ")
    sys.exit(1)


if __name__ == "__main__":
    main()
