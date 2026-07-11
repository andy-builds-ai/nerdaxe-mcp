"""Nerdaxe MCP server — read-only monitor for a NerdOS solo miner.

Exposes four read-only tools over the stdio transport. Every tool is a view
on a single API call (`/api/system/info`); the shared helper
`fetch_system_info()` carries the request, timeout and error handling once.
"""
import json
import logging
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Silence httpx's per-request INFO log: it prints the full miner URL (with the
# IP). The record goes to stderr (which Claude Desktop captures), so this keeps
# the IP out of the logs; the stdout stream the MCP protocol uses is unaffected.
logging.getLogger("httpx").setLevel(logging.WARNING)

# Load the miner IP from the .env next to THIS file, not the working directory.
# Claude Desktop starts the server with a foreign cwd, so a cwd-relative path
# would work in the terminal and fail in Desktop.
ENV_PATH = Path(__file__).parent / ".env"
load_dotenv(ENV_PATH)
MINER_IP = os.getenv("NERDAXE_IP")

# Seconds to wait for the miner before giving up.
REQUEST_TIMEOUT = 5.0

# The MCP server. The name is what Claude Desktop shows for this connection.
mcp = FastMCP("nerdaxe-monitor")


# --- formatting helpers: one calculation each, no I/O -----------------------

def _format_uptime(seconds) -> str:
    """Turn a duration in seconds into a 'Nd Nh Nm' string."""
    if seconds is None:
        return "unknown"
    seconds = int(seconds)
    days, rest = divmod(seconds, 86400)
    hours, rest = divmod(rest, 3600)
    minutes = rest // 60
    return f"{days}d {hours}h {minutes}m"


def _human_diff(value) -> str:
    """Turn a difficulty number into a short suffixed string.

    Scales by thousands: no suffix below 1000, then K/M/G/T/P, and E beyond.
    Returns 'n/a' for None.
    """
    if value is None:
        return "n/a"
    value = float(value)
    for suffix in ("", "K", "M", "G", "T", "P"):
        if abs(value) < 1000:
            return f"{value:.2f}{suffix}"
        value /= 1000
    return f"{value:.2f}E"


def _reject_rate(accepted, rejected) -> float:
    """Return the share reject rate in percent, guarding an empty total."""
    total = accepted + rejected
    if total == 0:
        return 0.0
    return rejected / total * 100


def _efficiency(power_w, hashrate_ghs) -> float:
    """Return energy efficiency in joules per terahash, guarding zero hashrate."""
    if not hashrate_ghs:
        return 0.0
    return power_w * 1000 / hashrate_ghs


# --- the single point of contact with the miner ----------------------------

def fetch_system_info():
    """Fetch the miner's /api/system/info once.

    Returns the parsed JSON dict on success, or a human-readable error string
    for the four failure cases: not configured / unreachable, timeout, HTTP
    error status, broken JSON. This is the one place the request, timeout and
    error handling live; the tools are views on its result.
    """
    if not MINER_IP:
        return "NERDAXE_IP is not set in .env — cannot reach the miner."

    url = f"http://{MINER_IP}/api/system/info"
    try:
        response = httpx.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except httpx.TimeoutException:
        return f"Miner did not answer within {REQUEST_TIMEOUT:.0f} s (timeout)."
    except httpx.ConnectError:
        return "Miner is not reachable — check that it is powered on and on the network."
    except httpx.HTTPStatusError as exc:
        return f"Miner replied with HTTP error status {exc.response.status_code}."
    except httpx.RequestError:
        return "Network error while reaching the miner."
    except json.JSONDecodeError:
        return "Miner replied with data that is not valid JSON."


# --- tools: read-only views on fetch_system_info() --------------------------

@mcp.tool()
def get_miner_status() -> str:
    """Return an at-a-glance health overview of the miner.

    Covers current hashrate (with the 1-hour average), ASIC and voltage
    regulator temperature, power draw, fan and uptime.
    """
    data = fetch_system_info()
    if isinstance(data, str):
        return data
    return (
        f"NerdAxe Gamma — status\n"
        f"Hashrate:    {data.get('hashRate', 0):.1f} GH/s "
        f"(1h avg {data.get('hashRate_1h', 0):.1f})\n"
        f"Temperature: {data.get('temp', 0):.1f} °C ASIC, "
        f"{data.get('vrTemp', 0):.1f} °C VR (limit {data.get('overheat_temp', 0)})\n"
        f"Power:       {data.get('power', 0):.1f} W\n"
        f"Fan:         {data.get('fanspeed', 0)} % at {data.get('fanrpm', 0)} rpm\n"
        f"Uptime:      {_format_uptime(data.get('uptimeSeconds'))}\n"
        f"Wi-Fi:       {data.get('wifiStatus', 'unknown')} "
        f"(RSSI {data.get('wifiRSSI', 0)} dBm)"
    )


@mcp.tool()
def get_pool_and_shares() -> str:
    """Return the pool connection and share statistics.

    Covers the active pool, accepted/rejected shares with the reject rate,
    the best share found (all-time and this session) against the network
    difficulty, and blocks found — the solo-mining picture.
    """
    data = fetch_system_info()
    if isinstance(data, str):
        return data
    accepted = data.get("sharesAccepted", 0)
    rejected = data.get("sharesRejected", 0)
    pools = data.get("stratum", {}).get("pools", [])
    connected = "connected" if pools and pools[0].get("connected") else "disconnected"
    which = "fallback" if data.get("stratum", {}).get("usingFallback") else "primary"
    return (
        f"Pool & shares\n"
        f"Pool:         {data.get('stratumURL', 'unknown')}:"
        f"{data.get('stratumPort', 0)} ({connected}, {which})\n"
        f"Shares:       {accepted} accepted / {rejected} rejected "
        f"({_reject_rate(accepted, rejected):.2f} % reject)\n"
        f"Best share:   {_human_diff(data.get('bestDiff'))} all-time, "
        f"{_human_diff(data.get('bestSessionDiff'))} this session\n"
        f"Network diff: {_human_diff(data.get('networkDifficulty'))}\n"
        f"Blocks found: {data.get('foundBlocks', 0)}"
    )


@mcp.tool()
def get_hardware_health() -> str:
    """Return thermal and electrical detail with derived efficiency.

    Covers ASIC and voltage regulator temperature against the overheat limit,
    fan, ASIC frequency, core voltage (set vs actual), power draw, and the
    derived energy efficiency in joules per terahash.
    """
    data = fetch_system_info()
    if isinstance(data, str):
        return data
    auto = "auto" if data.get("autofanspeed") else "manual"
    return (
        f"Hardware health\n"
        f"ASIC temp:    {data.get('temp', 0):.1f} °C "
        f"(overheat limit {data.get('overheat_temp', 0)})\n"
        f"VR temp:      {data.get('vrTemp', 0):.1f} °C\n"
        f"Fan:          {data.get('fanspeed', 0)} % at "
        f"{data.get('fanrpm', 0)} rpm ({auto})\n"
        f"Frequency:    {data.get('frequency', 0)} MHz\n"
        f"Core voltage: {data.get('coreVoltage', 0)} mV set / "
        f"{data.get('coreVoltageActual', 0)} mV actual\n"
        f"Power:        {data.get('power', 0):.1f} W at "
        f"{data.get('voltage', 0) / 1000:.2f} V, {data.get('currentA', 0):.2f} A\n"
        f"Efficiency:   {_efficiency(data.get('power', 0), data.get('hashRate', 0)):.1f} J/TH"
    )


@mcp.tool()
def get_device_info() -> str:
    """Return device identity, firmware version and uptime.

    Covers the device and ASIC model, hostname, firmware version, uptime, the
    last reset reason and free heap memory.
    """
    data = fetch_system_info()
    if isinstance(data, str):
        return data
    return (
        f"Device info\n"
        f"Model:      {data.get('deviceModel', 'unknown')} "
        f"(ASIC {data.get('ASICModel', 'unknown')} x{data.get('asicCount', 0)})\n"
        f"Hostname:   {data.get('hostname', 'unknown')}\n"
        f"Firmware:   {data.get('version', 'unknown')}\n"
        f"Uptime:     {_format_uptime(data.get('uptimeSeconds'))}\n"
        f"Last reset: {data.get('lastResetReason', 'unknown')}\n"
        f"Free heap:  {data.get('freeHeap', 0)} bytes"
    )


if __name__ == "__main__":
    # Default transport is stdio — the pipe Claude Desktop speaks over.
    mcp.run()
