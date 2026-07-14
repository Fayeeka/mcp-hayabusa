# Severity Guide

`level:` must be one of `low`, `medium`, `high`, `critical` (see
`SKILL.md` standard #2). This project doesn't use `informational` for
active detections — reserve that for pure telemetry/enrichment rules
that aren't meant to page anyone.

Severity is about **blast radius and confidence**, not just "how bad
the technique sounds." Ask two questions:

1. **If this fires and it's a true positive, how much damage is
   already done?** (scope: one account vs. one host vs. the whole
   domain)
2. **How likely is a legitimate process to produce this exact
   signal?** (a rule that's 100% certain when it fires can be one
   level higher than one that needs a human to rule out noise)

## critical

Use when a true positive means **domain-wide or irreversible**
compromise, or the signal has **no realistic benign explanation**.

- `dcsync_replication_request.yml` — a successful DCSync yields the
  krbtgt hash, enabling golden ticket forgery. That's domain-wide,
  not single-account.
- `lsass_memory_access_comsvcs_minidump.yml` — `rundll32.exe` invoking
  `comsvcs.dll,MiniDump` against LSASS has no common legitimate use;
  when it fires, it's very likely a real dump attempt, and a
  successful one exposes every logged-on user's credentials.

## high

Use when a true positive is a **strong precursor to compromise** but
either the blast radius is narrower than domain-wide, or there's a
plausible (if uncommon) legitimate explanation that needs to be ruled
out.

- `lsass_memory_access_procdump.yml` — the GrantedAccess values are a
  strong signal, but EDR/AV agents can request similar access
  legitimately, so it's not "no benign explanation" territory.
- `sam_hive_dump.yml` — SAM hashes are scoped to local accounts, not
  the whole domain (unlike DCSync/NTDS), so it's bounded unless
  combined with local password reuse elsewhere.
- `pass_the_hash_ntlm_logon.yml` — an empty/spoofed workstation name
  on an NTLM logon is suspicious, but some legacy apps and proxies
  produce the same pattern.

## medium

Use when the signal is a **real but noisy** indicator — something
worth a human looking at, but with a non-trivial legitimate-cause
rate, usually because it's threshold/volume-based or depends on
environment-specific configuration.

- `kerberoasting_many_service_tickets.yml` — a >15/5min ticket-request
  threshold is a good heuristic, but batch jobs, backup software, and
  scanners can also produce ticket floods.
- `kerberoasting_service_ticket_request.yml` — an RC4-encrypted TGS
  request is a strong Kerberoasting indicator, but legacy
  applications or misconfigured accounts without AES support can
  trigger it too.

## low

Use for things worth recording and correlating (e.g. in a larger
detection chain or threat-hunting query) but that, on their own, are
too common or too weak a signal to justify triage as an alert. This
project doesn't currently have a `low` example — if you're reaching
for it, double check the signal isn't actually `informational`
(pure telemetry, not a detection) instead.

## Anti-patterns

- **Don't** set `critical` just because the ATT&CK technique sounds
  scary (e.g. "credential access" in the title). Severity is about
  *this specific rule's* precision and blast radius, not the tactic.
- **Don't** set `high`/`critical` to compensate for a rule with weak
  selection logic that will be noisy in practice — fix the selection
  logic instead, or drop to `medium` and say why in the description.
- **Don't** leave severity unjustified. See `SKILL.md` standard #2 —
  every rule's `description:` must explain *why* that level was
  chosen, using the same reasoning style as the examples above.
