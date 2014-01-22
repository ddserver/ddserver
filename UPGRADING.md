ddserver - Upgrade instructions
===============================

If you are performing a fresh installation, please follow the
instructions given in file INSTALL.

If you are upgrading from a previous version of ddserver, please
follow the instructions below, that match the version you are
upgrading from.

In any case, you should create a backup of your ddserver database
before you perform an upgrade!


Upgrading from 0.1.x
--------------------

1. Make a backup of your ddserver database!
2. Stop ddserver.
3. Unpack and install the new version of ddserver.
   python setup.py install
4. Apply all the SQL statements from file
   ddserver/resources/doc/schema.upgrade.sql to your database.
5. Check /etc/ddserver/ddserver.conf.example for new configuration
   parameters and add them to your own configuration file
6. Start ddserver.
7. Restart powerdns ro reload the ddserver-recursor.
