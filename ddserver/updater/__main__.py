"""
Copyright 2013 Dustin Frisch<fooker@lab.sh>

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

from require import require

import ddserver.updater.nic  # @UnusedImport: for web application


@require(web='ddserver.web:Web')
def main(web):
  # Set up web server and run it
  web.run()


if __name__ == '__main__':
  main()
