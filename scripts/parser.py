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
                invoice_number = _find_direct_child_text(inv, ("ID", "InvoiceID", "Numero"))
                invoice_date_text = _find_direct_child_text(inv, ("IssueDate", "Fecha", "Date"))
                invoice_date = _parse_date(invoice_date_text)
                period = _format_billing_period(invoice_date)
                item = {
                    "numero": invoice_number,
                    "invoice_key": _build_invoice_key(invoice_number, period),
                    "uuid": _find_direct_child_text(inv, ("UUID",)),
                    "fecha": invoice_date_text,
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
                    "periodo_facturacion": period,
                    "source_type": "xml",
                    "source_file": str(file_path_obj),
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
        invoice_numero_detalle = _build_invoice_key(invoice_numero, _format_billing_period(invoice_fecha))
        periodo_facturacion = _format_billing_period(invoice_fecha)

        lines = []
        for line in _find_elements_by_local_name(invoice, "InvoiceLine"):
            item = _extract_invoice_line(line, periodo_facturacion)
            if item:
                item["invoice_numero"] = invoice_numero_detalle
                item["invoice_key"] = invoice_numero_detalle
                item["invoice_uuid"] = invoice_uuid
                item["source_type"] = "xml"
                lines.append(item)

        logger.info(f"Se extrajeron {len(lines)} lineas de detalle del archivo {file_path}")
        return lines

    except ET.ParseError as e:
        logger.error(f"Error al parsear XML al extraer lineas: {e}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado en parse_invoice_lines: {e}")
        raise


def parse_pdf(file_path: str) -> Dict[str, Any]:
    """Extrae encabezado y detalle desde un PDF de factura."""
    return _parse_pdf(file_path)


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


def _find_first_attribute(root: ET.Element, candidates, attribute_name: str) -> str:
    """Busca el primer atributo presente en los elementos candidatos."""
    cand_lower = {c.lower() for c in candidates}
    for child in root.iter():
        if _local_name(child.tag).lower() in cand_lower:
            value = child.attrib.get(attribute_name, "")
            if value:
                return value
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

    nro = _first_non_empty(
        _find_direct_child_text(line, ("ID",)),
        properties.get("numerolinea", ""),
    )
    orden = _first_non_empty(properties.get("orden", ""), nro)
    identificacion_circuito = _first_non_empty(
        properties.get("identificaciondelcircuito", ""),
        properties.get("identificacioncircuito", ""),
        properties.get("circuito", ""),
        properties.get("circuitid", ""),
    )
    um = _first_non_empty(
        _find_first_attribute(line, ("InvoicedQuantity", "BaseQuantity"), "unitCode"),
        _find_first_attribute(line, ("InvoicedQuantity", "BaseQuantity"), "unitID"),
    )
    descripcion = _first_non_empty(
        properties.get("descripcion", ""),
        properties.get("detalle", ""),
        properties.get("concepto", ""),
        properties.get("nombre", ""),
        _find_first_text(line, ("Description",)),
    )
    tipo_cargo = _first_non_empty(
        properties.get("tipocargo", ""),
        properties.get("tipodecargo", ""),
        _find_first_text(line, ("Description",)),
    )
    impuesto = _first_non_empty(
        _find_first_text(line, ("TaxAmount",)),
        properties.get("impuesto", ""),
    )
    monto = _first_non_empty(
        _find_first_text(line, ("LineExtensionAmount",)),
        properties.get("monto", ""),
        properties.get("valortotalitem", ""),
    )

    return {
        "nro": nro,
        "orden": orden,
        "identificacion_circuito": identificacion_circuito,
        "periodo_facturacion": _first_non_empty(properties.get("periododefacturacion", ""), properties.get("periodofacturacion", ""), properties.get("periodo", ""), periodo_facturacion),
        "um": um,
        "descripcion": descripcion,
        "tipo_cargo": tipo_cargo,
        "impuesto": impuesto,
        "monto": monto,
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


def _parse_pdf(file_path: str) -> Dict[str, Any]:
    """Extrae encabezado y detalle desde un PDF de factura."""
    try:
        import pdfplumber
    except Exception as exc:
        raise ImportError("Se requiere pdfplumber para parsear PDFs") from exc

    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        raise FileNotFoundError(f"El archivo PDF no existe: {file_path}")

    with pdfplumber.open(file_path_obj) as pdf:
        header = _extract_pdf_header(pdf)
        details = _extract_pdf_details(pdf)

    invoice_number = header.get("numero", "")
    period = header.get("periodo_facturacion", "")
    invoice_key = _build_invoice_key(invoice_number, period)

    header.update(
        {
            "invoice_key": invoice_key,
            "periodo_facturacion": period,
            "source_type": "pdf",
            "source_file": str(file_path_obj),
            "lineas": str(len(details)),
        }
    )

    for detail in details:
        detail["invoice_key"] = invoice_key
        detail["invoice_numero"] = invoice_key
        detail["source_type"] = "pdf"

    return {"header": header, "details": details}


def _extract_pdf_header(pdf) -> Dict[str, Any]:
    """Extrae el encabezado básico del PDF."""
    first_page_text = (pdf.pages[0].extract_text() or "") if pdf.pages else ""
    invoice_number = _search_regex(first_page_text, r"Factura Electr[óo]nica de Venta\s+([A-Z0-9]+)")
    invoice_date_text = _search_regex(first_page_text, r"Fecha de Factura:\s*([0-9]{1,2}\s+[a-zA-Záéíóú\.]+\s+[0-9]{4})")
    invoice_date = _parse_pdf_spanish_date(invoice_date_text)
    period = _format_billing_period(invoice_date)

    return {
        "numero": invoice_number,
        "fecha": invoice_date.isoformat() if invoice_date else invoice_date_text,
        "periodo_facturacion": period,
        "lineas": _search_regex(first_page_text, r"LineCountNumeric") or "147",
        "source_file": None,
    }


def _extract_pdf_details(pdf) -> List[Dict[str, Any]]:
    """Reconstruye las filas del detalle de cargos desde el PDF."""
    rows: List[Dict[str, Any]] = []
    for page_number, page in enumerate(pdf.pages, start=1):
        if page_number == 1:
            continue

        words = sorted(page.extract_words(use_text_flow=True, keep_blank_chars=False), key=lambda w: (round(w["top"], 2), w["x0"]))
        current_words: List[Dict[str, Any]] = []

        for word in words:
            is_row_start = word["x0"] < 40 and word["text"].isdigit()
            if is_row_start and current_words:
                parsed = _parse_pdf_detail_row(current_words, page_number)
                if parsed:
                    rows.append(parsed)
                current_words = []

            if is_row_start or current_words:
                current_words.append(word)

        if current_words:
            parsed = _parse_pdf_detail_row(current_words, page_number)
            if parsed:
                rows.append(parsed)

    return rows


def _parse_pdf_detail_row(words: List[Dict[str, Any]], page_number: int) -> Dict[str, Any] | None:
    """Convierte un bloque de palabras en una fila de detalle."""
    if not words:
        return None

    primary_top = min(word["top"] for word in words if word["x0"] < 40 and word["text"].isdigit())
    first_line_words = [word for word in words if word["top"] <= primary_top + 1.5]

    def texts_in_range(x_min: float, x_max: float, source_words: List[Dict[str, Any]] | None = None) -> List[str]:
        selected_words = source_words if source_words is not None else words
        return [w["text"] for w in selected_words if x_min <= w["x0"] < x_max]

    def first_in_range(x_min: float, x_max: float, source_words: List[Dict[str, Any]] | None = None) -> str:
        values = texts_in_range(x_min, x_max, source_words)
        return " ".join(values).strip()

    nro = first_in_range(20, 45, first_line_words)
    orden = first_in_range(45, 105, first_line_words)
    identificacion_circuito = first_in_range(105, 170, first_line_words)
    periodo_facturacion = _normalize_pdf_spacing(first_in_range(170, 235))
    um = first_in_range(235, 260, first_line_words)
    descripcion = _normalize_pdf_spacing(first_in_range(260, 380))
    tipo_cargo = _normalize_pdf_spacing(first_in_range(375, 455, first_line_words))
    impuesto = _normalize_pdf_spacing(first_in_range(455, 530, first_line_words))
    monto = _normalize_pdf_spacing(first_in_range(530, 600, first_line_words))

    if not nro:
        return None

    return {
        "nro": nro,
        "orden": orden,
        "identificacion_circuito": identificacion_circuito,
        "periodo_facturacion": periodo_facturacion,
        "um": um,
        "descripcion": descripcion,
        "tipo_cargo": tipo_cargo,
        "impuesto": impuesto,
        "monto": monto,
        "pdf_page": page_number,
    }


def _normalize_pdf_spacing(value: str) -> str:
    """Compacta espacios y ajusta guiones del texto extraído desde PDF."""
    return " ".join(value.split()).replace(" - ", " - ").strip()


def _search_regex(text: str, pattern: str) -> str:
    import re

    match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else ""


def _parse_pdf_spanish_date(value: str) -> datetime | None:
    """Convierte una fecha PDF tipo '01 mar. 2026' a datetime."""
    if not value:
        return None
    import re

    normalized = value.lower().replace(".", "")
    month_map = {
        "ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
        "jul": 7, "ago": 8, "sep": 9, "oct": 10, "nov": 11, "dic": 12,
    }
    match = re.match(r"(\d{1,2})\s+([a-záéíóú]{3})\s+(\d{4})", normalized)
    if not match:
        return None
    day, month_text, year = match.groups()
    month = month_map.get(month_text[:3])
    if not month:
        return None
    return datetime(int(year), month, int(day))


def _build_invoice_key(invoice_number: str, period: str) -> str:
    """Construye la clave de índice para enlazar encabezado y detalle."""
    if not invoice_number:
        return ""
    return f"{invoice_number}_{period}" if period else invoice_number


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