import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from miner.models import SbomInfo


def get_syft_version() -> Optional[str]:
    """Obtiene la versión instalada de Syft."""
    try:
        res = subprocess.run(
            ["syft", "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def generate_sbom(repo_path: Path, output_dir: Path) -> SbomInfo:
    """Ejecuta Syft en el repositorio especificado y exporta en formato CycloneDX JSON."""
    output_dir.mkdir(parents=True, exist_ok=True)
    sbom_file = output_dir / f"{repo_path.name}.cdx.json"
    syft_ver = get_syft_version()

    if not syft_ver:
        return SbomInfo(
            status="failed",
            error_message="Syft no se encuentra instalado o no está en el PATH.",
        )

    cmd = [
        "syft",
        str(repo_path),
        "-o",
        f"cyclonedx-json={sbom_file}",
    ]

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        
        # Conteo de componentes desde el archivo CycloneDX JSON
        components_count = 0
        if sbom_file.exists():
            with open(sbom_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                components_count = len(data.get("components", []))

        return SbomInfo(
            syft_version=syft_ver,
            status="success",
            generated_at=datetime.now(timezone.utc).isoformat(),
            components_count=components_count,
            sbom_path=str(sbom_file.resolve()),
        )
    except subprocess.CalledProcessError as e:
        return SbomInfo(
            syft_version=syft_ver,
            status="failed",
            error_message=e.stderr.decode("utf-8") if e.stderr else "Error desconocido al ejecutar Syft",
        )