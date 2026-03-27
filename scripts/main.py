import logging
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from parser import parse_xml
from transform import transform_to_df
from load_sql import insert_data
from config import Config

# Configurar logging
def setup_logging() -> None:
    """Configura el sistema de logging de la aplicación."""
    log_path = Path(Config.OUTPUT_LOG_PATH)
    log_path.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=Config.LOG_LEVEL,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_path / "etl_process.log"),
            logging.StreamHandler()
        ]
    )


def main(xml_file: Optional[str] = None) -> None:
    """
    Ejecuta el pipeline ETL completo.
    Coordina extracción, transformación y carga de datos.
    """
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Iniciando proceso ETL")
        Config.validate_config()
        
        # Usar archivo especificado o buscar en directorio default
        if not xml_file:
            xml_file = f"{Config.INPUT_DATA_PATH}factura.xml"
        
        # Extracción
        logger.info(f"Extrayendo datos de {xml_file}")
        data = parse_xml(xml_file)
        
        # Transformación
        logger.info("Transformando datos")
        df = transform_to_df(data)
        
        if df.empty:
            logger.warning("No hay datos para cargar después de transformación")
            return
        
        # Carga
        logger.info("Cargando datos a base de datos")
        inserted_rows = insert_data(df)
        
        logger.info(f"Proceso ETL completado exitosamente. Registros procesados: {inserted_rows}")
        
    except Exception as e:
        logger.error(f"Error fatal en proceso ETL: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    xml_file = sys.argv[1] if len(sys.argv) > 1 else None
    main(xml_file)