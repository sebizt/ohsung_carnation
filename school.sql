DROP DATABASE IF EXISTS school;
CREATE DATABASE school
  CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_unicode_ci;

USE school;

CREATE TABLE users (
  user_id    INT AUTO_INCREMENT PRIMARY KEY,
  email      VARCHAR(255),
  pw         VARCHAR(255),
  role       VARCHAR(255)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  AUTO_INCREMENT = 101;

CREATE TABLE teachers (
  teacher_id INT AUTO_INCREMENT PRIMARY KEY,
  name       VARCHAR(255),
  bio        VARCHAR(255)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

CREATE TABLE letters (
  letter_id   INT AUTO_INCREMENT PRIMARY KEY,
  sender_id   INT,
  receiver_id INT,
  title       VARCHAR(255),
  content     TEXT,
  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

CREATE TABLE emails (
  email_id    INT AUTO_INCREMENT PRIMARY KEY,
  email       VARCHAR(255),
  code        VARCHAR(255),
  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;
