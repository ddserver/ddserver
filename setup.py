"""
Copyright 2017 Sven Reissmann <sven@0x80.io>

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

import setuptools


version = open('./VERSION').read().strip()

setuptools.setup(
    license='GNU AGPLv3',

    name='ddserver',
    version=version,

    author='Sven Reissmann',
    author_email='sven@0x80.io',

    url='https://ddserver.org',

    description='A server-side application for dynamic DNS management.',
    long_description=open('README.md').read(),
    keywords='ddserver ddns dns nsupdate',

    install_requires=[
        'beaker >= 1.6',
        'bottle >= 0.11',
        'jinja2 >= 2.6',
        'formencode >= 1.3.0a1',
        'passlib >= 1.6',
        'mysql-connector >= 2.0.0, < 2.1.5',
        'require >= 0.1.0',
        'requests >= 2.5.0',
        'enum34 >= 1.0.0',
        'configparser >= 3.2',
        'yubico-client >= 1.9',
        'Pdns-Remotebackend == 0.6'
    ],

    packages=setuptools.find_packages(),

    zip_safe=False,

    package_data={
        'ddserver.resources': [
            'email/*.mail',
            'web/css/*.css',
            'web/fonts/*',
            'web/js/*.js',
            'templates/*.html',
        ],
    },
    include_package_data=True,

    data_files=[
        ('doc', ['README.md', 'INSTALL.md', 'VERSION', 'LICENSE',
                 'CHANGES.md', 'UPGRADING.md']),
        ('doc/conf', ['ddserver/resources/doc/ddserver.conf.example',
                      'ddserver/resources/doc/ddclient.conf.example',
                      'ddserver/resources/doc/motd']),
        ('doc/db', ['ddserver/resources/doc/schema.sql',
                    'ddserver/resources/doc/schema.upgrade.sql']),
        ('doc/init/centos.init.d', ['ddserver/resources/doc/centos.init.d/ddserver']),
        ('doc/init/debian.init.d', ['ddserver/resources/doc/debian.init.d/ddserver']),
        ('doc/systemd', ['ddserver/resources/doc/systemd/ddserver.service']),
        ('doc/wsgi', ['ddserver/resources/doc/ddserver.wsgi',
                      'ddserver/resources/doc/httpd.conf'])
    ],

    entry_points={
        'console_scripts': [
            'ddserver-interface = ddserver.interface.__main__:main',
            'ddserver-updater = ddserver.updater.__main__:main',
            'ddserver-bundle = ddserver.__main__:main',
            'ddserver-recursor = ddserver.recursor.__main__:main',
        ]
    },
)
