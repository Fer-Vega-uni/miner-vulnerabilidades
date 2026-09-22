# CodeQL & SBOM Miner

Herramienta de minería de datos, análisis estático de código e inventario de software (SBOM) diseñada para automatizar la detección de vulnerabilidades y la generación de componentes en proyectos alojados en GitHub. El sistema consulta la API de GitHub, clona los repositorios de una organización, analiza su código fuente mediante la CLI de CodeQL, genera un SBOM independiente por repositorio en formato CycloneDX JSON usando Syft y consolida los resultados en un reporte estandarizado en formato JSON.
## Requisitos del Sistema

Para el correcto funcionamiento de la herramienta se requiere disponer de las siguientes herramientas instaladas y configuradas en el entorno:

    Python: Versión 3.10 o superior.

    Git CLI: Configurado y accesible globalmente desde la línea de comandos.

    CodeQL CLI: Instalado y disponible en la variable de entorno PATH del sistema.

    Syft CLI: Instalado y disponible en la variable de entorno PATH del sistema.

### Instalación de Syft

Syft es requerido para la generación automática de los inventarios de software (SBOM).

En Linux / macOS:
curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin

En Windows (PowerShell):
curl.exe -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | powershell -Command -

Para verificar la instalación correcta:
syft --version
## Estructura del Proyecto

El código está organizado como un paquete modular en Python con separación de responsabilidades

.
├── pyproject.toml
├── README.md
├── .env.example
├── .gitignore
├── src/
│   └── miner/
│       ├── init.py
│       ├── analizador_codeql.py
│       ├── cli.py
│       ├── codeql_runner.py
│       ├── config.py
│       ├── github_client.py
│       ├── models.py
│       ├── sarif_parser.py
│       └── sbom_runner.py
└── tests/
├── test_models.py
└── test_sarif_parser.py
## Instalación

    Clonar el repositorio localmente:
    git clone https://github.com/Fer-Vega-uni/miner-vulnerabilidades.git
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
$env:GITHUB_TOKEN="tu_github_token_aqui"


## Uso de la Herramienta CLI

La herramienta expone la interfaz de línea de comandos miner construida sobre Typer, la cual soporta dos modos principales de ejecución:
1. Comando scan (Escaneo Completo: CodeQL + SBOM)

Ejecuta la clonación de repositorios, análisis CodeQL y la generación de SBOMs con Syft.

Sintaxis:
miner scan --organization NOMBRE_ORGANIZACION [OPCIONES]

## Opciones y Parámetros:
    -o, --organization   (Requerido) Nombre de la organización de GitHub a analizar.

    -out, --output       (Opcional) Ruta del reporte general consolidado JSON. Por defecto: results.json

    --sbom-dir           (Opcional) Directorio donde se guardarán los archivos CycloneDX JSON. Por defecto: sboms

    --keep-repos         (Opcional) Flag para conservar los repositorios clonados localmente tras el análisis.

### Ejemplo de ejecución completa conservando repositorios:
miner scan --organization py-pdf --output resultados.json --sbom-dir ./sboms --keep-repos
2. Comando sbom-only (Generación exclusiva de SBOMs)

Genera o actualiza los inventarios SBOM reutilizando los repositorios que ya fueron clonados localmente en la carpeta de trabajo, omitiendo la repetición del análisis de vulnerabilidades con CodeQL.

Sintaxis:
miner sbom-only --organization NOMBRE_ORGANIZACION [OPCIONES]

### Ejemplo de ejecución:
miner sbom-only --organization py-pdf --output resultados_sbom.json --sbom-dir ./sboms
Explicación de los Archivos de Salida

    Archivo de Salida General (JSON Consolidado, ej. results.json):
    Contiene el resumen global de la organización, datos de cada repositorio (nombre completo, commit hash analizado, URL, estado del análisis CodeQL, hallazgos) y un bloque sbom por cada repositorio que detalla:

        syft_version: Versión de Syft utilizada.

        status: Estado de la ejecución ("success" o "failed").

        generated_at: Fecha y hora exacta de la generación en formato ISO.

        components_count: Cantidad total de componentes/dependencias identificados.

        sbom_path: Ruta absoluta al archivo CycloneDX generado.

        error_message: Detalle de error en caso de fallo en la ejecución.

    Archivos SBOM independientes (ej. sboms/<nombre-repo>.cdx.json):
    Archivos independientes en formato estándar CycloneDX JSON v1.5/v1.7. Se exportan minificados por eficiencia de almacenamiento, conteniendo el inventario completo de dependencias, licencias, identificadores (PURL, UUID) y herramientas utilizadas.

## Análisis Comparativo y Verificación de Dependencias (Syft vs. Manifiestos)

Al verificar los SBOMs generados frente a los archivos de declaración de dependencias de los repositorios (como pyproject.toml o requirements.txt en el caso de pypdf), se constataron las siguientes observaciones:

    Dependencias Abstractas vs. Artefactos Concretos:
    Archivos como pyproject.toml declaran especificaciones de rangos (Pillow>=8.0.0, typing_extensions >= 4.0) pero no fijan versiones exactas al no contar con un archivo de bloqueo (lockfile) en la raíz del proyecto. Syft distingue esta ausencia y no inventa versiones sin metadatos de entorno o archivos .dist-info.

    Inventario de CI/CD y Cadena de Suministro:
    Syft inspecciona la totalidad del árbol de archivos del repositorio, identificando como componentes de software las GitHub Actions configuradas dentro de .github/workflows/ (ej. actions/checkout, codecov/codecov-action). Esto demuestra que el SBOM abarca la cadena de suministro global del proyecto y no únicamente las librerías del lenguaje principal.

    Distinción entre Ejecución Fallida y Sin Componentes:
    El sistema distingue correctamente entre un error de ejecución de la herramienta (registrando el estado "failed" junto a error_message) y una ejecución exitosa en repositorios sin dependencias ejecutables directas (registrando el estado "success" con components_count: 0), como ocurre en el caso de repositorios documentalistas como awesome-pdf.

## Ejecución de Pruebas Automatizadas

El proyecto incluye un conjunto de pruebas unitarias implementadas con pytest para verificar el comportamiento de los modelos Pydantic y el procesamiento de archivos SARIF.
Para ejecutar la suite de pruebas:
pytest