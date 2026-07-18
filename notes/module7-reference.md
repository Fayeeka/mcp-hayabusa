# Module 7 Reference: Hooks - Automation Triggers

## Claude Ecosystem Coverage

| Component | Feature | How We'll Use It |
|---|---|---|
| Hooks | Core concept | Event-driven automation |
| PreToolUse | Hook event | Validate before actions |
| PostToolUse | Hook event | Format/notify after actions |
| SessionStart | Hook event | Set up environment |
| settings.json | Configuration | Defining hooks |
| deniedPaths | Security | Protecting sensitive files |
| costThreshold | Budget control | Spending alerts and limits |

## Overview

Previous modules built tools (MCP), knowledge (resources), methodology
(skills), and workflows (commands) — but all rely on Claude or you
remembering to do something.

Hooks are deterministic automation — they always run based on events,
not decisions. When Claude edits a file, the hook runs. When a session
starts, the hook runs. No hoping Claude remembers, no manual triggers.

## The Problem

Wanting: every rule validated before saving, automatic formatting after
edits, a notification when a long task finishes, sensitive files
protected from accidental access. Without hooks, all of these rely on
remembering — Claude might forget to validate, you might forget to run
formatters, you might miss a completion, accidents happen with sensitive
files.

With hooks: validation runs automatically on every write, formatting
applies automatically, notifications fire automatically, sensitive paths
are blocked before Claude can access them. Hooks are great for
guardrails, sanity checks, and multi-agent "double verification" workflows.

## 7.1 How Hooks Work

### Event-Driven, Not Decision-Driven

| Event | When It Fires |
|---|---|
| PreToolUse | Before Claude uses any tool |
| PostToolUse | After Claude uses any tool |
| SessionStart | When a Claude Code session begins |
| Stop | When Claude finishes responding |
| Notification | When Claude needs user input |

### How Hooks Receive Data

Hooks receive JSON on stdin. For tool-related hooks:

```json
{
  "tool_name": "Write",
  "tool_input": {
    "file_path": "rules/test-rule.yml",
    "content": "..."
  }
}
```

Hook scripts parse this, typically with jq:
```bash
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
```

### Hook Exit Codes

| Exit Code | Behavior |
|---|---|
| 0 | Success. stdout parsed for JSON (if any); mostly shown only in verbose mode |
| 2 | Blocking error. stderr fed back as feedback (effect depends on event) |
| 1 or other | Non-blocking error. stderr shown in verbose mode only |

Exit 2 behavior by event:
- **PreToolUse**: Blocks the tool call, stderr sent to Claude
- **PostToolUse**: Shows stderr to Claude as feedback (tool already ran, can't undo)
- **SessionStart**: Shows stderr to user only (not Claude)
- **Stop**: Can block Claude from stopping (with JSON decision: "block")

**Critical**: for PreToolUse/PostToolUse, exit 2 sends stderr to Claude.
For other events, exit 2 may only show to the user.

### Hook Types

| Type | What It Does | Use Case |
|---|---|---|
| command | Runs a shell command | Linting, formatting, notifications |
| prompt | Single-turn LLM evaluation | Quick validation checks |
| agent | Multi-turn LLM with tools | Complex verification workflows |

Most hooks are command type. prompt/agent hooks can be powerful for
cybersecurity workflows needing multiple verification steps.

### The Matcher

```json
{
  "matcher": "Write|Edit",
  "hooks": [...]
}
```

Common matchers: `Write|Edit|MultiEdit` (all file mods), `Bash` (shell
only), `Read` (reads only), `.*` or `""` (match all tools).

## 7.2 Setting Up Hooks

Configured in `.claude/settings.json` (project) or
`~/.claude/settings.json` (user).

### The Easy Way: /hooks Command

`/hooks` walks through selecting an event, adding a matcher, specifying
a command — edits settings.json for you.

### Basic Hook Structure

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "./scripts/log-edit.sh"
          }
        ]
      }
    ]
  }
}
```

```bash
#!/bin/bash
# scripts/log-edit.sh - for testing that hooks work
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
echo "File modified: $FILE_PATH" >> hook-test.log
```

Note: hook syntax may drift over time — use `/doctor` if it fails, and
ask Claude to help troubleshoot.

### Testing

Restart Claude Code (`/exit`, `claude`), then trigger a file write and
check for the echo/log output. If terminal doesn't show echo directly,
redirect to a log file instead.

## 7.3 Building a Validation Hook

### The Goal

When Claude saves a YAML file in `rules/`, automatically check required
fields (title, description, ATT&CK tags), validate YAML syntax, report
issues.

### The Validator Script

`scripts/validate-rule.sh`:
1. Reads JSON from stdin, extracts file_path via jq
2. Checks if it's a YAML file in rules/
3. Uses Python to verify: title exists, description exists, tags
   contains at least one attack.t entry
4. Exits code 2 with errors to stderr if invalid
5. Exits code 2 with success message to stderr if valid (exit 2 used so
   Claude sees the feedback either way)

### Add the Hook

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "./scripts/validate-rule.sh"
          }
        ]
      }
    ]
  }
}
```

PostToolUse hooks can't undo the action (already happened), but exit 2
still provides feedback to Claude for future actions.

## 7.4 PreToolUse: Blocking Dangerous Actions

PostToolUse runs after; PreToolUse runs before and can block entirely.

### Protecting Sensitive Files

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "./scripts/check-sensitive.sh"
          }
        ]
      }
    ]
  }
}
```

`scripts/check-sensitive.sh`: reads JSON from stdin, extracts file_path,
checks against sensitive patterns (.env, *.key, *.pem, secrets/,
credentials/), exits 2 (blocking) if sensitive with a block message to
stderr, exits 0 (allow) otherwise.

**Exit code meaning for PreToolUse**: exit 2 blocks the action AND shows
feedback; exit 0 allows it.

### Using deniedPaths (Built-in Alternative)

```json
{
  "permissions": {
    "deniedPaths": [
      ".env*",
      "*.key",
      "*.pem",
      "secrets/",
      "credentials/"
    ]
  }
}
```

Simpler than a hook for basic path blocking. Use hooks when custom logic
is needed (e.g. some secrets/.env files should be readable, others not).

## 7.5 SessionStart: Environment Setup

Runs once when Claude Code starts. Use for: loading environment
variables, checking prerequisites, displaying project status.

Example — check prerequisites (jq, python3 installed):

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "./scripts/check-prereqs.sh"
          }
        ]
      }
    ]
  }
}
```

**Note**: unlike PreToolUse/PostToolUse, SessionStart hooks with exit 2
show stderr to the user, not to Claude. Use exit 0 and write warnings to
stderr for things the user should see.

**Important**: jq is required for hooks generally, since they receive
JSON on stdin.

## 7.6 Notifications

Useful for long-running tasks.

**macOS**: `osascript -e 'display notification "Task complete!" with title "Claude Code"'`
**Linux**: `notify-send "Claude Code" "Task complete!"`
**Windows (PowerShell)**:
```powershell
[System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms')
[System.Windows.Forms.MessageBox]::Show('Task complete!', 'Claude Code')
```

Add a Stop hook to fire on response completion — useful when working in
another window.

## 7.7 Cost Controls

Not technically hooks, but configured in the same settings.json:

```json
{
  "costThreshold": {
    "warningAt": 5.00,
    "hardLimit": 20.00
  }
}
```

`warningAt`: warns when session cost exceeds this.
`hardLimit`: stops when session cost exceeds this.

Can combine with a Stop hook that logs costs/timestamps to an audit
trail file.

## 7.8 Putting It Together

Complete example settings.json combining everything:

```json
{
  "hooks": {
    "SessionStart": [
      { "hooks": [{ "type": "command", "command": "./scripts/check-prereqs.sh" }] }
    ],
    "PreToolUse": [
      {
        "matcher": ".*",
        "hooks": [{ "type": "command", "command": "./scripts/check-sensitive.sh" }]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [{ "type": "command", "command": "./scripts/validate-rule.sh" }]
      }
    ],
    "Stop": [
      { "hooks": [{ "type": "command", "command": "./scripts/notify-complete.sh" }] }
    ]
  },
  "permissions": {
    "deniedPaths": [".env*", "*.key", "*.pem", "secrets/"],
    "allowedCommands": ["npm test", "python -m pytest"]
  },
  "costThreshold": {
    "warningAt": 5.00,
    "hardLimit": 20.00
  }
}
```

Scripts use exit 2 to show stderr feedback directly to Claude — no log
file redirection needed for that purpose.

Can reference `$CLAUDE_PROJECT_DIR` in paths:
`"command": "$CLAUDE_PROJECT_DIR/scripts/notify-complete.sh"`

This combination gives: prerequisites check on start, sensitive file
protection, auto-validation of detection rules, completion
notifications, and cost controls.

## Session Notes: A Real Gap in PostToolUse Feedback

While testing the validation hook (7.3), discovered a genuine
discrepancy from the course's documented behavior.

**What the course describes:** PostToolUse hooks exiting with code 2
should feed stderr back to Claude automatically as context — meaning
Claude should naturally mention validation failures in its next response,
without being asked.

**What actually happened:** Created rules/test-rule.yml (deliberately
incomplete — title only). hook-test.log confirmed the hook fired.
validate-rule.sh correctly detected and reported the missing description
and missing ATT&CK tag via stderr with exit code 2. However, Claude's
next conversational response made no mention of any validation failure
— the errors only surfaced when explicitly asked to check the log and
re-run the script manually.

**Claude's own honest account (asked directly):** confirmed it did not
see the stderr feedback automatically in its context. Uncertain whether
the feedback path isn't surfacing for this setup, or fired but wasn't
narrated. Either way, exit-2 output should not be assumed to reach
Claude automatically without verification.

**Practical implication:** the "no manual triggers, no hoping Claude
remembers" promise of hooks (this module's core premise) doesn't fully
hold in practice on this setup. A PostToolUse validation hook exists and
runs correctly, but its findings aren't reliably surfaced to Claude
without a human explicitly checking. This may be:
- A platform-specific bug or quirk (Windows / this Claude Code version)
- A gap between documented and actual hook feedback behavior
- Something that requires additional configuration not covered in the
  course material

**Mitigation used:** Claude saved a session memory to proactively
re-check validate-rule.sh output after future rule edits, rather than
assuming silence means success — but this is a workaround, not a fix for
the underlying automation gap. The irony is intentional to note: hooks
exist specifically to avoid relying on Claude remembering to do
something, yet the fallback here is Claude remembering to check.

**Takeaway for real-world use:** don't fully trust that hook automation
is silently working as documented — periodically verify hook output
directly (log files, manual script re-runs) rather than assuming no
news is good news.

## Follow-up: Debug Log Investigation

To dig further, ran a nested, non-interactive Claude Code session with
debug logging enabled (`claude --debug-file /tmp/claude-debug.log -p
"..."`) and recreated the invalid-rule write. Repeated this a second
time with the `hooks` debug category explicitly selected (`-d hooks
--debug-file ...`) to rule out a filtering gap. Both runs confirmed the
file write and the PostToolUse hooks firing (matching the earlier
hook-test.log evidence).

**Finding: the numeric hook exit code is not recorded anywhere in
`--debug-file` output**, in either run. The only trace of the hooks
executing is two identical lines immediately after `tool_dispatch_end
tool=Write`:

```
[DEBUG] Hook output does not start with {, treating as plain text
[DEBUG] Hook output does not start with {, treating as plain text
```

One line per configured PostToolUse hook (log-edit.py,
validate-rule.sh) — confirming both ran — but no `exitCode=`,
`PostToolUse`, or `stderr` field logged alongside either line.

**False alarm ruled out:** the log also contains `Registered 0 hooks
from 0 plugins` and `Hooks: Found 0 total hooks in registry`, which
looks like the project hooks never loaded. That registry turned out to
refer to *plugin-supplied* hooks only — a separate subsystem from
`settings.json` hooks. The log separately confirms
`.claude/settings.json` is being watched, and the two "plain text"
lines are direct evidence the project-level hooks did execute.

**Interesting side effect:** in the second nested session, Claude's
final response proactively flagged the validation caveat unprompted —
consistent with it having picked up the project memory saved earlier
about this exact feedback gap, suggesting that memory is being read
correctly on fresh sessions even though live hook stderr isn't.

**Conclusion:** this build's `--debug-file` does not surface hook exit
codes at all. The gap isn't just "stderr feedback doesn't always reach
Claude in conversation" — the exit code isn't observable in the debug
log either. The only reliable way to see the actual result is to run
the hook script manually against the file and inspect its exit code
directly, as done earlier (`missing 'description'...`, confirmed exit
2).

## Session Notes: costThreshold Is Not a Real Setting

Section 7.7's example config (warningAt/hardLimit under a costThreshold
key) does not correspond to any real field in the current Claude Code
settings.json schema — confirmed by attempting to add it and having it
rejected against the live schema validation. No cost/budget key exists
in settings.json at all.

This is a documented course concept, not a shipped feature.

**Real solution built instead:** scripts/cost_guard.py, wired into two
hooks:
- PreToolUse: estimates session cost from the transcript's token usage
  against a per-model pricing table, blocking tool calls (exit 2) once
  a $20 hard limit is reached — an actual enforcement mechanism.
- Stop: logs running cost every turn to logs/cost-audit.log, and fires
  a one-time Windows toast notification when cost crosses $5 (warning)
  and again at $20 (hard limit), deduplicated per session.

Verified against the real session transcript (~$1.89 computed
correctly) and tested end-to-end with temporarily lowered thresholds to
confirm both the warning and block actually fire.

**Takeaway:** this is the third genuine discrepancy found this module
between course-documented behavior and actual Claude Code behavior
(alongside the PostToolUse and SessionStart stderr-visibility gaps).
Worth treating course material as a conceptual guide rather than a
literal, guaranteed-accurate reference — verify against the live schema
or real behavior before trusting a documented field/setting exists.

## Module 7 Wrap-Up Summary

Built a complete, verified hook system for the mcp-hayabusa project:

| Event | Script | Purpose |
|---|---|---|
| SessionStart | check-prereqs.sh | Warns if required tools (jq) are missing |
| PreToolUse (.*) | check-sensitive.sh | Blocks tool calls touching sensitive paths |
| PreToolUse (.*) | cost_guard.py | Blocks tool calls once cost hits $20 hard limit |
| PostToolUse (Edit\|Write) | log-edit.py | Logs every file write/edit for verification |
| PostToolUse (Edit\|Write) | validate-rule.sh | Validates Sigma rule YAML on save |
| Stop | PowerShell toast | Desktop notification when a response completes |
| Stop | cost_guard.py | Logs running cost; warns at $5, blocks at $20 |

**Three real discrepancies discovered and documented this module** (all
verified through direct testing, not assumption):
1. PostToolUse exit-2 stderr doesn't reliably reach Claude's context or
   --debug-file logs — filed as github.com/anthropics/claude-code/issues/78393
2. SessionStart hook stderr (even on exit 0) doesn't reach Claude's
   context — only stdout does. Fixed by switching check-prereqs.sh to
   stdout, verified working after the fix.
3. costThreshold is not a real settings.json field — the course
   documents a concept with no corresponding shipped setting. Built
   real enforcement via cost_guard.py instead.

**Key methodological lesson:** this module's biggest takeaway wasn't
just "how hooks work" — it was learning to verify hook behavior
directly (sentinel files, transcript inspection, schema validation)
rather than trusting documentation or assuming success from silence.
Every hook in the final system was proven working through direct
evidence, not just "should work per the docs."

**On the module's core premise** ("no hoping Claude remembers, no
manual triggers"): mostly holds, with real caveats. The mechanics
(hooks firing, blocking, running scripts) are genuinely deterministic
and reliable. But whether feedback from those hooks reaches a human or
Claude depends on specific exit-code/stream combinations that aren't
fully documented — worth verifying for any hook where feedback
visibility matters.
