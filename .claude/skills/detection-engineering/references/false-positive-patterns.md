# False Positive Patterns

`falsepositives:` must be present and non-empty (`SKILL.md` standard
#3), but "non-empty" isn't the bar — a placeholder like `- Unknown`
or `- None known` doesn't help an analyst triage an alert at 2am.
Name the *specific* tool, process, or workflow that could produce the
same signal, not a vague category.

Bad: `- Legitimate admin activity`
Good: `- Windows Server Backup or Veeam saving the SAM/SYSTEM hives as part of a scheduled system state backup`

Below are the recurring patterns across this project's rules — use
them as a checklist when writing `falsepositives:` for a new rule, but
always make the entry specific to *your* selection logic, not a copy
of the pattern name.

## Backup / imaging software

Anything that legitimately reads or exports the exact data your rule
flags as suspicious when a human/attacker does it manually.

- `dcsync_replication_request.yml` — legitimate Domain Controllers and
  Azure AD Connect / Entra Connect servers perform real AD
  replication; the rule's `filter_known_dcs` excludes machine
  accounts, but third-party sync tools running under a user account
  won't be caught by that filter.
- `sam_hive_dump.yml` — Windows Server Backup, Veeam, Acronis, and
  similar tools save the SAM/SYSTEM/SECURITY hives as part of routine
  system-state backups.

## EDR / antivirus agents

Security tooling often needs the same access rights or performs the
same actions as the attack technique it's meant to detect.

- `lsass_memory_access_procdump.yml` — EDR and AV agents request
  similar `GrantedAccess` rights when scanning LSASS memory for
  known-bad injected code. The rule's `filter_known_edr` covers common
  install paths, but isn't exhaustive — say so in the description
  rather than implying the filter is complete.

## Legacy protocols / applications

Older software that hasn't been updated to modern auth standards
produces patterns that look identical to a downgrade attack.

- `kerberoasting_service_ticket_request.yml` — legacy applications or
  devices without AES support request RC4-encrypted tickets as their
  *only* option, not as an attacker-forced downgrade.
- `pass_the_hash_ntlm_logon.yml` — legacy applications and some
  load balancers/proxies strip or don't populate the workstation name
  field on NTLM logons, mimicking a Pass-the-Hash indicator.

## Administrative troubleshooting

The same action a real attacker takes is sometimes exactly what a
sysadmin does on purpose during an incident, migration, or debugging
session.

- `lsass_memory_access_comsvcs_minidump.yml` / `example-rules/lsass_memory_access.yml`
  — an admin manually dumping LSASS (via Task Manager, ProcDump, etc.)
  for legitimate troubleshooting produces an identical signal to an
  attacker doing the same thing. Document it, but don't use it to
  justify lowering severity — the point of the false positive list is
  faster triage, not fewer alerts.

## Volume / threshold noise

Anything detected by counting events in a window will have a
legitimate-cause tail: automation, scanners, and bulk service
operations all generate volume.

- `kerberoasting_many_service_tickets.yml` — batch jobs, backup
  software, vulnerability scanners, and domain controllers servicing
  many clients can all generate high ticket-request volume from a
  single source in a short window.

## Adding a new pattern

If you document a false positive that doesn't fit any pattern above,
add a new `##` section here once you've seen it recur across 2+
rules — a one-off doesn't need a pattern, just a good specific entry
in that rule's `falsepositives:` list.
