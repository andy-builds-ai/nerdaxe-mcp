# Bauplan — Nerdaxe MCP Server

Finalisiert in der Baubesprechung am 11.07.2026. Erster Prompt für die
Werkstatt-Session: „Lies BAUPLAN.md und setze ihn exakt so um."

---

Neues Projekt: mein erster eigener MCP-Server — read-only Monitor für
meinen Nerdaxe Gamma Solo Miner (AxeOS-Firmware, REST-API im lokalen
Netz). Fingerübung vor einem größeren Server; klein und sauber schlägt
vollständig.

## Rahmen

- Dieses Repo (nerdaxe-mcp) — lokal, kein Remote, kein Push.
- Python mit dem OFFIZIELLEN MCP Python SDK (Paket `mcp`, darin
  `mcp.server.fastmcp.FastMCP`), installiert als `pip install "mcp[cli]"`.
  Nicht das Community-Paket „FastMCP 2.x" — gleicher Name, anderes Projekt.
- stdio-Transport für Claude Desktop.
- Gerüst über den module-scaffolder-Skill: .gitignore zuerst (.env, venv,
  __pycache__), README-Stub, requirements.txt (mcp[cli], httpx,
  python-dotenv). Dann .env mit der Miner-IP (frag mich, ich trage sie
  selbst ein) und .env.example mit neutralem Platzhalter
  (NERDAXE_IP=<miner-ip>, kein IP-Muster).

## Vorgehen

1. Zuerst die AxeOS-API einmal live abfragen (GET /api/system/info,
   IP aus der .env) und mir die echten Felder zeigen. Erst danach die
   Tools schneiden — nichts aus dem Gedächtnis annehmen. Dabei auch
   prüfen, ob es weitere sinnvolle Endpunkte gibt.
2. Drei bis vier read-only Tools aus den echten Feldern (Vorschlag:
   Status-Überblick mit Hashrate/Temperatur/Uptime, Shares/Pool-Stand,
   Rest nach Befund). Eine interne Hilfsfunktion `fetch_system_info()`
   trägt Request, Timeout und Fehlerbehandlung EINMAL; die Tools sind
   Sichten darauf. Jedes Tool eine klare Funktion mit Docstring.
3. Fehlerfall von Anfang an: HTTP-Timeout 3–5 Sekunden, und vier Fälle
   sauber abgedeckt — Miner nicht erreichbar, Timeout, HTTP-Fehlerstatus,
   kaputtes JSON. Jeweils verständliche Meldung als Tool-Antwort, kein
   Crash, kein Traceback nach außen.
4. Die .env relativ zur Skript-Datei laden (`Path(__file__).parent /
   ".env"`), NICHT übers Arbeitsverzeichnis — Claude Desktop startet den
   Server mit fremdem cwd, sonst läuft er im Terminal und stirbt in
   Desktop.
5. Teststufe vor Claude Desktop: `mcp dev server.py` (MCP Inspector im
   Browser), jedes Tool von Hand aufrufen. Erst wenn das steht, der
   Eintrag in claude_desktop_config.json (absoluter Pfad zum
   venv-Python, escaped Backslashes) als letzter Schritt.
6. Ich bin am Lernen: benenne jedes Konzept in dem Moment, in dem es
   entsteht (FastMCP, Tool-Definition, stdio-Transport, MCP Inspector,
   Config-Eintrag), je ein Satz wozu es gut ist.
7. Code-Review-Loop: nach dem Schreiben jede Datei komplett zurücklesen
   und mir zeigen; ich gehe sie durch, bevor irgendetwas läuft.

## Bewusst NICHT im Umfang

Config-Schreiben, Neustart-Tool, Historie/Datenbank — read-only und
fertig werden schlägt vollständig.

## Grenzen

Nur dieses Repo, kein Vault-Zugriff. Die Miner-IP erscheint nirgends
außer in der .env — nicht im Code, nicht in Commits, nicht in
Beispielen. Commits als Conventional Commits, Vorschlag zeigen, auf
mein go warten, kein Push.
