# V1 Release Checklist

Use this checklist before publishing an external developer release.

## Repository

- [Project overview](../project-overview.md) explains the product, quick start, repo layout, interfaces, and V1 boundaries.
- Firmware, application, SDK, hardware, manufacturing, and docs are discoverable from the repo root.
- Root `README.md`, software license, hardware license notice, issue templates, and CI workflows are present.
- Generated caches, local KiCad files, old backup archives, Python bytecode, and egg-info files are not tracked.
- No user-local absolute paths remain in tracked source files.
- A license file is added before public distribution.

## Firmware

- `pio run -e node1 -e node2` passes from a clean checkout.
- Fresh flash succeeds on at least one dongle per node role.
- Serial boot message includes product, firmware version, protocol version, role, radio health, AP IP, and BLE name.
- `wdb --serial <port> self-test` passes.
- Firmware browser dashboard loads at `http://192.168.4.1`.
- WebSocket packet stream receives RF packet events.
- BLE command transport responds to `status`.
- Protocol 1.1 commands `settings_get`, `settings_set`, `settings_save`, `settings_reset`, `diagnostics`, and `identify` pass over USB serial.
- Optional auth is validated over HTTP, WebSocket, and BLE.

## SDK

- `python -m pip install -e ".[all]"` succeeds in a fresh virtual environment.
- `python -m pytest` passes without hardware.
- CLI works over serial, HTTP, WebSocket, and BLE where hardware is available.
- `wdb discover`, `wdb identify`, `wdb diagnostics`, `wdb pair-test`, and `wdb report` work in supported environments.
- Examples support `--help` and document required optional dependencies.

## Local Web Workbench

- `python -m pip install -r application/requirements.txt` succeeds in a fresh virtual environment.
- `python application/main.py` starts from the repository root.
- `GET http://127.0.0.1:5173/health` returns `{"ok": true}` while the workbench is running.
- The workbench can run `status`, `self_test`, RF config, RF send, address, and bridge commands through the shared SDK client.
- The workbench keeps separate open connections per endpoint so switching between two serial ports does not reset boards during runtime RF testing.
- The Live Events tab receives WebSocket packet events and BLE packet events where hardware is available.
- The workbench can export a support report JSON.
- Serial, HTTP, WebSocket, and BLE transport labels match the SDK and API documentation.

## RF Validation

- One `node1` and one `node2` pass `examples/rf_ping.py` over USB serial.
- `examples/production_demo.py --flash` generates a passing JSON report for a packaged two-dongle kit.
- ACK-required traffic succeeds in both directions.
- Packet monitor shows expected payloads and timestamps.
- Status counters show expected `rf_tx`, `rf_rx`, `rf_tx_fail`, Wi-Fi client count, and BLE connection state.
- RF config values reset to known defaults after reboot.

## Hardware

- KiCad ERC/DRC has been reviewed for the V1 release commit.
- Tracked KiCad source does not contain user-local absolute paths.
- Gerber and drill files match the current KiCad PCB.
- Board images match the released hardware revision.
- Fab notes for stackup, thickness, copper, finish, and assembly options are captured outside the Gerber folder or in the release notes.
- BOM, assembly notes, board revision notes, and pinout card are present or attached as release artifacts.

## Security And Support

- V1 lab-network trust boundaries are documented.
- Known limitations are documented.
- Support and issue-reporting expectations are clear.
