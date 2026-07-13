import json
import subprocess
import tempfile
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("hayabusa")

HAYABUSA_PATH = Path(__file__).resolve().parent / "hayabusa" / "hayabusa.exe"
SEVERITY_LEVELS = ["informational", "low", "medium", "high", "critical"]
SEVERITY_RANK = {level: i for i, level in enumerate(SEVERITY_LEVELS)}
SCAN_TIMEOUT_SECONDS = 600


@mcp.tool()
def scan_evtx(path: str, min_severity: str = "informational") -> dict:
    """Run Hayabusa against an EVTX file and return structured findings.

    Args:
        path: Path to the EVTX file to scan.
        min_severity: Minimum severity level to include (informational, low, medium, high, critical).
    """
    if min_severity not in SEVERITY_RANK:
        return {"error": f"Invalid min_severity '{min_severity}'. Must be one of {SEVERITY_LEVELS}"}

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

    return {"count": len(filtered), "findings": filtered}


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
