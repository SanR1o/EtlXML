# Documentación: transform.py

## Descripción General

El módulo `transform.py` es responsable de transformar datos extraídos del XML en un DataFrame de Pandas optimizado. Implementa validación, limpieza y conversión de tipos para garantizar la calidad de los datos antes de la carga a base de datos.

## Función: transform_to_df

### Propósito

Convierte lista de diccionarios en DataFrame de Pandas, aplicando validaciones y normalizaciones.

### Firma

```python
def transform_to_df(data: List[Dict[str, Any]]) -> pd.DataFrame
```

### Parámetros

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `data` | List[Dict[str, Any]] | Lista de diccionarios extraídos por parser.py |

### Retorna

`pd.DataFrame`: DataFrame con columnas validadas, tipadas y limpias. Retorna DataFrame vacío si entrada está vacía.

### Excepciones

| Excepción | Causa |
|-----------|-------|
| Genera logging WARNING | Si la entrada está vacía |
| Genera logging ERROR | Si hay error en transformación (propaga excepción) |

### Ejemplo de Uso

```python
from parser import parse_xml
from transform import transform_to_df

# Extrae datos
data = parse_xml("data/factura.xml")

# Transforma a DataFrame
df = transform_to_df(data)

# Verifica resultado
print(f"Registros validados: {len(df)}")
print(df.dtypes)  # Ver tipos de datos
```

## Función Auxiliar: _validate_and_clean

### Propósito

Valida presencia de campos requeridos y limpia datos de espacios en blanco innecesarios.

### Firma

```python
def _validate_and_clean(df: pd.DataFrame) -> pd.DataFrame
```

### Operaciones Realizadas

1. **Verificación de campos**: Asegura que existan columnas requeridas
   - numero
   - fecha
   - cliente
   - total

2. **Limpieza de espacios**: Elimina espacios en blanco al inicio/final

3. **Remoción de filas incompletas**: Elimina registros con campos críticos vacíos

### Lógica Detallada

```python
# Agregar columnas faltantes
for campo in ["numero", "fecha", "cliente", "total"]:
    if campo not in df.columns:
        df[campo] = ""

# Limpiar espacios para campos de texto
df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

# Remover filas con datos incompletos
df = df[(df["numero"] != "") & 
        (df["fecha"] != "") & 
        (df["cliente"] != "") & 
        (df["total"] != "")]
```

### Ejemplo de Aplicación

```python
# Entrada
data = [
    {"numero": "  FAC001  ", "fecha": "2024-01-01", "cliente": "ABC", "total": "100"},
    {"numero": "", "fecha": "2024-01-02", "cliente": "XYZ", "total": "200"},  # Se elimina
    {"numero": "FAC003", "fecha": "", "cliente": "", "total": "300"}  # Se elimina
]

# Después de _validate_and_clean
# Solo 1 fila, con "numero" = "FAC001" (sin espacios)
```

## Función Auxiliar: _convert_data_types

### Propósito

Convierte campos de texto a tipos de datos apropiados (fecha, numérico) con manejo tolerante de errores.

### Firma

```python
def _convert_data_types(df: pd.DataFrame) -> pd.DataFrame
```

### Conversiones Aplicadas

| Campo | Tipo Original | Tipo Destino | Método |
|-------|---------------|--------------|--------|
| fecha | str | datetime | `pd.to_datetime()` con errors="coerce" |
| total | str | float/numeric | `pd.to_numeric()` con errors="coerce" |

### Estrategia de Manejo de Errores

- **errors="coerce"**: Convierte valores inválidos a NaN en lugar de lanzar excepción
- **Tolerancia**: Continúa procesando incluso si hay errores de conversión
- **Logging**: Registra advertencia pero no detiene ejecución

### Ejemplo

```python
df = pd.DataFrame({
    "fecha": ["2024-01-01", "fecha-invalida", "2024-01-03"],
    "total": ["100.50", "abc", "300.75"]
})

# Después de conversión
# fecha column: [2024-01-01, NaT, 2024-01-03]
# total column: [100.50, NaN, 300.75]
# LOG: WARNING - Error en conversión de tipos
```

## Flujo Completo de Transformación

```
1. Entrada: Lista de diccionarios
   ↓
2. Crear DataFrame básico
   ↓
3. Validar y limpiar (remove NAs, trim spaces)
   ↓
4. Convertir tipos (fecha, total)
   ↓
5. Salida: DataFrame optimizado
```

## Cambios de Datos

### Antes

```python
[
    {"numero": "  FAC-001  ", "fecha": "2024-01-15", "cliente": "Empresa A", "total": "1500.50"},
    {"numero": "FAC-002", "fecha": "", "cliente": "Empresa B", "total": "2300"},
]
```

### Después

```
   numero   fecha   cliente      total
0  FAC-001  2024-01-15  Empresa A  1500.50
# Fila con fecha vacía fue eliminada
```

## Validaciones Implementadas

### Campos Requeridos

- `numero`: No puede estar vacío
- `fecha`: No puede estar vacío (será parseada a datetime)
- `cliente`: No puede estar vacío
- `total`: No puede estar vacío (será convertido a número)

### Coerciones de Tipo

- Fechas inválidas: Convertidas a NaT (Not a Time)
- Totales no numéricos: Convertidos a NaN

## Logging

### Mensajes Registrados

```
INFO: DataFrame creado con 45 registros
WARNING: Se removieron 3 registros incompletos
WARNING: Error en conversión de tipos: [mensaje]
WARNING: No hay datos para transformar
ERROR: Error en transformación de datos: [excepción]
```

## Rendimiento

### Complejidad

- **Temporal**: O(n) donde n = número de filas
- **Espacial**: O(n) por DataFrame resultante

### Optimizaciones Implementadas

- Uso de operaciones vectorizadas de Pandas (no loops explícitos)
- Método `apply()` eficiente sobre columnas
- Conversiones con `pd.to_datetime()` y `pd.to_numeric()` optimizadas

## Extensibilidad

### Agregar Nueva Validación

```python
def _validate_and_clean(df: pd.DataFrame) -> pd.DataFrame:
    # ... código existente ...
    
    # Nueva validación: verificar rango de valores
    if "total" in df.columns:
        df = df[df["total"] > 0]  # Solo totales positivos
    
    return df
```

### Agregar Nueva Conversión de Tipo

```python
def _convert_data_types(df: pd.DataFrame) -> pd.DataFrame:
    # ... código existente ...
    
    # Nueva conversión: campo 'cantidad'
    if "cantidad" in df.columns:
        df["cantidad"] = pd.to_numeric(df["cantidad"], errors="coerce")
    
    return df
```

## Integración

### Con parser.py

```python
from parser import parse_xml
data = parse_xml("file.xml")
# Retorna: List[Dict[str, Any]]
```

### Con load_sql.py

```python
from transform import transform_to_df
df = transform_to_df(data)
# Retorna: pd.DataFrame con tipos correctos
# Esperado por insert_data(df)
```

### Con main.py

```python
from transform import transform_to_df
df = transform_to_df(data)

if df.empty:
    logger.warning("No hay datos después de transformación")
```

## Mejores Prácticas

1. Siempre validar que df no esté vacío antes de siguiente etapa
2. Revisar logs para identificar qué registros fueron removidos
3. Usar type hints cuando se extienda el módulo
4. Mantener consistencia con campos esperados por load_sql.py
5. Documentar cualquier cambio en validaciones

## Casos de Uso Especiales

### Manejo de NaN

```python
# Después de transformación
print(df.isnull().sum())  # Ver cantidad de NaN por columna

# En load_sql.py, NaN se manejan gracefully
# (se insertan como NULL en SQL)
```

### Debugging

```python
# Ver qué registros fueron filtrados
df_original = pd.DataFrame(data)
df_cleaned = transform_to_df(data)
removed = len(df_original) - len(df_cleaned)
print(f"Registros removidos: {removed}")
```

## Tipos de Datos Finales

```python
df.dtypes
# numero        object (str)
# fecha         datetime64
# cliente       object (str)
# total         float64
```
