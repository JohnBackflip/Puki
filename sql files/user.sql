CREATE TABLE `user` (
  `user_id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(64) NOT NULL,
  `email` VARCHAR(128) UNIQUE NOT NULL,
  `password_hash` VARCHAR(256) NOT NULL,
  `role` ENUM('admin', 'staff') NOT NULL,
  PRIMARY KEY (`user_id`)
);

