import os
import shutil
import subprocess
from pathlib import Path
from miner.config import REPOS_DIR
from miner.models import CodeQLAnalysisResult
from miner.sarif_parser import parse_sarif


def run_codeql_analysis(
    repo_name: str, language: str
) -> CodeQLAnalysisResult:
    """Crea la BD de CodeQL, ejecuta el análisis, procesa el SARIF y limpia archivos temporales."""
    repo_path = Path(REPOS_DIR) / repo_name
    db_path = Path("codeql_dbs") / f"{repo_name}_db"
    sarif_output = Path("results_sarif") / f"{repo_name}.sarif"

    db_path.parent.mkdir(parents=True, exist_ok=True)
    sarif_output.parent.mkdir(parents=True, exist_ok=True)

    cmd_create = [
        "codeql",
        "database",
        "create",
        str(db_path),
        f"--language={language}",
        f"--source-root={str(repo_path)}",
        "--overwrite",
    ]

    try:
        subprocess.run(
            cmd_create, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError as e:
        return CodeQLAnalysisResult(
            status="db_creation_failed",
            language=language,
            error_message=e.stderr.decode().strip(),
        )

    cmd_analyze = [
        "codeql",
        "database",
        "analyze",
        str(db_path),
        "--format=sarif-latest",
        f"--output={str(sarif_output)}",
    ]

    try:
        subprocess.run(
            cmd_analyze,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as e:
        # Limpiar BD creada si falla el análisis
        if db_path.exists():
            shutil.rmtree(db_path, ignore_errors=True)
        return CodeQLAnalysisResult(
            status="analysis_failed",
            language=language,
            error_message=e.stderr.decode().strip(),
        )

    findings = parse_sarif(sarif_output)

    if db_path.exists():
        shutil.rmtree(db_path, ignore_errors=True)
    if sarif_output.exists():
        os.remove(sarif_output)

    return CodeQLAnalysisResult(
        status="analyzed", language=language, findings=findings
    )