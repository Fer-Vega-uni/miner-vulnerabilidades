from collections import defaultdict
import os
from miner.config import CODEQL_LANGUAGES, REPOS_DIR


def analizar_repositorio_para_codeql(ruta_repo):
    """Escanea un directorio local buscando archivos compatibles con CodeQL."""
    conteo_extensiones = defaultdict(int)
    coincidencias_lenguajes = defaultdict(int)

    carpetas_ignoradas = {
        "node_modules",
        ".git",
        "venv",
        ".venv",
        "build",
        "dist",
        "vendor",
    }

    for raiz, dirs, archivos in os.walk(ruta_repo):
        dirs[:] = [d for d in dirs if d not in carpetas_ignoradas]

        for archivo in archivos:
            _, ext = os.path.splitext(archivo)
            ext = ext.lower()
            if not ext:
                continue

            conteo_extensiones[ext] += 1

            for lang_key, info in CODEQL_LANGUAGES.items():
                if ext in info["exts"]:
                    coincidencias_lenguajes[lang_key] += 1

    return coincidencias_lenguajes, conteo_extensiones


def ejecutar_analisis():
    if not os.path.exists(REPOS_DIR):
        print(
            f"Error: La carpeta '{REPOS_DIR}' no existe. Clona primero los repositorios."
        )
        return

    repositorios = [
        d
        for d in os.listdir(REPOS_DIR)
        if os.path.isdir(os.path.join(REPOS_DIR, d))
    ]

    if not repositorios:
        print(f"No hay repositorios en '{REPOS_DIR}' para analizar.")
        return

    print(
        f"=== Análisis de Analizabilidad con CodeQL en '{REPOS_DIR}' ===\n"
    )

    for repo in repositorios:
        ruta_repo = os.path.join(REPOS_DIR, repo)
        coincidencias, _ = analizar_repositorio_para_codeql(ruta_repo)

        print(f"📁 Repositorio: {repo}")

        if coincidencias:
            print("  ✅ Lenguajes analizables por CodeQL detectados:")
            for lang_key, cantidad in coincidencias.items():
                nombre_lang = CODEQL_LANGUAGES[lang_key]["nombre"]
                print(
                    f"     - {nombre_lang} ('{lang_key}'): {cantidad} archivo(s)"
                )
        else:
            print("  ⚠️  No se encontraron archivos analizables por CodeQL.")

        print("-" * 50)


if __name__ == "__main__":
    ejecutar_analisis()