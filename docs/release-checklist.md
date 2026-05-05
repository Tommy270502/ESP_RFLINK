# V1 Release Checklist

Use this checklist before publishing an external developer release.

## Repository

- Root README explains the product, quick start, repo layout, interfaces, and V1 boundaries.
- Firmware, SDK, hardware, manufacturing, and docs are discoverable from the repo root.
- Generated caches, local KiCad files, old backup archives, Python bytecode, and egg-info files are not tracked.
- No user-local absolute paths remain in tracked source files.
- A license file is added before public distribution.

## Firmware

- `pio run -e node1 -e node2` passes from a clean checkout.
- Fresh flash succeeds on at least one dongle per node role.
- Serial boot message includes product, firmware version, protocol version, role, radio health, AP IP, and BLE name.
- `wdb --serial <port> self-test` passes.
- Browser dashboard loads at `http://192.168.4.1`.
- WebSocket packet stream receives RF packet events.
- BLE command transport responds to `status`.

## SDK

- `python -m pip install -e ".[all]"` succeeds in a fresh virtual environment.
- `python -m pytest` passes without hardware.
- CLI works over serial, HTTP, WebSocket, and BLE where hardware is available.
- Examples support `--help` and document required optional dependencies.

## RF Validation

- One `node1` and one `node2` pass `examples/rf_ping.py` over USB serial.
- ACK-required traffic succeeds in both directions.
- Packet monitor shows expected payloads and timestamps.
- RF config values reset to known defaults after reboot.

## Hardware

- KiCad ERC/DRC has been reviewed for the V1 release commit.
- Gerber and drill files match the current KiCad PCB.
- Board images match the released hardware revision.
- Fab notes for stackup, thickness, copper, finish, and assembly options are captured outside the Gerber folder or in the release notes.

## Security And Support

- V1 lab-network trust boundaries are documented.
- Known limitations are documented.
- Support and issue-reporting expectations are clear.
