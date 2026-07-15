# Module 6 Reference: Slash Commands - Repeatable Workflows

## Claude Ecosystem Coverage

| Component | Feature | How We'll Use It |
|---|---|---|
| Slash Commands | Core concept | Explicitly invoked workflows with /command |
| .claude/commands/ | Command location | Where command files live |
| Command arguments | Parameterization | Passing query and options to commands |
| MCP + Commands | Integration | Using MCP tools from within commands |
| Obsidian markdown | Output format | Generating graph-friendly investigation notes |

## Overview

In Module 5, skills activate automatically based on context. Sometimes
you want explicit control instead — a workflow you trigger deliberately,
with specific inputs, producing consistent output every time.

Slash commands give you this. Type /query and Claude runs your
investigation workflow. Type /triage and Claude follows your alert
handling procedure. The command defines the steps; you control when it runs.

## The Problem

Example scenario: investigating an alert or crafting a new SIEM
detection query. You need to: run a SIEM query to pull related events,
analyze results for suspicious patterns, map findings to ATT&CK
techniques, and document everything for investigation notes. Without a
command, this is done manually every time.

With a /query command:

```
/query queries/mimikatz-hunt.spl
```

Claude reads the query from the file, runs it against your SIEM,
analyzes results, maps to ATT&CK techniques, generates Obsidian-compatible
notes with [[T1003.001]] backlinks, and outputs a ready-to-save
investigation document — same workflow, every time, triggered with one command.

## 6.1 Commands vs. Skills

| Aspect | Skills | Commands |
|---|---|---|
| Activation | Automatic (context-based) OR manual via /<skill-name> | Manual (/command-name) |
| Trigger | Claude decides | You decide |
| Use case | "Always apply these standards" | "Run this workflow now" |
| Input | Implicit (current task) | Explicit (arguments you provide) |

Skills = Background methodology (like a style guide Claude follows)
Commands = Foreground workflows (like a button you press)

**When to use Commands:** workflows with specific inputs, multi-step
processes you want consistent, tasks triggered deliberately not
contextually, workflows that produce structured output.

**When to use Skills:** standards that apply across many contexts,
methodology you want Claude to always follow, background knowledge not
foreground actions.

## 6.2 Command Structure

Commands live in .claude/commands/, each a markdown file with YAML
frontmatter (same as skills), but with an added arguments field:

```yaml
---
name: query
description: Run a SIEM query and document results with ATT&CK mapping
arguments:
  - name: query_file
    description: Path to a file containing the SIEM query
    required: true
  - name: timerange
    description: Time range for the query (e.g., "-24h", "-7d")
    required: false
    default: "-24h"
---
```

Key differences from skills: commands accept arguments, are invoked with
/query <args>, and never auto-activate.

## 6.3 Building the /query Command

Prerequisites: SIEM access (Splunk REST API, Elastic API, or other).
Course uses Splunk's REST API as the example; the pattern adapts to any SIEM.

The command should: accept a query file path + optional timerange, read
and run the query, analyze results for suspicious patterns, map findings
to ATT&CK techniques, and generate Obsidian-compatible markdown with YAML
frontmatter, [[backlinks]] to techniques, findings summary, raw
query/result count, and an analyst notes section — saved to investigations/.

Assumes environment variables SPLUNK_HOST and SPLUNK_TOKEN for API access.

Test query file: queries/whoami.spl containing `index=sysmon whoami`
(kept in a text file rather than pasted inline, to avoid formatting issues).

Test with: `/query queries/whoami.spl` after restarting Claude Code to
load the new command.

**Production note:** specify particular indexes/time ranges/guardrails
against long-running queries; consider whether Claude should analyze
results at all vs. just running the query and returning raw results.

## 6.4 Obsidian Integration

YAML frontmatter (date, tags, techniques, status) lets Obsidian filter
notes by tag, search by technique, track investigation status.

[[T1003.001]]-style backlinks create graph connections in Obsidian
between investigation notes and technique notes (creating a placeholder
if the technique note doesn't exist yet).

Suggested vault structure:
```
vault/
├── investigations/
│   ├── 2026-02-28-mimikatz-detection.md
│   └── 2026-02-27-lateral-movement.md
├── techniques/
│   ├── T1003.001.md
│   ├── T1550.002.md
│   └── T1059.001.md
└── templates/
    └── investigation-template.md
```

Graph view benefits: clusters of related techniques, common attack
patterns, gaps in technique documentation, investigation timelines —
useful for tracking campaigns, identifying patterns across incidents,
building institutional knowledge.

## 6.5 Making the Command SIEM-Agnostic

**Option 1 — Environment-based selection:** command detects which SIEM
is configured (SPLUNK_HOST, ELASTIC_HOST, or a browser-based fallback).

**Option 2 — Multiple commands:** separate query-splunk.md,
query-elastic.md, query-sentinel.md files, aliased via CLAUDE.md ("Our
SIEM is Splunk. When I say /query, use the Splunk workflow.")

**Option 3 — MCP integration:** if a SIEM MCP server exists (like the
Hayabusa wrapper from Module 3), the command calls MCP tools instead of
hardcoding API calls directly — separating SIEM integration (MCP) from
the workflow (command).

## 6.6 Parameterized Commands

Example expanded arguments: severity (info/low/medium/high/critical),
assignee, case_id, output_dir (default: investigations/).

```
/query queries/lateral-movement.spl --severity high --assignee "Anton" --case_id CASE-1234
```

Argument types: required, optional (with defaults), flags (boolean),
positional vs. named.

Validation example: verify valid SPL syntax, check timerange format,
confirm severity is a valid value, warn on malformed case_id.

## 6.7 Combining Commands with MCP (Optional)

**Query + Detection Coverage:** combine with the Module 4 detection MCP
resource to check, for each ATT&CK technique found, whether a rule
exists — surfacing coverage gaps directly in the investigation note:

| Technique | Status | Rule |
|---|---|---|
| [[T1003.001]] | Covered | `lsass_memory_access.yml` |
| [[T1550.002]] | Gap | No rule found |

**Query + Hayabusa Correlation:** a combined `/investigate-endpoint`
workflow — run the SIEM query, run a Hayabusa EVTX scan if files are
available, correlate findings between both sources, generate one unified
note.

Note: Splunk's free license doesn't support API access — browser
automation could work around this for testing purposes.
