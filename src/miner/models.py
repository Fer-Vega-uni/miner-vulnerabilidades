from typing import Optional
from pydantic import BaseModel, Field


class CodeQLAnalysisResult(BaseModel):
    status: (
        str  # "analyzed", "db_creation_failed", "analysis_failed", "unsupported"
    )
    language: Optional[str] = None
    findings: list["Finding"] = Field(default_factory=list)
    error_message: Optional[str] = None


class Finding(BaseModel):
    rule_id: str
    severity: str
    message: str
    file: str
    start_line: int


class RepositoryResult(BaseModel):
    name: str
    url: str
    status: (
        str  # Estados: "analyzed", "clone_failed", "unsupported", "db_creation_failed", "analysis_failed"
    )
    languages: list[str] = Field(default_factory=list)
    error_message: Optional[str] = None
    findings: list[Finding] = Field(default_factory=list)

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


class MinerReport(BaseModel):
    organization: str
    summary: Summary
    repositories: list[RepositoryResult] = Field(default_factory=list)

    def organize_and_finalize(self) -> None:
        """
        - Ordena alfabéticamente los repositorios por nombre[cite: 1].
        - Ordena los hallazgos dentro de cada repositorio[cite: 1].
        - Recalcula las métricas del resumen global.
        """
        self.repositories.sort(key=lambda r: r.name.lower())

        total_analyzed = 0
        total_failed = 0
        total_unsupported = 0
        total_findings = 0

        for repo in self.repositories:
            repo.sort_findings()

            if repo.status == "analyzed":
                total_analyzed += 1
            elif repo.status == "unsupported":
                total_unsupported += 1
            else:
                total_failed += 1

            total_findings += len(repo.findings)

        self.summary = Summary(
            repositories=len(self.repositories),
            analyzed=total_analyzed,
            failed=total_failed,
            unsupported=total_unsupported,
            findings=total_findings,
        )