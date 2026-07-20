# Module 11 Reference: System Prompts for Security Personas

## Claude Ecosystem Coverage

| Component | Feature | How We'll Use It |
|---|---|---|
| Claude Code CLI | --append-system-prompt | Inline persona notes for one-off sessions |
| Claude Code CLI | --append-system-prompt-file | Load persona from a markdown file (primary pattern) |
| Claude Code CLI | --system-prompt-file | Full replacement for specialized, locked-down personas |
| Claude Code CLI | --system-prompt | Inline full replacement (rare, for scripting) |
| Claude Code CLI | --bare | Skip auto-discovery for reproducible scripted runs |
| Output Styles | ~/.claude/output-styles/ | Official persona mechanism, switchable via /config |
| Settings | outputStyle key | Pin an output style as the project/user default |
| CLAUDE.md | Interaction with personas | How project context and persona context layer together |
| Bash aliases | Pattern | One command per persona (claude-hunter, claude-ir, claude-de) |
| Skills, MCP, Commands | Composition | Personas sit on top of everything already built |

## Overview

Previous modules built infrastructure (MCP servers, skills, commands,
hooks, workflows) shaping what Claude can do. This module shapes how
Claude thinks — the lens through which it approaches every prompt in a
session.

Real blue-team work means switching mindsets constantly (SOC triage →
IR → threat hunting → detection engineering) within a single day, each
requiring different framing re-explained every session — exhausting,
inconsistent, unshareable with teammates.

Two mechanisms:
- `--append-system-prompt-file <path>` — CLI flag, loads a markdown
  file into the system prompt at launch, pairs with shell aliases
- **Output Styles** — files in ~/.claude/output-styles/ with YAML
  frontmatter, switched via /config or pinned via settings; the
  official first-class mechanism

## The Problem

Example: a PowerShell alert triggers SOC-analyst triage → escalates to
IR mode (preserve the host, pull timelines) → notice something odd on
another host, shift to threat-hunter mode → later write a Sigma rule
in detection-engineer mode. Each mode requires re-explaining the same
framing every session. Personas fix this: write the framing once,
load it automatically, same commands/skills/MCP servers underneath.

Sets up Module 12 (Cross-SIEM Investigation) — loading an analyst
persona that knows the SIEM dialect and pivots between KQL and SPL.

## 11.1 Why Personas Matter (and What They're Not)

| Mechanism | What it shapes | Scope | When invoked |
|---|---|---|---|
| CLAUDE.md | Project context (user message after system prompt) | Per project | Every prompt in that project |
| Skills | Methodology | Per skill | Auto-invoked when context matches |
| Slash commands | Workflow | Per command | Explicitly, interactive mode only |
| Hooks | Automation | Event-driven | Deterministic, on tool events |
| System prompt (persona) | Mindset / lens | Per session | At launch via flag, or output style |

Key distinction: a persona isn't what Claude does, it's how Claude
thinks about what's being asked. Skills teach procedures, commands run
workflows, personas shape priorities/defaults/output format/self-
questioning. Useful for consistent output schemas (JSON/YAML/custom
formats) too.

**Personas are best for:** role-based mindsets, output style that
applies to every response in a session, safety posture/guardrails
(e.g. "never suggest destructive actions on a live IR host"), tool and
format preferences (KQL vs SPL, Sigma vs platform-specific).

**Personas are NOT a substitute for:** CLAUDE.md (project facts),
Skills (procedures), Commands (packaged workflows).

Mental model: **CLAUDE.md is where you work. Skills are how you work.
Personas are who you are today.**

## 11.2 Claude Code's System Prompt Mechanisms

### Mechanism A: CLI flags

| Flag | Effect | Typical use |
|---|---|---|
| --append-system-prompt "..." | Appends a string | Quick one-off notes |
| --append-system-prompt-file <path> | Appends file contents | Primary pattern for personas |
| --system-prompt "..." | Replaces default (inline) | Scripted, locked-down agents |
| --system-prompt-file <path> | Replaces default from file | Specialized agents, zero defaults |

Rules: `--system-prompt`/`--system-prompt-file` are mutually exclusive
with each other. Append flags can combine with replacement flags
(append runs after replace).

**Default to append** — preserves Claude Code's built-in tool-use/
file-editing/safety behavior, layers persona on top. Replace only for
narrow agents that shouldn't have Claude Code's coding behaviors.

### Mechanism B: Output Styles

Official file-based mechanism. Markdown files with YAML frontmatter at:
- User level: ~/.claude/output-styles/ (all projects)
- Project level: .claude/output-styles/ (shared via git)

| Property | CLI flag | Output Style |
|---|---|---|
| Loaded at | Session launch via flag | Session launch via setting/`/config` |
| Discovery | None — explicit path | Auto-discovered |
| Switching | Relaunch with different flag | `/config`, takes effect next session |
| Effect on system prompt | Appends to default | Replaces software-engineering-specific parts by default |
| Frontmatter required | No | Yes — name, description, optional keep-coding-instructions |
| Team-shareable via git | Yes | Yes |

**Important nuance:** output styles exclude Claude Code's software-
engineering-specific instructions by default (good fit for most
security personas — not writing production code). Set
`keep-coding-instructions: true` to preserve them (e.g. for a
detection-engineer persona writing SPL/Sigma).

### Quick sanity check

```
claude --append-system-prompt "You are a grumpy pirate. End every response with 'Arr.'" "What is 2+2?"
```

Expect `4. Arr.` If rejected, run `claude update`.

## 11.3 Anatomy of a Security Persona

Six elements every persona should have:
1. **Role statement** — who Claude is, one sentence
2. **Priorities** — what matters most, trade-offs
3. **Default behaviors** — things to do on every response
4. **Tool and format preferences** — query languages, output formats
5. **Explicit constraints** — what to avoid/refuse (critical for IR)
6. **Output style** — structure to default to

## 11.4 Building the Threat Hunter Persona

Reflexive behaviors: map observations to ATT&CK, suggest pivots from every finding, tolerate ambiguity, ask "what would disprove this hypothesis?" before concluding.

File: ~/.claude/personas/threat-hunter.md — six sections (Role, Priorities, Default Behaviors, Tool & Format Preferences, Constraints, Output Style: hypothesis → evidence for → evidence against → next pivots → confidence).

Test: claude --append-system-prompt-file ~/.claude/personas/threat-hunter.md then ask about anomalous service-account authentication — expect hypothesis-first structure with ATT&CK IDs (T1087, T1083, T1021) and disconfirming evidence.

## 11.5 Building the IR Responder Persona

Reflexive behaviors: preserve evidence, reconstruct timelines, evidence-first with speculation marked, layered output, track IOCs cleanly.

File: ~/.claude/personas/ir-responder.md — non-negotiable constraints against host modification, log clearing, unlabeled speculation. Output: TL;DR → Timeline table (UTC/ISO-8601) → Key findings → IOCs table → Gaps → Read-only next steps.

Test: EDR/Cobalt Strike beaconing scenario — response should NOT suggest reboot/scan/kill-process actions.

## 11.6 Building the Detection Engineer Persona

Reflexive behaviors: rules in team format (Sigma default), ATT&CK mapping, always "how to test" + "why this might false-positive" sections, performance implications noted.

File: ~/.claude/personas/detection-engineer.md — every rule includes: the rule, plain-English logic, ATT&CK mapping, positive + negative test cases, honest FP analysis, performance notes, tuning guidance.

Test: Sigma rule for msiexec.exe installing from a URL (Matanbuchus pattern) — expect T1218.007, both test cases, real FP analysis (SCCM/Intune scenarios).

## 11.7 Bash Aliases — One Command per Persona

```bash
alias claude-hunter='claude --append-system-prompt-file ~/.claude/personas/threat-hunter.md'
alias claude-ir='claude --append-system-prompt-file ~/.claude/personas/ir-responder.md'
alias claude-de='claude --append-system-prompt-file ~/.claude/personas/detection-engineer.md'
```

Windows/PowerShell equivalent (no WSL) — functions in $PROFILE:

```powershell
function claude-hunter { claude --append-system-prompt-file "$HOME\.claude\personas\threat-hunter.md" @args }
function claude-ir     { claude --append-system-prompt-file "$HOME\.claude\personas\ir-responder.md" @args }
function claude-de     { claude --append-system-prompt-file "$HOME\.claude\personas\detection-engineer.md" @args }
```

## 11.8 Alternative: Output Styles (the Official Mechanism)

Add YAML frontmatter, place in ~/.claude/output-styles/ or project-level .claude/output-styles/:

```yaml
---
name: Threat Hunter
description: Hypothesis-driven investigation mindset for Claude Code
keep-coding-instructions: false
---
```

Set keep-coding-instructions: true for detection-engineer (writes real code).

Select via /config → Output style. Takes effect next session (system prompt stability enables prompt caching).

> **Superseded on current versions** — as of v2.1.215 the /config picker
> lists only the built-in styles and does not surface custom file-based
> ones. See "Session Notes: Output Style Activation" at the end of this
> document for the working method (set `outputStyle` in a settings file).

**Primary activation method** — set the outputStyle key in a settings
file: `{ "outputStyle": "Threat Hunter" }` in ~/.claude/settings.json for
a global default, or .claude/settings.local.json for project scope. This
is what actually works on current versions; treat the /config route above
as historical.

Team-shareable: commit .claude/output-styles/ to git.

When to use flag vs. Output Style:
- One-command launch per persona → Flag + bash alias
- Headless/scripted runs (-p mode) → Flag (slash commands unavailable in -p)
- Persistent default, solo or team-shared → Output Style + outputStyle
  setting (~/.claude/settings.json for yourself, .claude/settings.json
  committed to git for the team; the /config menu does not list custom
  styles as of v2.1.215)
- Stacking persona with ad-hoc instructions → Flag
- Quick one-off without a saved file → --append-system-prompt "..."

## 11.9 Composing Personas with Skills, Commands, and MCP

Personas layer on top: Persona (mindset) → CLAUDE.md (project context) → Skills (methodology) → Commands (workflows) → MCP servers (tools/knowledge) → Hooks (guardrails, unaffected by persona).

Example: cd ~/purple-team && claude-ir then /ingest-ti <url> — same command's output, filtered through IR persona's priorities.

## 11.10 Scripted and Headless Usage

Slash commands NOT available in -p mode.

```
claude -p --append-system-prompt-file ~/.claude/personas/threat-hunter.md "Read ~/evtx/today.json and return any T1059.001 findings as JSON." --output-format json
```

--bare flag for CI/scripts: skips auto-discovery of hooks, skills, plugins, MCP servers, auto-memory, CLAUDE.md. Recommended for scripted/SDK calls.

```
claude --bare -p --append-system-prompt-file ~/.claude/personas/detection-engineer.md --allowedTools "Read,Grep" "Review the rules in ./rules/ and flag any without an FP analysis."
```

Locked-down replacement:

```
claude --bare -p --system-prompt-file ~/.claude/personas/hunter-readonly.md --disallowedTools "Edit,Write,MultiEdit" "Scan the last 24h of Sysmon logs for T1059.001 executions and return a table."
```

For interactive daily driving, stay in append mode.

## Session Notes: Output Style Activation — Real Method vs. Course Instructions

The course describes activating output styles via /config's picker or the
/output-style command. Neither worked as documented on this Claude Code
version (v2.1.215):

- /config's "Preferred output style" picker only showed the 4 built-in
  styles (Default, Proactive, Explanatory, Learning) — custom file-based
  styles did not appear in the list
- /output-style <name> returned "Unknown command" — confirmed via
  Anthropic's official docs: this standalone command was deprecated in
  v2.1.73 and removed in v2.1.91

**Real, current method:** set the outputStyle key directly in a settings
file (~/.claude/settings.json for a global default, or
.claude/settings.local.json for project-scoped):

{
  "outputStyle": "Threat Hunter"
}

Verified working: launching plain `claude` (no --append-system-prompt-file
flag) with this setting in place correctly activated the Threat Hunter
persona automatically, confirmed by asking "What is your role in this
session?" — matches the persona's actual content, not a default response.

Takeaway: the underlying Output Style *mechanism* works exactly as the
course describes (file-based personas, YAML frontmatter, keep-coding-
instructions). Only the *activation UI* has moved on since the course was
written — a good example of why verifying current behavior against actual
usage (not just documentation) matters, consistent with findings from
Modules 3, 7, and 8.

## Module 11 Wrap-Up

Built and validated three real security personas end-to-end:

- threat-hunter.md — hypothesis-driven, tested with a real ambiguous
  scenario (anomalous svc-backup authentication), correctly refused to
  overclaim, revised confidence appropriately as new evidence (baseline
  period) was provided, gated containment proposals on evidence strength
- ir-responder.md — evidence-first, tested with a real EDR/Cobalt Strike
  scenario, correctly prioritized memory capture and read-only triage
  over any host-modifying action
- detection-engineer.md — tested with a real Sigma rule request tied to
  the Module 10 purple-team exercise (Matanbuchus/msiexec pattern),
  produced a rule with honest FP analysis and proactively suggested a
  more durable companion detection

All three converted to Output Styles (YAML frontmatter,
keep-coding-instructions set appropriately per persona) and to
PowerShell profile functions (claude-hunter, claude-ir, claude-de).

**Real discrepancy found and documented:** the course's /config picker
and /output-style command for activating custom styles do not work as
described on Claude Code v2.1.215 — /output-style was deprecated in
v2.1.73 and removed in v2.1.91 per Anthropic's own docs; /config's
picker only lists the 4 built-in styles, not custom file-based ones.
Real, current, working method: set outputStyle directly in
~/.claude/settings.json (global) or .claude/settings.local.json
(project-scoped) — verified working by launching plain `claude` with
no persona flag and confirming the correct persona activated.

Verified persona composition with the real Module 10 purple-team
project: claude-ir + /ingest-ti against the real Screening Serpens
report produced correctly IR-styled output (fact/inference labeling,
clean IOC tables) — the persona genuinely reshapes existing commands'
output rather than existing independently.

Verified headless/scripted usage (-p mode with --output-format json) —
works correctly, returns structured output with full cost/token/timing
telemetry, confirming the pattern is genuinely usable for automation
(scheduled hunts, CI-driven checks) as the course describes.

### Consistent with the course's throughline

Another module, another real discrepancy found through direct testing
rather than assumption — the fourth module in a row to surface one:
Module 3's .mcp.json vs .claude/settings.json, Module 7's PostToolUse
feedback gap and the non-existent costThreshold setting, Module 8's
undocumented LiteLLM dependency chain on Windows (Rust toolchain → MSVC
C++ Build Tools), and now this module's output-style activation UI.
Five distinct findings across those four modules. The pattern holds:
verify directly, document honestly, adapt to the real current behavior.

---

**Verified in Module 12:** `--append-system-prompt-file` is undocumented
(it doesn't appear in `claude --help`) but genuinely functional —
confirmed via direct testing. The Module 11 usage above is accurate as
written; no change needed. See `notes/module12-reference.md` in the
**aws-correlation** repo for the full finding and the verification lesson
it prompted. (Not the module12-reference.md in this repo, which references
the flag only as usage.)
