from miner.models import Finding, MinerReport, RepositoryResult, Summary


def test_finding_creation():
    f = Finding(
        rule_id="py/sql-injection",
        severity="error",
        message="Posible inyección SQL",
        file="app/main.py",
        start_line=10,
    )
    assert f.rule_id == "py/sql-injection"
    assert f.start_line == 10


def test_report_sorting_and_summary():
    repo_b = RepositoryResult(
        name="repo-b",
        url="https://github.com/org/repo-b",
        status="analyzed",
        findings=[
            Finding(
                rule_id="rule2",
                severity="low",
                message="m2",
                file="z.py",
                start_line=20,
            ),
            Finding(
                rule_id="rule1",
                severity="high",
                message="m1",
                file="a.py",
                start_line=5,
            ),
        ],
    )

    repo_a = RepositoryResult(
        name="repo-a",
        url="https://github.com/org/repo-a",
        status="unsupported",
    )

    report = MinerReport(
        organization="test-org",
        summary=Summary(),
        repositories=[repo_b, repo_a],
    )

    report.organize_and_finalize()

    # Comprobar orden alfabético de repositorios
    assert report.repositories[0].name == "repo-a"
    assert report.repositories[1].name == "repo-b"

    # Comprobar ordenamiento de hallazgos dentro de repo-b (a.py antes que z.py)
    assert report.repositories[1].findings[0].file == "a.py"

    # Comprobar cálculo del resumen
    assert report.summary.repositories == 2
    assert report.summary.analyzed == 1
    assert report.summary.unsupported == 1
    assert report.summary.findings == 2