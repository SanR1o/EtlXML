# Documentación: main.py

## Descripción General

El archivo `main.py` es el punto de entrada de la aplicación. Coordina el flujo completo del pipeline ETL (Extracción, Transformación, Carga) y proporciona logging centralizado para toda la aplicación.

## Función: setup_logging

### Propósito

Configura el sistema de logging global para la aplicación.

### Firma

```python
def setup_logging() -> None
```

### Comportamiento

1. Lee configuración de logging desde `config.py`
2. Crea directorio de logs si no existe
3. Configura dos handlers simultáneos:
   - **FileHandler**: Escribe logs a archivo `logs/etl_process.log`
   - **StreamHandler**: Escribe logs a consola (stdout)

### Formato de Log

```
2024-01-27 14:35:42,123 - parser - INFO - Se extrajeron 25 facturas del archivo
```

Componentes:
- Timestamp: Fecha y hora del evento
- Logger: Módulo que generó el evento (parser, transform, load_sql)
- Nivel: INFO, WARNING, ERROR, DEBUG
- Mensaje: Descripción del evento

### Niveles de Log Configurables

| Nivel | Uso | Desde Variable |
|-------|-----|-------------------|
| DEBUG | Información detallada para diagnosis | LOG_LEVEL=DEBUG |
| INFO | Eventos normales (default) | LOG_LEVEL=INFO |
| WARNING | Situaciones inesperadas pero recuperables | LOG_LEVEL=WARNING |
| ERROR | Errores que impiden operación | LOG_LEVEL=ERROR |

## Función: main

### Propósito

Ejecuta el pipeline ETL completo: extrae, transforma y carga datos.

### Firma

```python
def main(xml_file: Optional[str] = None) -> None
```

### Parámetros

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `xml_file` | Optional[str] | Ruta a archivo XML específico. Si None, usa default de config |

### Flujo de Ejecución

```
1. Configurar logging
2. Obtener logger de main
3. Iniciar proceso ETL
4. Validar configuración crítica
5.
   EXTRACCIÓN:
   - Determinar archivo XML
   - Llamar parse_xml()
   - Registrar en log
6.
   TRANSFORMACIÓN:
   - Llamar transform_to_df()
   - Validar DataFrame no vacío
   - Registrar cantidad de registros
7.
   CARGA:
   - Llamar insert_data()
   - Registrar cantidad insertada
8. Reportar éxito o error
```

### Ejemplo de Uso Directo

```python
# Usar archivo default (data/factura.xml)
main()

# Especificar archivo específico
main("data/factura_especial.xml")
```

## Script de Ejecución

### Bloque Principal

```python
if __name__ == "__main__":
    xml_file = sys.argv[1] if len(sys.argv) > 1 else None
    main(xml_file)
```

Permite:
- Ejecutar desde línea de comandos
- Pasar parámetros por argumentos
- No ejecutar si se importa como módulo

## Ejecución desde Terminal

### Sintaxis Básica

```bash
# Usar archivo default
python scripts/main.py

# Especificar archivo
python scripts/main.py data/factura_especial.xml

# Con rutas absolutas
python scripts/main.py C:\datos\factura.xml
```

### Desde Raíz del Proyecto

```bash
cd c:\Users\sanrio\Downloads\Projects\EtlXML
python scripts/main.py
```

### Resultado Esperado

```
2024-01-27 14:35:40,123 - __main__ - INFO - Iniciando proceso ETL
2024-01-27 14:35:41,456 - parser - INFO - Se extrajeron 45 facturas
2024-01-27 14:35:42,789 - transform - INFO - DataFrame creado con 45 registros
2024-01-27 14:35:43,234 - load_sql - INFO - Se insertaron 45 registros
2024-01-27 14:35:43,567 - __main__ - INFO - Proceso ETL completado exitosamente
```

## Manejo de Errores

### Validación de Configuración

```python
try:
    Config.validate_config()
except ValueError as e:
    logger.error(f"Configuración inválida: {e}")
    # Detiene ejecución
```

Valida que:
- `DB_USER` esté configurado
- `DB_PASSWORD` esté configurado

### Errores por Etapa

#### Etapa de Extracción

```
ERROR: Archivo no encontrado: data/factura.xml
ERROR: Error al parsear XML: invalid format
ERROR: Error inesperado en parse_xml: [excepción]
```

#### Etapa de Transformación

```
WARNING: No hay datos para transformar
ERROR: Error en transformación de datos: [excepción]
```

#### Etapa de Carga

```
ERROR: Error al conectar a base de datos: [excepción]
ERROR: Error durante inserción en lote: [excepción]
```

### Captura de Excepciones

```python
try:
    main(xml_file)
except Exception as e:
    logger.error(f"Error fatal en proceso ETL: {e}", exc_info=True)
    raise
```

- `exc_info=True`: Incluye stack trace completo en log
- `raise`: Propaga excepción para que llamador sepa del error

## Importación de Módulos

### Path Setup

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
```

Permite importar desde módulos hermanos:
- main.py está en `scripts/`
- parser, transform, load_sql están en `scripts/`
- config está en raíz

### Importaciones

```python
from parser import parse_xml
from transform import transform_to_df
from load_sql import insert_data
from config import Config
```

## Validaciones Implementadas

### 1. Configuración

```python
Config.validate_config()
# Lanza ValueError si falta credenciales
```

### 2. Archivo XML

```python
if not xml_file:
    xml_file = f"{Config.INPUT_DATA_PATH}factura.xml"
```

Usa archivo default si no se especifica.

### 3. Datos Transformados

```python
if df.empty:
    logger.warning("No hay datos para cargar después de transformación")
    return
```

Detiene si transformación resultó en DataFrame vacío.

## Logging Detallado

### Información Registrada

```
INICIO:
  - Timestamp de inicio
  - Variables de configuración (sin credenciales)
  - Archivo XML a procesar

EXTRACCIÓN:
  - Cantidad de facturas extraídas
  - Errores durante parsing

TRANSFORMACIÓN:
  - Cantidad de registros en DataFrame
  - Registros removidos por validación

CARGA:
  - Cantidad de registros insertados
  - Cantidad de fallos

FIN:
  - Timestamp de término
  - Resultado general (éxito/error)
```

### Archivo de Log

Ubicación: `logs/etl_process.log`

Contiene historial completo de todas las ejecuciones con timestamps.

## Extensibilidad

### Agregar Nueva Etapa

```python
# En main():
logger.info("Nueva operación iniciada")
result = nueva_funcion(df)
logger.info("Nueva operación completada")
```

### Agregar Parámetro de Entrada

```python
def main(xml_file: Optional[str] = None, 
         batch_size: Optional[int] = None) -> None:
    if batch_size:
        Config.BATCH_SIZE = batch_size
```

### Agregar Validación

```python
try:
    # ... código ETL ...
    if resultado_inesperado:
        logger.error("Validación fallida")
        raise ValueError("Descripción del error")
except ValueError as e:
    logger.error(f"Error de validación: {e}")
```

## Integración con Otros Módulos

### Dependencias

```
main.py
├── parser.py (parse_xml)
├── transform.py (transform_to_df)
├── load_sql.py (insert_data)
└── config.py (Config)
```

### Contrato de Interfaces

```
parse_xml(str) -> List[Dict[str, Any]]
transform_to_df(List[Dict]) -> pd.DataFrame
insert_data(pd.DataFrame) -> int
Config.validate_config() -> bool
Config.get_db_connection_string() -> str
```

## Testing

### Caso de Prueba 1: Ejecución Normal

```bash
python scripts/main.py
# Expected: Logs INFO, proceso completa éxito
```

### Caso de Prueba 2: Archivo Especificado

```bash
python scripts/main.py data/otra_factura.xml
# Expected: Procesa archivo específico
```

### Caso de Prueba 3: Error de Configuración

```bash
# En terminal, sin .env configurado:
python scripts/main.py
# Expected: ERROR - credenciales no configuradas
```

### Caso de Prueba 4: Archivo No Existe

```bash
python scripts/main.py data/inexistente.xml
# Expected: ERROR - archivo no encontrado
```

## Mejores Prácticas

1. Usar variables de entorno para configuración
2. Siempre usar logging en lugar de print()
3. Validar antes de cada etapa importante
4. Incluir exc_info=True en logs de error
5. Verificar que DataFrame no esté vacío
6. Usar type hints en firmas de funciones
7. Mantener main() legible y modular

## Estructura de Proyecto Esperada

```
EtlXML/
├── config.py
├── requirements.txt
├── .env                # NO incluir en git
├── scripts/
│   ├── main.py        # Este archivo
│   ├── parser.py
│   ├── transform.py
│   └── load_sql.py
├── data/
│   └── factura.xml
├── logs/
│   └── etl_process.log
└── docs/              # Documentación
```

## Notas de Administración

- Revisar `logs/etl_process.log` regularmente para monitorear proceso
- Configurar renovación de logs cada 7 días
- Documentar cambios en config.py
- Mantener .env seguro con permisos apropiados
