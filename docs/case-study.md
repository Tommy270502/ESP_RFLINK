# Case Study: Wireless Dev Bridge

## Problem

Engineers working with nRF24L01+ radios need a reliable way to send, receive, and monitor 2.4 GHz RF packets from a development host. Existing approaches require custom firmware per project, manual serial protocol parsing, and no standard tooling for RF pair testing or production validation.

## Constraints

- Must work from a single USB-C dongle with no external power or adapters.
- Must expose RF operations through transports that scripts, browsers, mobile apps, and BLE hosts can all reach.
- Must use one shared command protocol across all transports to avoid per-transport divergence.
- Must support two-dongle RF pair testing for production validation workflows.
- Must include hardware source and manufacturing outputs for reproducibility.
- V1 scope: no OTA, cloud, packet decoding, mesh, or production security hardening.

## Architecture Decisions

**ESP32-S3 as the host MCU.** Native USB CDC serial eliminates the need for an external FTDI or CP2102. Wi-Fi AP mode, BLE GATT, and SPI for the nRF24L01+ are all available on one chip.

**JSON command protocol.** One command/response envelope (`ok`, `cmd`, `data`, `error`) shared across USB serial (JSONL), HTTP, WebSocket, and BLE. This lets the same SDK client, CLI, and workbench code work over any transport without translation layers.

**FastAPI local web workbench.** A browser-based host tool at `http://127.0.0.1:5173` backed by FastAPI and the Python SDK. Provides RF config, packet send, address presets, bridge toggles, live events (via SSE), and command/event logs. Keeps SDK client connections open per `(transport, endpoint, timeout)` to prevent USB CDC reconnect resets when switching between two dongles.

**Firmware browser dashboard.** A minimal dashboard served by the ESP32-S3 SoftAP at `http://192.168.4.1`. Provides status, RF controls, and event visibility when a host tool is not available.

**Python SDK with optional transports.** HTTP works with the standard library. Serial, WebSocket, and BLE are optional dependencies. The CLI wraps the SDK for terminal workflows. Hardware-free tests validate command mapping and report formatting without connected dongles.

**NVS settings persistence.** Protocol 1.1 added `settings_save` and `settings_reset` so RF config, addresses, bridge state, device names, and optional auth survive reboots.

## Implementation Summary

| Layer | Technology | Key files |
| --- | --- | --- |
| Firmware | PlatformIO + Arduino, ESP32-S3 | `Firmware/ESP32_RFLINK/src/` |
| Command dispatch | `CommandService.cpp` | Parses JSON, dispatches to RF/settings/bridge/diagnostics services |
| RF driver | `RadioService.cpp` + RF24 library | nRF24L01+ config, TX/RX, listen, flush, address |
| Settings | `SettingsService.cpp` + ESP-IDF NVS | Persist/restore RF, bridge, device, security settings |
| Web | `WebService.cpp` + `WebUi.cpp` | SoftAP, HTTP API, firmware browser dashboard, WebSocket events |
| BLE | `BleService.cpp` | BLE GATT UART-style command/event transport |
| Bridge | `BridgeService.cpp` | RF packet forwarding to WebSocket and BLE |
| SDK | Python (`wireless_dev_bridge/`) | Serial, HTTP, WebSocket, BLE client; CLI; examples |
| Workbench | Python + FastAPI (`application/`) | Local browser UI backed by SDK |
| Hardware | KiCad (`hardware/kicad/`) | Schematic and PCB source |

## Validation Evidence

The following checks are automated in CI or run locally:

- **SDK tests**: 25 hardware-free tests covering command mapping, CLI bridge, and examples (`sdk/python/tests/`).
- **Application compile**: `python -m py_compile application/main.py` verifies the FastAPI backend is syntactically valid.
- **Docs link check**: `python scripts/check_docs_links.py` verifies all Markdown cross-references resolve.
- **Conflict-marker check**: `rg "^(<<<<<<<|=======|>>>>>>>)" .` ensures no merge artifacts remain.
- **Firmware build**: `pio run -e node1 -e node2` builds both node roles (requires PlatformIO).

## Unverified Items

The following require hardware that may not be available in every environment:

- USB serial command round-trip with physical dongles.
- Two-dongle RF ACK traffic and `pair-test` validation.
- WebSocket and BLE live packet event streaming.
- NVS settings persistence across reboot cycles.
- Optional token auth enforcement over HTTP, WebSocket, and BLE.
- nRF24L01+ radio initialization on the production PCB.
- Firmware browser dashboard rendering and control on the SoftAP.

These items are documented in the [Beta Validation](beta-validation.md) matrix and [Release Checklist](release-checklist.md).

## Business Value

This repository demonstrates:

- **Full-stack embedded product delivery**: firmware, host tools, hardware source, manufacturing outputs, and documentation in one package.
- **Multi-transport architecture**: one command protocol serving four transports without code duplication.
- **Developer experience focus**: SDK, CLI, browser workbench, and examples that work without writing embedded code.
- **Production readiness awareness**: validation checklists, support report infrastructure, and honest documentation of what has and has not been hardware-validated.
- **Reproducible hardware**: KiCad source and Gerber/drill exports included for board fabrication.
