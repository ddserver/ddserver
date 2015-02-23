-- Copyright 2014 Sven Reissmann <sven@0x80.io>
--
-- This file is part of ddserver.
--
-- ddserver is free software: you can redistribute it and/or modify
-- it under the terms of the GNU Affero General Public License as
-- published by the Free Software Foundation, either version 3 of the
-- License, or (at your option) any later version.
--
-- ddserver is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
-- GNU Affero General Public License for more details.
--
-- You should have received a copy of the GNU Affero General Public License
-- along with ddserver.  If not, see <http://www.gnu.org/licenses/>.


--
-- Upgrading from version 0.2.x
--

ALTER TABLE `hosts`
  ADD `abuse` TEXT NULL ;



--
-- Upgrading from version 0.1.x
--

ALTER TABLE `users`
  CHANGE `password`
  `password` VARCHAR( 255 )
  CHARACTER SET utf8 COLLATE utf8_general_ci
  NULL DEFAULT NULL ;

ALTER TABLE `users`
  CHANGE `authcode`
  `authcode` VARCHAR( 36 )
  CHARACTER SET utf8 COLLATE utf8_general_ci
  NULL DEFAULT NULL ;

ALTER TABLE `hosts`
  CHANGE `address`
  `address` VARCHAR( 15 )
  CHARACTER SET utf8 COLLATE utf8_general_ci
  NULL DEFAULT NULL ;

 ALTER TABLE `hosts`
  CHANGE `description`
  `description` VARCHAR( 255 )
  CHARACTER SET utf8 COLLATE utf8_general_ci
  NULL DEFAULT NULL ;

ALTER TABLE `users`
  ADD `maxhosts` INT NULL DEFAULT NULL ;

ALTER TABLE `suffixes`
  DROP INDEX `name_2` ;

ALTER TABLE `users`
  DROP INDEX `username_2` ;

ALTER TABLE `hosts`
  DROP FOREIGN KEY `hosts_ibfk_1`,
  DROP FOREIGN KEY`hosts_ibfk_2` ;
