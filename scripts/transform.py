import logging
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime
from decimal import Decimal, InvalidOperation

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


def transform_lines_to_df(data: List[Dict[str, Any]]) -> pd.DataFrame:
    """Transforma el detalle de líneas de factura a DataFrame."""
    try:
        if not data:
            logger.warning("No hay lineas para transformar")
            return pd.DataFrame()

        df = pd.DataFrame(data)
        df = _clean_line_dataframe(df)
        df = _convert_line_types(df)
        logger.info(f"DataFrame de lineas creado con {len(df)} registros")
        return df
    except Exception as e:
        logger.error(f"Error en transformación de lineas: {e}")
        raise


def _validate_and_clean(df: pd.DataFrame) -> pd.DataFrame:
    """
    Valida que los campos requeridos existan y limpia datos.
    Remueve filas con datos críticos incompletos.
    """
    campos_requeridos = ["numero", "invoice_key", "fecha", "cliente", "total"]
    campos_opcionales = [
        "uuid",
        "hora",
        "cliente_nit",
        "proveedor",
        "proveedor_nit",
        "moneda",
        "subtotal",
        "impuestos",
        "lineas",
        "tipo_documento",
        "periodo_facturacion",
        "source_type",
        "source_file",
    ]
    
    # Verificar que existan los campos
    for campo in campos_requeridos:
        if campo not in df.columns:
            df[campo] = ""

    for campo in campos_opcionales:
        if campo not in df.columns:
            df[campo] = ""
    
    # Eliminar espacios en blanco
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    
    # Remover filas con campos críticos vacíos
    df_initial_count = len(df)
    mask_requeridos = df[campos_requeridos].notna().all(axis=1) & (df[campos_requeridos] != "").all(axis=1)
    df = df.loc[mask_requeridos].copy()
    
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
            df["total"] = df["total"].apply(_parse_decimal_value)

        for field in ("subtotal", "impuestos"):
            if field in df.columns:
                df[field] = df[field].apply(_parse_decimal_value)

        if "lineas" in df.columns:
            df["lineas"] = pd.to_numeric(df["lineas"], errors="coerce").astype("Int64")
        
        return df
        
    except Exception as e:
        logger.warning(f"Error en conversión de tipos: {e}. Continuando con tipos originales")
        return df


def _clean_line_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Asegura columnas mínimas para el detalle de líneas."""
    required = ["invoice_key", "nro", "orden", "identificacion_circuito", "periodo_facturacion", "um", "tipo_cargo", "impuesto", "monto"]
    optional = ["descripcion", "source_type"]

    for col in required + optional:
        if col not in df.columns:
            df[col] = ""

    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    mask = df[required].notna().all(axis=1) & (df[required] != "").all(axis=1)
    return df.loc[mask].copy()


def _convert_line_types(df: pd.DataFrame) -> pd.DataFrame:
    """Convierte las columnas de detalle a tipos adecuados."""
    if "nro" in df.columns:
        df["nro"] = pd.to_numeric(df["nro"], errors="coerce").astype("Int64")

    if "orden" in df.columns:
        df["orden"] = df["orden"].astype("string").fillna("")

    for field in ("impuesto", "monto"):
        if field in df.columns:
            df[field] = df[field].apply(_parse_decimal_value)

    return df


def _parse_decimal_value(value: Any):
    """Convierte texto monetario local en Decimal compatible con MySQL."""
    if value is None or value == "":
        return pd.NA

    if isinstance(value, Decimal):
        return value

    try:
        if pd.isna(value):
            return pd.NA
    except Exception:
        pass

    text = str(value).strip()
    if not text:
        return pd.NA

    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    else:
        text = text.replace(",", "")

    try:
        return Decimal(text)
    except (InvalidOperation, ValueError):
        return pd.NA