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
    uuid VARCHAR(200) NULL,
    fecha DATETIME NULL,
    hora VARCHAR(50) NULL,
    cliente VARCHAR(255) NULL,
    cliente_nit VARCHAR(80) NULL,
    proveedor VARCHAR(255) NULL,
    proveedor_nit VARCHAR(80) NULL,
    moneda VARCHAR(10) NULL,
    subtotal DECIMAL(18,2) NULL,
    impuestos DECIMAL(18,2) NULL,
    total DECIMAL(18,2) NULL,
    lineas INT NULL,
    tipo_documento VARCHAR(50) NULL,
    CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS FacturasDetalle (
    ID INT AUTO_INCREMENT PRIMARY KEY,
    invoice_numero VARCHAR(100) NOT NULL,
    invoice_uuid VARCHAR(200) NULL,
    invoice_fecha DATETIME NULL,
    linea_numero INT NULL,
    descripcion VARCHAR(500) NULL,
    cantidad DECIMAL(18,4) NULL,
    unidad_medida VARCHAR(50) NULL,
    valor_linea DECIMAL(18,2) NULL,
    precio_unitario DECIMAL(18,2) NULL,
    cantidad_base DECIMAL(18,4) NULL,
    impuesto_valor DECIMAL(18,2) NULL,
    impuesto_porcentaje DECIMAL(18,2) NULL,
    CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_invoice_numero (invoice_numero)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Validacion rapida
SELECT 'Base de datos lista' AS estado;
SHOW TABLES;
