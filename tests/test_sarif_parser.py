import json
from miner.sarif_parser import parse_sarif


def test_parse_sarif_valid(tmp_path):
    sarif_content = {
        "runs": [
            {
                "tool": {
                    "driver": {
                        "rules": [
                            {
                                "id": "py/unused-import",
                                "defaultConfiguration": {"level": "warning"},
                            }
                        ]
                    }
                },
                "results": [
                    {
                        "ruleId": "py/unused-import",
                        "message": {"text": "Import no utilizado"},
                        "locations": [
                            {
                                "physicalLocation": {
                                    "artifactLocation": {"uri": "src/utils.py"},
                                    "region": {"startLine": 12},
                                }
                            }
                        ],
                    }
                ],
            }
        ]
    }

    sarif_file = tmp_path / "sample.sarif"
    sarif_file.write_text(json.dumps(sarif_content), encoding="utf-8")

    findings = parse_sarif(sarif_file)

    assert len(findings) == 1
    assert findings[0].rule_id == "py/unused-import"
    assert findings[0].file == "src/utils.py"
    assert findings[0].start_line == 12