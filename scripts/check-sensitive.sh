#!/bin/bash
# PreToolUse hook: blocks tool calls that target sensitive file paths.
# Reads the tool-call JSON from stdin, extracts file_path, and checks it
# against a set of sensitive-file patterns (.env, *.key, *.pem, secrets/,
# credentials/). Exits 2 (blocking) with a message on stderr if sensitive,
# exits 0 (allow) otherwise.
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

# Not a file-targeting tool call, nothing to check.
if [ -z "$FILE_PATH" ]; then
    exit 0
fi

BASENAME=$(basename -- "$FILE_PATH")

case "$FILE_PATH" in
    *.env|*.env.*|*/secrets/*|secrets/*|*/credentials/*|credentials/*)
        MATCH=1
        ;;
    *)
        MATCH=0
        ;;
esac

case "$BASENAME" in
    .env|.env.*|*.key|*.pem)
        MATCH=1
        ;;
esac

if [ "$MATCH" -eq 1 ]; then
    echo "BLOCKED: '$FILE_PATH' matches a sensitive file pattern (.env, *.key, *.pem, secrets/, credentials/)." >&2
    echo "Refusing to allow this tool call to proceed." >&2
    exit 2
fi

exit 0
