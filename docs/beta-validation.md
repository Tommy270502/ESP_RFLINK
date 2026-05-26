# Beta Validation

Use this matrix before calling a release product-ready.

## Host Platforms

| Platform | Required checks |
| --- | --- |
| Windows | USB serial identify, diagnostics, local web workbench start, support report export, pair-test |
| Linux | USB serial identify, diagnostics, local web workbench start, support report export, pair-test |
| macOS | USB serial identify, diagnostics, local web workbench start, support report export, pair-test |

HTTP, WebSocket, and BLE should be validated where host adapters and permissions are available.

## Hardware-In-Loop

- Flash one `node1` and one `node2`.
- Run `wdb pair-test`.
- Verify WebSocket packet events through the firmware browser dashboard or local web workbench.
- Verify BLE packet events with `packet_monitor.py --ble`.
- Save settings, reboot, and confirm `settings_get` reports persisted values.
- Enable auth, confirm unauthorized HTTP/WebSocket/BLE commands fail, then confirm token-authenticated commands pass.

## Release Evidence

Store these with the release notes:

- CI run URL.
- Firmware build hashes or artifacts.
- SDK package artifact.
- Gerber zip artifact.
- DRC/ERC review note.
- At least one support report from a passing two-dongle kit.
