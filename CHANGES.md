1.0.0
================

Complete rewrite. 

New features:

* Publish to any DNS server by dynamic updates (RFC 2136) with TSIG; failed
  updates are retried, admins see them on the DNS page
* IPv6 addresses can be updated with the dyndns2 protocol, also together with IPv4
* Optional wildcard per hostname
* Sign-up modes: open, restricted to mail domains, closed; optional admin approval
* Change of the email address, resend of activation mails
* Start page text (motd) for everyone or for logged-in users only
* Command line for users, zones, DNS and mail
* SQLite by default, schema migrations with Alembic
* Configuration in TOML
* Example setup with gunicorn, Caddy and systemd

Changes:

* Python 3.12 or newer, Flask instead of Bottle, Bootstrap 5
* Passwords hashed with Argon2; 0.3 hashes keep working and are rehashed on use
* Update credentials only via HTTP Basic auth, no longer as URL parameters
* `nohost` instead of `badauth` for unknown users, `badagent` for invalid
  addresses
* No more MySQL and PowerDNS remote backend

Removed:

* Yubikey OTP authentication
* reCAPTCHA
* Blocking of hostnames by admins (abuse)

0.3
===

New features:

* Added a ddserver logo
* Added support for python 3.3
* Use the public require library insted of the out-dated buildin one
* Added support for Yubikey OTP authentication
* Allow administrators to disable hostnames (i.e., on abuse)
* Use the powerdns remote backend, instead of the pipe backend

Fixes:

* Fixed wrong comparison when modifying own admin privileges

0.2
===

New features:

* Updated and added configuration examples
* Switched to bootstrap3 using fontawesome icons
* Performed lots of look and feel optimizations
* Added some statistics to index page
* Added password strength meters to password forms
* Configurable TTL of A records and lower default value
* Added description field to hostnames
* Set an individual number of maximum hostnames per user
* Added a manual add-user function for administrators
* Added basic support for blacklisting hostnames

Fixes:

* Fixed issues with the mysql schema
* Catch exceptions from mail and database modules
* Do not show details of other users hosts
* Only allow valid ip addresses in update requests
* Fixed issues in hostname and username validator
* Fixed an issue, which led to database connection errors

0.1.5
=====

Fixes:

* Do not show details of other users hosts

0.1.4
=====

Fixes:

* Only allow valid ip addresses in update requests

0.1.3
=====

Fixes:

* Fix critical bug which allowed the use of any character in hostnames

0.1.2
=====

Fixes:

* Fixed an issue, which led to database connection errors

0.1.1
=====

Fixes:

* Fixed an issue with non-admin users not being able to add hostnames

0.1.0
=====

Initial stable releaseof ddserver
