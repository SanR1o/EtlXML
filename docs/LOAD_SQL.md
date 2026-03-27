# Documentación: load_sql.py

## Descripción General

El módulo `load_sql.py` gestiona la conexión a base de datos MSSQL y la carga de datos en forma eficiente y robusta. Implementa el patrón de gestor de recursos con soporte para context managers y manejo de transacciones.

## Clase: DatabaseManager

### Propósito

Encapsula todas las operaciones de base de datos, proporcionando una interfaz limpia y segura.

### Responsabilidades

- Establecer y mantener conexión a MSSQL
- Insertar datos con integridad transaccional
- Manejar errores y recuperación
- Registrar operaciones en logs

## Iniciación

### Constructor

```python
def __init__(self)
```

Inicializa el gestor con conexión nula. La conexión se establece bajo demanda.

### Ejemplo Básico

```python
from load_sql import DatabaseManager

db = DatabaseManager()
inserted = db.insert_data(df)
db.disconnect()
```

### Con Context Manager

```python
from load_sql import DatabaseManager

with DatabaseManager() as db:
    count = db.insert_data(df)
    # Conexión se cierra automáticamente
```

## Método: connect

### Propósito

Establece conexión a base de datos MSSQL usando credenciales de config.py.

### Firma

```python
def connect(self) -> pyodbc.Connection
```

### Retorna

`pyodbc.Connection`: Objeto de conexión. Si ya existe conexión activa, la reutiliza.

### Excepciones

| Excepción | Causa |
|-----------|-------|
| `pyodbc.DatabaseError` | Error de autenticación o servidor no disponible |
| `Exception` | Otros errores inesperados |

### Ejemplo

```python
db = DatabaseManager()

try:
    conn = db.connect()
    print("Conectado exitosamente")
except pyodbc.DatabaseError as e:
    print(f"Error de conexión: {e}")
```

### Cadena de Conexión

Utiliza formato ODBC con parámetros de config.py:

```
DRIVER={ODBC Driver 17 for SQL Server};
SERVER=localhost;
DATABASE=FacturasDB;
UID=usuario;
PWD=contraseña
```

## Método: disconnect

### Propósito

Cierra la conexión a base de datos de forma segura.

### Firma

```python
def disconnect(self) -> None
```

### Comportamiento

- Verifica que exista conexión activa
- Cierra conexión
- Establece referencia a None
- Registra en log

### Ejemplo

```python
db = DatabaseManager()
db.connect()
# ... operaciones ...
db.disconnect()
```

## Método: insert_data

### Propósito

Inserta múltiples filas de DataFrame en tabla Facturas de forma transaccional.

### Firma

```python
def insert_data(self, df: pd.DataFrame) -> int
```

### Parámetros

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `df` | pd.DataFrame | DataFrame con 4 columnas: numero, fecha, cliente, total |

### Retorna

`int`: Cantidad de filas insertadas exitosamente.

### Excepciones

| Excepción | Causa | Acción |
|-----------|-------|--------|
| Logs WARNING | DataFrame vacío | Retorna 0 |
| Logs ERROR | Fila con datos inválidos | Rollback y continúa |
| Propaga Exception | Error crítico de BD | Rollback y termina |

### Ejemplo de Uso

```python
from load_sql import DatabaseManager
import pandas as pd

df = pd.DataFrame({
    'numero': ['FAC-001', 'FAC-002'],
    'fecha': ['2024-01-01', '2024-01-02'],
    'cliente': ['Empresa A', 'Empresa B'],
    'total': [100.50, 200.75]
})

db = DatabaseManager()
try:
    inserted = db.insert_data(df)
    print(f"Insertados {inserted} registros")
finally:
    db.disconnect()
```

### Flujo de Ejecución

```
1. Verificar DataFrame no vacío
2. Conectar a base de datos
3. Para cada fila:
   a. Ejecutar INSERT statement
   b. Si error: log WARNING, ROLLBACK, continuar
   c. Si OK: incrementar contador
4. COMMIT transacción
5. Retornar contador de insertados
```

### SQL Statement

```sql
INSERT INTO Facturas (numero, fecha, cliente, total)
VALUES (?, ?, ?, ?)
```

Usa prepared statements para prevenir SQL injection.

### Transacciones

- **Estrategia**: Una transacción por lote completo
- **Commit**: Al final exitosamente (todas las filas)
- **Rollback**: Si ocurre error crítico

## Context Manager

### Propósito

Permite usar DatabaseManager con statement `with` para garantizar limpieza de recursos.

### Métodos Especiales

```python
def __enter__(self):
    """Establece conexión al entrar context"""
    self.connect()
    return self

def __exit__(self, exc_type, exc_val, exc_tb):
    """Cierra conexión al salir context"""
    self.disconnect()
```

### Ventajas

- Garantiza cierre automático de conexión
- Limpia incluso si hay excepciones
- Código más limpio y pythónico

### Ejemplo

```python
with DatabaseManager() as db:
    count = db.insert_data(df)
    print(f"Insertados: {count}")
# Conexión se cierra automáticamente aquí
```

## Función: insert_data (Wrapper)

### Propósito

Función de conveniencia que usa DatabaseManager internamente.

### Firma

```python
def insert_data(df: pd.DataFrame) -> int
```

### Implementación

```python
def insert_data(df: pd.DataFrame) -> int:
    db_manager = DatabaseManager()
    try:
        return db_manager.insert_data(df)
    finally:
        db_manager.disconnect()
```

### Uso Simplificado

```python
from load_sql import insert_data

count = insert_data(df)  # Maneja conexión internamente
```

## Manejo de Errores

### Estrategia

1. **Errores de conexión**: Detiene ejecución (propaga)
2. **Errores de fila**: Loguea y continúa con siguientes
3. **Errores de transacción**: Rollback y loguea

### Ejemplo de Recuperación

```python
from load_sql import DatabaseManager

db = DatabaseManager()
try:
    inserted = db.insert_data(df)
except Exception as e:
    print(f"Error: {e}")
    # Base de datos está en estado consistente (rollback automático)
finally:
    db.disconnect()
```

## Logging

### Mensajes de Información

```
INFO: Conexión a base de datos establecida
INFO: Se insertaron 50 registros. Fallos: 0
INFO: Conexión a base de datos cerrada
```

### Mensajes de Advertencia

```
WARNING: DataFrame vacío, nada que insertar
WARNING: Se removieron 3 registros incompletos
```

### Mensajes de Error

```
ERROR: Error al conectar a la base de datos: [detalles]
ERROR: Error insertando fila 5: foreign key constraint violation
ERROR: Error durante inserción en lote: connection timeout
```

## Configuración de Base de Datos

### Requisitos SQL

La tabla `Facturas` debe existir con estructura:

```sql
CREATE TABLE Facturas (
    ID INT PRIMARY KEY IDENTITY(1,1),
    numero VARCHAR(50) NOT NULL,
    fecha DATETIME2,
    cliente VARCHAR(255) NOT NULL,
    total DECIMAL(18,2),
    CreatedDate DATETIME2 DEFAULT GETDATE()
)
```

### ODBC Driver

Requiere: `ODBC Driver 17 for SQL Server`

Verificar disponibilidad:
```powershell
# En Windows
Get-OdbcDriver | Select Name
```

## Rendimiento y Optimizaciones

### Características

- **Reutilización de conexión**: No abre/cierra per fila
- **Transacción única**: Commit una sola vez
- **Prepared statements**: Previene SQL injection

### Complejidad

- **Temporal**: O(n) donde n = número de filas
- **Espacial**: O(1) por fila (no acumula en memoria)

### Mejoras Futuras

- Batch inserting (INSERT multiple filas al mismo tiempo)
- Connection pooling para múltiples insercciones
- Async/await para operaciones no bloqueantes

## Troubleshooting

### Error: "Microsoft ODBC Driver not found"

```powershell
# Instalar driver en Windows
# Descargar desde: https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server
```

### Error: "Login failed for user"

Verificar credenciales en `.env`:
```
DB_USER=correcto_usuario
DB_PASSWORD=correcta_contraseña
```

### Error: "Connection timeout"

Verificar:
- Servidor MSSQL está corriendo
- Red está disponible
- Firewall permite conexión

## Integración

### Con transform.py

```python
from transform import transform_to_df
from load_sql import insert_data

df = transform_to_df(data)
count = insert_data(df)
```

### Con main.py

```python
from load_sql import DatabaseManager

db_manager = DatabaseManager()
try:
    rows_inserted = db_manager.insert_data(df)
    logger.info(f"Carga completada: {rows_inserted} registros")
finally:
    db_manager.disconnect()
```

## Mejores Prácticas

1. Usar context manager cuando sea posible
2. Validar DataFrame antes de insertar
3. Revisar logs para identificar filas problemáticas
4. No insertar datos sin transformación previa
5. Mantener credenciales en variables de entorno
6. Usar prepared statements (ya implementado)
7. Verificar integridad de datos antes de BD

## Extensibilidad

### Agregar Método de Actualización

```python
def update_data(self, df: pd.DataFrame, where_clause: str) -> int:
    """Actualiza registros en base de datos"""
    # Implementación similar a insert_data
```

### Agregar Validación de Tabla

```python
def validate_table_exists(self, table_name: str) -> bool:
    """Verifica que tabla exista antes de insertar"""
    # Query sys.tables
```
