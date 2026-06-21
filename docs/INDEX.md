# Índice de Documentación del Proyecto ETL XML

Documentación técnica detallada de cada componente del sistema.

## Navegación Rápida

### Documentos Principales

| Documento | Descripción |
|-----------|-------------|
| [INSTALACION.md](INSTALACION.md) | Instalación y ejecución rápida paso a paso |
| [FASE2_XML_PDF.md](FASE2_XML_PDF.md) | Guía nueva de uso, arquitectura y motivos de las herramientas |
| [CONFIG.md](CONFIG.md) | Configuración centralizada y variables de entorno |
| [PARSER.md](PARSER.md) | Extracción de datos desde archivos XML y PDF |
| [TRANSFORM.md](TRANSFORM.md) | Validación, limpieza y transformación de datos |
| [LOAD_SQL.md](LOAD_SQL.md) | Carga de datos a base de datos MySQL |
| [MAIN.md](MAIN.md) | Orquestador del pipeline ETL |

## Flujo del Proyecto

```
1. main.py (ORQUESTADOR)
   ├─ Configura logging
   ├─ Valida configuración
   └─ Coordina las 3 fases:

2. EXTRACCIÓN: parser.py
   └─ Lee ficheros XML y PDF
   └─ Extrae datos de facturas y detalle
   └─ Valida estructura
   └─ Retorna lista de diccionarios

3. TRANSFORMACIÓN: transform.py
   └─ Convierte a DataFrame
   └─ Limpia datos (espacios, valores nulos)
   └─ Convierte tipos (fechas, números)
   └─ Valida campos requeridos
   └─ Retorna DataFrame limpio

4. CARGA: load_sql.py
   └─ Conecta a MySQL
   └─ Inserta registros en transacción
   └─ Maneja errores
   └─ Cierra conexión seguramente

5. CONFIG.py (SOPORTE)
   └─ Centraliza configuración
   └─ Lee variables de entorno
   └─ Genera strings de conexión
```

## Componentes por Responsabilidad

### Extracción de Datos
- **Archivo**: [parser.py](PARSER.md)
- **Función principal**: `parse_xml(file_path: str)` / `parse_pdf(file_path: str)`
- **Descripción**: Lee archivos XML y PDF y extrae información de facturas
- **Salida**: `List[Dict[str, Any]]`

### Transformación y Validación
- **Archivo**: [transform.py](TRANSFORM.md)
- **Función principal**: `transform_to_df(data: List[Dict])`
- **Descripción**: Convierte a DataFrame, valida, limpia y tipifica datos
- **Salida**: `pd.DataFrame`

### Carga de Base de Datos
- **Archivo**: [load_sql.py](LOAD_SQL.md)
- **Clase principal**: `DatabaseManager`
- **Descripción**: Gestiona conexión a MySQL e inserción de registros
- **Método**: `insert_data(df: pd.DataFrame) -> int`

### Configuración
- **Archivo**: [config.py](CONFIG.md)
- **Clase**: `Config`
- **Descripción**: Centraliza variables de configuración y credenciales
- **Métodos**: `get_db_connection_string()`, `validate_config()`

### Orquestación
- **Archivo**: [main.py](MAIN.md)
- **Función principal**: `main(xml_file: Optional[str])`
- **Descripción**: Coordina el flujo completo ETL
- **Setup**: Configura logging para toda la aplicación

## Mejoras Implementadas

### Seguridad
- Credenciales en variables de entorno (archivo `.env`)
- Prepared statements en queries SQL
- Validación de configuración en startup

### Robustez
- Manejo exhaustivo de excepciones
- Logging en múltiples niveles (INFO, WARNING, ERROR)
- Transacciones SQL para integridad de datos
- Rollback automático en caso de error

### Calidad
- Type hints en todas las funciones
- Validación y limpieza de datos
- Conversión segura de tipos (con `errors="coerce"`)
- Documentación detallada en cada módulo

### Mantenibilidad
- Modularización clara (separación ETL)
- Comentarios generales en código
- Documentación técnica específica en carpeta `docs/`
- Reutilización de conexiones
- Context managers para gestión de recursos

## Convenciones de Documentación

### En el Código (comentarios generales)
```python
# Descripción del qué y por qué
# No detalles de implementación
```

### En Ficheros MD (documentación específica)
```markdown
# Función: nombre_funcion

## Propósito
Explicación clara del objetivo

## Firma
Firma de la función con tipos

## Parámetros
Tabla con tipos y descripciones

## Ejemplo
Caso de uso práctico
```

## Cómo Navegar la Documentación

### Para Entender el Flujo Completo
1. Leer [README.md](../README.md) en raíz (visión general)
2. Leer [MAIN.md](MAIN.md) (orquestador)
3. Seguir en orden: PARSER.md → TRANSFORM.md → LOAD_SQL.md → CONFIG.md

### Para Entender un Componente Específico
- [parser.py](PARSER.md): Ir directamente a PARSER.md
- [transform.py](TRANSFORM.md): Ir directamente a TRANSFORM.md
- [load_sql.py](LOAD_SQL.md): Ir directamente a LOAD_SQL.md
- [config.py](CONFIG.md): Ir directamente a CONFIG.md

### Para Resolver Problemas
1. Ver logs en `logs/etl_process.log`
2. Buscar nivel de error (ERROR, WARNING)
3. Consultar documentación del módulo relevante en carpeta `docs/`
4. Revisar sección "Troubleshooting" en el MD

## Variables de Entorno Necesarias

Ver [CONFIG.md](CONFIG.md) para lista completa.

Variables críticas:
- `DB_USER`: Usuario de base de datos
- `DB_PASSWORD`: Contraseña de base de datos
- `DB_SERVER`: Servidor SQL Server

## Comandos Útiles

```bash
# Ver logs en tiempo real
tail -f logs/etl_process.log

# Ejecutar con archivo específico
python scripts/main.py data/factura_especial.xml

# Con nivel de logging DEBUG
LOG_LEVEL=DEBUG python scripts/main.py

# Verificar configuración
python -c "from config import Config; print(Config.get_db_connection_string())"
```

## Estructura de la Carpeta docs/

```
docs/
├── INDEX.md         # Este archivo
├── CONFIG.md        # Configuración centralizada
├── PARSER.md        # Extracción XML
├── TRANSFORM.md     # Transformación y validación
├── LOAD_SQL.md      # Carga a MSSQL
└── MAIN.md          # Orquestación ETL
```

## Mantenimiento de Documentación

- Actualizar MD cuando cambies funcionalidad
- Mantener comentarios en código generales
- Documentar nuevos campos en tablas
- Actualizar ejemplos de uso
- Revisar índice cuando agreges nuevos documentos
