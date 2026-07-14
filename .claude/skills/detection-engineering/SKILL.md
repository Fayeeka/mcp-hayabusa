---
name: detection-engineering
description: |
  Detection rule development standards for this team's Sigma rules. Activate when:
  - Writing or creating Sigma rules
  - Reviewing detection rules for quality or completeness
  - Discussing detection coverage, gaps, or improvements
  - Working with YAML files containing detection logic (rules/*.yml)
  - Asked to validate, check, or audit a detection rule
---

# Detection Engineering Standards

This project maintains hand-authored Sigma rules in `rules/` (see the
`detection://rules` MCP resources and the `analyze_coverage` /
`suggest_rule` tools in `server.py`). Every rule placed in `rules/`
must meet all five standards below before it's considered done —
whether it was written from scratch, edited, or started as a
`suggest_rule` draft template.

## 1. ATT&CK Technique Mapping

`tags:` must include at least one technique tag in `attack.tXXXX` or
`attack.tXXXX.XXX` format (lowercase, e.g. `attack.t1003.002`). Prefer
the most specific sub-technique available over the parent technique.
Also include the relevant tactic tag(s) (e.g. `attack.credential-access`)
alongside the technique tag — this project's existing rules do both:

```yaml
tags:
    - attack.credential-access
    - attack.t1003.002
```

A rule with no `attack.t*` tag is not acceptable — coverage tooling
(`analyze_coverage`, `suggest_rule`) depends on this tag to find the
rule at all.

## 2. Severity With Justification

`level:` must be exactly one of: `low`, `medium`, `high`, `critical`.

The choice of severity must be justified, not just asserted. Justify it
in the `description:` field (a sentence explaining why this level was
chosen — e.g. "critical because this is a direct precursor to full
domain compromise" or "medium because high-volume ticket requests are
suspicious but have legitimate causes"). Don't leave severity
unexplained.

## 3. False Positive Conditions

`falsepositives:` must be present and non-empty, with specific,
realistic conditions — not a placeholder like `- Unknown`. Think about
what legitimate admin tools, backup software, or business processes
could trigger the same selection, and name them.

## 4. Test Case

Every rule must document at least one concrete test case: a realistic
command line, event field value, or log snippet that would trigger the
detection. Add it as a YAML comment directly above `detection:`, e.g.:

```yaml
# Test case:
#   reg.exe save hklm\sam C:\temp\sam.hive
detection:
    ...
```

This is what someone would run (or what an EVTX/log record would
contain) to confirm the rule actually fires — not a restatement of the
Sigma logic in prose.

## 5. Naming Convention

Rule filenames must be lowercase with underscores, no spaces or
hyphens: `sam_hive_dump.yml`, not `SAM-Hive-Dump.yml` or
`sam hive dump.yml`. The `id:` field must be a fresh UUIDv4, not reused
from another rule.

## Checklist

Before treating a rule as finished, confirm:

- [ ] `tags:` includes an `attack.tXXXX[.XXX]` technique tag (most specific available)
- [ ] `tags:` includes the matching tactic tag(s)
- [ ] `level:` is one of low/medium/high/critical
- [ ] `description:` explains *why* that severity was chosen
- [ ] `falsepositives:` lists specific, realistic conditions
- [ ] A `# Test case:` comment block sits above `detection:` with a concrete trigger example
- [ ] Filename is lowercase_with_underscores.yml
- [ ] `id:` is a unique UUIDv4

If a rule is missing any of these, say so explicitly and fix it rather
than treating it as done.
