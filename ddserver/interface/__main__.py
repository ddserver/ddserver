'''
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
'''

import ddserver.interface.pages.index  # @UnusedImport: for web application
import ddserver.interface.pages.signup  # @UnusedImport: for web application
import ddserver.interface.pages.lostpasswd  # @UnusedImport: for web application
import ddserver.interface.pages.login  # @UnusedImport: for web application
import ddserver.interface.pages.user.account  # @UnusedImport: for web application
import ddserver.interface.pages.user.hosts  # @UnusedImport: for web application
import ddserver.interface.pages.user.host  # @UnusedImport: for web application
import ddserver.interface.pages.admin.users  # @UnusedImport: for web application
import ddserver.interface.pages.admin.suffixes  # @UnusedImport: for web application

from require import require



@require(web = 'ddserver.web:Web')
def main(web):
  # Set up web server and run it
  web.run()



if __name__ == '__main__':
    main()
