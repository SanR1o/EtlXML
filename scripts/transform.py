import logging
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


def transform_to_df(data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Transforma datos extraídos a DataFrame y aplica validaciones.
    Limpia y normaliza los datos para garantizar calidad.
    """
    try:
        if not data:
            logger.warning("No hay datos para transformar")
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        
        # Validación y limpieza
        df = _validate_and_clean(df)
        
        # Conversión de tipos
        df = _convert_data_types(df)
        
        logger.info(f"DataFrame creado con {len(df)} registros")
        return df
        
    except Exception as e:
        logger.error(f"Error en transformación de datos: {e}")
        raise


def _validate_and_clean(df: pd.DataFrame) -> pd.DataFrame:
    """
    Valida que los campos requeridos existan y limpia datos.
    Remueve filas con datos críticos incompletos.
    """
    campos_requeridos = ["numero", "fecha", "cliente", "total"]
    
    # Verificar que existan los campos
    for campo in campos_requeridos:
        if campo not in df.columns:
            df[campo] = ""
    
    # Eliminar espacios en blanco
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    
    # Remover filas con campos críticos vacíos
    df_initial_count = len(df)
    df = df[df[campos_requeridos].notna() & (df[campos_requeridos] != "")]
    
    if len(df) < df_initial_count:
        logger.warning(f"Se removieron {df_initial_count - len(df)} registros incompletos")
    
    return df


def _convert_data_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convierte los tipos de datos a los formatos apropiados.
    """
    try:
        if "fecha" in df.columns:
            df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
        
        if "total" in df.columns:
            df["total"] = pd.to_numeric(df["total"], errors="coerce")
        
        return df
        
    except Exception as e:
        logger.warning(f"Error en conversión de tipos: {e}. Continuando con tipos originales")
        return df