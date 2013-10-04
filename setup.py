'''
Copyright 2013 Sven Reissmann <sven@0x80.io>

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
along with ddserver. If not, see <http://www.gnu.org/licenses/>.
'''

import setuptools


version = open('./VERSION').read().strip()

setuptools.setup(
    license = 'GNU GPLv3',

    name = 'ddserver',
    version = version,

    author = 'Sven Reissmann',
    author_email = 'sven@0x80.io',

    url = 'http://dev.open-desk.net/projects/ddserver',

    description = 'A server-side application for dynamic DNS management.',
    long_description = open('README').read(),
    keywords = 'ddserver ddns',

    install_requires = [
        'beaker >= 1.6',
        'bottle >= 0.11',
        'jinja2 >= 2.6',
        'formencode >= 1.2',
        'passlib >= 1.6',
        'recaptcha-client >= 1.0'
    ],

    data_files = [
        ('/etc/ddserver', ['resources/config/settings.conf']),
        ('/usr/share/ddserver', ['resources/web', 'resources/schema.sql']),
    ],

    entry_points = {
        'console_scripts' : [
            'ddserver = ddserver.__main__:main',
        ]
    },
)
