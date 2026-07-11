# nerdaxe-mcp

A small, read-only MCP server that monitors a Nerdaxe Gamma solo miner
running the NerdOS firmware over its local REST API.

Built with the official MCP Python SDK (`mcp`) and served over the stdio
transport for Claude Desktop.

## Status

Scaffold stage. The tools are defined only after querying the live miner
API once, so the fields are real and nothing is assumed from memory.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows (PowerShell / cmd)
pip install -r requirements.txt

cp .env.example .env          # then enter the real miner IP in .env
```

## Usage

```bash
mcp dev server.py             # MCP Inspector in the browser, for testing
```

Once verified, register the server in `claude_desktop_config.json` with an
absolute path to the venv Python.

## Tools

To be defined after the live API exploration. Planned direction: a status
overview (hashrate / temperature / uptime) and a shares / pool view.

## Scope and limits

- Read-only. No config writes, no restart, no history or database.
- The miner IP lives only in `.env`, which is gitignored.
- Local repository. No remote, no push.
