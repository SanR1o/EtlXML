import logging
import xml.etree.ElementTree as ET
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


def parse_xml(file_path: str) -> List[Dict[str, Any]]:
    """
    Extrae información de facturas desde archivos XML.
    Maneja validación básica y manejo de errores.
    """
    try:
        file_path_obj = Path(file_path)
        
        if not file_path_obj.exists():
            raise FileNotFoundError(f"El archivo XML no existe: {file_path}")
        
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        data = []
        
        for factura in root.findall('.//Factura'):
            try:
                item = {
                    "numero": _safe_get_text(factura, "Numero"),
                    "fecha": _safe_get_text(factura, "Fecha"),
                    "cliente": _safe_get_text(factura, "Cliente"),
                    "total": _safe_get_text(factura, "Total")
                }
                data.append(item)
            except Exception as e:
                logger.warning(f"Error procesando factura: {e}")
                continue
        
        logger.info(f"Se extrajeron {len(data)} facturas del archivo {file_path}")
        return data
        
    except ET.ParseError as e:
        logger.error(f"Error al parsear XML: {e}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado en parse_xml: {e}")
        raise


def _safe_get_text(element: ET.Element, tag: str) -> str:
    """
    Obtiene el texto de un elemento de forma segura.
    Retorna cadena vacía si el elemento no existe o está vacío.
    """
    found_element = element.findtext(tag)
    return found_element if found_element else ""