-- Script de inicializacion para MySQL
-- Ejecutar con un usuario con privilegios suficientes, idealmente root.

CREATE DATABASE IF NOT EXISTS FacturasDB
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'etluser'@'localhost' IDENTIFIED BY 'etlpassword';
GRANT ALL PRIVILEGES ON FacturasDB.* TO 'etluser'@'localhost';
FLUSH PRIVILEGES;

USE FacturasDB;

CREATE TABLE IF NOT EXISTS Facturas (
    ID INT AUTO_INCREMENT PRIMARY KEY,
    numero VARCHAR(100) NOT NULL,
    fecha DATETIME NULL,
    cliente VARCHAR(255) NULL,
    total DECIMAL(18,2) NULL,
    CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Validacion rapida
SELECT 'Base de datos lista' AS estado;
SHOW TABLES;
