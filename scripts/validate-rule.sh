#!/bin/bash
# PostToolUse hook: validates Sigma rules saved under rules/.
# Reads the tool-call JSON from stdin, checks the edited/written file is a
# YAML rule under rules/, then verifies required fields with Python.
# Always exits 2 so Claude sees the result (pass or fail) as feedback.
# No jq dependency: file_path is extracted with a small inline Python
# snippet instead, so this script only requires Python.

if python3 --version >/dev/null 2>&1; then
    PYTHON=python3
else
    PYTHON=python
fi

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | "$PYTHON" -c '
import json, sys
try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)
print(data.get("tool_input", {}).get("file_path", ""))
')

# Not a file-modifying tool call we care about, nothing to check.
if [ -z "$FILE_PATH" ]; then
    exit 0
fi

# Only validate YAML files under rules/.
case "$FILE_PATH" in
    rules/*.yml|rules/*.yaml|*/rules/*.yml|*/rules/*.yaml)
        ;;
    *)
        exit 0
        ;;
esac

if [ ! -f "$FILE_PATH" ]; then
    exit 0
fi

ERRORS=$("$PYTHON" - "$FILE_PATH" <<'PYEOF'
import sys
import yaml

path = sys.argv[1]

try:
    with open(path, "r", encoding="utf-8") as f:
        rule = yaml.safe_load(f)
except Exception as exc:
    print(f"Failed to parse YAML: {exc}")
    sys.exit(1)

if not isinstance(rule, dict):
    print("Top-level YAML content is not a mapping (not a valid Sigma rule)")
    sys.exit(1)

errors = []

if not rule.get("title"):
    errors.append("missing 'title' field")

if not rule.get("description"):
    errors.append("missing 'description' field")

tags = rule.get("tags") or []
if not any(isinstance(tag, str) and tag.startswith("attack.t") for tag in tags):
    errors.append("'tags' does not contain an 'attack.t*' ATT&CK technique entry")

if errors:
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

sys.exit(0)
PYEOF
)
STATUS=$?

if [ $STATUS -ne 0 ]; then
    echo "Sigma rule validation FAILED for $FILE_PATH:" >&2
    echo "$ERRORS" >&2
    exit 2
fi

echo "Sigma rule validation passed for $FILE_PATH" >&2
exit 2
