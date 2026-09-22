from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CodeQLAnalysisResult(BaseModel):
    status: str  # "analyzed", "db_creation_failed", "analysis_failed", "unsupported"
    language: Optional[str] = None
    findings: list["Finding"] = Field(default_factory=list)
    error_message: Optional[str] = None


class Finding(BaseModel):
    rule_id: str
    severity: str
    message: str
    file: str
    start_line: int


class SbomInfo(BaseModel):
    syft_version: Optional[str] = None
    status: str  # "success", "failed", "skipped"
    generated_at: Optional[str] = None
    components_count: int = 0
    sbom_path: Optional[str] = None
    error_message: Optional[str] = None


class RepositoryResult(BaseModel):
    name: str
    full_name: str = ""
    url: str
    commit_hash: Optional[str] = None
    status: str  # Estados: "analyzed", "clone_failed", "unsupported", "db_creation_failed", "analysis_failed"
    languages: list[str] = Field(default_factory=list)
    error_message: Optional[str] = None
    findings: list[Finding] = Field(default_factory=list)
    sbom: Optional[SbomInfo] = None

    def sort_findings(self) -> None:
        """Ordena los hallazgos de forma reproducible por archivo, línea y regla[cite: 1]."""
        self.findings.sort(
            key=lambda f: (f.file, f.start_line, f.rule_id, f.message)
        )


class Summary(BaseModel):
    repositories: int = 0
    analyzed: int = 0
    failed: int = 0
    unsupported: int = 0
    findings: int = 0
    sboms_generated: int = 0
    total_components: int = 0


class MinerReport(BaseModel):
    organization: str
    summary: Summary
    repositories: list[RepositoryResult] = Field(default_factory=list)

    def organize_and_finalize(self) -> None:
        """
        - Ordena alfabéticamente los repositorios por nombre[cite: 1].
        - Ordena los hallazgos dentro de cada repositorio[cite: 1].
        - Recalcula las métricas del resumen global (CodeQL + SBOMs).
        """
        self.repositories.sort(key=lambda r: r.name.lower())

        total_analyzed = 0
        total_failed = 0
        total_unsupported = 0
        total_findings = 0
        total_sboms = 0
        total_components = 0

        for repo in self.repositories:
            repo.sort_findings()

            # Asegurar que full_name tenga un valor si viene vacío
            if not repo.full_name:
                repo.full_name = f"{self.organization}/{repo.name}"

            if repo.status == "analyzed":
                total_analyzed += 1
            elif repo.status == "unsupported":
                total_unsupported += 1
            else:
                total_failed += 1

            total_findings += len(repo.findings)

            if repo.sbom:
                if repo.sbom.status == "success":
                    total_sboms += 1
                total_components += repo.sbom.components_count

        self.summary = Summary(
            repositories=len(self.repositories),
            analyzed=total_analyzed,
            failed=total_failed,
            unsupported=total_unsupported,
            findings=total_findings,
            sboms_generated=total_sboms,
            total_components=total_components,
        )