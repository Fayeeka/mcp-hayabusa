# Module 4 Reference: MCP Resources (Detection Knowledge Base)

## 4.1 Resources vs. Tools

| Aspect | Tools | Resources |
|---|---|---|
| Purpose | Do something | Read something |
| Direction | Claude → External action | External data → Claude |
| Examples | Run scan, execute query | Read rules, browse ATT&CK |
| Side effects | Can modify state | Read-only |
| Invocation | Claude calls with parameters | Claude reads URI |

**Tools** = "Claude, do this thing"
**Resources** = "Claude, here's data you can read"

### When to Use Resources
- Reference documentation Claude should know
- Structured data (rules, configs, mappings)
- Knowledge bases that change over time
- Anything you'd otherwise paste into chat repeatedly

### Resource URIs

Resources are identified by URIs (like URLs) — you design the structure:

```
detection://rules/sigma/credential-access/lsass_memory_access
detection://attack/techniques/T1003.001
detection://playbooks/credential-theft-response
```

Claude browses these like a filesystem, reading what it needs.

## 4.2 Setting Up the Knowledge Base

Extends the Hayabusa MCP server from Module 3, adding resources that expose:
- Sigma detection rules
- ATT&CK technique mappings
- Detection coverage analysis

### Project Structure

If continuing Module 3's project:
```
cd ~/mcp-hayabusa
claude
```

If starting fresh:
```
mkdir ~/mcp-detection-kb
cd ~/mcp-detection-kb
claude
/init
```

### CLAUDE.md content to add:

```
Update the existing project, in addition to the current functionality, this
project is an MCP server providing a detection engineering knowledge base.

Goals:
- Expose Sigma rules as browsable resources
- Expose ATT&CK technique mappings
- Allow Claude to query detection coverage
- Combine with Hayabusa scanning from Module 3

Structure:
- rules/ - Sigma detection rules (YAML)
- mappings/ - ATT&CK technique to rule mappings
- server.py - MCP server with resources and tools
```

### Get Sample Rules

Prompt: "Create a rules/ directory with 5-6 sample Sigma rules covering:
LSASS memory access (T1003.001), Kerberoasting (T1558.003), DCSync
(T1003.006), Pass-the-Hash (T1550.002). Use realistic Sigma format with
proper ATT&CK tags."

Or clone real rules: `git clone https://github.com/SigmaHQ/sigma.git sigma-rules`

## 4.3 Adding Resources to the MCP Server

### Resource Structure

Resources in MCP have:
- **URI** — Unique identifier (like `detection://rules/lsass`)
- **Name** — Human-readable name
- **Description** — What the resource contains
- **MIME type** — Content type (usually `text/plain` or `application/json`)

### Basic Resource Implementation

Prompt:
```
Add MCP resources to server.py that expose our Sigma rules.

Create these resource endpoints:
1. detection://rules - List all available rules
2. detection://rules/{rule_name} - Get a specific rule's content
3. detection://rules/by-technique/{technique_id} - List rules for a technique

Use the rules/ directory as the data source.
```

Example implementation:

```python
from mcp.types import Resource

@server.list_resources()
async def list_resources():
    resources = []

    # Root: list all rules
    resources.append(Resource(
        uri="detection://rules",
        name="Detection Rules",
        description="Browse all Sigma detection rules",
        mimeType="application/json"
    ))

    # Individual rules
    rules_dir = Path(__file__).parent / "rules"
    for rule_file in rules_dir.glob("*.yml"):
        rule_name = rule_file.stem
        resources.append(Resource(
            uri=f"detection://rules/{rule_name}",
            name=rule_name,
            description=f"Sigma rule: {rule_name}",
            mimeType="text/yaml"
        ))

    return resources

@server.read_resource()
async def read_resource(uri: str):
    if uri == "detection://rules":
        rules = []
        for rule_file in rules_dir.glob("*.yml"):
            with open(rule_file) as f:
                rule = yaml.safe_load(f)
            rules.append({
                "name": rule_file.stem,
                "title": rule.get("title"),
                "techniques": extract_techniques(rule),
                "level": rule.get("level")
            })
        return json.dumps(rules, indent=2)

    if uri.startswith("detection://rules/"):
        rule_name = uri.replace("detection://rules/", "")
        rule_file = rules_dir / f"{rule_name}.yml"
        if rule_file.exists():
            return rule_file.read_text()
        return f"Rule not found: {rule_name}"
```

### Add ATT&CK Mapping Resource

Prompt:
```
Add a resource at detection://attack/techniques/{technique_id} that returns:
- Technique name and description
- Which of our rules detect this technique
- Coverage assessment (covered, partial, gap)
- You can find ATT&CK data in json format here: https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/enterprise-attack/enterprise-attack.json

Parse the ATT&CK tags from our Sigma rules to build this mapping.
```

## 4.4 Testing Resources

### Restart and Verify

```
/exit
cd ~/mcp-hayabusa
claude
/mcp
```

You should see resources listed alongside tools.

### Browse the Knowledge Base

Prompt: "What detection rules do we have available?" — Claude should browse
`detection://rules` and list your rules.

To use the real Hayabusa-bundled Sigma rules instead of a separate clone:
```
what detection rules are available from Hayabusa? the rules are here:
  /path/to/mcp-hayabusa/hayabusa/rules/sigma, make sure to search recursively
```

Try technique-based queries: "What rules do we have that detect T1003.001?"

### Test Coverage Questions

"Do we have detection coverage for Kerberoasting? What about DCSync?" —
Claude browses the knowledge base and gives real answers based on actual
rules.

## 4.5 Combining Resources and Tools

The real power comes from combining resources (knowledge) with tools (actions).

### Add a Coverage Analysis Tool

Prompt:
```
Add a tool called "analyze_coverage" that:
1. Takes an ATT&CK technique ID or tactic name
2. Reads our detection rules (from resources)
3. Identifies which techniques are covered vs. gaps
4. Returns a coverage report
```

Usage: "Analyze our detection coverage for the Credential Access tactic" —
Claude reads the rules resource, extracts ATT&CK mappings, compares against
known Credential Access techniques, and reports coverage and gaps.

**Note:** This isn't AI generating rules or making security decisions — it's
providing clear instructions over an already-generated, real dataset.

### Add a Rule Suggestion Tool

Prompt:
```
Add a tool called "suggest_rule" that:
1. Takes an ATT&CK technique ID
2. Checks if we already have coverage (via resources)
3. If not, suggests a detection approach
4. Optionally creates a rule template in rules/
```

This helps fill coverage gaps identified by resources. Claude cross-references
the technique against the existing rule set and links the ATT&CK ID to the
MITRE data source and detection strategy — referencing existing knowledge
bases rather than hallucinating.

## 4.6 Real-World Knowledge Base Patterns

### Pattern 1: Playbook Library

```
detection://playbooks - List all playbooks
detection://playbooks/credential-theft - Specific playbook
detection://playbooks/by-alert/{alert_name} - Playbook for an alert type
```

Claude can reference IR procedures during investigations.

### Pattern 2: Environment Context

```
detection://environment/hosts - Known hosts and roles
detection://environment/services - Critical services
detection://environment/baselines - Normal behavior baselines
```

Claude can factor in your environment when analyzing alerts.

### Pattern 3: Historical Investigations

```
detection://investigations - List past cases
detection://investigations/{case_id} - Case details
detection://investigations/by-technique/{tid} - Cases involving a technique
```

Claude can reference how similar incidents were handled before.

## Module 4 Wrap-Up Summary

Built a detection-engineering knowledge base on top of the Module 3
Hayabusa MCP server:
- 6 custom Sigma rules (LSASS, Kerberoasting x2, DCSync, Pass-the-Hash,
  plus a real SAM hive dump rule built via suggest_rule)
- Three MCP resources: detection://rules, detection://rules/{rule_name},
  detection://rules/by-technique/{technique_id}
- Two new tools: analyze_coverage (gap analysis vs. upstream Hayabusa
  corpus, with custom/upstream/combined modes) and suggest_rule
  (data-driven detection suggestions + real, Hayabusa-validated rule
  templates)
- Confirmed the full loop works: found a real gap (T1003.002, 3% custom
  coverage), generated a working draft, fleshed it into a real tested
  rule, re-ran analysis to confirm coverage improved (3.0% → 4.0%)

Key lesson: Resources = read-only knowledge Claude can browse (URIs).
Tools = actions with side effects. The real power is combining them —
Claude reasons over real data (never hallucinating rule content) and
uses tools to act on what it finds.

**Real-world extension patterns (not built, but the same approach applies):**
- Playbook library (detection://playbooks/...) — IR procedures Claude
  can reference during investigations
- Environment context (detection://environment/...) — host/service/
  baseline data so Claude's analysis is specific to your environment
- Historical investigations (detection://investigations/...) —
  institutional memory of past incidents

**Rule of thumb:** if you're repeatedly re-explaining the same background
context to Claude across conversations, that's a signal it belongs as a
Resource, not something re-typed each time.
