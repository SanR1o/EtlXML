# Guía de Instalación y Uso Rápido

Esta guía reúne el paso a paso completo para instalar y ejecutar el proyecto ETL de XML a MSSQL con el menor número de pasos.

## 1. Prerrequisitos

Asegúrate de tener instalado:

- Python 3.14 (o la versión usada en tu entorno)
- SQL Server accesible desde tu equipo
- ODBC Driver 17 o superior para SQL Server

Verifica Python en terminal:

```powershell
python --version
```

## 2. Ubícate en la raíz del proyecto

Desde PowerShell:

```powershell
cd C:\Users\sanrio\Downloads\Projects\EtlXML
```

## 3. Crear y activar entorno virtual

Crear entorno:

```powershell
python -m venv .venv
```

Activar entorno:

```powershell
.\.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea scripts, habilita ejecución una sola vez:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Luego vuelve a activar:

```powershell
.\.venv\Scripts\Activate.ps1
```

## 4. Instalar dependencias

Actualiza pip:

```powershell
python -m pip install --upgrade pip
```

Instala paquetes del proyecto:

```powershell
pip install -r requirements.txt
```

Verifica instalación:

```powershell
pip list
```

## 5. Configurar variables de entorno

Copia plantilla:

```powershell
copy .env.example .env
```

Edita el archivo .env con tus datos reales:

```env
DB_DRIVER=ODBC Driver 17 for SQL Server
DB_SERVER=localhost
DB_NAME=FacturasDB
DB_USER=tu_usuario
DB_PASSWORD=tu_password
INPUT_DATA_PATH=data/
OUTPUT_LOG_PATH=logs/
BATCH_SIZE=1000
ENCODING=utf-8
LOG_LEVEL=INFO
```

## 6. Preparar XML de entrada

Coloca tu XML en la carpeta data.

Ejemplo esperado:

- data/factura.xml

Si usarás otro nombre, luego lo pasas como argumento al ejecutar.

## 7. Ejecutar el ETL

Modo normal (usa data/factura.xml):

```powershell
python scripts/main.py
```

Modo con archivo específico:

```powershell
python scripts/main.py data/mi_factura.xml
```

## 8. Revisar resultado

- Consola: muestra el avance y errores del proceso
- Log: se genera en logs/etl_process.log

Para leer el log:

```powershell
Get-Content logs/etl_process.log
```

## 9. Flujo mínimo diario

Cuando ya está instalado, tu flujo rápido queda así:

```powershell
cd C:\Users\sanrio\Downloads\Projects\EtlXML
.\.venv\Scripts\Activate.ps1
python scripts/main.py data/archivo_del_dia.xml
```

## 10. Problemas comunes

### Error instalando pandas

Causa típica: versión de pandas no compatible con la versión de Python.  
Solución: mantener el requirements actualizado y reinstalar:

```powershell
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### Error de conexión a SQL Server

Revisa en .env:

- DB_SERVER
- DB_NAME
- DB_USER
- DB_PASSWORD

También confirma que el driver ODBC esté instalado.

### No encuentra archivo XML

Verifica ruta y nombre del archivo pasado en el comando.

## 11. Referencias

Para detalle técnico por módulo:

- CONFIG.md
- PARSER.md
- TRANSFORM.md
- LOAD_SQL.md
- MAIN.md
