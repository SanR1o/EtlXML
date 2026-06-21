# Proyecto ETL XML + PDF a MySQL

Herramienta profesional para descubrir, extraer, transformar y cargar facturas desde archivos XML y PDF hacia una base de datos MySQL.

## Descripción General

Este proyecto implementa un pipeline ETL robusto que:
- Descubre automáticamente archivos XML y PDF en la carpeta de entrada
- Extrae encabezado y detalle de facturas desde ambos formatos
- Complementa la información entre XML y PDF cuando falta algún campo
- Usa MySQL como índice de facturas mediante `invoice_key`
- Aplica validación, limpieza y normalización de datos
- Registra todo el proceso con logging detallado

## Inicio Rápido

Para instalación y ejecución paso a paso, usa esta guía:

- [docs/INSTALACION.md](docs/INSTALACION.md)

## Requisitos

- Python 3.14 o superior
- MySQL Server 8 o superior
- Las dependencias en `requirements.txt`

## Instalación

1. Clonar el repositorio:
```bash
git clone <repository_url>
cd EtlXML
```

2. Crear ambiente virtual:
```bash
python -m venv venv
venv\Scripts\activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Configurar variables de entorno:
```bash
copy .env.example .env
# Editar .env con valores reales
```

## Configuración

Crear archivo `.env` en la raíz del proyecto con:

```
DB_SERVER=localhost
DB_NAME=FacturasDB
DB_USER=tu_usuario
DB_PASSWORD=tu_contraseña
INPUT_DATA_PATH=data/
OUTPUT_LOG_PATH=logs/
BATCH_SIZE=1000
LOG_LEVEL=INFO
```

## Uso

Ejecutar el proceso ETL completo sobre la carpeta `data`:
```bash
python scripts/main.py
```

O especificar una ruta concreta a un XML o PDF:
```bash
python scripts/main.py data/factura_especifica.xml
python scripts/main.py data/factura_especifica.pdf
```

El proceso hará lo siguiente:
- Identifica los archivos disponibles
- Parsea XML y PDF por separado
- Fusiona ambos por `invoice_key`
- Usa XML para completar lo que el PDF no trae, y viceversa si aplica
- Inserta un encabezado y sus líneas de detalle en MySQL

Guía completa de la nueva fase:

- [docs/FASE2_XML_PDF.md](docs/FASE2_XML_PDF.md)

## Estructura de Carpetas

```
EtlXML/
├── config.py              # Configuración centralizada
├── requirements.txt       # Dependencias Python
├── README.md             # Este archivo
├── .env.example          # Plantilla de variables de entorno
├── scripts/
│   ├── main.py          # Orquestador del pipeline ETL
│   ├── parser.py        # Extracción de datos XML y PDF
│   ├── transform.py     # Validación y transformación
│   └── load_sql.py      # Carga a base de datos
├── data/                # Archivos XML de entrada
├── logs/                # Archivos de log
└── docs/                # Documentación técnica detallada
```

## Características Principales

- Modularización clara con separación de responsabilidades
- Validación robusta de datos con manejo de errores
- Logging centralizado para auditoría
- Configuración segura sin credenciales hardcodeadas
- Type hints para mejorar mantenibilidad
- Soporte para múltiples archivos XML y PDF
- Índice de facturas por `invoice_key`
- Complementación de datos entre fuentes
- Transacciones de base de datos para integridad
- Extracción de encabezado y detalle de la factura

## Mejores Prácticas Implementadas

1. **Seguridad**: Credenciales en variables de entorno
2. **Robustez**: Manejo exhaustivo de excepciones
3. **Trazabilidad**: Logging en archivo y consola
4. **Validación**: Limpieza y normalización de datos
5. **Reusabilidad**: Conexiones persistentes
6. **Documentación**: Type hints y comentarios claros

## Resolución de Problemas

Ver carpeta `docs/` para guías detalladas sobre cada componente.

Guía recomendada para instalación y uso diario:

- [docs/INSTALACION.md](docs/INSTALACION.md)

Logs disponibles en: `logs/etl_process.log`

## Contribuciones

Para reportar problemas o sugerencias, crear un issue en el repositorio.

## Licencia

Ver LICENSE para más detalles.
