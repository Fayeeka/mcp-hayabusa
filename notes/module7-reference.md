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
