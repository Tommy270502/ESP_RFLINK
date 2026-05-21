# Documentation

Project documentation for Wireless Dev Bridge V1.

Start here:

- [Getting Started](getting-started.md): clone-to-hardware workflow.
- [First Run](first-run.md): product path for identifying, validating, saving settings, and exporting reports.
- [API Reference](api-reference.md): shared JSON command protocol, HTTP routes, WebSocket events, and BLE UUIDs.
- [Firmware Guide](firmware.md): PlatformIO environments, modules, pin map, runtime defaults, and command examples.
- [Hardware Guide](hardware.md): KiCad source, board assets, manufacturing review notes, and firmware pin alignment.
- [Security Model](security-model.md): trusted-bench defaults and optional token auth.
- [Troubleshooting](troubleshooting.md): support report, serial, RF, Wi-Fi, BLE, and reset guidance.
- [Beta Validation](beta-validation.md): cross-platform and hardware-in-loop validation matrix.
- [Release Checklist](release-checklist.md): pre-release checks across firmware, host tools, RF validation, hardware, security, and support.

Host tool documentation lives with the tool:

- [Desktop Workbench](../application/desktop-workbench.md)
- [Python SDK](../sdk/python/python-sdk-guide.md)

Validated V1 workflows:

- Two-dongle nRF24 ACK traffic over USB serial control.
- Runtime RF configuration from the desktop workbench, CLI, SDK, HTTP, WebSocket, or BLE.
- Live packet monitoring through WebSocket and BLE notifications.
- Wi-Fi AP station count, BLE connection state, and RF TX/RX counters through `status`.
- Protocol 1.1 settings persistence, diagnostics, identify, optional auth, and support report export.
