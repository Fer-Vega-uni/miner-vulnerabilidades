import json
from unittest.mock import patch
from miner.models import SbomInfo
from miner.sbom_runner import generate_sbom


def test_generate_sbom_success(tmp_path):
    repo_dir = tmp_path / "sample_repo"
    repo_dir.mkdir()
    out_dir = tmp_path / "sboms"

    # Simular la salida CycloneDX JSON que genera Syft
    mock_cyclonedx = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "components": [
            {"name": "requests", "version": "2.31.0"},
            {"name": "urllib3", "version": "2.0.0"},
        ],
    }

    # Parchear subprocess.run y get_syft_version para no requerir la CLI real durante los tests
    with patch("miner.sbom_runner.get_syft_version", return_value="syft 1.52.0"), \
         patch("subprocess.run") as mock_run:

        # Simular que subprocess.run escribe el archivo JSON esperado
        def side_effect(*args, **kwargs):
            sbom_file = out_dir / f"{repo_dir.name}.cdx.json"
            out_dir.mkdir(parents=True, exist_ok=True)
            sbom_file.write_text(json.dumps(mock_cyclonedx), encoding="utf-8")

        mock_run.side_effect = side_effect

        sbom_info: SbomInfo = generate_sbom(repo_dir, out_dir)

        assert sbom_info.status == "success"
        assert sbom_info.components_count == 2
        assert sbom_info.syft_version == "syft 1.52.0"
        assert sbom_info.error_message is None


def test_generate_sbom_zero_components(tmp_path):
    repo_dir = tmp_path / "empty_repo"
    repo_dir.mkdir()
    out_dir = tmp_path / "sboms"

    mock_cyclonedx = {
        "bomFormat": "CycloneDX",
        "components": [],
    }

    with patch("miner.sbom_runner.get_syft_version", return_value="syft 1.52.0"), \
         patch("subprocess.run") as mock_run:

        def side_effect(*args, **kwargs):
            sbom_file = out_dir / f"{repo_dir.name}.cdx.json"
            out_dir.mkdir(parents=True, exist_ok=True)
            sbom_file.write_text(json.dumps(mock_cyclonedx), encoding="utf-8")

        mock_run.side_effect = side_effect

        sbom_info: SbomInfo = generate_sbom(repo_dir, out_dir)

        # Debe distinguir entre éxito con 0 componentes y una falla
        assert sbom_info.status == "success"
        assert sbom_info.components_count == 0