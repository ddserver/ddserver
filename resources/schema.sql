-- Copyright 2013 Dustin Frisch<fooker@lab.sh>
-- 
-- This file is part of ddns.
-- 
-- ddns is free software: you can redistribute it and/or modify
-- it under the terms of the GNU General Public License as published by
-- the Free Software Foundation, either version 3 of the License, or
-- (at your option) any later version.
-- 
-- ddns is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
-- GNU General Public License for more details.
-- 
-- You should have received a copy of the GNU General Public License
-- along with ddns.  If not, see <http://www.gnu.org/licenses/>.


DROP TABLE IF EXISTS `hosts`;
DROP TABLE IF EXISTS `users`;


CREATE TABLE `users` (
  `id`          INT            NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `username`    VARCHAR(255)   NOT NULL UNIQUE,
  `password`    VARCHAR(255)   NOT NULL,
  `email`       VARCHAR(255)   NOT NULL,
  `created`     TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  
  INDEX (`username`)
);

CREATE TABLE `hosts` (
  `id`          INT             NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `user_id`     INT             NOT NULL,
  `hostname`    VARCHAR(255)    NOT NULL UNIQUE,
  `address`     VARCHAR(15)     NULL,
  `updated`     TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  
  FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  
  INDEX (`hostname`),
  INDEX (`address`),
  
  INDEX (`user_id`, `hostname`)
);


INSERT INTO `users` VALUES (1, 'major',  '$6$rounds=61868$ix.et15etZ5iCo3i$RzjlA9Sg8OczEZesjARktmFPICiLWEx91Gx9sziNHWBwZKWQ.txgDtCjYX1xDf/UEnKc6/VT2GHWAa3FEmSIz0', 'foo', NOW()),
                           (2, 'fooker', '$6$rounds=60024$Fo5CiSSxZ6.8ImPd$nxmZpbnEUtLiAsMfOaTqQROfskLPYF65asHgqBlo9ErlknBUfI7WN6gbo3kj8QUGun9jfczDBZ5WMXY0YXLYT0', 'foo', NOW());

INSERT INTO `hosts` VALUES (1, 2, 'fooker', NULL, NOW()),
                           (2, 2, 'home.fooker', NULL, NOW()),
                           (3, 2, 'mom.fooker', NULL, NOW()),
                           (4, 2, 'fooker1', NULL, NOW()),
                           (5, 2, 'fooker2', NULL, NOW()),
                           (6, 1, 'a', NULL, NOW()),
                           (7, 1, 'b', NULL, NOW());