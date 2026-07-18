## Summary

Per the hooks documentation, a PostToolUse hook that exits with code 2
should have its stderr fed back to Claude as context — the expectation
is that Claude sees the feedback automatically on its next turn, with
no manual polling required. In testing, this did not happen: a
validation hook correctly detected an invalid file and exited 2, but
neither Claude's conversational response nor `--debug-file` debug
output surfaced the failure or its exit code.

## Environment

- OS: Windows 11 Home, build 10.0.26200
- Shell: PowerShell 7 (primary), Git Bash also used for POSIX-style commands
- Claude Code version: 2.1.211 (`cc_version=2.1.211.2b9` per debug log attribution header)
- Hook interpreter: `bash` (via Git Bash), hook script uses `python`/`python3` for YAML parsing

## Expected behavior (per docs)

- PostToolUse hook exit code 2 → stderr is shown to Claude as feedback (tool already ran, can't be undone, but Claude should see and can act on the result).
- This is documented as the mechanism that removes the need for "manual triggers" or "hoping Claude remembers" to check validation output.

## Observed behavior

1. Claude wrote `rules/test-rule.yml` containing only `title: Test Rule` (deliberately incomplete — missing `description` and an `attack.t*` ATT&CK tag).
2. The configured PostToolUse hooks (`scripts/log-edit.py` and `scripts/validate-rule.sh`, wired via `.claude/settings.json` with matcher `Edit|Write`) fired — confirmed via `hook-test.log`, which logged the write event.
3. `scripts/validate-rule.sh` correctly detected the missing fields and printed errors to stderr, exiting with code 2 (verified independently by manually piping the same tool-call JSON into the script):
   ```
   $ echo '{"tool_input": {"file_path": "rules/test-rule.yml"}}' | bash scripts/validate-rule.sh
   Sigma rule validation FAILED for rules/test-rule.yml:
   - missing 'description' field
   - 'tags' does not contain an 'attack.t*' ATT&CK technique entry
   exit: 2
   ```
4. Despite this, Claude's next conversational response after the original Write made **no mention** of any validation failure. The failure only surfaced when the user explicitly asked Claude to check `hook-test.log` and re-run the validation script manually.
5. Asked directly, Claude confirmed it did not see any stderr feedback in its context for that tool call.

## Debug log investigation

To rule out an environment-specific quirk, ran two nested, non-interactive sessions with debug logging enabled, each recreating the write to a `rules/*.yml` file:

```
claude --debug-file /tmp/claude-debug.log -p "Create a file rules/debug-test-invalid.yml containing exactly: title: Test Rule" --allowedTools "Write"
claude -d hooks --debug-file /tmp/claude-debug2.log -p "Create a file rules/debug-test-invalid2.yml containing exactly: title: Test Rule" --allowedTools "Write"
```

(Second run explicitly selected the `hooks` debug category to rule out a default-filter gap.)

**Finding:** in both logs, the only trace of the PostToolUse hooks executing is two identical lines immediately after `tool_dispatch_end tool=Write`:

```
[DEBUG] Hook output does not start with {, treating as plain text
[DEBUG] Hook output does not start with {, treating as plain text
```

One line per configured hook (`log-edit.py`, `validate-rule.sh`) — confirming both ran — but **no `exitCode`, `PostToolUse`, or `stderr` field is logged alongside either line, in either run.** The actual exit code (2) is not observable anywhere in `--debug-file` output.

### Red herring ruled out

Both logs also contain:
```
[DEBUG] Registered 0 hooks from 0 plugins
[DEBUG] Hooks: Found 0 total hooks in registry
```
This initially looked like the project's hooks never loaded. On closer inspection, this registry refers to **plugin-supplied** hooks only, a separate subsystem from `settings.json`-configured hooks. The log separately confirms `.claude/settings.json` is being watched (`Watching for changes in setting files ...`), and the two "plain text" hook-output lines are direct evidence the project-level hooks did execute. Filing this here in case the log wording is worth clarifying too, since it's easy to misread as "hooks aren't registered."

## Impact

The core value proposition of PostToolUse hooks — "no manual triggers, no hoping Claude remembers" — doesn't fully hold in this environment. The hook infrastructure works (script runs, detects the issue, exits 2 as designed), but:

- Claude does not reliably narrate the failure without being explicitly asked to check.
- There's no way to verify the exit code via `--debug-file` either, making it hard to confirm from tooling alone whether the documented feedback path is firing at all.

## Suggested follow-ups

- Confirm whether exit-2 stderr injection into Claude's context is expected to work reliably on Windows / this Claude Code version, or if there's a known gap.
- Consider logging the hook's exit code and stderr content (not just "starts with `{` or not") in `--debug-file` output, so this kind of investigation doesn't require a separate manual repro.
- Consider clarifying the "Found 0 total hooks in registry" log line to distinguish plugin-hook registry state from project `settings.json` hook state, since it currently reads as evidence hooks aren't loaded.

## Reproduction steps

1. Add a PostToolUse hook in `.claude/settings.json` (matcher `Edit|Write`) that always exits 2 with a message to stderr.
2. Have Claude write/edit a file matching the hook's target pattern.
3. Observe Claude's next conversational turn — no mention of the hook's stderr output.
4. Re-run the hook script manually against the same file/input to confirm it does produce exit 2 and a stderr message.
5. Optionally, repeat via `claude --debug-file <path> -p "<prompt>"` and grep the log for exit-code/stderr detail — none is present.
