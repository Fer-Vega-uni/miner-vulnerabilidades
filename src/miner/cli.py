import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console

from miner.analizador_codeql import analizar_repositorio_para_codeql
from miner.codeql_runner import run_codeql_analysis
from miner.config import CODEQL_LANGUAGES, REPOS_DIR
from miner.github_client import GitHubClient, GitHubClientError
from miner.models import Finding, MinerReport, RepositoryResult, Summary

app = typer.Typer(
    help="Miner CLI: Automatiza el análisis estático con CodeQL en organizaciones de GitHub.",
    no_args_is_help=True,
)
console = Console()


def clonar_repo(clone_url: str, repo_path: Path) -> bool:
    """Clona un repositorio individual en la ruta especificada."""
    try:
        subprocess.run(
            ["git", "clone", "--quiet", clone_url, str(repo_path)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        return True
    except subprocess.CalledProcessError:
        return False


@app.command(name="scan")
def scan(
    organization: str = typer.Option(
        ...,
        "--organization",
        "-o",
        help="Nombre de la organización de GitHub a analizar.",
    ),
    output: Path = typer.Option(
        Path("results.json"),
        "--output",
        "-out",
        help="Ruta del archivo JSON de salida.",
    ),
):
    """Ejecuta el pipeline completo de minería y análisis estático con CodeQL."""
    console.print(
        f"[bold blue]Iniciando escaneo para la organización:[/bold blue] {organization}"
    )

    try:
        client = GitHubClient()
        console.print("[cyan]Obteniendo lista de repositorios...[/cyan]")
        repos_data = client.fetch_organization_repos(organization)
    except GitHubClientError as e:
        console.print(f"[bold red]Error en la API de GitHub:[/bold red] {e}")
        raise typer.Exit(code=1)

    if not repos_data:
        console.print(
            "[yellow]No se encontraron repositorios en la organización.[/yellow]"
        )
        raise typer.Exit(code=0)

    console.print(
        f"[green]Se encontraron {len(repos_data)} repositorios.[/green]\n"
    )

    resultados_repos: list[RepositoryResult] = []
    base_repos_dir = Path(REPOS_DIR)
    base_repos_dir.mkdir(exist_ok=True)

    for idx, repo_info in enumerate(repos_data, 1):
        name = repo_info["name"]
        clone_url = repo_info["clone_url"]
        html_url = repo_info["html_url"]
        repo_path = base_repos_dir / name

        console.print(
            f"[{idx}/{len(repos_data)}] [bold]Procesando:[bold] {name}..."
        )

        if repo_path.exists():
            shutil.rmtree(repo_path, ignore_errors=True)

        if not clonar_repo(clone_url, repo_path):
            console.print(
                "  └─ [red]Error:[red] No se pudo clonar el repositorio."
            )
            resultados_repos.append(
                RepositoryResult(
                    name=name,
                    url=html_url,
                    status="clone_failed",
                    error_message="Error al clonar el repositorio vía Git CLI.",
                )
            )
            continue

        coincidencias, _ = analizar_repositorio_para_codeql(str(repo_path))

        if not coincidencias:
            console.print(
                "  └─ [yellow]Omitido:[yellow] Lenguajes no soportados por CodeQL."
            )
            resultados_repos.append(
                RepositoryResult(
                    name=name,
                    url=html_url,
                    status="unsupported",
                    languages=[],
                )
            )
            # Limpiar carpeta del repo clonado
            shutil.rmtree(repo_path, ignore_errors=True)
            continue

        lenguaje_principal = max(coincidencias, key=coincidencias.get)
        lenguajes_detectados = list(coincidencias.keys())

        console.print(
            f"  └─ Ejecutando CodeQL para lenguaje: [cyan]{lenguaje_principal}[cyan]..."
        )

        codeql_res = run_codeql_analysis(name, lenguaje_principal)

        if codeql_res.status == "analyzed":
            console.print(
                f"  └─ [green]Éxito:[green] {len(codeql_res.findings)} hallazgo(s) encontrado(s)."
            )
            resultados_repos.append(
                RepositoryResult(
                    name=name,
                    url=html_url,
                    status="analyzed",
                    languages=lenguajes_detectados,
                    findings=codeql_res.findings,
                )
            )
        else:
            console.print(
                f"  └─ [red]Error en CodeQL ({codeql_res.status}):[red] {codeql_res.error_message}"
            )
            resultados_repos.append(
                RepositoryResult(
                    name=name,
                    url=html_url,
                    status=codeql_res.status,
                    languages=lenguajes_detectados,
                    error_message=codeql_res.error_message,
                )
            )

        if repo_path.exists():
            shutil.rmtree(repo_path, ignore_errors=True)

    reporte = MinerReport(
        organization=organization,
        summary=Summary(),
        repositories=resultados_repos,
    )

    reporte.organize_and_finalize()

    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        f.write(reporte.model_dump_json(indent=2))

    console.print(
        "\n[bold green] Análisis completado exitosamente.[/bold green]"
    )
    console.print(f"Reporte guardado en: [bold]{output.resolve()}[/bold]")


@app.callback()
def main():
    """Herramienta de minería de datos y análisis de seguridad con CodeQL."""
    pass


if __name__ == "__main__":
    app()