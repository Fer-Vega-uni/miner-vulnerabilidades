import json
from pathlib import Path
from miner.models import Finding


def parse_sarif(sarif_path: Path) -> list[Finding]:
    """Lee un archivo SARIF y extrae los hallazgos mapeados a Pydantic."""
    if not sarif_path.exists():
        return []

    with open(sarif_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    findings: list[Finding] = []

    for run in data.get("runs", []):
        rules = {}
        driver = run.get("tool", {}).get("driver", {})
        for rule in driver.get("rules", []):
            rules[rule["id"]] = rule.get("defaultConfiguration", {}).get(
                "level", "warning"
            )

        for result in run.get("results", []):
            rule_id = result.get("ruleId", "unknown")
            message = result.get("message", {}).get("text", "")

            severity = result.get("level", rules.get(rule_id, "warning"))

            locations = result.get("locations", [])
            file_path = "unknown"
            start_line = 0

            if locations:
                physical_loc = locations[0].get("physicalLocation", {})
                file_path = physical_loc.get("artifactLocation", {}).get(
                    "uri", "unknown"
                )
                start_line = physical_loc.get("region", {}).get("startLine", 0)

            findings.append(
                Finding(
                    rule_id=rule_id,
                    severity=severity,
                    message=message,
                    file=file_path,
                    start_line=start_line,
                )
            )

    return findings