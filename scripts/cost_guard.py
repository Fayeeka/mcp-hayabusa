#!/usr/bin/env python3
"""Cost enforcement hook: tracks estimated session spend from the transcript
and enforces the thresholds settings.json's costThreshold field cannot
actually enforce (Claude Code has no native cost-limit setting).

Wired as both a PreToolUse hook (blocks tool calls once HARD_LIMIT is hit)
and a Stop hook (logs running cost every turn, pops a Windows notification
once when WARNING_AT / HARD_LIMIT is first crossed each session).
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

WARNING_AT = 5.00
HARD_LIMIT = 20.00

PROJECT_ROOT = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
AUDIT_LOG = os.path.join(PROJECT_ROOT, "logs", "cost-audit.log")
STATE_DIR = os.path.join(PROJECT_ROOT, "logs", ".cost-state")

# USD per million tokens: (input, output, cache_write_5m, cache_read)
# Cache write for 1h ephemeral blocks is ~2x the 5m rate; approximated below.
PRICING = {
    "opus": (15.00, 75.00, 18.75, 1.50),
    "sonnet": (3.00, 15.00, 3.75, 0.30),
    "haiku": (0.80, 4.00, 1.00, 0.08),
}
DEFAULT_PRICING = PRICING["sonnet"]


def price_for(model):
    model = (model or "").lower()
    for key, prices in PRICING.items():
        if key in model:
            return prices
    return DEFAULT_PRICING


def session_cost(transcript_path):
    total = 0.0
    if not transcript_path or not os.path.isfile(transcript_path):
        return total

    with open(transcript_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("type") != "assistant":
                continue
            message = entry.get("message", {})
            usage = message.get("usage")
            if not usage:
                continue

            in_price, out_price, cache_write_price, cache_read_price = price_for(
                message.get("model")
            )
            total += usage.get("input_tokens", 0) / 1_000_000 * in_price
            total += usage.get("output_tokens", 0) / 1_000_000 * out_price
            total += (
                usage.get("cache_creation_input_tokens", 0)
                / 1_000_000
                * cache_write_price
            )
            total += (
                usage.get("cache_read_input_tokens", 0) / 1_000_000 * cache_read_price
            )

    return total


def append_audit_line(session_id, event, cost):
    os.makedirs(os.path.dirname(AUDIT_LOG), exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    with open(AUDIT_LOG, "a", encoding="utf-8") as f:
        f.write(f"{timestamp} session={session_id} event={event} cost=${cost:.4f}\n")


def marker_path(session_id, name):
    return os.path.join(STATE_DIR, f"{session_id}.{name}")


def already_notified(session_id, name):
    return os.path.isfile(marker_path(session_id, name))


def mark_notified(session_id, name):
    os.makedirs(STATE_DIR, exist_ok=True)
    open(marker_path(session_id, name), "w").close()


def notify_windows(title, text):
    script = (
        "if (Get-Module -ListAvailable -Name BurntToast) { "
        "Import-Module BurntToast; "
        f"New-BurntToastNotification -Text '{title}','{text}' "
        "} else { "
        "Add-Type -AssemblyName System.Windows.Forms,System.Drawing; "
        "$n = New-Object System.Windows.Forms.NotifyIcon; "
        "$n.Icon = [System.Drawing.SystemIcons]::Warning; "
        "$n.Visible = $true; "
        f"$n.BalloonTipTitle = '{title}'; "
        f"$n.BalloonTipText = '{text}'; "
        "$n.ShowBalloonTip(8000); Start-Sleep -Seconds 9; $n.Dispose() "
        "}"
    )
    try:
        subprocess.Popen(
            ["powershell", "-NoProfile", "-Command", script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        pass


def main():
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {}

    event = data.get("hook_event_name", "")
    session_id = data.get("session_id", "unknown")
    cost = session_cost(data.get("transcript_path"))

    if event == "PreToolUse":
        if cost >= HARD_LIMIT:
            print(
                f"Session cost hard limit reached (${cost:.2f} >= "
                f"${HARD_LIMIT:.2f}). Tool call blocked.",
                file=sys.stderr,
            )
            sys.exit(2)
        sys.exit(0)

    if event == "Stop":
        append_audit_line(session_id, event, cost)

        if cost >= HARD_LIMIT and not already_notified(session_id, "hard"):
            mark_notified(session_id, "hard")
            notify_windows(
                "Claude Code - cost limit hit",
                f"Session cost ${cost:.2f} reached the ${HARD_LIMIT:.2f} hard limit. "
                "Further tool use is now blocked.",
            )
        elif cost >= WARNING_AT and not already_notified(session_id, "warning"):
            mark_notified(session_id, "warning")
            notify_windows(
                "Claude Code - cost warning",
                f"Session cost ${cost:.2f} passed the ${WARNING_AT:.2f} warning threshold.",
            )
        sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
