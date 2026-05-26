import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """
    Configuración centralizada de la aplicación.
    Todas las variables sensibles se obtienen desde variables de entorno.
    """

    # Configuración de base de datos MySQL
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
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
    def get_db_connection_params(cls) -> dict:
        """Genera los parámetros de conexión a la base de datos."""
        return {
            "host": cls.DB_HOST,
            "port": cls.DB_PORT,
            "database": cls.DB_NAME,
            "user": cls.DB_USER,
            "password": cls.DB_PASSWORD,
        }

    @classmethod
    def validate_config(cls) -> bool:
        """Valida que las variables críticas estén configuradas."""
        if not cls.DB_USER or not cls.DB_PASSWORD:
            raise ValueError("Las credenciales de base de datos no están configuradas. Configure las variables de entorno DB_USER y DB_PASSWORD")
        try:
            import mysql.connector  # noqa: F401
        except Exception:
            raise ValueError("No se pudo cargar el conector de MySQL. Verifique que mysql-connector-python esté instalado en el entorno.")
        return True
