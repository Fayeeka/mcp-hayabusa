#!/bin/bash
# SessionStart hook: checks that expected CLI prerequisites are installed.
# Prints a warning to stdout for each missing tool -- on SessionStart, exit-0
# stdout is added to Claude's context automatically, whereas stderr on exit 0
# only reaches the debug log. Never blocks the session (always exits 0) --
# this is an informational check only.

MISSING=()

if ! command -v jq >/dev/null 2>&1; then
    MISSING+=("jq")
fi

if ! command -v python3 >/dev/null 2>&1 && ! command -v python >/dev/null 2>&1; then
    MISSING+=("python3")
fi

if [ "${#MISSING[@]}" -gt 0 ]; then
    echo "WARNING: missing prerequisite(s): ${MISSING[*]}"
    echo "Some project scripts may not work correctly until these are installed."
fi

exit 0
