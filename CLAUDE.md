# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

This project is an MCP server that wraps Hayabusa for EVTX analysis.

## Goals

- Expose a `scan_evtx` tool that runs Hayabusa against EVTX files
- Return results as structured JSON
- Support filtering by severity level
- Handle errors gracefully

## Stack

- Python with the `mcp` library
- Hayabusa CLI (installed locally)
