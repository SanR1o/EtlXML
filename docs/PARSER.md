# Documentación: parser.py

## Descripción General

El módulo `parser.py` es responsable de la extracción de datos desde archivos XML. Implementa parsing robusto con validación, manejo de errores y logging detallado para garantizar la integridad de los datos extraídos.

## Función: parse_xml

### Propósito

Extrae información de facturas desde un archivo XML y retorna datos en formato de lista de diccionarios.

### Firma

```python
def parse_xml(file_path: str) -> List[Dict[str, Any]]
```

### Parámetros

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `file_path` | str | Ruta absoluta o relativa al archivo XML a procesar |

### Retorna

`List[Dict[str, Any]]`: Lista de diccionarios donde cada diccionario representa una factura con claves:
- `numero`: String con número de factura
- `fecha`: String con fecha de factura
- `cliente`: String con nombre del cliente
- `total`: String con monto total

### Excepciones

| Excepción | Causa |
|-----------|-------|
| `FileNotFoundError` | Archivo XML no existe en la ruta especificada |
| `xml.etree.ElementTree.ParseError` | Archivo XML tiene formato inválido o está corrupto |

### Ejemplo de Uso

```python
from parser import parse_xml

# Caso básico
data = parse_xml("data/factura.xml")
for invoice in data:
    print(f"Factura {invoice['numero']}: {invoice['total']}")

# Con manejo de errores
try:
    data = parse_xml("data/factura_especial.xml")
except FileNotFoundError:
    print("Archivo no encontrado")
except Exception as e:
    print(f"Error: {e}")
```

### Lógica Interna

1. **Validación de ruta**: Verifica que el archivo exista
2. **Parsing XML**: Lee y parsea el documento con ElementTree
3. **Iteración**: Busca todos los elementos `<Factura>`
4. **Extracción segura**: Obtiene datos usando `_safe_get_text()`
5. **Recolección**: Almacena cada factura como diccionario
6. **Logging**: Registra cantidad de facturas extraídas

## Función Auxiliar: _safe_get_text

### Propósito

Extrae texto de un elemento XML de forma segura, evitando excepciones cuando el elemento no existe.

### Firma

```python
def _safe_get_text(element: ET.Element, tag: str) -> str
```

### Parámetros

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `element` | ET.Element | Elemento XML padre |
| `tag` | str | Nombre del tag a buscar |

### Retorna

`str`: Texto contenido en el elemento, o string vacío ("") si:
- El elemento no existe
- El elemento está vacío
- El contenido es None

### Ejemplo

```python
# Asumiendo: <Factura><Numero>123</Numero></Factura>
import xml.etree.ElementTree as ET

elem = ET.fromstring("<Factura><Numero>123</Numero></Factura>")
numero = _safe_get_text(elem, "Numero")  # Retorna "123"
cliente = _safe_get_text(elem, "Cliente")  # Retorna "" (no existe)
```

## Estructura XML Esperada

### Formato Requerido

```xml
<?xml version="1.0" encoding="utf-8"?>
<root>
    <Factura>
        <Numero>FAC-001</Numero>
        <Fecha>2024-01-15</Fecha>
        <Cliente>Empresa S.A.</Cliente>
        <Total>1500.50</Total>
    </Factura>
    <Factura>
        <Numero>FAC-002</Numero>
        <Fecha>2024-01-16</Fecha>
        <Cliente>Empresa B Ltda.</Cliente>
        <Total>2300.00</Total>
    </Factura>
</root>
```

### Variaciones Soportadas

El parser maneja:
- Espacios en blanco adicionales
- Elementos faltantes (se retorna string vacío)
- Diferentes niveles de anidamiento con xpath `.//Factura`

### Variaciones NO Soportadas (Aún)

- Namespaces XML complejos
- Atributos de elementos
- CDATA sections
- Referencias a entidades externas

## Manejo de Errores

### Errores Capturados

1. **FileNotFoundError**: Archivo no existe
   - Loguea: ERROR
   - Propagar: Sí
   - Acción: Detiene ejecución

2. **ParseError**: XML malformado
   - Loguea: ERROR
   - Propagar: Sí
   - Acción: Detiene ejecución

3. **Error en iteración de facturas**: Elemento corrupto
   - Loguea: WARNING
   - Propagar: No
   - Acción: Salta factura, continúa con siguientes

### Estrategia de Logging

```
INFO: Se extrajeron 45 facturas del archivo data/factura.xml
WARNING: Error procesando factura: KeyError en elemento 3
ERROR: El archivo XML no existe: data/inexistente.xml
```

## Rendimiento y Optimizaciones

### Características

- **Streaming**: No carga todo el XML en memoria
- **XPath optimizado**: `.//Factura` es más eficiente que búsqueda recursiva
- **Sin duplicación**: Cada factura se procesa una sola vez

### Complejidad

- **Temporal**: O(n) donde n = número de facturas
- **Espacial**: O(n) por lista de diccionarios resultante
- **Recomendación**: Para archivos > 100MB, considerar chunking

## Extensibilidad Futura

### Mejoras Potenciales

1. Soporte para namespaces XML
2. Validación de formato de campos (ej: fecha ISO)
3. Parsing paralelo para múltiples archivos
4. Caché de resultados ya procesados
5. Soporte para XSD validation

### Cómo Agregar Campos

```python
# En parse_xml(), agregar a diccionario item:
item = {
    "numero": _safe_get_text(factura, "Numero"),
    "fecha": _safe_get_text(factura, "Fecha"),
    "cliente": _safe_get_text(factura, "Cliente"),
    "total": _safe_get_text(factura, "Total"),
    # Nuevos campos:
    "rut_proveedor": _safe_get_text(factura, "RutProveedor"),
    "cantidad_items": _safe_get_text(factura, "CantidadItems"),
}
```

## Integración

### Con transform.py

```python
from parser import parse_xml
from transform import transform_to_df

data = parse_xml("data/factura.xml")
df = transform_to_df(data)  # Espera exactamente este formato
```

### Con main.py

```python
from parser import parse_xml

xml_file = f"{Config.INPUT_DATA_PATH}factura.xml"
data = parse_xml(xml_file)
```

## Testing

### Casos de Prueba Recomendados

```python
# Test 1: XML válido con múltiples facturas
# Test 2: XML con elemento Factura faltante
# Test 3: XML con campos faltantes en Factura
# Test 4: Archivo no existe
# Test 5: Archivo XML corrupto
# Test 6: Archivo XML con namespaces
```

## Mejores Prácticas

1. Validar ruta del archivo antes de llamar a parse_xml()
2. Usar try-except en main.py para manejar excepciones
3. Verificar logs para identificar facturas problemáticas
4. No modificar estructura del diccionario retornado
5. Usar config.py para rutas en lugar de hardcodearlas
