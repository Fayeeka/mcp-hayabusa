#!/bin/bash
# SessionStart hook: checks that expected CLI prerequisites are installed.
# Prints a warning to stderr for each missing tool. Never blocks the
# session (always exits 0) -- this is an informational check only.

MISSING=()

if ! command -v jq >/dev/null 2>&1; then
    MISSING+=("jq")
fi

if ! command -v python3 >/dev/null 2>&1 && ! command -v python >/dev/null 2>&1; then
    MISSING+=("python3")
fi

if [ "${#MISSING[@]}" -gt 0 ]; then
    echo "WARNING: missing prerequisite(s): ${MISSING[*]}" >&2
    echo "Some project scripts may not work correctly until these are installed." >&2
fi

exit 0
