ddserver - Installation instructions
====================================

Welcome to ddserver.


Prerequisites
-------------

Before you start to install ddserver, please make sure that you have installed
python2.7, MySQL and PowerDNS (including the pipe-backend) on your server.

On Debian GNU/Linux you will need to install these packages:

 libmysqlclient-dev
 python-dev
 python-setuptools

On CentOS you will need to install these packages:

 mysql-devel
 python-devel
 python-setuptools


Installation
------------

1. To install ddserver you can just run:
```
    python setup.py install
```

2. After this step, ddserver installed to the following locations:
  * /usr/local/lib/python2.7/dist-packages/ contains the installed python packages
  * /etc/ddserver contains the configuration file
  * /etc/init.d/ddserver is a debian init-script for controlling ddserver
  * /usr/share/doc/ddserver contains the database schema and some readme files
  * /usr/share/ddserver contains static files like CSS, JavaScript, eMail-Templates, ..
  * /usr/local/bin contains the ddserver executables

3. Create a new database (i.e. named ddserver) and a database user with
   usage privileges (at least SELECT, DELETE, UPDATE) for the database.

4. Install the database using /usr/share/doc/ddserver/schema.sql

  Note: When installing the default database schema, an initial user will be
  installed to log into the Web-UI. The default login is: admin:admin

5. Copy the configuration file /etc/ddserver/ddserver.conf.example to
   /etc/ddserver/ddserver.conf and edit it to fit your needs.

6. Start ddserver using /etc/init.d/ddserver

7. Run the ddserver-recursor by adding the following lines to your powerdns
   configuration and restart powerdns.
```
    launch=pipe
    pipe-command=/usr/local/bin/ddserver-recursor
```

Documentation and Support
-------------------------

Please refer to https://ddserver.0x80.io for further documentation and
support. If you have any problems using ddserver you can send an email
to ddserver@0x80.io or file a bugreport at
https://github.com/ddserver/ddserver/issues
