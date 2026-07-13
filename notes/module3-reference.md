## 3.8 What You Built In This Module

```
mcp-hayabusa/
├── CLAUDE.md              # Project context
├── requirements.txt       # Dependencies
├── server.py              # MCP server
├── hayabusa/               # Hayabusa binary
├── samples/                # Test EVTX files
└── .mcp.json               # MCP registration (note: actual location differs
                              from the course's .claude/settings.json diagram)
```

An MCP server that:
- Wraps Hayabusa for EVTX analysis
- Supports severity filtering and rule selection
- Returns structured results Claude can analyze
- Works with both Claude Code and Claude Desktop

More importantly, this taught the pattern for wrapping any CLI tool.

## 3.9 Applying This Elsewhere

The wrapper pattern applies to any CLI tool used regularly:

**Forensics workflow:**
- Wrap Volatility for memory analysis
- Wrap strings/binwalk for binary analysis
- Wrap exiftool for metadata extraction

**Detection engineering:**
- Wrap Sigma CLI to compile rules
- Wrap YARA to run rule scans
- Wrap your SIEM's CLI for query execution

**Threat intelligence:**
- Wrap IOC lookup tools
- Wrap WHOIS/DNS tools
- Wrap reputation checking APIs

**The "alt-tab test":** When deciding whether a tool needs to be wrapped in an
MCP server, ask "What tools do I alt-tab to repeatedly?" Those are candidates
for MCP wrappers. Think of an MCP as an AI-native interface to your favorite
tool of choice, similar to what an API is to a web application.
