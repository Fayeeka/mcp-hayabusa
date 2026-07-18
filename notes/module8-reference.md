# Module 8 Reference: Complex Analysis - Threat Intel & Multi-Source Correlation

## Claude Ecosystem Coverage

| Component | Feature | How We'll Use It |
|---|---|---|
| Slash Commands | /ingest-ti | Threat intel ingestion and TTP extraction |
| Plan Mode | Shift+Tab | Investigation scoping and planning |
| Subagents | .claude/agents/ | Parallel analysis of endpoint vs cloud logs |
| /model | Model selection | Opus for complex TTP extraction |
| Web Search | Threat intelligence | Research IOCs and threat actors |
| /context | Context monitoring | Track usage during large investigations |
| /compact | Context management | Preserve findings across long sessions |
| LiteLLM + Ollama | Multi-model verification | Cross-check analysis with local models |

## External Tools

| Tool | Purpose | Install |
|---|---|---|
| defuddle-cli | Extract clean content from threat intel URLs | npm install -g defuddle-cli |
| LiteLLM | Multi-model proxy | pip install 'litellm[proxy]' |
| Ollama | Local model runtime | curl -fsSL https://ollama.com/install.sh \| sh |

## Overview

Previous modules built tools for specific tasks — parsing logs,
validating rules, running queries. This module tackles two complex
analysis challenges:

1. **Threat Intelligence Processing**: Turn a threat report URL into
   actionable TTPs and a simulation plan
2. **Multi-Source Correlation**: Correlate events across endpoint
   (Windows) and cloud (Azure) logs

Both require Claude to reason through complex, unstructured inputs.

By the end:
- A /ingest-ti command that processes threat intel reports into ATT&CK
  mappings and simulation plans
- Experience correlating Windows and cloud logs
- Patterns for using Opus on complex reasoning tasks
- Techniques for plan mode, subagents, and context management
- Multi-model verification workflow using LiteLLM and local models

## The Problem

### Problem 1: Threat Intel Reports Are Unstructured

A threat intel team shares a blog post about a new campaign. Need to:
- Extract the TTPs described
- Map them to ATT&CK techniques
- Create a simulation plan for a purple team exercise

Manually reading and mapping is slow, difficult, and not repeatable.

### Problem 2: Multi-Source Correlation Is Hard

Investigating a potential compromise, with:
- Windows Security and Sysmon logs (endpoint)
- Azure AD sign-in and audit logs (cloud)

Each source tells part of the story. The challenge is correlating
across both to build a coherent timeline.
