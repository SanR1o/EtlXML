# Guía de la Fase 2: XML + PDF

Esta guía resume cómo usar la versión actual del proyecto, qué hace cada herramienta y por qué existe cada parte del flujo.

## Objetivo

El sistema ya no depende solo del XML. Ahora puede:
- Detectar automáticamente archivos XML y PDF en la carpeta de entrada
- Parsear ambos formatos
- Unificar la información usando `invoice_key`
- Completar campos faltantes entre XML y PDF cuando sea necesario
- Cargar encabezado y detalle en MySQL

## Cuándo usar esta versión

Usa esta fase cuando:
- El XML tenga información incompleta del detalle
- El PDF contenga los campos de detalle que el XML no trae
- Necesites procesar una carpeta completa sin indicar archivo por archivo
- Quieras dejar un índice de facturas en base de datos para evitar duplicados y facilitar cruces futuros

## Flujo general

1. `main.py` descubre los archivos disponibles
2. `parser.py` extrae encabezado y detalle desde XML o PDF
3. `transform.py` limpia, valida y normaliza los datos
4. `load_sql.py` crea o ajusta las tablas e inserta la información en MySQL

## Cómo usarlo

### 1. Coloca los archivos en `data/`

Puedes dejar uno o varios archivos:
- XML de factura
- PDF de factura
- Ambos para la misma factura

### 2. Ejecuta el proceso

Desde la raíz del proyecto:

```powershell
python scripts/main.py
```

También puedes pasar una ruta concreta:

```powershell
python scripts/main.py data/factura.xml
python scripts/main.py data/factura.pdf
python scripts/main.py data
```

### 3. Revisa el resultado

- La consola muestra el avance del proceso
- El log queda en `logs/etl_process.log`
- MySQL guarda encabezado y detalle

## Qué hace cada herramienta y por qué existe

### `scripts/main.py`

**Qué hace**
- Busca archivos XML y PDF
- Agrupa por `invoice_key`
- Combina la información de ambas fuentes
- Llama a transformación y carga

**Por qué existe**
- Evita procesar un solo archivo aislado
- Permite una orquestación simple y reproducible
- Centraliza la lógica de complementación entre fuentes

### `scripts/parser.py`

**Qué hace**
- Lee XML de facturas
- Lee PDF de facturas
- Extrae encabezado y detalle
- Reconstruye filas del PDF con posiciones de palabras

**Por qué existe**
- El XML no trae todo el detalle operativo de la factura
- El PDF sí trae la tabla completa de cargos
- El PDF no se puede leer como tabla estructurada de forma confiable, por eso se usa lectura por coordenadas

### `scripts/transform.py`

**Qué hace**
- Limpia textos y nulos
- Convierte importes al formato correcto para MySQL
- Conserva `orden` como texto cuando el PDF lo representa de forma mixta
- Valida que existan los campos mínimos

**Por qué existe**
- Los datos de factura vienen con formatos locales como `1.234.567,89`
- MySQL necesita valores numéricos compatibles
- Mantiene el dataset consistente antes de guardar

### `scripts/load_sql.py`

**Qué hace**
- Crea o ajusta el esquema de tablas
- Usa `invoice_key` como índice principal de factura
- Inserta encabezado con upsert
- Inserta detalle con unicidad por factura y número de línea

**Por qué existe**
- Permite volver a correr el ETL sin duplicar facturas
- Convierte la base de datos en índice de control del proceso
- Facilita futuras consultas y cruces entre XML y PDF

### `config.py`

**Qué hace**
- Centraliza variables de entorno
- Valida que la conexión a MySQL esté lista
- Define rutas base de entrada y salida

**Por qué existe**
- Evita credenciales hardcodeadas
- Hace el proyecto portable entre equipos
- Reduce errores de configuración

## Qué columnas se esperan en el detalle

La tabla de detalle trabaja con estos campos principales:
- `nro`
- `orden`
- `identificacion_circuito`
- `periodo_facturacion`
- `um`
- `descripcion`
- `tipo_cargo`
- `impuesto`
- `monto`

## Cómo funciona la complementación XML + PDF

La regla práctica es:
- El PDF se toma como fuente principal del detalle
- El XML completa campos vacíos cuando el PDF no trae algún valor
- Ambos se unen por `nro` dentro de la misma factura
- `invoice_key` sirve para agrupar todo en una sola factura lógica

Esto permite conservar el detalle visual del PDF y aprovechar los datos estructurados del XML.

## Por qué se usa `invoice_key`

`invoice_key` se usa como clave de negocio porque:
- Identifica la factura de forma consistente
- Permite deduplicar registros
- Hace posible combinar fuentes distintas
- Sirve como índice de la tabla principal de facturas

## Recomendación de operación diaria

1. Copia los XML y PDF nuevos a `data/`
2. Ejecuta `python scripts/main.py`
3. Revisa el log si hubo advertencias
4. Consulta MySQL para verificar encabezado y detalle

## Problemas comunes

### No se detectan archivos

Verifica que estén dentro de `data/` o que la ruta pasada al comando exista.

### El detalle queda incompleto

Puede pasar si falta información tanto en XML como en PDF. En ese caso el dato se inserta solo si el campo crítico está disponible.

### Error de importes

Si aparece un valor numérico raro, revisa que el texto siga el formato local esperado. La transformación ya convierte la mayoría de estos casos.

## Siguiente paso recomendado

Si vas a seguir creciendo el proyecto, el siguiente paso útil es:
- crear una tabla de control para archivos procesados
- agregar validación de re-ejecución por fecha o nombre de archivo
- almacenar trazabilidad entre XML, PDF y factura consolidada
