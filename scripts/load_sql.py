import logging
import pandas as pd
import mysql.connector
from mysql.connector import Error
from config import Config

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Gestor de conexiones a base de datos MySQL.
    Maneja inserción de datos con manejo robusto de errores.
    """
    
    def __init__(self):
        """Inicializa el gestor de base de datos."""
        self.connection = None
    
    def connect(self):
        """
        Establece conexión a la base de datos.
        Reutiliza conexión existente si está disponible.
        """
        try:
            if self.connection:
                return self.connection
            
            connection_params = Config.get_db_connection_params()
            self.connection = mysql.connector.connect(**connection_params)
            self._ensure_schema(self.connection)
            logger.info("Conexión a base de datos establecida")
            return self.connection
            
        except Error as e:
            logger.error(f"Error al conectar a la base de datos: {e}")
            raise
        except Exception as e:
            logger.error(f"Error inesperado al conectarse: {e}")
            raise
    
    def disconnect(self) -> None:
        """Cierra la conexión a la base de datos."""
        try:
            if self.connection:
                self.connection.close()
                self.connection = None
                logger.info("Conexión a base de datos cerrada")
        except Exception as e:
            logger.error(f"Error al cerrar conexión: {e}")
    
    def insert_data(self, df: pd.DataFrame) -> int:
        """
        Inserta datos del DataFrame en la base de datos.
        Utiliza transacciones para garantizar integridad.
        Retorna cantidad de filas insertadas.
        """
        if df.empty:
            logger.warning("DataFrame vacío, nada que insertar")
            return 0
        
        conn = None
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            inserted_count = 0
            failed_count = 0
            
            for idx, row in df.iterrows():
                try:
                    invoice_key = _normalize_value(row.get("invoice_key"))
                    if not invoice_key:
                        invoice_key = _build_invoice_key(
                            _normalize_value(row.get("numero")),
                            _normalize_value(row.get("periodo_facturacion")),
                        )
                    cursor.execute(
                        """
                        INSERT INTO Facturas (
                            invoice_key, numero, periodo_facturacion, uuid, fecha, hora,
                            cliente, cliente_nit, proveedor, proveedor_nit,
                            moneda, subtotal, impuestos, total, lineas,
                            tipo_documento, source_type, source_file
                        )
                        VALUES (
                            %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s,
                            %s, %s, %s, %s, %s,
                            %s, %s, %s
                        )
                        ON DUPLICATE KEY UPDATE
                            numero = VALUES(numero),
                            periodo_facturacion = VALUES(periodo_facturacion),
                            uuid = VALUES(uuid),
                            fecha = VALUES(fecha),
                            hora = VALUES(hora),
                            cliente = VALUES(cliente),
                            cliente_nit = VALUES(cliente_nit),
                            proveedor = VALUES(proveedor),
                            proveedor_nit = VALUES(proveedor_nit),
                            moneda = VALUES(moneda),
                            subtotal = VALUES(subtotal),
                            impuestos = VALUES(impuestos),
                            total = VALUES(total),
                            lineas = VALUES(lineas),
                            tipo_documento = VALUES(tipo_documento),
                            source_type = VALUES(source_type),
                            source_file = VALUES(source_file)
                        """,
                        (
                            invoice_key,
                            _normalize_value(row["numero"]),
                            _normalize_value(row.get("periodo_facturacion")),
                            _normalize_value(row.get("uuid")),
                            _normalize_value(row.get("fecha")),
                            _normalize_value(row.get("hora")),
                            _normalize_value(row.get("cliente")),
                            _normalize_value(row.get("cliente_nit")),
                            _normalize_value(row.get("proveedor")),
                            _normalize_value(row.get("proveedor_nit")),
                            _normalize_value(row.get("moneda")),
                            _normalize_value(row.get("subtotal")),
                            _normalize_value(row.get("impuestos")),
                            _normalize_value(row["total"]),
                            _normalize_value(row.get("lineas")),
                            _normalize_value(row.get("tipo_documento")),
                            _normalize_value(row.get("source_type")),
                            _normalize_value(row.get("source_file")),
                        )
                    )
                    inserted_count += 1
                    
                except Exception as e:
                    logger.error(f"Error insertando fila {idx}: {e}")
                    failed_count += 1
                    # skip this row and continue; do not execute SQL ROLLBACK here
                    continue
            
            if conn:
                conn.commit()
            logger.info(f"Se insertaron {inserted_count} registros. Fallos: {failed_count}")
            return inserted_count
            
        except Exception as e:
            logger.error(f"Error durante inserción en lote: {e}")
            try:
                if conn:
                    conn.rollback()
            except Exception:
                logger.error("No se pudo hacer rollback de la transacción")
            raise

    def insert_line_data(self, df: pd.DataFrame) -> int:
        """Inserta el detalle de líneas de factura."""
        if df.empty:
            logger.warning("DataFrame de lineas vacío, nada que insertar")
            return 0

        conn = None
        try:
            conn = self.connect()
            cursor = conn.cursor()

            inserted_count = 0
            failed_count = 0

            for idx, row in df.iterrows():
                try:
                    cursor.execute(
                        """
                        INSERT INTO FacturasDetalle (
                            invoice_key, invoice_numero, nro, orden, identificacion_circuito,
                            periodo_facturacion, um, descripcion, tipo_cargo,
                            impuesto, monto, source_type
                        )
                        VALUES (
                            %s, %s, %s, %s, %s,
                            %s, %s, %s, %s,
                            %s, %s, %s
                        )
                        ON DUPLICATE KEY UPDATE
                            orden = VALUES(orden),
                            identificacion_circuito = VALUES(identificacion_circuito),
                            periodo_facturacion = VALUES(periodo_facturacion),
                            um = VALUES(um),
                            descripcion = VALUES(descripcion),
                            tipo_cargo = VALUES(tipo_cargo),
                            impuesto = VALUES(impuesto),
                            monto = VALUES(monto),
                            source_type = VALUES(source_type)
                        """,
                        (
                            _normalize_value(row.get("invoice_key")) or _normalize_value(row.get("invoice_numero")),
                            _normalize_value(row.get("invoice_numero")) or _normalize_value(row.get("invoice_key")),
                            _normalize_value(row.get("nro")),
                            _normalize_value(row.get("orden")),
                            _normalize_value(row.get("identificacion_circuito")),
                            _normalize_value(row.get("periodo_facturacion")),
                            _normalize_value(row.get("um")),
                            _normalize_value(row.get("descripcion")),
                            _normalize_value(row.get("tipo_cargo")),
                            _normalize_value(row.get("impuesto")),
                            _normalize_value(row.get("monto")),
                            _normalize_value(row.get("source_type")),
                        )
                    )
                    inserted_count += 1
                except Exception as e:
                    logger.error(f"Error insertando linea {idx}: {e}")
                    failed_count += 1
                    continue

            if conn:
                conn.commit()
            logger.info(f"Se insertaron {inserted_count} lineas. Fallos: {failed_count}")
            return inserted_count

        except Exception as e:
            logger.error(f"Error durante inserción de detalle en lote: {e}")
            try:
                if conn:
                    conn.rollback()
            except Exception:
                logger.error("No se pudo hacer rollback de las lineas")
            raise
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()

    def _ensure_schema(self, conn) -> None:
        """Asegura que existan las tablas y columnas para encabezado y detalle."""
        desired_columns = {
            "invoice_key": "VARCHAR(150) NULL",
            "numero": "VARCHAR(100) NOT NULL",
            "periodo_facturacion": "VARCHAR(100) NULL",
            "uuid": "VARCHAR(200) NULL",
            "fecha": "DATETIME NULL",
            "hora": "VARCHAR(50) NULL",
            "cliente": "VARCHAR(255) NULL",
            "cliente_nit": "VARCHAR(80) NULL",
            "proveedor": "VARCHAR(255) NULL",
            "proveedor_nit": "VARCHAR(80) NULL",
            "moneda": "VARCHAR(10) NULL",
            "subtotal": "DECIMAL(18,2) NULL",
            "impuestos": "DECIMAL(18,2) NULL",
            "total": "DECIMAL(18,2) NULL",
            "lineas": "INT NULL",
            "tipo_documento": "VARCHAR(50) NULL",
            "source_type": "VARCHAR(20) NULL",
            "source_file": "VARCHAR(255) NULL",
        }

        cursor = conn.cursor()

        desired_detail_columns = {
            "invoice_key",
            "invoice_numero",
            "nro",
            "orden",
            "identificacion_circuito",
            "periodo_facturacion",
            "um",
            "descripcion",
            "tipo_cargo",
            "impuesto",
            "monto",
            "source_type",
            "CreatedDate",
        }

        cursor.execute(
            """
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'FacturasDetalle'
            """
        )
        detail_existing_columns = {row[0] for row in cursor.fetchall()}

        if detail_existing_columns and detail_existing_columns != desired_detail_columns:
            cursor.execute("DROP TABLE IF EXISTS FacturasDetalle")
            detail_existing_columns = set()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS FacturasDetalle (
                ID INT AUTO_INCREMENT PRIMARY KEY,
                invoice_key VARCHAR(150) NOT NULL,
                invoice_numero VARCHAR(150) NULL,
                nro INT NULL,
                orden VARCHAR(100) NULL,
                identificacion_circuito VARCHAR(200) NULL,
                periodo_facturacion VARCHAR(100) NULL,
                um VARCHAR(50) NULL,
                descripcion VARCHAR(500) NULL,
                tipo_cargo VARCHAR(255) NULL,
                impuesto VARCHAR(50) NULL,
                monto DECIMAL(18,2) NULL,
                source_type VARCHAR(20) NULL,
                CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uniq_invoice_line (invoice_key, nro),
                INDEX idx_invoice_key (invoice_key)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
        )

        cursor.execute("SELECT DATABASE()")
        database_name = cursor.fetchone()[0]
        cursor.execute(
            """
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'Facturas'
            """,
            (database_name,)
        )
        existing_columns = {row[0] for row in cursor.fetchall()}

        if not existing_columns:
            column_defs = ",\n    ".join(
                [
                    "ID INT AUTO_INCREMENT PRIMARY KEY",
                    *[f"`{name}` {definition}" for name, definition in desired_columns.items()],
                    "CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP",
                ]
            )
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS Facturas (
                    {column_defs}
                    , UNIQUE KEY uniq_invoice_key (invoice_key)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """
            )
            conn.commit()
            return

        for column_name, column_definition in desired_columns.items():
            if column_name not in existing_columns:
                cursor.execute(
                    f"ALTER TABLE Facturas ADD COLUMN `{column_name}` {column_definition}"
                )
        try:
            cursor.execute("ALTER TABLE Facturas ADD UNIQUE KEY uniq_invoice_key (invoice_key)")
        except Exception:
            pass
        conn.commit()


def insert_data(df: pd.DataFrame) -> int:
    """
    Función wrapper para insertar datos usando el gestor de base de datos.
    """
    db_manager = DatabaseManager()
    try:
        return db_manager.insert_data(df)
    finally:
        db_manager.disconnect()


def insert_line_data(df: pd.DataFrame) -> int:
    """Inserta el detalle de líneas de factura en la tabla de detalle."""
    db_manager = DatabaseManager()
    try:
        return db_manager.insert_line_data(df)
    finally:
        db_manager.disconnect()


def _normalize_value(value):
    """Convierte valores de Pandas a tipos compatibles con MySQL."""
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    if hasattr(value, "to_pydatetime"):
        return value.to_pydatetime()
    return value