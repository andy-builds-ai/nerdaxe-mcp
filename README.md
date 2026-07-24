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

## Live proof

Example output from the four tools against a running miner:

```
NerdAxe Gamma — status
Hashrate:    1093.2 GH/s (1h avg 1069.5)
Temperature: 63.9 °C ASIC, 59.8 °C VR (limit 70)
Power:       17.6 W
Fan:         46 % at 3536 rpm
Uptime:      58d 22h 45m

Pool & shares
Shares:       160084 accepted / 438 rejected (0.27 % reject)
Best share:   5.73G all-time, 731.83M this session
Network diff: 127.17T
Blocks found: 0

Hardware health
ASIC temp:    63.9 °C (overheat limit 70)
VR temp:      59.8 °C
Fan:          46 % at 3536 rpm (auto)
Frequency:    550 MHz
Core voltage: 1025 mV set / 1007 mV actual
Power:        17.6 W at 4.97 V, 3.54 A
Efficiency:   16.1 J/TH

Device info
Model:      NerdAxeGamma (ASIC BM1370 x1)
Firmware:   v1.0.37.1
Uptime:     58d 22h 45m
Last reset: SYSTEM.RESET_SOFTWARE
Free heap:  7023824 bytes
```

## Scope and limits

- Read-only. No config writes, no restart, no history or database.
- The miner IP lives only in `.env`, which is gitignored.
