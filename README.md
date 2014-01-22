ddserver - A dynamic DNS service
================================

About
-----

ddserver is a server-side application for dynamic DNS.

It allows you to specify hostnames (subdomains) inside a dynamic DNS zone, and
to update the IPv4 address of those hostnames using the dyndns2 update protocol
(http://www.noip.com/integrate). This enables you to access hosts with dynamic
IP addresses by a static domain name, even if the IP address changes.


Features
--------

* Nice and intuitive Web-UI
  - Automatic / Semi-automatic registration or manual user management
  - Administrators can add and manage zones
  - Users can add and manage hostnames
  - Re-captcha support
* IP-address update using the dyndns2 protocol
  - Update multiple hostnames at once
  - Works with most homerouters, ddclient or even wget
  - Manual IP-address updates via Web-UI
* Support for multiple domains
* Configurable number of hosts per user
* Strong encryption of all passwords (host and user)
* Supports distributed installation
  - Separate packages for Web-UI, updater and DNS-backend
  - Redundancy support


Mode of operation
-----------------

ddserver is written in Python (2.7) using the Bottle Web Framework and comes
with a clean HTML5 frontend using the Bootstrap3 CSS framework.

All user and hostname information is stored in a MySQL database. For name
resolution ddserver depends on PowerDNS as the DNS server.

The individual parts of ddserver, which may run on one server, or distributed
on different machines, are

* ddserver-bundle is the bundled version of
  - ddserver-interface: A nice-looking webinterface for adding hostnames or zones and managing users.
  - ddserver-updater: The implementation of the dyndns2 update protocol.
* ddserver-recursor answers DNS queries. It runs as a pipe-backend for the PowerDNS server.


License
-------

ddserver is free software and can be redistributed and/or modified under the
terms of the GNU Affero General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your option) any
later version.
