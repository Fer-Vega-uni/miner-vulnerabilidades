import shutil
import subprocess
from pathlib import Path
import typer
from rich.console import Console

from miner.analizador_codeql import analizar_repositorio_para_codeql
from miner.codeql_runner import run_codeql_analysis
from miner.config import REPOS_DIR
from miner.github_client import GitHubClient, GitHubClientError
from miner.models import MinerReport, RepositoryResult, Summary
from miner.sbom_runner import generate_sbom

app = typer.Typer(
    help="Miner CLI: Automatiza análisis CodeQL y generación de SBOMs con Syft.",
    no_args_is_help=True,
)
console = Console()


def get_commit_hash(repo_path: Path) -> str:
    """Obtiene el hash del commit actual del repositorio clonado."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except subprocess.CalledProcessError:
        return "unknown"


@app.command(name="scan")
def scan(
    organization: str = typer.Option(
        ..., "--organization", "-o", help="Nombre de la organización en GitHub."
    ),
    output: Path = typer.Option(
        Path("results.json"), "--output", "-out", help="Ruta del JSON general."
    ),
    sbom_dir: Path = typer.Option(
        Path("sboms"), "--sbom-dir", help="Directorio donde guardar los SBOMs."
    ),
    keep_repos: bool = typer.Option(
        False, "--keep-repos", help="Conserva los repositorios clonados localmente."
    ),
):
    """Ejecuta el pipeline de clonación, análisis CodeQL y generación de SBOMs."""
    try:
        client = GitHubClient()
        repos_data = client.fetch_organization_repos(organization)
    except GitHubClientError as e:
        console.print(f"[bold red]Error en API de GitHub:[/bold red] {e}")
        raise typer.Exit(code=1)

    resultados_repos: list[RepositoryResult] = []
    base_repos_dir = Path(REPOS_DIR)
    base_repos_dir.mkdir(exist_ok=True)

    for idx, repo_info in enumerate(repos_data, 1):
        name = repo_info["name"]
        full_name = repo_info.get("full_name", f"{organization}/{name}")
        clone_url = repo_info["clone_url"]
        html_url = repo_info["html_url"]
        repo_path = base_repos_dir / name

        console.print(f"[{idx}/{len(repos_data)}] Procesando {full_name}...")

        # Clonar repo si no se reutiliza
        if not repo_path.exists():
            try:
                subprocess.run(
                    ["git", "clone", "--quiet", clone_url, str(repo_path)],
                    check=True,
                )
            except subprocess.CalledProcessError:
                resultados_repos.append(
                    RepositoryResult(
                        name=name,
                        full_name=full_name,
                        url=html_url,
                        status="clone_failed",
                        error_message="No se pudo clonar el repositorio.",
                    )
                )
                continue

        commit_hash = get_commit_hash(repo_path)

        # 1. Generar SBOM
        sbom_info = generate_sbom(repo_path, sbom_dir)

        # 2. Análisis CodeQL
        coincidencias, _ = analizar_repositorio_para_codeql(str(repo_path))
        if not coincidencias:
            resultados_repos.append(
                RepositoryResult(
                    name=name,
                    full_name=full_name,
                    url=html_url,
                    commit_hash=commit_hash,
                    status="unsupported",
                    sbom=sbom_info,
                )
            )
        else:
            lenguaje_principal = max(coincidencias, key=coincidencias.get)
            codeql_res = run_codeql_analysis(name, lenguaje_principal)
            
            resultados_repos.append(
                RepositoryResult(
                    name=name,
                    full_name=full_name,
                    url=html_url,
                    commit_hash=commit_hash,
                    status=codeql_res.status,
                    languages=list(coincidencias.keys()),
                    findings=codeql_res.findings,
                    error_message=codeql_res.error_message,
                    sbom=sbom_info,
                )
            )

        # Limpiar repositorio si no se especificó la opción de conservarlo
        if not keep_repos and repo_path.exists():
            shutil.rmtree(repo_path, ignore_errors=True)

    # Consolidar informe
    reporte = MinerReport(
        organization=organization,
        summary=Summary(),
        repositories=resultados_repos,
    )
    reporte.organize_and_finalize()

    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        f.write(reporte.model_dump_json(indent=2))

    console.print(f"[bold green]Proceso finalizado. Reporte:[/bold green] {output.resolve()}")


@app.command(name="sbom-only")
def sbom_only(
    organization: str = typer.Option(..., "--organization", "-o"),
    output: Path = typer.Option(Path("results.json"), "--output", "-out"),
    sbom_dir: Path = typer.Option(Path("sboms"), "--sbom-dir"),
):
    """Genera SBOMs reutilizando repositorios ya clonados localmente sin ejecutar CodeQL."""
    base_repos_dir = Path(REPOS_DIR)
    if not base_repos_dir.exists():
        console.print("[red]No se encontró el directorio de repositorios clonados.[/red]")
        raise typer.Exit(code=1)

    resultados_repos: list[RepositoryResult] = []

    for repo_path in base_repos_dir.iterdir():
        if repo_path.is_dir() and (repo_path / ".git").exists():
            name = repo_path.name
            full_name = f"{organization}/{name}"
            commit_hash = get_commit_hash(repo_path)
            
            console.print(f"Generando SBOM para {name}...")
            sbom_info = generate_sbom(repo_path, sbom_dir)

            resultados_repos.append(
                RepositoryResult(
                    name=name,
                    full_name=full_name,
                    url=f"https://github.com/{full_name}",
                    commit_hash=commit_hash,
                    status="analyzed",
                    sbom=sbom_info,
                )
            )

    reporte = MinerReport(
        organization=organization,
        summary=Summary(),
        repositories=resultados_repos,
    )
    reporte.organize_and_finalize()

    with open(output, "w", encoding="utf-8") as f:
        f.write(reporte.model_dump_json(indent=2))


@app.callback()
def main():
    pass


if __name__ == "__main__":
    app()