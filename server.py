import json
import re
import subprocess
import tempfile
from pathlib import Path

import yaml
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("hayabusa")

HAYABUSA_PATH = Path(__file__).resolve().parent / "hayabusa" / "hayabusa.exe"
RULES_DIR = HAYABUSA_PATH.parent / "rules"
SIGMA_RULES_DIR = Path(__file__).resolve().parent / "rules"
SEVERITY_LEVELS = ["informational", "low", "medium", "high", "critical"]
SEVERITY_RANK = {level: i for i, level in enumerate(SEVERITY_LEVELS)}
OUTPUT_FORMATS = ["summary", "full"]
SUMMARY_FIELDS = ["Timestamp", "RuleTitle", "Level", "Computer", "Channel", "EventID", "RecordID"]
SCAN_TIMEOUT_SECONDS = 600
TECHNIQUE_ID_RE = re.compile(r"^t?(\d{4})(\.\d{3})?$", re.IGNORECASE)

_rules_cache: list[dict] | None = None
_sigma_rules_cache: list[dict] | None = None


@mcp.tool()
def scan_evtx(
    path: str,
    min_severity: str = "informational",
    rule_filter: str = "",
    output_format: str = "summary",
    max_results: int = 0,
) -> dict:
    """Run Hayabusa against an EVTX file and return structured findings.

    Args:
        path: Path to the EVTX file to scan.
        min_severity: Minimum severity level to include (informational, low, medium, high, critical).
        rule_filter: Only include findings whose rule title contains this substring (case-insensitive).
        output_format: "summary" for condensed fields (default), or "full" for all details.
        max_results: Maximum number of findings to return (0 for no limit).
    """
    if min_severity not in SEVERITY_RANK:
        return {"error": f"Invalid min_severity '{min_severity}'. Must be one of {SEVERITY_LEVELS}"}

    if output_format not in OUTPUT_FORMATS:
        return {"error": f"Invalid output_format '{output_format}'. Must be one of {OUTPUT_FORMATS}"}

    if max_results < 0:
        return {"error": f"Invalid max_results '{max_results}'. Must be 0 or a positive integer"}

    evtx_path = Path(path)
    if not evtx_path.is_file():
        return {"error": f"EVTX file not found: {path}"}

    if not HAYABUSA_PATH.is_file():
        return {
            "error": f"Hayabusa binary not found at {HAYABUSA_PATH}. "
            "Run scripts/download_hayabusa.py to install it."
        }

    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = Path(tmp_dir) / "results.jsonl"
        cmd = [
            str(HAYABUSA_PATH),
            "json-timeline",
            "-f", str(evtx_path),
            "-o", str(output_path),
            "-L",  # JSONL-output: one compact JSON object per line
            "-b",  # disable-abbreviations: full severity words, not "med"/"info"
            "-w",  # no-wizard: don't prompt interactively
            "-Q",  # quiet-errors: don't write an error log file
            "-q",  # quiet: suppress the launch banner
            "-K",  # no-color: keep output free of ANSI codes
            "-C",  # clobber: overwrite the output file
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=SCAN_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            return {"error": f"Hayabusa scan timed out after {SCAN_TIMEOUT_SECONDS}s"}
        except OSError as exc:
            return {"error": f"Failed to run Hayabusa: {exc}"}

        if result.returncode != 0:
            return {
                "error": "Hayabusa scan failed",
                "returncode": result.returncode,
                "stderr": result.stderr.strip(),
            }

        lines = (
            output_path.read_text(encoding="utf-8").splitlines()
            if output_path.exists()
            else []
        )

    findings = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            findings.append(json.loads(line))
        except json.JSONDecodeError as exc:
            return {"error": f"Failed to parse Hayabusa output line: {exc}"}

    min_rank = SEVERITY_RANK[min_severity]
    filtered = [
        f for f in findings
        if SEVERITY_RANK.get(str(f.get("Level", "informational")).lower(), 0) >= min_rank
    ]

    if rule_filter:
        needle = rule_filter.lower()
        filtered = [f for f in filtered if needle in str(f.get("RuleTitle", "")).lower()]

    if output_format == "summary":
        filtered = [{k: f.get(k) for k in SUMMARY_FIELDS} for f in filtered]

    total_count = len(filtered)
    if max_results:
        filtered = filtered[:max_results]

    return {"count": total_count, "returned": len(filtered), "findings": filtered}


def _load_rules() -> list[dict]:
    global _rules_cache
    if _rules_cache is not None:
        return _rules_cache

    rules = []
    for rule_path in list(RULES_DIR.rglob("*.yml")) + list(RULES_DIR.rglob("*.yaml")):
        rel_parts = rule_path.relative_to(RULES_DIR).parts
        if ".git" in rel_parts or rel_parts[0] == "config":
            continue
        try:
            with open(rule_path, encoding="utf-8") as f:
                data = yaml.load(f, Loader=yaml.CSafeLoader)
        except yaml.YAMLError:
            continue
        if not isinstance(data, dict) or "title" not in data:
            continue
        rules.append({
            "id": data.get("id", ""),
            "title": data.get("title", ""),
            "level": data.get("level", ""),
            "status": data.get("status", ""),
            "ruletype": data.get("ruletype", ""),
            "category": (data.get("logsource") or {}).get("category", ""),
            "tags": data.get("tags") or [],
            "description": data.get("description") or "",
        })

    _rules_cache = rules
    return rules


@mcp.tool()
def get_hayabusa_rules(keyword: str = "", max_results: int = 100) -> dict:
    """List available Hayabusa detection rules, optionally filtered by keyword.

    Args:
        keyword: Only include rules whose id, title, description, category, or tags contain this substring (case-insensitive).
        max_results: Maximum number of rules to return (0 for no limit).
    """
    if max_results < 0:
        return {"error": f"Invalid max_results '{max_results}'. Must be 0 or a positive integer"}

    if not RULES_DIR.is_dir():
        return {"error": f"Rules directory not found at {RULES_DIR}."}

    rules = _load_rules()

    if keyword:
        needle = keyword.lower()
        rules = [
            r for r in rules
            if needle in r["id"].lower()
            or needle in r["title"].lower()
            or needle in r["description"].lower()
            or needle in r["category"].lower()
            or any(needle in str(tag).lower() for tag in r["tags"])
        ]

    total_count = len(rules)
    if max_results:
        rules = rules[:max_results]

    return {"count": total_count, "returned": len(rules), "rules": rules}


def _load_sigma_rules() -> list[dict]:
    global _sigma_rules_cache
    if _sigma_rules_cache is not None:
        return _sigma_rules_cache

    rules = []
    for rule_path in sorted(SIGMA_RULES_DIR.glob("*.yml")) + sorted(SIGMA_RULES_DIR.glob("*.yaml")):
        try:
            with open(rule_path, encoding="utf-8") as f:
                data = yaml.load(f, Loader=yaml.CSafeLoader)
        except yaml.YAMLError:
            continue
        if not isinstance(data, dict) or "title" not in data:
            continue

        tags = data.get("tags") or []
        techniques = sorted({
            tag.split(".", 1)[1].upper()
            for tag in tags
            if isinstance(tag, str) and tag.lower().startswith("attack.t")
        })

        rules.append({
            "name": rule_path.stem,
            "path": rule_path,
            "id": data.get("id", ""),
            "title": data.get("title", ""),
            "level": data.get("level", ""),
            "status": data.get("status", ""),
            "tags": tags,
            "techniques": techniques,
            "description": (data.get("description") or "").strip(),
        })

    _sigma_rules_cache = rules
    return rules


@mcp.resource(
    "detection://rules",
    name="Detection Rules",
    description="Browse all Sigma detection rules",
    mime_type="application/json",
)
def list_sigma_rules() -> str:
    rules = _load_sigma_rules()
    summary = [
        {k: r[k] for k in ("name", "id", "title", "level", "status", "techniques")}
        for r in rules
    ]
    return json.dumps(summary, indent=2)


@mcp.resource(
    "detection://rules/{rule_name}",
    name="Sigma Rule",
    description="Get a specific Sigma rule's raw YAML content",
    mime_type="text/yaml",
)
def get_sigma_rule(rule_name: str) -> str:
    for r in _load_sigma_rules():
        if r["name"] == rule_name:
            return r["path"].read_text(encoding="utf-8")
    return f"Rule not found: {rule_name}"


@mcp.resource(
    "detection://rules/by-technique/{technique_id}",
    name="Rules By Technique",
    description="List Sigma rules that map to a given ATT&CK technique ID",
    mime_type="application/json",
)
def get_rules_by_technique(technique_id: str) -> str:
    needle = technique_id.upper()
    matches = [
        {k: r[k] for k in ("name", "id", "title", "level", "status", "techniques")}
        for r in _load_sigma_rules()
        if needle in r["techniques"]
    ]
    return json.dumps(matches, indent=2)


RULE_SOURCES = ["custom", "upstream", "combined"]


def _rule_label(rule: dict) -> str:
    return rule.get("name") or rule.get("id") or rule.get("title") or ""


def _rule_techniques(rule: dict) -> list[str]:
    if "techniques" in rule:
        return rule["techniques"]
    return sorted({
        tag.split(".", 1)[1].upper()
        for tag in rule.get("tags") or []
        if isinstance(tag, str) and tag.lower().startswith("attack.t")
    })


@mcp.tool()
def analyze_coverage(technique_or_tactic: str, rule_source: str = "custom") -> dict:
    """Report detection coverage for an ATT&CK technique ID or tactic name.

    Compares a set of "our" rules against the broader Hayabusa/Sigma rule
    corpus (used as the reference universe of known techniques). For a
    technique ID, reports whether "our" rules cover it. For a tactic name,
    builds the set of techniques the corpus has detections for, then reports
    which of those are covered vs. gaps.

    Args:
        technique_or_tactic: An ATT&CK technique ID (e.g. "T1003.001" or
            "T1003"), or a tactic name (e.g. "credential-access",
            "Lateral Movement").
        rule_source: Which rules count as "ours" for the coverage check:
            "custom" (default) - only our own rules in rules/;
            "upstream" - the full bundled Hayabusa/Sigma corpus itself,
                i.e. what coverage looks like if that corpus is your
                detection layer;
            "combined" - custom rules plus the upstream corpus.
    """
    value = technique_or_tactic.strip()
    if not value:
        return {"error": "technique_or_tactic must not be empty"}

    if rule_source not in RULE_SOURCES:
        return {"error": f"Invalid rule_source '{rule_source}'. Must be one of {RULE_SOURCES}"}

    if not RULES_DIR.is_dir():
        return {"error": f"Rules directory not found at {RULES_DIR}."}

    reference_rules = _load_rules()
    if rule_source == "custom":
        our_rules = _load_sigma_rules()
    elif rule_source == "upstream":
        our_rules = reference_rules
    else:
        our_rules = _load_sigma_rules() + reference_rules

    match = TECHNIQUE_ID_RE.match(value)
    if match:
        technique_id = value.upper()
        if not technique_id.startswith("T"):
            technique_id = "T" + technique_id

        our_matches = [r for r in our_rules if technique_id in _rule_techniques(r)]
        needle = f"attack.{technique_id.lower()}"
        ref_matches = [
            r for r in reference_rules
            if any(isinstance(t, str) and t.lower() == needle for t in r["tags"])
        ]

        return {
            "query_type": "technique",
            "technique_id": technique_id,
            "rule_source": rule_source,
            "covered": bool(our_matches),
            "gap": not our_matches and bool(ref_matches),
            "our_rules": [
                {"name": _rule_label(r), "title": r["title"], "level": r["level"]}
                for r in our_matches
            ],
            "reference_rule_count": len(ref_matches),
            "reference_rules_sample": [
                {"title": r["title"], "level": r["level"], "category": r["category"]}
                for r in ref_matches[:10]
            ],
        }

    tactic = value.lower().replace(" ", "-").replace("_", "-")

    universe: dict[str, set[str]] = {}
    for r in reference_rules:
        tags_lower = {t.lower() for t in r["tags"] if isinstance(t, str)}
        if f"attack.{tactic}" not in tags_lower:
            continue
        for tag in r["tags"]:
            if isinstance(tag, str) and tag.lower().startswith("attack.t"):
                universe.setdefault(tag.split(".", 1)[1].upper(), set()).add(r["title"])

    if not universe:
        return {
            "query_type": "tactic",
            "tactic": tactic,
            "error": (
                f"No rules found tagged with tactic '{tactic}'. Check spelling, "
                "e.g. 'credential-access', 'lateral-movement', 'privilege-escalation'."
            ),
        }

    our_technique_index: dict[str, list[dict]] = {}
    for r in our_rules:
        for technique in _rule_techniques(r):
            our_technique_index.setdefault(technique, []).append(r)

    covered, gaps = [], []
    for technique_id, ref_titles in universe.items():
        our_matches = our_technique_index.get(technique_id, [])
        entry = {"technique_id": technique_id, "reference_rule_count": len(ref_titles)}
        if our_matches:
            entry["our_rules"] = [
                {"name": _rule_label(r), "title": r["title"], "level": r["level"]}
                for r in our_matches
            ]
            covered.append(entry)
        else:
            gaps.append(entry)

    covered.sort(key=lambda e: e["technique_id"])
    gaps.sort(key=lambda e: e["reference_rule_count"], reverse=True)

    total = len(universe)
    return {
        "query_type": "tactic",
        "tactic": tactic,
        "rule_source": rule_source,
        "techniques_in_scope": total,
        "covered_count": len(covered),
        "gap_count": len(gaps),
        "coverage_pct": round(100 * len(covered) / total, 1) if total else 0.0,
        "covered": covered,
        "gaps": gaps,
    }


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
