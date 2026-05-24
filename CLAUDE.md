# Claude Guidance

Use this file as repo-wide operating guidance. Keep changes scoped, preserve the
V1 protocol surface, and avoid spending tokens on unrelated hardware or
manufacturing assets.

## Repo Orientation

Wireless Dev Bridge is an ESP32-S3 plus nRF24 developer tool. This repository is
a V1 external developer package with firmware, host tools, hardware source,
manufacturing outputs, and docs.

Key paths:

- `Firmware/ESP32_RFLINK/`: PlatformIO firmware for the ESP32-S3 dongle.
- `application/`: local FastAPI/browser workbench for the shared command protocol.
- `application/main.py`: workbench backend and entry point.
- `application/static/index.html`: bundled local workbench UI.
- `sdk/python/`: Python SDK, CLI, examples, and hardware-free tests.
- `docs/`: product, API, firmware, hardware, getting-started, and release docs.
- `hardware/`: KiCad source.
- `manufacturing/`: Gerber/drill production outputs.

## Token Discipline

- Start with `rg` or `rg --files`; do not scan broad directories by default.
- Inspect outlines before reading large files. Read only the line ranges needed.
- Do not read KiCad, Gerber, drill, or board asset files unless the task is
  explicitly hardware/manufacturing-related.
- Do not paste long command output or full files into chat. Summarize and cite paths.
- Keep plans short. Update plans only when the next action changes materially.
- Prefer small, cohesive edits over broad rewrites.
- Explain decisions that affect behavior, dependencies, protocols, or tests.

## Cross-Cutting Rules

- Preserve the shared JSON command model across USB serial, HTTP, WebSocket, and BLE.
- Do not change firmware behavior, protocol field names, command names, response
  envelopes, BLE UUIDs, or HTTP/WebSocket routes unless the task explicitly
  requires it and docs/tests are updated.
- Keep V1 boundaries intact: no cloud features, auth systems, OTA, packet
  decoding, persistence, mesh behavior, or new product scope unless requested.
- Keep host-side defaults aligned across docs, SDK, CLI, and workbench:
  `192.168.4.1`, `WirelessDev-Node1`, timeout `3.0`, serial baud `115200`.
- If dependencies change, update the nearest README and install instructions.
- When touching docs, remove stale references in related docs instead of only
  updating one page.

## Firmware

- Work inside `Firmware/ESP32_RFLINK/` only for firmware tasks.
- Keep PlatformIO environments and node roles aligned with firmware docs.
- Maintain module boundaries such as command handling, radio, bridge, BLE, web,
  and app state unless a refactor is explicitly requested.
- Verify with PlatformIO where available:
  `pio run -e node1 -e node2`.

## Python SDK And CLI

- SDK source lives in `sdk/python/wireless_dev_bridge/`.
- Keep examples in `sdk/python/examples/` compatible with the public SDK API.
- Optional dependencies are defined in `sdk/python/pyproject.toml`.
- Prefer hardware-free tests for SDK/CLI behavior:
  `cd sdk/python && python -m pytest tests`.

## Local Web Workbench

The workbench is a local browser-hosted host tool. Preserve behavior before
changing presentation.

Required behavior:

- `python application/main.py` starts the local server from the repository root.
- The backend imports the local SDK from `sdk/python` when running from checkout.
- Supported command transports: USB serial, HTTP, WebSocket, BLE.
- Supported live event transports: WebSocket, BLE.
- Keep SDK clients open per `(transport, endpoint, timeout)` to avoid USB CDC
  reconnect resets while switching between devices.
- Keep serial port discovery through `serial.tools.list_ports` when `pyserial`
  is installed.
- Preserve quick commands, device overview, RF config, packet send, address
  presets, bridge toggles, live events, raw JSON, command log, event log, auto
  status refresh, dirty RF config protection, and disconnect cleanup.

Implementation rules:

- Keep `application/main.py` as the entry point.
- Keep frontend assets local in `application/static/`; do not add CDNs.
- Run blocking SDK calls off the web server event loop.
- Use REST for commands/state and Server-Sent Events for browser event updates
  unless there is a clear reason to change.
- If UI changes are requested, build an operational workbench, not a marketing
  page. Keep it dense, readable, responsive, and usable for repeated bench work.
- Do not remove Raw JSON or logs; they are developer tools.

## Hardware And Manufacturing

- Treat `hardware/` and `manufacturing/` as sensitive release assets.
- Do not edit KiCad or Gerber/drill files unless the task is specifically about
  hardware/manufacturing.
- If hardware docs change, keep `docs/hardware.md`, `hardware/README.md`, and
  manufacturing notes aligned where relevant.

## Documentation

- Root `README.md` should stay high level: product, quick start, layout,
  interfaces, validated workflow, docs links, and V1 boundaries.
- `docs/getting-started.md` should remain clone-to-hardware oriented.
- `docs/api-reference.md` documents the firmware/device protocol, not the
  workbench's private local backend unless explicitly requested.
- `application/README.md` documents the local web workbench install, runtime,
  local API, workflows, and troubleshooting.
- `sdk/python/README.md` documents SDK/CLI usage and examples.

## Verification

Choose checks based on touched areas:

- Python syntax: `python -m compileall application sdk/python/wireless_dev_bridge`
- SDK tests: `cd sdk/python && python -m pytest tests`
- Workbench smoke: start Uvicorn or import `application.main` and verify `/health`
  plus the root page.
- Firmware build: `cd Firmware/ESP32_RFLINK && pio run -e node1 -e node2`
- Docs-only changes: no hardware test required, but check links/commands for
  stale names and wrong paths.

When hardware is unavailable, say which USB serial, WebSocket, BLE, RF, or
firmware-flashing checks were not run.
