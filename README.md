# nerdaxe-mcp

A small, read-only MCP server that monitors a Nerdaxe Gamma solo miner
running the NerdOS firmware over its local REST API.

Built with the official MCP Python SDK (`mcp`) and served over the stdio
transport for Claude Desktop.

## Status

Started as my first MCP server, a warm-up before a larger one — small and
clean over complete. Now done: all four tools query the live miner and were
verified end to end — each tool by hand in the MCP Inspector, plus a live
run from Claude Desktop. The tool set was cut from the real
`/api/system/info` fields; nothing is assumed from memory.

## Setup

```bash
py -m venv .venv              # `python` may hit the Windows Store stub; use py
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

All four are read-only views on a single `/api/system/info` call.

- `get_miner_status` — at-a-glance health: hashrate (with the 1h average),
  ASIC/VR temperature, power, fan, uptime.
- `get_pool_and_shares` — pool connection, accepted/rejected shares with the
  reject rate, best share vs network difficulty, blocks found.
- `get_hardware_health` — thermal and electrical detail plus the derived
  energy efficiency (J/TH).
- `get_device_info` — device and ASIC model, firmware version, uptime, last
  reset reason.

## Scope and limits

- Read-only. No config writes, no restart, no history or database.
- The miner IP lives only in `.env`, which is gitignored.
