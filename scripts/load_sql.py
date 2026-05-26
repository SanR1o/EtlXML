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
                    cursor.execute(
                        """
                        INSERT INTO Facturas (numero, fecha, cliente, total)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (
                            _normalize_value(row["numero"]),
                            _normalize_value(row["fecha"]),
                            _normalize_value(row["cliente"]),
                            _normalize_value(row["total"]),
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
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


def insert_data(df: pd.DataFrame) -> int:
    """
    Función wrapper para insertar datos usando el gestor de base de datos.
    """
    db_manager = DatabaseManager()
    try:
        return db_manager.insert_data(df)
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