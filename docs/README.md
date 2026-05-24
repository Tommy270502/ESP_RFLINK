# Documentation

Project documentation for Wireless Dev Bridge V1.

Start here:

- [Getting Started](getting-started.md): clone-to-hardware workflow.
- [API Reference](api-reference.md): shared JSON command protocol, HTTP routes, WebSocket events, and BLE UUIDs.
- [Firmware Guide](firmware.md): PlatformIO environments, modules, pin map, runtime defaults, and command examples.
- [Hardware Guide](hardware.md): KiCad source, board assets, manufacturing review notes, and firmware pin alignment.
- [Release Checklist](release-checklist.md): pre-release checks across firmware, host tools, RF validation, hardware, security, and support.

Host tool documentation lives with the tool:

- [Local Web Workbench](../application/README.md)
- [Python SDK](../sdk/python/README.md)

Validated V1 workflows:

- Two-dongle nRF24 ACK traffic over USB serial control.
- Runtime RF configuration from the local web workbench, CLI, SDK, HTTP, WebSocket, or BLE.
- Live packet monitoring through WebSocket and BLE notifications.
- Wi-Fi AP station count, BLE connection state, and RF TX/RX counters through `status`.
