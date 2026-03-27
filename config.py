import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

class Config:
    """
    Configuración centralizada de la aplicación.
    Todas las variables sensibles se obtienen desde variables de entorno.
    """

    # Configuración de base de datos
    DB_DRIVER: str = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
    DB_SERVER: str = os.getenv("DB_SERVER", "localhost")
    DB_NAME: str = os.getenv("DB_NAME", "FacturasDB")
    DB_USER: str = os.getenv("DB_USER", "")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    
    # Configuración de rutas
    INPUT_DATA_PATH: str = os.getenv("INPUT_DATA_PATH", "data/")
    OUTPUT_LOG_PATH: str = os.getenv("OUTPUT_LOG_PATH", "logs/")
    
    # Configuración de procesamiento
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "1000"))
    ENCODING: str = os.getenv("ENCODING", "utf-8")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def get_db_connection_string(cls) -> str:
        """Genera la cadena de conexión a la base de datos."""
        return (
            f"DRIVER={{{cls.DB_DRIVER}}};"
            f"SERVER={cls.DB_SERVER};"
            f"DATABASE={cls.DB_NAME};"
            f"UID={cls.DB_USER};"
            f"PWD={cls.DB_PASSWORD}"
        )

    @classmethod
    def validate_config(cls) -> bool:
        """Valida que las variables críticas estén configuradas."""
        if not cls.DB_USER or not cls.DB_PASSWORD:
            raise ValueError("Las credenciales de base de datos no están configuradas. Configure las variables de entorno DB_USER y DB_PASSWORD")
        return True
