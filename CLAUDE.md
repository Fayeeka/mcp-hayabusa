# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

This project is an MCP server that wraps Hayabusa for EVTX analysis. In
addition to the current functionality, this project is an MCP server
providing a detection engineering knowledge base.

## Goals

- Expose a `scan_evtx` tool that runs Hayabusa against EVTX files
- Return results as structured JSON
- Support filtering by severity level
- Handle errors gracefully
- Expose Sigma rules as browsable resources
- Expose ATT&CK technique mappings
- Allow Claude to query detection coverage
- Combine with Hayabusa scanning from Module 3

## Structure

- `rules/` - Sigma detection rules (YAML)
- `mappings/` - ATT&CK technique to rule mappings
- `server.py` - MCP server with resources and tools

## Stack

- Python with the `mcp` library
- Hayabusa CLI (installed locally)
