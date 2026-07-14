# Module 5 Reference: Skills

## 5.1 How Skills Work

### Auto-Activation

Skills are different from slash commands:

- **Slash commands** = You explicitly invoke with `/command-name`
- **Skills** = Claude automatically activates when context matches OR invoked with a `/skill-name` notation, similar to a slash command

Put another way, slash commands are only invoked manually and skills can be invoked automatically through prompting/conversation or manually.

Claude reads the skill's description and decides: "Does this skill apply to what the user is asking?" If yes, Claude loads and follows the skill's instructions.

### Skill Structure

```
.claude/skills/
└── detection-engineering/
    ├── SKILL.md           # Required: instructions + trigger description
    ├── scripts/            # Optional: validation scripts
    │   └── validate-rule.py
    └── references/         # Optional: standards, examples
        ├── sigma-format.md
        └── example-rules/
```

### The SKILL.md File

Every skill needs a `SKILL.md` with two parts:

1. **YAML frontmatter** - Name and trigger description
2. **Markdown content** - The actual instructions

Example YAML frontmatter:

```yaml
---
name: detection-engineering
description: Detection rule development standards for this team. 
  Activate when writing Sigma rules, reviewing detection logic,
  or discussing detection coverage and gaps.
---
```

Corresponding markdown instructions:

```markdown
# Detection Engineering Standards

When working with detection rules, always:
1. Include ATT&CK technique mapping (TID format)
2. Document severity with justification
3. List known false positive conditions
4. Provide at least one test case

[... rest of instructions ...]
```

### The Trigger Description

The `description` field is critical — it's what Claude uses to decide whether to activate the skill. Make it:

- **Specific**: "Sigma rules, detection logic, coverage gaps" not just "security stuff"
- **Action-oriented**: "Activate when writing, reviewing, discussing..."
- **Pushy**: Don't be shy — tell Claude when to use it

## 5.2 Building the Detection Engineering Skill

Now that we have the theoretical background on skills, let's build a skill that enforces your team's detection standards.

### Create the Skill Directory

In your detection project (or create a new one):

```bash
cd ~/mcp-detection-kb  # or your project
claude
```

Prompt Claude to create the skill structure:

```
Create a .claude/skills/detection-engineering/ directory with a SKILL.md file.

The skill should enforce these detection rule standards:
1. Every rule must have ATT&CK technique mapping (attack.tXXXX format)
2. Severity must be one of: low, medium, high, critical - with justification
3. False positive conditions must be documented
4. At least one test case is required
5. Rule names should be lowercase with underscores

The trigger description should activate when:
- Writing or creating Sigma rules
- Reviewing detection rules
- Discussing detection coverage
- Working with YAML detection files
```

Review the generated `SKILL.md` file. If you have trouble finding it, you can just ask Claude to give you the full path. Claude creates both the YAML frontmatter (the trigger description) and the markdown content (the actual standards). You can edit this file to match your team's specific requirements — this is your methodology, so customize it.

A small tip: if you are working on a Mac or Linux host and are looking at these files via terminal, check out `bat`, which supports syntax highlighting.

### Test the Skill

Exit and restart Claude Code to load the new skill:

```
/exit
claude
```

Now test that the skill activates:

```
Write a Sigma rule to detect LSASS memory access via MiniDump
```

If you still have your Hayabusa MCP loaded, you might need to tweak the prompt to:

```
Write a Sigma rule to detect LSASS memory access via MiniDump - don't check for existing coverage, just write the rule
```

If that doesn't work, make sure Claude is aware of your newly created skill:

```
!ls -la .claude/skills/detection-engineering/
```

Claude should automatically apply your standards — producing a rule with ATT&CK mapping, severity justification, false positives, and test cases without you asking.

If the skill doesn't activate, check:

- Is `SKILL.md` in `.claude/skills/detection-engineering/`?
- Is the YAML frontmatter valid?
- Is the trigger description specific enough?
- Try listing the skill directory: run `!ls -la .claude/skills/detection-engineering/` — sometimes Claude needs to "see" the skill files before it becomes aware of them
- Did you restart Claude Code after creating the skill?

## 5.3 Making Skills Activate Reliably

### Trigger Description Patterns

Too vague (won't activate reliably):

```yaml
description: Security detection stuff
```

Too narrow (misses relevant contexts):

```yaml
description: Only when user says "create a Sigma rule"
```

Just right (specific + comprehensive):

```yaml
description: |
  Detection rule development standards. Activate when:
  - Writing, creating, or modifying Sigma/YARA rules
  - Reviewing detection rules for quality or completeness
  - Discussing detection coverage, gaps, or improvements
  - Working with YAML files containing detection logic
  - Asked to validate, check, or audit detection rules
  - Converting detections between formats (Sigma to KQL, SPL, etc.)
```

### Multiple Activation Phrases

List several ways users might invoke this context:

```yaml
description: |
  Incident response procedures. Activate when:
  - Investigating security alerts or incidents
  - User mentions "IR", "incident", "breach", "compromise"
  - Analyzing suspicious activity across log sources
  - Building investigation timelines
  - Documenting findings for incident reports
```

### Testing Activation

Try different prompts to see if the skill activates:

```
# Should activate
Write a detection rule for credential theft

# Should activate  
Review this Sigma rule for completeness

# Should activate
What ATT&CK techniques should I map this to?

# Should NOT activate 
What's the weather like?
```

If activation is inconsistent, refine the trigger description.

## 5.4 Adding Validation Scripts

Skills can include scripts that Claude runs to validate work.

### Create a Validation Script

Prompt Claude:

```
Create a scripts/validate-rule.py in the detection-engineering skill that:
1. Takes a YAML file path as argument
2. Parses the Sigma rule
3. Checks for:
   - ATT&CK tags present (attack.tXXXX pattern)
   - Valid severity level
   - False positives section exists
   - At least one test case comment
4. Returns JSON with validation results and any issues found
```

### Reference the Script in SKILL.md

Update your `SKILL.md` to mention the validation script:

```markdown
---
name: detection-engineering
description: |
  Detection rule development standards. Activate when writing, 
  reviewing, or validating Sigma rules.
---

# Detection Engineering Standards

[... existing content ...]

## Validation

After creating or modifying a rule, validate it:

python .claude/skills/detection-engineering/scripts/validate-rule.py path/to/rule.yml

This checks all requirements and reports any issues.
```

Now when Claude writes rules, it knows to validate them with your script.

### Worked Example

Using this Sigma rule from the official Sigma repo as a validation target:

```yaml
title: Applications That Are Using ROPC Authentication Flow
id: 55695bc0-c8cf-461f-a379-2535f563c854
status: test
description: |
    Resource owner password credentials (ROPC) should be avoided if at all possible as this requires the user to expose their current password credentials to the application directly.
    The application then uses those credentials to authenticate the user against the identity provider.
references:
    - https://learn.microsoft.com/en-us/entra/architecture/security-operations-applications#application-authentication-flows
author: Mark Morowczynski '@markmorow', Bailey Bercik '@baileybercik'
date: 2022-06-01
tags:
    - attack.t1078
    - attack.defense-evasion
    - attack.persistence
    - attack.privilege-escalation
    - attack.initial-access
logsource:
    product: azure
    service: signinlogs
detection:
    selection:
        properties.message: ROPC
    condition: selection
falsepositives:
    - Applications that are being used as part of automated testing or a legacy application that cannot use any other modern authentication flow
level: medium
```

Put it somewhere Claude can access, then ask Claude to validate it using the detection engineering skill (which includes the validation script from above):

```
validate the azure_app_ropc_authentication.yml sigma rule against our detection engineering standards
```

If you haven't used the skill before, Claude will load it automatically and ask permission to use it.

This confirms the validation script and skill are both functional. The key point: we're not just letting Claude write Sigma rules from scratch — we're forcing it to use our own internal standard, best practices, and conventions. The combination of natural language instructions and the ability to run custom scripts make skills a very powerful tool. Skills can be shared as well.

## 5.5 Adding Reference Documents

Skills can include reference docs Claude reads when the skill activates.

### Add Example Rules

Create a `references/` directory with examples. Prompt Claude:

```
Create a references/ directory in the detection-engineering skill with:
1. example-rules/lsass_memory_access.yml - A properly formatted example
2. severity-guide.md - When to use each severity level
3. false-positive-patterns.md - Common FP patterns to document
```

Then add a References section to your `SKILL.md` file — or have Claude do it for you:

```markdown
## References

When writing rules, consult:
- `references/example-rules/` - Well-formatted examples to follow
- `references/severity-guide.md` - Severity level guidance
- `references/false-positive-patterns.md` - Common FP documentation
```

Now Claude will reference the above when invoking the skill.

## 5.6 Installing Third-Party Skills

So far in this module, we've built our own skills. But there's a growing ecosystem of community and vendor-created skills you can install and use. This section covers how to find, evaluate, and install third-party skills safely, using the [trailofbits/skills](https://github.com/trailofbits/skills) GitHub repo as an example.

### Plugin Marketplaces

Claude Code distributes skills through plugin marketplaces — GitHub repositories that bundle skills, commands, and other extensions.

#### Adding a Marketplace

To add the Trail of Bits marketplace:

```
/plugin marketplace add trailofbits/skills
```

This registers the marketplace. Now browse available plugins:

```
/plugin menu
```

You'll see a list of available skills organized by category:

- Smart contract security
- Code auditing
- Reverse engineering
- Verification
- And more

### Example: The YARA-Authoring Skill

Let's walk through installing and using a real third-party skill: `yara-authoring` from Trail of Bits.

#### What It Does

The `yara-authoring` skill guides you in writing high-quality YARA-X detection rules. It includes:

- Expert heuristics for string selection and atom quality
- Decision trees for common judgment calls
- Validation scripts for rule linting
- Best practices from VirusTotal's production systems

#### Installing

```bash
# Add the Trail of Bits marketplace (if not already added)
/plugin marketplace add trailofbits/skills

# Install the yara-authoring plugin
/plugin install yara-authoring
```

#### Prerequisites

The `yara-authoring` skill requires YARA-X (the Rust-based successor to legacy YARA) for its validation scripts to work:

```bash
# macOS
brew install yara-x

# Or from source (requires Rust)
cargo install yara-x

# Verify installation
yr --version
```

Without YARA-X installed, the skill's guidance will still work, but commands like `yr scan`, `yr check`, and the validation scripts (`yara_lint.py`, `atom_analyzer.py`) will fail.

#### Using the Skill

Once installed, the skill auto-activates when you work on YARA rules, just like the custom skills built earlier in this module:

```
Write a YARA rule to detect Cobalt Strike beacon payloads
```

Claude will apply the yara-authoring methodology:

- Selecting strings that generate good atoms
- Avoiding common pitfalls
- Following naming conventions
- Adding proper metadata

The skill also includes validation scripts:

```bash
# Lint a YARA rule
uv run yara_lint.py rule.yar

# Analyze atom quality
uv run atom_analyzer.py rule.yar
```

### Security Evaluation for Third-Party Skills

Before tinkering too much with third-party skills, it's important to recall that:

> **Skills can execute code on your system.** Before installing any third-party skill, evaluate it for security issues.

#### What Skills Can Do

A skill can include:

- Scripts that Claude executes (Python, bash, etc.)
- Hooks that run automatically on events (`SessionStart`, `PreToolUse`, etc.)
- MCP servers that have network access and file system access
- Commands that execute arbitrary workflows

Before installing a skill, it's always worth checking what scripts, hooks, commands, and MCP servers are bundled with it, so as to avoid unwanted or potentially malicious code running on your system.

You can even use Claude for this task — ask it to review a third-party skill for security issues before installing.

#### Evaluation Checklist

**1. Source Reputation**

| Check | What to Look For |
|---|---|
| Publisher | Known security company? Individual with track record? |
| Repository | Stars, forks, recent activity, open issues |
| License | Permissive license? Clear terms? |
| Contributors | Real profiles with history, or anonymous/new accounts? |

**2. Review the SKILL.md**

Read the skill's instructions:

```bash
# Clone the repo locally first
git clone https://github.com/trailofbits/skills
cd skills/plugins/yara-authoring

# Read the skill definition
cat SKILL.md
```

Look for:
- Clear, legitimate purpose
- No instructions to disable security features
- No requests for sensitive data (API keys, credentials)
- No obfuscated or encoded content

**3. Audit Scripts**

If the skill includes scripts, read them:

```bash
# List all scripts
find . -name "*.py" -o -name "*.sh" -o -name "*.js"

# Read each one
cat scripts/*.py
```

Red flags to keep an eye out for:
- Network requests to unknown domains
- File operations outside the project directory
- Encoded/obfuscated code (base64, eval, exec)
- Credential harvesting patterns
- Subprocess calls with user input

**4. Check Hooks**

Hooks run automatically — they're the highest-risk component:

```bash
# Check for hook configurations
cat .claude-plugin/manifest.json
# or
cat plugin.json
```

Review any hooks carefully:
- `SessionStart` hooks run every time you start Claude Code
- `PreToolUse` hooks can intercept and modify commands
- `PostToolUse` hooks see all tool outputs

A legitimate hook might auto-format code. A malicious hook might exfiltrate every file you read.

**5. Verify MCP Servers**

If the skill includes an MCP server:

```bash
# Find MCP server code
find . -name "*.py" | xargs grep -l "mcp\|FastMCP"

# Review the server
cat path/to/mcp_server.py
```

Check:
- What tools does it expose?
- Does it make network requests?
- What file system access does it need?
- Are there any hardcoded URLs or IPs?

**6. Test in Isolation**

For skills you're uncertain about:

```bash
# Create a throwaway directory
mkdir ~/skill-test
cd ~/skill-test

# Install and test there
claude
/plugin install suspicious-skill

# Test with non-sensitive data
# Monitor network activity if paranoid
```

#### Quick Security Assessment

| Risk Level | Criteria | Action |
|---|---|---|
| Low | Known publisher, no scripts/hooks, read-only skill | Install freely |
| Medium | Known publisher, has scripts, clear purpose | Review scripts, then install |
| High | Unknown publisher, has hooks or MCP servers | Full audit before installing |
| Critical | Obfuscated code, requests credentials, unknown network calls | Do not install |

### Uninstalling Skills

If you decide a skill isn't for you:

```
/plugin uninstall yara-authoring
```

Or remove the entire marketplace:

```
/plugin marketplace remove trailofbits/skills
```

## 5.7 Skill Organization Patterns

### Pattern 1: Single Comprehensive Skill

One skill covering a broad domain:

```
.claude/skills/
└── security-operations/
    ├── SKILL.md           # IR, detection, threat hunting
    ├── scripts/
    └── references/
```

**Pros:** Simple, one place for everything
**Cons:** May activate when not needed

### Pattern 2: Multiple Focused Skills

Separate skills for different activities:

```
.claude/skills/
├── detection-engineering/
│   └── SKILL.md           # Rule writing standards
├── incident-response/
│   └── SKILL.md           # IR procedures
└── threat-hunting/
    └── SKILL.md           # Hunting methodology
```

**Pros:** Precise activation, focused instructions
**Cons:** More files to maintain

### Pattern 3: Layered Skills

Base skill + specialized extensions:

```
.claude/skills/
├── security-base/
│   └── SKILL.md           # Core standards, terminology
├── detection-sigma/
│   └── SKILL.md           # Sigma-specific (references security-base)
└── detection-kql/
    └── SKILL.md           # KQL-specific (references security-base)
```

**Pros:** Avoids repetition, specialized
**Cons:** More complex
