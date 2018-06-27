"""
Copyright 2015 Sven Reissmann <sven@0x80.io>

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

import pdns.remotebackend
from require import require, extend
from ddserver.config import parse_bool


@extend('ddserver.config:ConfigDeclaration')
def config_dns(config_decl):
    with config_decl.declare('dns') as s:
        s('ttl',
          conv=int,
          default=60)
        s('answer_soa',
          conv=parse_bool,
          default=False)


class DdserverHandler(pdns.remotebackend.Handler):
    db = require('ddserver.db:Database')
    logger = require('ddserver.utils.logger:Logger')
    config = require('ddserver.config:Config')

    def answer_soa(self, qname):
        """ answer questions of type SOA.
            this should be done by another backend (together with NS, MX, ...)
        """
        with self.db.cursor() as cur:
            cur.execute('''
                SELECT *
                  FROM `suffixes`
                 WHERE `name` = %(name)s
            ''', {'name': qname})
            suffix = cur.fetchone()

            if suffix:
                content = ' '.join(('ns.' + qname + '.',
                                    'hostmaster.' + qname + '.',
                                    '2015999901',
                                    '43200',     # 12h
                                    '7200',      # 2h
                                    '604800',    # 7d
                                    '43200'))    # 12h
                self.result.append(self.record_prio_ttl(qname, 'SOA', content, 0, 300))

    def answer_a(self, qname):
        """ answer questions of type A or ANY

            note: with version 4 of pdns, the final dot for the root zone
                  is appended to the query sent to the backends (which is
                  totally correct). we remove the dot, to be compatible
                  with all versions of pdns.
        """
        if qname[-1:] == '.':
            qname = qname[:-1]

        with self.db.cursor() as cur:
            cur.execute('''
                SELECT
                  `host`.`hostname` AS `hostname`,
                  `suffix`.`name` AS `suffix`,
                  `host`.`address` AS `address`
                FROM `hosts` AS `host`
                LEFT JOIN `suffixes` AS `suffix`
                  ON ( `suffix`.`id` = `host`.`suffix_id` )
                WHERE `host`.`address` IS NOT NULL
                  AND CONCAT(`host`.`hostname`, '.', `suffix`.`name`) = %(name)s
            ''', {'name': qname})
            host = cur.fetchone()

            if host and host['address'] is not None:
                response = self.record_prio_ttl(qname, 'A', host['address'], 0, self.config.dns.ttl)
                self.logger.debug('response: %s', response)
                self.result.append(response)

    def answer_aaaa(self, qname):
        """ answer questions of type AAAA or ANY

            note: with version 4 of pdns, the final dot for the root zone
                  is appended to the query sent to the backends (which is
                  totally correct). we remove the dot, to be compatible
                  with all versions of pdns.
        """
        if qname[-1:] == '.':
            qname = qname[:-1]

        with self.db.cursor() as cur:
            cur.execute('''
                SELECT
                  `host`.`hostname` AS `hostname`,
                  `suffix`.`name` AS `suffix`,
                  `host`.`address_v6` AS `address_v6`
                FROM `hosts` AS `host`
                LEFT JOIN `suffixes` AS `suffix`
                  ON ( `suffix`.`id` = `host`.`suffix_id` )
                WHERE `host`.`address` IS NOT NULL
                  AND CONCAT(`host`.`hostname`, '.', `suffix`.`name`) = %(name)s
            ''', {'name': qname})
            host = cur.fetchone()

            if host and host['address_v6'] is not None:
                response = self.record_prio_ttl(qname, 'AAAA', host['address_v6'], 0, self.config.dns.ttl)
                self.logger.debug('response: %s', response)
                self.result.append(response)

    def do_lookup(self, args):
        """ decide what to answer
        """
        self.result = []
        self.logger.debug('request: %s', args)

        if self.config.dns.answer_soa and (args['qtype'] == 'ANY' or args['qtype'] == 'SOA'):
            self.answer_soa(args['qname'])

        if args['qtype'] == 'ANY' or args['qtype'] == 'A':
            self.answer_a(args['qname'])

        if args['qtype'] == 'ANY' or args['qtype'] == 'AAAA':
            self.answer_aaaa(args['qname'])


def main():
    pdns.remotebackend.PipeConnector(DdserverHandler).run()


if __name__ == '__main__':
    main()
