import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config
from scripts.parser import parse_xml
from scripts.parser import parse_invoice_lines
from scripts.parser import parse_pdf
from scripts.transform import transform_to_df, transform_lines_to_df
from scripts.load_sql import insert_data, insert_line_data

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
        
        input_path = Path(xml_file) if xml_file else Path(Config.INPUT_DATA_PATH)
        documents = _build_documents_index(input_path)

        if not documents:
            logger.warning(f"No se encontraron archivos XML/PDF en {input_path}")
            return

        total_headers = 0
        total_details = 0

        for invoice_key, document in documents.items():
            header = document.get("header", {})
            details = document.get("details", [])

            if not header:
                logger.warning(f"Documento sin encabezado utilizable: {invoice_key}")
                continue

            header_df = transform_to_df([header])
            detail_df = transform_lines_to_df(details)

            if header_df.empty:
                logger.warning(f"Encabezado vacío después de transformar: {invoice_key}")
                continue

            logger.info(f"Cargando documento {invoice_key}")
            total_headers += insert_data(header_df)
            if not detail_df.empty:
                total_details += insert_line_data(detail_df)

        logger.info(
            f"Proceso ETL completado exitosamente. Encabezados: {total_headers}. Detalles: {total_details}"
        )
        
    except Exception as e:
        logger.error(f"Error fatal en proceso ETL: {e}", exc_info=True)
        raise


def _build_documents_index(input_path: Path) -> Dict[str, Dict[str, Any]]:
    """Descubre XML/PDF y consolida un documento por factura."""
    documents: Dict[str, Dict[str, Any]] = {}
    files = _discover_input_files(input_path)

    for file_path in files:
        suffix = file_path.suffix.lower()
        try:
            if suffix == ".xml":
                headers = parse_xml(str(file_path))
                detail_rows = parse_invoice_lines(str(file_path))
                for header in headers:
                    invoice_key = header.get("invoice_key") or _build_invoice_key_from_header(header)
                    document = documents.setdefault(
                        invoice_key,
                        {"header": {}, "details": [], "xml_details": [], "pdf_details": [], "sources": []},
                    )
                    document["header"] = _merge_missing(document["header"], header)
                    if detail_rows:
                        document["xml_details"] = detail_rows
                    document["sources"].append(str(file_path))

            elif suffix == ".pdf":
                parsed = parse_pdf(str(file_path))
                header = parsed.get("header", {})
                details = parsed.get("details", [])
                invoice_key = header.get("invoice_key") or _build_invoice_key_from_header(header)
                document = documents.setdefault(
                    invoice_key,
                    {"header": {}, "details": [], "xml_details": [], "pdf_details": [], "sources": []},
                )
                document["header"] = _merge_missing(document["header"], header)
                if details:
                    document["pdf_details"] = details
                document["sources"].append(str(file_path))

        except Exception as exc:
            logger.error(f"No se pudo procesar {file_path}: {exc}")

    for invoice_key, document in documents.items():
        document["header"].setdefault("invoice_key", invoice_key)
        document["header"]["source_file"] = " | ".join(document["sources"])
        document["header"]["source_type"] = _infer_source_type(document["sources"])

        document["details"] = _merge_detail_rows(
            document.get("xml_details", []),
            document.get("pdf_details", []),
            invoice_key,
        )

    return documents


def _discover_input_files(input_path: Path) -> List[Path]:
    """Devuelve archivos XML y PDF a procesar."""
    if input_path.is_file():
        return [input_path]

    if not input_path.exists():
        return []

    return sorted(
        [path for path in input_path.rglob("*") if path.suffix.lower() in {".xml", ".pdf"}]
    )


def _merge_missing(base: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
    """Completa valores vacíos en base usando incoming sin sobreescribir datos ya presentes."""
    merged = dict(base)
    for key, value in incoming.items():
        if _is_missing(merged.get(key)) and not _is_missing(value):
            merged[key] = value
    return merged


def _merge_detail_rows(xml_rows: List[Dict[str, Any]], pdf_rows: List[Dict[str, Any]], invoice_key: str) -> List[Dict[str, Any]]:
    """Fusiona detalle XML y PDF usando el PDF como fuente principal."""
    if not xml_rows and not pdf_rows:
        return []

    xml_index = {str(row.get("nro")): row for row in xml_rows if row.get("nro") not in (None, "")}
    pdf_index = {str(row.get("nro")): row for row in pdf_rows if row.get("nro") not in (None, "")}

    ordered_keys = sorted(
        set(xml_index) | set(pdf_index),
        key=lambda value: int(value) if str(value).isdigit() else str(value),
    )

    merged_rows: List[Dict[str, Any]] = []
    for nro in ordered_keys:
        merged = _merge_missing(pdf_index.get(nro, {}), xml_index.get(nro, {}))
        merged.setdefault("invoice_key", invoice_key)
        merged.setdefault("invoice_numero", invoice_key)
        merged_rows.append(merged)

    return merged_rows


def _is_missing(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _build_invoice_key_from_header(header: Dict[str, Any]) -> str:
    numero = header.get("numero", "")
    periodo = header.get("periodo_facturacion", "")
    return f"{numero}_{periodo}" if numero and periodo else numero


def _infer_source_type(sources: List[str]) -> str:
    suffixes = {Path(source).suffix.lower().lstrip(".") for source in sources}
    if suffixes == {"xml"}:
        return "xml"
    if suffixes == {"pdf"}:
        return "pdf"
    if "xml" in suffixes and "pdf" in suffixes:
        return "xml+pdf"
    return "+".join(sorted(suffixes)) if suffixes else "unknown"


if __name__ == "__main__":
    xml_file = sys.argv[1] if len(sys.argv) > 1 else None
    main(xml_file)