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

import setuptools


version = open('./VERSION').read().strip()

setuptools.setup(
    license = 'GNU AGPLv3',

    name = 'ddserver',
    version = version,

    author = 'Sven Reissmann',
    author_email = 'sven@0x80.io',

    url = 'http://dev.open-desk.net/projects/ddserver',

    description = 'A server-side application for dynamic DNS management.',
    long_description = open('README').read(),
    keywords = 'ddserver ddns',

    install_requires = [
        'enum >= 0.4',
        'beaker >= 1.6',
        'bottle >= 0.11',
        'jinja2 >= 2.6',
        'formencode >= 1.2',
        'passlib >= 1.6',
        'recaptcha-client >= 1.0',
        'MySQL-python >= 1.2.0'
    ],

    packages = setuptools.find_packages(),

    package_data = {
        'ddserver.resources': [
            'email/*.mail',
            'web/css/*.html',
            'web/img/*.png',
            'web/js/*.js',
            'web/templates/*.html',
        ],
    },
    include_package_data = True,

    data_files = [
        ('/etc/ddserver', ['ddserver/resources/ddserver.conf.example'])
    ],

    entry_points = {
        'console_scripts' : [
            'ddserver-interface = ddserver.interface.__main__:main',
            'ddserver-updater = ddserver.updater.__main__:main',
            'ddserver-bundle = ddserver.__main__:main',
            'ddserver-recursor = ddserver.recursor.__main__:main',
        ]
    },
)
