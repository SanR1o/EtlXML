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

        # Collect candidate invoice elements:
        invoice_roots: List[ET.Element] = []

        # 1) Direct elements named Invoice/Factura (namespace-agnostic)
        for elem in root.iter():
            ln = _local_name(elem.tag)
            if ln.lower() in ("invoice", "factura", "comprobante"):
                invoice_roots.append(elem)

        # 2) Look for CDATA or embedded XML inside text nodes (e.g., cbc:Description containing an <Invoice> document)
        for elem in root.iter():
            text = (elem.text or "").strip()
            if not text:
                continue
            # try to find embedded XML start
            idx = text.find("<?xml")
            if idx == -1:
                idx = text.find("<Invoice")
                if idx == -1:
                    idx = text.find("<Factura")
            if idx != -1:
                xml_fragment = text[idx:]
                try:
                    frag_root = ET.fromstring(xml_fragment)
                    invoice_roots.append(frag_root)
                except ET.ParseError:
                    # ignore fragments that can't be parsed
                    continue

        # Remove duplicates (by id of element)
        seen = set()
        unique_invoices = []
        for ir in invoice_roots:
            key = id(ir)
            if key not in seen:
                unique_invoices.append(ir)
                seen.add(key)

        # For each discovered invoice element, extract fields flexibly
        for inv in unique_invoices:
            try:
                numero = _find_first_text(inv, ("ID", "InvoiceID", "Numero"))
                fecha = _find_first_text(inv, ("IssueDate", "Fecha", "Date"))
                cliente = _find_first_text(inv, ("RegistrationName", "CustomerName", "Nombre", "AccountName"))
                total = _find_first_text(inv, ("PayableAmount", "Total", "LegalMonetaryTotal", "Amount"))

                item = {
                    "numero": numero,
                    "fecha": fecha,
                    "cliente": cliente,
                    "total": total
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


def _local_name(tag: str) -> str:
    """Devuelve el nombre local de una etiqueta XML (sin namespace)."""
    if tag is None:
        return ""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _find_first_text(root: ET.Element, candidates) -> str:
    """Busca en el árbol el primer elemento cuyo nombre local esté en candidates y devuelve su texto.

    candidates: iterable of local names (case-insensitive)
    """
    cand_lower = {c.lower() for c in candidates}
    for elem in root.iter():
        ln = _local_name(elem.tag).lower()
        if ln in cand_lower:
            text = (elem.text or "").strip()
            if text:
                return text
    return ""