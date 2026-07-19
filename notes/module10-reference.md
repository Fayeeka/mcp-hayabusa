# Module 10 Reference: End-to-End Purple Team Workflow

## Claude Ecosystem Coverage

| Component | Feature | How We Use It |
|---|---|---|
| MCP Tools | Hayabusa, detection KB | Detection and validation |
| Skills | Detection engineering | Rule validation and standards |
| Slash Commands | /ingest-ti, /query | Threat intel and SIEM queries |
| Claude Desktop | Document generation | Reports and presentations |
| Plugins | Bundled distribution | Packaging for team sharing |

## Overview

Components built throughout the course:
- MCP servers that wrap security tools (Module 3) and expose knowledge
  bases (Module 4)
- Skills that encode methodology (Module 5)
- Commands for repeatable workflows (Modules 6, 8)
- Hooks for automation (Module 7)
- Report generation (Module 9)

This module connects them into a complete purple team loop: from
threat intelligence to simulation to detection to validation to
reporting.

By the end:
- A working end-to-end purple team workflow
- Understanding of how ecosystem components connect
- A plugin structure for sharing with your team
- Patterns for adapting to your environment

## The Problem

Purple teaming involves many disconnected steps: read a threat report,
extract TTPs manually, find matching Atomic Red Team tests, run tests
in the lab, check if detections fired, validate in the SIEM, document
results somewhere, track coverage over time. Each step uses different
tools, requires context-switching, and risks losing information
between stages. Course components built so far automate parts of
this — this module connects them.

## 10.1 The Purple Team Loop

Threat Intel (/ingest-ti) → Atomic Red Team Mapping → Execute in Lab →
Detect (Hayabusa MCP) → Validate (/query) → Report (Module 9) → Track
(Vectr). Each stage uses components already built across the course.

## 10.2 Setting Up the Purple Team Project

New project (~/purple-team), no copying from previous modules —
commands and agents defined fresh here.

Structure: CLAUDE.md, .claude/settings.json (MCP servers),
.claude/commands/{ingest-ti,query,purple-loop}.md,
.claude/agents/atomic-mapper.md, exercises/, reports/.

**ingest-ti**: fetch content (defuddle-cli or web_fetch fallback),
extract TTPs with extended thinking, map to ATT&CK, generate a
simulation plan grouped by kill chain phase.

**query**: build SIEM query (default Splunk SPL), execute (via SIEM
MCP if available, else manual), analyze + map to ATT&CK, generate
Obsidian notes with backlinks.

**purple-loop**: orchestrates the full 8-step workflow — threat intel
→ test planning (atomic-mapper) → execution checklist → detection
analysis (hayabusa) → SIEM validation (/query) → gap analysis → 
documentation → tracking reminder (Vectr). Maintains context between
steps, offers handoff documents.

**atomic-mapper agent**: maps ATT&CK technique IDs to Atomic Red Team
tests — filters for platform, prioritizes low-prerequisite/clear-
telemetry/lab-safe tests, outputs test name, Invoke-AtomicTest command,
cleanup command, expected telemetry (Event IDs/log sources).

MCP config points hayabusa's cwd at the actual Module 3 mcp-hayabusa
folder path. Verify with /mcp after restart.

## 10.3 Step 1: Threat Intelligence Ingestion

/ingest-ti <url> — real example in the course: a Huntress report on
ClickFix + Matanbuchus 3.0 + AstarionRAT, extracting ~19 TTPs across
the full kill chain (initial access through C2), each with confidence
and simulate/observe priority. Output saved as
exercises/YYYY-MM-DD/threat-intel.md — feeds the next step.

## 10.4 Step 2: Mapping to Atomic Red Team Tests

Invoke atomic-mapper agent against the saved threat-intel.md — returns
a full test plan (commands, cleanup, expected telemetry) per technique.

## 10.5 Step 3: Execute Tests in Lab

Prerequisite: Install-AtomicRedTeam -getAtomics (one-time PowerShell
setup). Run selected tests (e.g. T1082, T1069.002, T1136.001) via
Invoke-AtomicTest. Export EVTX afterward:
wevtutil epl Security / "Microsoft-Windows-Sysmon/Operational".

## 10.6 Step 4: Detect with Hayabusa MCP

Verify /mcp shows hayabusa connected. Ask Claude to scan the exercise's
EVTX files, scoped to the test date, focused on the specific techniques
tested — returns detections grouped by severity.

Useful pattern: local Hayabusa-first pass over large EVTX volumes
before/instead of a full SIEM, or as a way to pre-filter before
transferring to a SIEM.

## 10.7 Step 5: Validate in SIEM

/query for the same findings in the SIEM — confirms cross-source
correlation, generates Obsidian notes with backlinks. From here, feed
into Module 9 report generation or a dedicated purple-team tracker
(e.g. Vectr).

## 10.8 The Orchestration Command

/purple-loop ties everything together — walks through all 8 steps
interactively. The broader point: security teams often run disconnected
tools (SIEM, EDR, vuln management, inventory, ticketing) that don't
talk to each other; AI-driven workflows can bridge that gap and reduce
time spent bouncing between systems.

## 10.9 Building Plugins for Distribution

Plugins bundle skills, commands, hooks, subagents, MCP configs, and
CLAUDE.md templates for team sharing.

Structure: plugin.json (manifest: name, version, description,
components list, external/mcp-server dependencies), README.md,
skills/, commands/, agents/, hooks/settings-fragment.json,
mcp/server-configs.json, templates/CLAUDE.md.

Install: /plugins install ./purple-team-plugin or from a git repo URL.

Best practices: document dependencies, include setup instructions,
provide usage examples per component, version plugins, test before
distributing.

## 10.10 Extending: Browser Automation for SIEMs

For SIEMs lacking good APIs, or cloud-console-only workflows:
agent-browser (Vercel's CLI tool for AI agents) — more efficient than
Playwright MCP via "Snapshot + Refs" (up to 93% less context).

Install: npm install -g agent-browser, then agent-browser install
(downloads Chromium; --with-deps on Linux if needed).

**Windows note:** agent-browser has known issues with native
PowerShell/CMD — requires WSL on Windows.

Usage: Claude runs agent-browser commands via bash — logs into a SIEM
web UI, runs a search, captures/returns results for analysis.

## Session Notes: Section 10.10 (Browser Automation) — Not Attempted

agent-browser (Vercel's CLI tool for AI browser agents) explicitly
requires WSL on Windows per its own documentation — native PowerShell/
CMD is not supported. Given this project has no WSL setup and no live
SIEM to automate against anyway (same gap noted in Module 6), this
section was covered conceptually rather than attempted:

The pattern: agent-browser logs into a SIEM web interface, executes
searches, extracts results, and returns them to Claude for analysis —
useful when a SIEM lacks a good API, or for cloud-console-only
workflows. It uses a "Snapshot + Refs" approach that's reportedly far
more context-efficient (up to 93% less) than Playwright MCP for this
kind of agentic browser automation.

If a real Windows-based purple-team workflow needed this in the
future, WSL would need to be set up first — a bigger, separate
infrastructure decision, not something to bolt on casually.

## Module 10 Wrap-Up: Full Capstone Summary

Built and ran a complete, real end-to-end purple team exercise
(Screening Serpens / UNC1549) connecting components from across the
entire course:

- /ingest-ti (adapted from Module 8) extracted 26 distinct ATT&CK
  techniques from a real Unit 42 threat report
- atomic-mapper agent researched real Atomic Red Team tests (downloading
  actual test YAMLs from GitHub), correctly flagging its own uncertainty
  on one disputed technique ID rather than presenting it as fact, and
  honestly identifying 2 techniques with no packaged atomic test at all
- Execution checklist documented (not live-executed — no dedicated lab
  environment; real EVTX sample data from Modules 3/8 substituted)
- Hayabusa MCP (Module 3) scanned real substitute telemetry, correctly
  identifying it only validated ~7% of planned techniques and zero of
  the three "crown jewel" techniques
- SIEM validation step adapted (Module 6's pattern) — query staged and
  documented since no live SIEM is connected
- Gap analysis produced a genuinely calibrated verdict: "detection
  tooling is proven; campaign coverage is not"
- Full documentation package generated: team report (MD, DOCX-ready),
  leadership deck (MD, PPTX-ready), and a polished HTML visual dashboard
  artifact
- A real GitHub tracking issue (#1) opened with 3 labeled, actionable
  follow-ups, linked back to the exercise record
- A genuinely working plugin package built (purple-team-plugin/) with
  real components throughout — including honestly flagging and then
  fixing a manifest claim that wasn't yet backed by real content
- Section 10.10 (browser automation) covered conceptually — genuine
  Windows/WSL platform limitation, not attempted

### The throughline across all 10 modules

Every module surfaced at least one genuine environment limitation or
real bug (Node version incompatibilities, a confirmed Claude Code hook
feedback bug filed upstream as issue #78393, a non-existent
costThreshold setting, LiteLLM's Windows build-toolchain requirement,
no live SIEM/Azure/lab environment) — and every single one was handled
the same way: verify directly rather than assume, document honestly
rather than paper over, and adapt pragmatically rather than force
through. That discipline, more than any specific tool, is the real
skill this course built.

### Final artifact count across the course
- 4 GitHub repositories: sysmon-parser, mcp-hayabusa, complex-analysis, purple-team
- 1 real upstream bug report filed and confirmed live (anthropics/claude-code#78393)
- 1 real tracking issue on own work (purple-team#1)
- Dozens of commits, all with honest, descriptive messages
- Real DOCX/PPTX/HTML deliverables generated from genuine investigation
  and exercise data, not placeholder content, throughout Modules 9-10
