# Proyecto ETL XML a Base de Datos

Herramienta profesional para extraer, transformar y cargar facturas desde archivos XML a una base de datos MSSQL.

## Descripción General

Este proyecto implementa un pipeline ETL robusto que:
- Extrae información de facturas desde archivos XML
- Aplica validación y limpieza de datos
- Carga los datos en MSSQL de forma eficiente
- Registra todo el proceso con logging detallado
- Guarda encabezado y detalle de factura en MySQL

## Inicio Rápido

Para instalación y ejecución paso a paso, usa esta guía:

- [docs/INSTALACION.md](docs/INSTALACION.md)

## Requisitos

- Python 3.7 o superior
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
DB_DRIVER=ODBC Driver 17 for SQL Server
DB_SERVER=tu_servidor
DB_NAME=FacturasDB
DB_USER=tu_usuario
DB_PASSWORD=tu_contraseña
INPUT_DATA_PATH=data/
OUTPUT_LOG_PATH=logs/
BATCH_SIZE=1000
LOG_LEVEL=INFO
```

## Uso

Ejecutar el proceso ETL:
```bash
python scripts/main.py
```

O especificar archivo XML:
```bash
python scripts/main.py data/factura_especifica.xml
```

## Estructura de Carpetas

```
EtlXML/
├── config.py              # Configuración centralizada
├── requirements.txt       # Dependencias Python
├── README.md             # Este archivo
├── .env.example          # Plantilla de variables de entorno
├── scripts/
│   ├── main.py          # Orquestador del pipeline ETL
│   ├── parser.py        # Extracción de datos XML
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
- Support para múltiples archivos XML
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
