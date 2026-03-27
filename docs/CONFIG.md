# Documentación: config.py

## Descripción General

El archivo `config.py` centraliza toda la configuración de la aplicación. Implementa el patrón de configuración segura utilizando variables de entorno a través de `python-dotenv`, evitando así credenciales hardcodeadas en el código fuente.

## Clase: Config

### Responsabilidades

- Centralizar todas las variables de configuración
- Obtener valores desde variables de entorno con defaults seguros
- Generar cadenas de conexión a base de datos
- Validar configuración crítica

### Atributos Principales

#### Configuración de Base de Datos

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `DB_DRIVER` | str | Driver ODBC para SQL Server (default: "ODBC Driver 17 for SQL Server") |
| `DB_SERVER` | str | Servidor SQL destino (default: "localhost") |
| `DB_NAME` | str | Nombre de la base de datos (default: "FacturasDB") |
| `DB_USER` | str | Usuario de base de datos |
| `DB_PASSWORD` | str | Contraseña de base de datos |

#### Configuración de Rutas

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `INPUT_DATA_PATH` | str | Ruta donde se encuentran archivos XML (default: "data/") |
| `OUTPUT_LOG_PATH` | str | Ruta donde se generan logs (default: "logs/") |

#### Configuración de Procesamiento

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `BATCH_SIZE` | int | Cantidad de registros por lote (default: 1000) |
| `ENCODING` | str | Encoding de archivos (default: "utf-8") |
| `LOG_LEVEL` | str | Nivel de logging: DEBUG, INFO, WARNING, ERROR (default: "INFO") |

### Métodos

#### `get_db_connection_string() -> str`

**Propósito**: Genera la cadena de conexión formateada para pyodbc.

**Retorna**: String con formato compatible con pyodbc.connect()

**Ejemplo**:
```python
conn_string = Config.get_db_connection_string()
# DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=FacturasDB;UID=usuario;PWD=pass
```

#### `validate_config() -> bool`

**Propósito**: Verifica que las variables críticas estén configuradas.

**Raises**: `ValueError` si `DB_USER` o `DB_PASSWORD` no están definidas.

**Retorna**: `True` si la validación es exitosa.

**Uso**:
```python
try:
    Config.validate_config()
except ValueError as e:
    logger.error(f"Configuración inválida: {e}")
```

## Flujo de Carga de Configuración

1. `load_dotenv()` lee el archivo `.env` en la raíz del proyecto
2. Cada atributo intenta obtener el valor de `os.getenv()`
3. Si no existe variable de entorno, usa el valor default
4. En tiempo de ejecución, `validate_config()` verifica variables críticas

## Configuración de Variables de Entorno

Crear archivo `.env` en raíz del proyecto:

```
DB_DRIVER=ODBC Driver 17 for SQL Server
DB_SERVER=mi_servidor.database.windows.net
DB_NAME=FacturasDB
DB_USER=admin@mi_servidor
DB_PASSWORD=MiContraseñaSegura123!
INPUT_DATA_PATH=data/
OUTPUT_LOG_PATH=logs/
BATCH_SIZE=500
LOG_LEVEL=DEBUG
```

## Jerarquía de Prioridad

1. Variable de entorno (máxima prioridad)
2. Valor default en config.py
3. Error de validación si es crítica

## Seguridad

- **NUNCA** incluir `.env` en control de versión (está en `.gitignore`)
- **NUNCA** harcodear credenciales en el código
- Usar `.env.example` como plantilla sin valores reales
- Para CI/CD, configurar variables de entorno en la plataforma
- Cambiar contraseña si fue expuesta en repositorio

## Integración con Otros Módulos

### Desde load_sql.py
```python
from config import Config

connection_string = Config.get_db_connection_string()
pyodbc.connect(connection_string)
```

### Desde main.py
```python
Config.validate_config()
log_path = Path(Config.OUTPUT_LOG_PATH)
xml_file = f"{Config.INPUT_DATA_PATH}factura.xml"
```

## Extensibilidad

Para agregar nuevas configuraciones:

```python
# En config.py
NUEVA_VARIABLE: str = os.getenv("NUEVA_VARIABLE", "default_value")

# En .env
NUEVA_VARIABLE=valor_real
```

## Type Hints

Todos los atributos utilizan type hints siguiendo PEP 484:
- `str`: para variables de texto
- `int`: para valores numéricos
- `Dict`, `Any`: para estructuras complejas

Esto permite que IDEs como VS Code proporcionen autocompletado y detección de errores.
