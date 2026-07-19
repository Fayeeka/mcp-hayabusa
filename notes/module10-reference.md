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
