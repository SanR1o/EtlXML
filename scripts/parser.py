import logging
import xml.etree.ElementTree as ET
from datetime import datetime
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

        invoice_roots = _collect_invoice_roots(root)

        # For each discovered invoice element, extract fields flexibly
        for inv in invoice_roots:
            try:
                item = {
                    "numero": _find_direct_child_text(inv, ("ID", "InvoiceID", "Numero")),
                    "uuid": _find_direct_child_text(inv, ("UUID",)),
                    "fecha": _find_direct_child_text(inv, ("IssueDate", "Fecha", "Date")),
                    "hora": _find_direct_child_text(inv, ("IssueTime", "Time")),
                    "cliente": _find_scope_text(inv, ("AccountingCustomerParty", "ReceiverParty"), ("RegistrationName", "Name", "PartyName")),
                    "cliente_nit": _find_scope_text(inv, ("AccountingCustomerParty", "ReceiverParty"), ("CompanyID",)),
                    "proveedor": _find_scope_text(inv, ("AccountingSupplierParty", "SenderParty"), ("RegistrationName", "Name", "PartyName")),
                    "proveedor_nit": _find_scope_text(inv, ("AccountingSupplierParty", "SenderParty"), ("CompanyID",)),
                    "moneda": _find_direct_child_text(inv, ("DocumentCurrencyCode", "CurrencyCode")),
                    "subtotal": _find_scope_text(inv, ("LegalMonetaryTotal",), ("TaxExclusiveAmount",)),
                    "impuestos": _find_scope_text(inv, ("TaxTotal",), ("TaxAmount",)),
                    "total": _find_scope_text(inv, ("LegalMonetaryTotal",), ("PayableAmount", "TaxInclusiveAmount", "Total")),
                    "lineas": _find_direct_child_text(inv, ("LineCountNumeric",)),
                    "tipo_documento": _find_direct_child_text(inv, ("InvoiceTypeCode", "DocumentType")),
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


def parse_invoice_lines(file_path: str) -> List[Dict[str, Any]]:
    """Extrae el detalle de líneas de la factura real dentro del XML."""
    try:
        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            raise FileNotFoundError(f"El archivo XML no existe: {file_path}")

        tree = ET.parse(file_path)
        root = tree.getroot()
        invoice = _get_primary_invoice(root)

        if invoice is None:
            logger.warning("No se encontró una factura real para extraer líneas")
            return []

        invoice_numero = _find_direct_child_text(invoice, ("ID", "InvoiceID", "Numero"))
        invoice_uuid = _find_direct_child_text(invoice, ("UUID",))
        invoice_fecha_text = _find_direct_child_text(invoice, ("IssueDate", "Fecha", "Date"))
        invoice_fecha = _parse_date(invoice_fecha_text)
        invoice_numero_detalle = _build_detail_invoice_number(invoice_numero, invoice_fecha)
        periodo_facturacion = _format_billing_period(invoice_fecha)

        lines = []
        for line in _find_elements_by_local_name(invoice, "InvoiceLine"):
            item = _extract_invoice_line(line, periodo_facturacion)
            if item:
                item["invoice_numero"] = invoice_numero_detalle
                item["invoice_uuid"] = invoice_uuid
                lines.append(item)

        logger.info(f"Se extrajeron {len(lines)} lineas de detalle del archivo {file_path}")
        return lines

    except ET.ParseError as e:
        logger.error(f"Error al parsear XML al extraer lineas: {e}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado en parse_invoice_lines: {e}")
        raise


def _safe_get_text(element: ET.Element, tag: str) -> str:
    """
    Obtiene el texto de un elemento de forma segura.
    Retorna cadena vacía si el elemento no existe o está vacío.
    """
    found_element = element.findtext(tag)
    return found_element if found_element else ""


def _collect_invoice_roots(root: ET.Element) -> List[ET.Element]:
    """Retorna solo nodos Invoice reales, ya sea embebidos como XML o presentes en el árbol."""
    invoice_roots: List[ET.Element] = []

    for elem in root.iter():
        if _local_name(elem.tag).lower() == "invoice":
            invoice_roots.append(elem)

    for elem in root.iter():
        text = (elem.text or "").strip()
        if not text:
            continue

        start = text.find("<?xml")
        if start == -1:
            start = text.find("<Invoice")
        if start == -1:
            continue

        xml_fragment = text[start:]
        try:
            frag_root = ET.fromstring(xml_fragment)
        except ET.ParseError:
            continue

        if _local_name(frag_root.tag).lower() == "invoice":
            invoice_roots.append(frag_root)

    unique_invoices: List[ET.Element] = []
    seen = set()
    for invoice in invoice_roots:
        key = ET.tostring(invoice, encoding="utf-8")
        if key in seen:
            continue
        seen.add(key)
        unique_invoices.append(invoice)

    return unique_invoices


def _get_primary_invoice(root: ET.Element) -> ET.Element | None:
    """Retorna la primera factura real encontrada."""
    invoices = _collect_invoice_roots(root)
    return invoices[0] if invoices else None


def _find_elements_by_local_name(root: ET.Element, local_name: str) -> List[ET.Element]:
    """Busca elementos por nombre local en todo el subárbol."""
    return [elem for elem in root.iter() if _local_name(elem.tag).lower() == local_name.lower()]


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


def _find_direct_child_text(root: ET.Element, candidates) -> str:
    """Busca solo en los hijos directos del nodo actual."""
    cand_lower = {c.lower() for c in candidates}
    for child in list(root):
        ln = _local_name(child.tag).lower()
        if ln in cand_lower:
            text = (child.text or "").strip()
            if text:
                return text
    return ""


def _find_scope_text(root: ET.Element, scope_candidates, value_candidates) -> str:
    """Busca el primer valor dentro del subárbol del primer scope directo que coincida."""
    scope_lower = {c.lower() for c in scope_candidates}
    for child in list(root):
        if _local_name(child.tag).lower() in scope_lower:
            value = _find_first_text(child, value_candidates)
            if value:
                return value
    return ""


def _extract_invoice_line(line: ET.Element, periodo_facturacion: str) -> Dict[str, Any]:
    """Extrae los campos requeridos para el detalle de factura."""
    properties = _collect_additional_item_properties(line)

    orden_numero = _first_non_empty(
        _find_direct_child_text(line, ("ID",)),
        properties.get("numerolinea", ""),
        properties.get("orden", ""),
    )
    identificacion_circuito = _first_non_empty(
        properties.get("identificaciondelcircuito", ""),
        properties.get("identificacioncircuito", ""),
        properties.get("circuito", ""),
        properties.get("circuitid", ""),
    )
    descripcion = _first_non_empty(
        properties.get("descripcion", ""),
        properties.get("detalle", ""),
        properties.get("concepto", ""),
        properties.get("nombre", ""),
    )
    tipo_cargo = _first_non_empty(
        properties.get("tipocargo", ""),
        properties.get("tipodecargo", ""),
        _find_first_text(line, ("Description",)),
    )

    return {
        "orden_numero": orden_numero,
        "identificacion_circuito": identificacion_circuito,
        "periodo_facturacion": _first_non_empty(properties.get("periododefacturacion", ""), properties.get("periodofacturacion", ""), properties.get("periodo", ""), periodo_facturacion),
        "descripcion": descripcion,
        "tipo_cargo": tipo_cargo,
    }


def _collect_additional_item_properties(line: ET.Element) -> Dict[str, str]:
    """Recopila AdditionalItemProperty como un diccionario normalizado nombre -> valor."""
    properties: Dict[str, str] = {}
    for element in line.iter():
        if _local_name(element.tag).lower() != "additionalitemproperty":
            continue

        name = ""
        value = ""
        for child in list(element):
            local = _local_name(child.tag).lower()
            if local == "name":
                name = (child.text or "").strip()
            elif local == "value":
                value = (child.text or "").strip()

        if name:
            properties[_normalize_key(name)] = value

    return properties


def _normalize_key(value: str) -> str:
    """Normaliza una clave de propiedad para comparación flexible."""
    return "".join(character for character in value.lower() if character.isalnum())


def _first_non_empty(*values: str) -> str:
    """Retorna el primer valor no vacío."""
    for value in values:
        if value:
            return value
    return ""


def _parse_date(value: str) -> datetime | None:
    """Convierte una fecha ISO simple a datetime."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        try:
            return datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            return None


def _format_billing_period(invoice_date: datetime | None) -> str:
    """Devuelve el periodo de facturación en formato 'mes_aaaa'."""
    if not invoice_date:
        return ""
    months = [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
    ]
    return f"{months[invoice_date.month - 1]}_{invoice_date.year}"


def _build_detail_invoice_number(invoice_number: str, invoice_date: datetime | None) -> str:
    """Construye el identificador de detalle con número de factura y periodo."""
    if not invoice_number:
        return ""
    suffix = _format_billing_period(invoice_date)
    return f"{invoice_number}_{suffix}" if suffix else invoice_number