#!/usr/bin/env python3
"""PostToolUse hook: logs Edit/Write file paths to hook-test.log for verifying hooks fire."""
import json
import sys
from datetime import datetime, timezone

LOG_PATH = "hook-test.log"


def main():
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {}

    tool_name = data.get("tool_name", "unknown")
    file_path = data.get("tool_input", {}).get("file_path", "unknown")
    timestamp = datetime.now(timezone.utc).isoformat()

    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"{timestamp} {tool_name} {file_path}\n")


if __name__ == "__main__":
    main()
