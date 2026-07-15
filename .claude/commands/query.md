---
description: Scan an EVTX file with Hayabusa, map findings to ATT&CK techniques, check detection coverage, and generate an Obsidian-compatible investigation note
argument-hint: [target_file] [min_severity]
---

Run an EVTX investigation workflow and produce an Obsidian-ready note.

Arguments:
- `$1` (required) - path to a text file containing the path of the EVTX file to investigate. The text file holds the EVTX path on its first non-blank line (this stands in for a Splunk SPL query file, since scanning is done locally via Hayabusa instead of a live SIEM).
- `$2` (optional) - minimum severity to include: `informational`, `low`, `medium`, `high`, or `critical`. Default to `medium` if not given.

Steps:

1. Read `$1` and extract the EVTX file path from its contents.
2. Call the `scan_evtx` MCP tool with `path` set to that EVTX file path and `min_severity` set to `$2` (or `medium` if `$2` was not given). Use `output_format: "full"` so MITRE fields are available.
3. Analyze the returned findings for suspicious patterns: which rules fired most often, which hosts/channels are involved, any high/critical severity findings that stand out.
4. Map findings to ATT&CK techniques:
   - For each distinct `RuleTitle` in the findings, call `get_hayabusa_rules` with `keyword` set to that title to retrieve the matching rule's `tags`.
   - Extract technique IDs from tags matching `attack.tXXXX` or `attack.tXXXX.XXX`, normalized to `TXXXX`/`TXXXX.XXX` form.
   - Build a deduplicated list of all techniques observed in this scan.
5. For each technique found, call `analyze_coverage` with `technique_or_tactic` set to the technique ID (default `rule_source: "custom"`) to determine whether one of our own Sigma rules already covers it.
6. Generate a single Obsidian-compatible markdown document with:
   - YAML frontmatter: `date` (today, ISO format), `tags` (include `investigation` plus one tag per technique, e.g. `t1003-001`), `techniques` (list of technique IDs found), `status` (`needs-review`).
   - A `[[TXXXX.XXX]]`-style backlink for every technique found (e.g. `[[T1003.001]]`), placed inline wherever that technique is discussed.
   - A **Findings Summary** section: prose summary of what fired and why it matters.
   - A **Detection Coverage** table with columns `Technique`, `Status` (`Covered` or `Gap`), `Rule` (our matching rule name, or `No rule found`) - one row per technique from step 5.
   - A **Scan Parameters** section: the EVTX path scanned, `min_severity` used, and the result count (`returned` vs total `count` from `scan_evtx`).
   - An **Analyst Notes** section left blank (a placeholder heading) for the human investigator to fill in.
7. Save the document to `investigations/` (create the directory if it doesn't exist), named `investigations/<date>-<short-slug>.md`, where `<short-slug>` is a short kebab-case description derived from the top finding or EVTX filename.
8. Report back the path of the file you wrote and a one-line summary of what was found.
