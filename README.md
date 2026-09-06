# CodeQL Miner

Herramienta de minería de datos y análisis estático de código diseñada para automatizar la detección de vulnerabilidades en proyectos alojados en GitHub. El sistema consulta las API de GitHub, clona los repositorios de una organización, analiza su código fuente mediante la CLI de CodeQL y consolida los hallazgos en un reporte estandarizado en formato JSON.

---

## Requisitos del Sistema

Para el correcto funcionamiento de la herramienta se requiere disponer de las siguientes herramientas instaladas y configuradas en el entorno:

* **Python:** Versión 3.10 o superior.
* **Git CLI:** Configurado y accesible globalmente desde la línea de comandos.
* **CodeQL CLI:** Instalado y disponible en la variable de entorno `PATH` del sistema.

---

## Estructura del Proyecto

El código está organizado como un paquete modular en Python con separación de responsabilidades:

```text
.
├── pyproject.toml
├── README.md
├── .env.example
├── .gitignore
├── src/
│   └── miner/
│       ├── __init__.py
│       ├── analizador_codeql.py
│       ├── cli.py
│       ├── codeql_runner.py
│       ├── config.py
│       ├── github_client.py
│       ├── models.py
│       └── sarif_parser.py
└── tests/
    ├── test_models.py
    └── test_sarif_parser.py


--- 

## Instalación

    Clonar el repositorio localmente:

        git clone [https://github.com/Fer-Vega-uni/miner-vulnerabilidades.git](https://github.com/Fer-Vega-uni/miner-vulnerabilidades.git)
        cd Miner-vulnerabilidades

    Crear y activar un entorno virtual de Python:
        python -m venv .venv
        source .venv/bin/activate

    Instalar el proyecto y sus dependencias en modo ejecutable:
        pip install -e .

## Configuración de Autenticación

Para realizar consultas a la REST API de GitHub y evitar restricciones de tasa de peticiones (rate-limiting), es obligatorio suministrar un Personal Access Token (PAT) mediante una variable de entorno.
En sistemas Linux / macOS:
    export GITHUB_TOKEN="tu_github_token_aqui"

En sistemas Windows (CMD / PowerShell):
    set GITHUB_TOKEN="tu_github_token_aqui"



## Uso de la Herramienta CLI

La herramienta expone la interfaz de línea de comandos miner construida sobre Typer.
Sintaxis básica:
    miner scan --organization NOMBRE_ORGANIZACION --output RUTA_SALIDA

Opciones y Parámetros:
Parámetro|Forma Corta|Requerido|Descripción	Por Defecto
--organization|	-o  |	Sí	|Nombre de la organización de GitHub a analizar.
--output      |	-out|	No	|Ruta donde se guardará el reporte consolidado en formato JSON.	results.json
Ejemplo de ejecución:
    miner scan --organization py-pdf --output resultados.json

## Ejecución de Pruebas Automatizadas

El proyecto incluye un conjunto de pruebas unitarias implementadas con pytest para verificar el comportamiento de los modelos Pydantic y el procesamiento de archivos SARIF sin requerir llamadas externas a la red.

Para ejecutar la suite de pruebas:
    pytest