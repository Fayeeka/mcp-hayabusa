#!/usr/bin/env python3
"""Validate a Sigma rule YAML file against this team's detection engineering standards.

Usage:
    python validate-rule.py path/to/rule.yml

Prints a JSON validation report to stdout. Exit code is 0 if the rule
passes every check, 1 if any check fails, 2 on a usage/parse error.
"""

import json
import re
import sys
from pathlib import Path

import yaml

VALID_LEVELS = {"low", "medium", "high", "critical"}
TECHNIQUE_TAG_RE = re.compile(r"^attack\.t\d{4}(\.\d{3})?$", re.IGNORECASE)
TEST_CASE_COMMENT_RE = re.compile(r"^\s*#.*test case", re.IGNORECASE)


def _error(message: str) -> dict:
    return {"valid": False, "error": message}


def validate(path: Path) -> dict:
    if not path.is_file():
        return _error(f"File not found: {path}")

    raw_text = path.read_text(encoding="utf-8")

    try:
        rule = yaml.safe_load(raw_text)
    except yaml.YAMLError as exc:
        return _error(f"Failed to parse YAML: {exc}")

    if not isinstance(rule, dict):
        return _error("Top-level YAML content is not a mapping (not a valid Sigma rule)")

    checks = {}
    issues = []

    tags = rule.get("tags") or []
    technique_tags = [
        tag for tag in tags
        if isinstance(tag, str) and TECHNIQUE_TAG_RE.match(tag)
    ]
    checks["attack_technique_tag"] = {
        "passed": bool(technique_tags),
        "found": technique_tags,
    }
    if not technique_tags:
        issues.append(
            "No ATT&CK technique tag found. tags: must include an entry matching "
            "'attack.tXXXX' or 'attack.tXXXX.XXX' (e.g. attack.t1003.002)."
        )

    level = rule.get("level")
    level_valid = isinstance(level, str) and level.lower() in VALID_LEVELS
    checks["severity_level"] = {
        "passed": level_valid,
        "found": level,
    }
    if not level_valid:
        issues.append(
            f"level: '{level}' is not valid. Must be one of: {sorted(VALID_LEVELS)}."
        )

    falsepositives = rule.get("falsepositives")
    fp_valid = isinstance(falsepositives, list) and len(falsepositives) > 0
    checks["false_positives_documented"] = {
        "passed": fp_valid,
        "found": falsepositives,
    }
    if not fp_valid:
        issues.append(
            "falsepositives: is missing or empty. Document at least one realistic "
            "false positive condition."
        )

    has_test_case = any(TEST_CASE_COMMENT_RE.match(line) for line in raw_text.splitlines())
    checks["test_case_present"] = {"passed": has_test_case}
    if not has_test_case:
        issues.append(
            "No test case found. Add a '# Test case:' YAML comment with a concrete "
            "trigger example (command line, event field values, etc.)."
        )

    return {
        "valid": len(issues) == 0,
        "file": str(path),
        "title": rule.get("title"),
        "checks": checks,
        "issues": issues,
    }


def main() -> int:
    if len(sys.argv) != 2:
        print(json.dumps(_error("Usage: validate-rule.py <path/to/rule.yml>")))
        return 2

    result = validate(Path(sys.argv[1]))
    print(json.dumps(result, indent=2))

    if "error" in result:
        return 2
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
