# Documentation

Project documentation for Wireless Dev Bridge V1.

## Getting Started

- [Getting Started](getting-started.md): clone-to-hardware workflow.
- [First Run](first-run.md): product path for identifying, validating, saving settings, and exporting reports.

## Architecture And Protocol

- [Architecture](architecture.md): Mermaid diagrams for host tools, transports, command layer, services, and hardware.
- [API Reference](api-reference.md): shared JSON command protocol, HTTP routes, WebSocket events, and BLE UUIDs.
- [Firmware Guide](firmware.md): PlatformIO environments, modules, pin map, runtime defaults, and command examples.
- [Security Model](security-model.md): trusted-bench defaults and optional token auth.

## Host Tools

- [Local Web Workbench](../application/desktop-workbench.md): FastAPI/browser workbench at `http://127.0.0.1:5173`.
- [Python SDK](../sdk/python/python-sdk-guide.md): SDK, CLI, examples, and hardware-free tests.

## Hardware And Manufacturing

- [Hardware Guide](hardware.md): KiCad source, board assets, manufacturing review notes, and firmware pin alignment.
- [Manufacturing Guide](../manufacturing/manufacturing-guide.md): Gerber/drill export and production notes.
- [Hardware License](../hardware/LICENSE.md): hardware license notice.

## Operations

- [Troubleshooting](troubleshooting.md): support report, serial, RF, Wi-Fi, BLE, and reset guidance.
- [Beta Validation](beta-validation.md): cross-platform and hardware-in-loop validation matrix.
- [Release Checklist](release-checklist.md): pre-release checks across firmware, host tools, RF validation, hardware, security, and support.

## Case Study

- [Case Study](case-study.md): problem, constraints, architecture, implementation, and validation evidence.

## Validated V1 Workflows

- Two-dongle nRF24 ACK traffic over USB serial control.
- Runtime RF configuration from the local web workbench, CLI, SDK, HTTP, WebSocket, or BLE.
- Live packet monitoring through WebSocket and BLE notifications.
- Wi-Fi AP station count, BLE connection state, and RF TX/RX counters through `status`.
- Protocol 1.1 settings persistence, diagnostics, identify, optional auth, and support report export.
