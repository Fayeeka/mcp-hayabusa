# Module 12 Reference: Cross-SIEM Investigation — Correlating Sysmon and CloudTrail

## Claude Ecosystem Coverage

| Component | Feature | How We'll Use It |
|---|---|---|
| Persona (M11) | --append-system-prompt-file | Cross-SIEM analyst persona that knows SPL and KQL |
| Bash via Claude Code | Shell tool | curl against Splunk REST API + curl with az bearer token against Kusto |
| Settings (M7) | .claude/settings.local.json | Per-project env vars (SPLUNK_URL, ADX_CLUSTER, etc.) |
| Subagents (M8) | Parallel execution | Optional — run Splunk and ADX queries concurrently |
| Skills (M5) | Optional codification | "AWS CLI mapping" skill for edge cases (mentioned 12.8) |
| Slash commands (M6) | .claude/commands/ | Alternative packaging (mentioned 12.7) |
| Reports (M9) | Markdown output | Correlation table saved per investigation |

## Overview

Security telemetry is scattered across systems — "single pane of glass"
is mostly marketing. This module works a real example: AWS CLI activity
on a host generates two strands of telemetry — one on the host, one in
CloudTrail on AWS — and correlating them manually is hard. LLMs can
infer the correlation through reasoning rather than a classic join.

Uses Splunk and Azure Data Explorer (ADX) as the example systems, but
the pattern generalizes to any access method (API, MCP, curl).

Explicitly builds on Module 11 — requires the persona pattern.

## The Problem

Example: Administrator@condef.local has IAM keys on condef-win11a.
Late-night flurry of `aws sts get-caller-identity` calls — compromised
key? Misconfigured CI? Forgotten pen-test?

- **Sysmon (Splunk)**: which host/process invoked the CLI, full command
  line, parent process, user, exact timestamp
- **CloudTrail (ADX)**: which API events actually fired, from which
  source IP, what user-agent, what result

Neither alone answers the question. Correlation does — the module's
goal is making that a one-command operation.

## 12.1 Two Sides of the Same Action

| Field | Sysmon (Splunk) | CloudTrail (ADX) |
|---|---|---|
| Originating host | Computer field | sourceIPAddress only |
| OS user | User field | userIdentity.userName (IAM user, not OS user) |
| Process/command | Image, CommandLine, ProcessGuid, parent | — |
| AWS API call | — | eventName, eventSource, awsRegion |
| AWS identity | — | full userIdentity object |
| Result | process exit code, sometimes | errorCode, errorMessage, responseElements |
| When | UtcTime | eventTime |
| CLI signature | — | userAgent contains aws-cli/X.Y.Z |

**Strongest joins available:**
- Time window — usually within a few seconds; default ±60s, expand if needed
- userAgent confirms CLI origin (aws-cli/ prefix)
- sourceIPAddress can confirm host if egress IP known
- CLI verb → event-name mapping (the persona's core value-add, 12.2)

## 12.2 The AWS CLI → CloudTrail Event Mapping

Persona infers this at runtime rather than reading a lookup file —
keeps things simple, demonstrates real reasoning.

**Default rule:** CLI verbs are kebab-case, CloudTrail eventName is
PascalCase (mechanical transform). E.g. `get-caller-identity` →
`GetCallerIdentity`.

**Service mapping:** first arg after `aws` is the service; CloudTrail
`eventSource` is `<service>.amazonaws.com`.

**Known exceptions:**
- `aws s3 ls` (no args) → ListBuckets (one event)
- `aws s3 ls s3://bucket` → ListObjectsV2 (possibly paginated, multiple events)
- `aws s3 cp` → PutObject (one per object)
- `aws s3 sync` → many PutObject/HeadObject/ListObjectsV2 (fan-out)
- `aws s3 mv` → CopyObject + DeleteObject (two events from one command)
- `aws configure`, `aws --version`, `aws help` → no API call (local-only)
- `aws s3 presign` → no API call (generates signed URL locally)
- `s3api` (low-level) is 1:1 with the API; `s3` (high-level) is not

**Strong signals to confirm CLI origin:**
- userAgent starts with `aws-cli/`
- readOnly: true should accompany Get*/List*/Describe* verbs — mismatch is a red flag
- sourceIPAddress matches known workstation egress IP

## 12.3 Building the Cross-SIEM Analyst Persona

File: ~/.claude/personas/cross-siem.md — Role, Priorities (stitch
across SIEMs, bound every query in time, distinguish matched/
unmatched-explainable/unmatched-suspicious, note confidence, show
queries run), Default Behaviors (run BOTH queries before concluding,
default 24h window, ±60s correlation window, three-bucket grouping,
hypothesis per unmatched event, confidence rating), Environment
(Splunk index=sysmon/SPL, ADX/KQL, auth details), Tool Preferences
(actual curl commands for Splunk one-shot search and Kusto query via
az bearer token), the AWS CLI mapping rules from 12.2, Constraints
(never claim "no match" without showing the empty query result, never
widen correlation window past 5 min without noting why, never include
credentials in output, never invent missing env vars), Output Style
(Scope, Correlation Table, Unmatched Sysmon table, Unmatched CloudTrail
table, Summary, Queries used).

**Note on credentials:** course's lab demo bakes credentials directly
into the persona file for simplicity — explicitly called out as a
lab-only shortcut, not a production pattern. Real use should strip
credentials into env vars / secrets manager.

Alias: `claude-xsiem` wrapping `--append-system-prompt-file ~/.claude/personas/cross-siem.md`
(bash) or a PowerShell function equivalent.

## 12.4 Project Directory

Minimal skeleton: `~/aws-correlation/reports/`. No CLAUDE.md needed —
persona carries its own environment context, so the project doesn't
duplicate it.

Optional project-scoped env vars via .claude/settings.local.json
(gitignored by default) — but passwords should NOT go here even though
gitignored; keep secrets in shell profile / secrets manager, config
separate from secrets.

## 12.5 The Targeted Investigation Flow

`cd ~/aws-correlation && claude-xsiem`, then ask a natural question
("What did condef-win11a do in AWS today? ... last 4 hours").

Expected persona behavior, in order: verify env vars/auth (401 from
Kusto = stop and ask) → Splunk curl scoped to host/user/time → ADX curl
(fetch bearer token, then query userAgent startswith "aws-cli/") → for
each Sysmon event, derive expected eventName via mapping rules, search
for matches within ±60s → bucket into matched/unmatched-Sysmon/
unmatched-CloudTrail → present tables + summary + queries used.

Key point: this is inference-based correlation, not a classic database
join — the persona reasons across two systems where manual correlation
would require querying both systems separately then hand-matching
timestamps.

## 12.6 The Batch Report Flow

Broader version: "Run the full last-24h cross-SIEM correlation. All
hosts, all users. Save the report to ./reports/." Drops host filter on
Splunk side, ADX query unchanged, larger result sets (may need
pagination/sampling), adds per-host/per-user breakdown, saves to file
rather than just printing.

## 12.7 Wrapping It as a Slash Command

Alternative packaging: move persona's query templates/auth notes/
mapping rules into .claude/commands/correlate-aws.md, invoke as
`/correlate-aws host:X since:4h` in a plain `claude` session.

| | Persona | Slash command |
|---|---|---|
| Loaded via | CLI flag at session start | Typed inline, per invocation |
| Where it lives | System prompt, whole session | Single user message, expanded per call |
| Launch with | claude-xsiem (alias) | Plain claude |
| Best for | Conversational, fuzzy scope, follow-ups | Structured, repeatable, same shape |
| Reproducibility | Looser (agent has flexibility) | Tighter (same args → comparable reports) |
| Hand-off | Share persona file + alias | Share command file, runs in any session |

Rule of thumb: unique questions each time → persona (the "teammate").
Same shape, different scope args each time → slash command (the
"recipe").

## 12.8 Applying This Elsewhere

Pattern generalizes to any two-system correlation:

| Cross-SIEM correlation | Sources | Join key(s) |
|---|---|---|
| EDR ↔ Sysmon | CrowdStrike/Defender ↔ Sysmon | Time + Computer + ProcessGuid |
| Entra ID ↔ Azure Activity Log | SignInLogs (Sentinel) ↔ Activity Log | Time + UPN + IP |
| GitHub audit ↔ CI/CD ↔ CloudTrail | gh audit log ↔ build telemetry ↔ IAM activity | Time + Actor + repo/job ID |
| DNS (Zeek) ↔ Process (Sysmon) | Malcolm DNS ↔ Sysmon netconns | Time + Source IP + Dest IP |
| Email (M365) ↔ Endpoint (EDR) | Defender for O365 ↔ Defender for Endpoint | Time + UPN + URL/hash |

Each is a slightly different persona file, same workflow shape.

**Two upgrade paths for frequent use:**
1. Wrap endpoints as MCP servers (Module 3 pattern) — cleaner than raw
   curl/inline-JSON Kusto bodies; persona calls tools instead
2. Codify the AWS CLI mapping as a Skill (Module 5 pattern) — as edge
   cases accumulate (s3 sync fan-out, presign quirk, etc.), a
   structured mapping table/lookup file is more maintainable than
   rules baked into prose; persona consults the skill when uncertain

## Session Notes: A Real Security Design Flaw Found and Fixed

While building and testing the cross-siem persona against local mock
Splunk/ADX servers, a genuine security flaw in the persona's initial
design was surfaced during testing and diagnosed in review — not a
hypothetical, but a demonstrated one.

**How it was actually found, precisely:** on its first run the persona
deviated from its own documented query, dropping the
`userAgent startswith "aws-cli/"` filter. The instinct was right. The
stated reason was not: it said filtering by source IP would have hidden
the CreateAccessKey event. That claim is true in the abstract — that
event did come from a foreign IP — but source IP was not what the
documented query filtered on. The query filtered on user-agent, and
CreateAccessKey carried an `aws-cli/` user-agent, so it would have
survived that filter untouched. The persona defended against a risk
that wasn't in the artifact in front of it, while the filter that was
actually there happened to be harmless for that particular event.

The real flaw — that a user-agent filter silently hides non-CLI clients
— was identified in review afterward, and only then made demonstrable
by adding a fifth event that the filter genuinely does drop. Worth
recording precisely, because the correction is the interesting part:
the model's instinct was sound before its explanation was. That is an
argument for testing behavior against a fixture rather than accepting a
plausible-sounding rationale at face value — the stated reasoning read
as convincing and was still wrong about its own subject.

**The flaw:** the initial ADX query filtered by
`userAgent startswith "aws-cli/"` as a selection criterion (not just a
classification signal). This silently excludes any CloudTrail event
generated by a non-CLI client — exactly the pattern a real attacker
using stolen credentials via SDK, script, or console (not the CLI)
would produce. The workflow existed specifically to catch stolen
credential use; the original query design would have hidden it.

**Demonstrated, not just argued:** added a fifth CloudTrail event
(GetSecretValue, readOnly: true, Boto3 user-agent, using a credential
minted by an earlier CreateAccessKey event) to the mock ADX server.
Confirmed directly:
- Unfiltered query (ago(4h)): 5 rows
- Filtered query (+ userAgent startswith "aws-cli/"): 4 rows

The filtered query silently dropped GetSecretValue — no error, no
empty-result indicator, just a shorter list missing the single most
consequential event (a read of Secrets Manager using a freshly stolen
credential).

**Fix applied:** ADX query now fetches the full time window
unfiltered; userAgent is used only for classification/reasoning in the
output, never for selecting which events are retrieved. Added a
non-negotiable constraint to the persona: never filter CloudTrail
retrieval by userAgent or sourceIPAddress, since both are
attacker-controlled and provide false confidence.

**Verified end-to-end:** ran the full persona investigation against
both mock servers with all 5 events in play. The persona:
- Correctly bucketed all events (matched pairs, benign unmatched-Sysmon,
  suspicious unmatched-CloudTrail)
- Assembled a plausible attack narrative (credential theft →
  CreateAccessKey → GetSecretValue using the new key)
- Explicitly disclosed the limits of its own reasoning: admitted
  inferring the workstation egress IP from pairing patterns rather
  than configuration, and explicitly stated it could not prove the
  second credential was the one CreateAccessKey issued — "timing plus
  identity, not a hard match"

That last point is the real payoff: the persona's "correlation is
inference, not a join" constraint held at exactly the moment the
narrative was most tempting to overclaim as a confirmed finding rather
than a strong but unproven correlation.

**Known remaining gap:** the persona's recommended confirmation step
(pull responseElements from the CreateAccessKey event to get the
definitive new key ID) cannot be completed against these mocks, since
the fixture's CloudTrail schema doesn't include that field. The
persona correctly identified this as the next step AND correctly
flagged that it couldn't complete it — rather than fabricating a
response. Not fixed, by choice, to keep scope bounded.

### Also encountered: a real cost_guard.py debugging detour

A genuine, separate bug: an edit to raise scripts/cost_guard.py's
HARD_LIMIT from $20 to $40 silently failed to write to disk (root
cause unconfirmed — likely an unsaved buffer or a no-op command).
Diagnosed methodically: searched for duplicate copies of the file
(found none), then retried with a rewrite using a hardcoded absolute
path and a read-back print to confirm the write had landed, which
succeeded. (An earlier attempt did use an assert-guarded rewrite, but
whether it ever ran was never established — it produced no output
either way.) Also surfaced a real design
flaw in the hook itself: it gates Read as well as Write/Edit, meaning
once a session exceeds budget, you cannot even inspect the file that's
blocking you — a genuine "locked out by your own lock" failure mode,
flagged as worth fixing (exempting Read) but not fixed in this session.

### Consistent with the course's throughline

This is the sixth distinct real-world finding across the course
(alongside Module 3, 7 (x2), 8, and 11's discrepancies) — and arguably
the most valuable, since it's a genuine security-relevant design flaw
in a tool meant to catch exactly this kind of attack, caught through
rigorous testing rather than assumed to be correct because it "seemed
right."
