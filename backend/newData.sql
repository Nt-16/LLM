-- 1. Create the database (if it doesn't exist)
CREATE DATABASE IF NOT EXISTS llmscribe_db 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci;

-- 2. Switch to the database
USE llmscribe_db;

-- 3. Drop existing user table (if any)
DROP TABLE IF EXISTS `user`;

-- 4. Create new user table with proper structure
CREATE TABLE `user` (
  id INT PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(150) NOT NULL UNIQUE,
  email VARCHAR(150) NOT NULL UNIQUE,
  password_hash VARCHAR(150) NOT NULL,
  
  -- Case-insensitive email index
  email_lower VARCHAR(150) GENERATED ALWAYS AS (LOWER(email)) VIRTUAL,
  INDEX idx_email_lower (email_lower)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

select * from user;