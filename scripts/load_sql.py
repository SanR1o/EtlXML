import logging
import pandas as pd
import pyodbc
from typing import Optional
from config import Config

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Gestor de conexiones a base de datos MSSQL.
    Maneja inserción de datos con manejo robusto de errores.
    """
    
    def __init__(self):
        """Inicializa el gestor de base de datos."""
        self.connection: Optional[pyodbc.Connection] = None
    
    def connect(self) -> pyodbc.Connection:
        """
        Establece conexión a la base de datos.
        Reutiliza conexión existente si está disponible.
        """
        try:
            if self.connection:
                return self.connection
            
            connection_string = Config.get_db_connection_string()
            self.connection = pyodbc.connect(connection_string)
            logger.info("Conexión a base de datos establecida")
            return self.connection
            
        except pyodbc.DatabaseError as e:
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
                        VALUES (?, ?, ?, ?)
                        """,
                        row["numero"],
                        row["fecha"],
                        row["cliente"],
                        row["total"]
                    )
                    inserted_count += 1
                    
                except Exception as e:
                    logger.error(f"Error insertando fila {idx}: {e}")
                    failed_count += 1
                    cursor.execute("ROLLBACK")
                    continue
            
            conn.commit()
            logger.info(f"Se insertaron {inserted_count} registros. Fallos: {failed_count}")
            return inserted_count
            
        except Exception as e:
            logger.error(f"Error durante inserción en lote: {e}")
            if conn:
                conn.rollback()
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