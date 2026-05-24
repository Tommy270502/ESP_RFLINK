# Changelog

## 0.1.0-v1

- Initial V1 developer launch package.
- ESP32-S3 PlatformIO firmware with USB serial, Wi-Fi HTTP, WebSocket, and BLE GATT command transports.
- nRF24L01+ send, receive, listen, flush, address, and RF configuration commands.
- RF-to-Wi-Fi/WebSocket and RF-to-BLE bridge toggles.
- Browser dashboard served from the dongle SoftAP.
- Python SDK, CLI, desktop workbench, hardware-free tests, and launch examples.
- Desktop workbench RF config, packet send, persistent two-port serial control, and WebSocket/BLE live event monitoring.
- KiCad hardware source, board images, and Gerber/drill export.

## Unreleased

- Added protocol `1.1` settings, diagnostics, identify, optional auth, and status metadata.
- Added SDK/CLI helpers for settings, diagnostics, identify, support reports, pair-test, discovery, setup, and firmware flashing.
- Added desktop workbench auth token support, diagnostics/identify/settings quick actions, and support report export.
- Expanded browser dashboard with diagnostics, address controls, BLE bridge toggle, settings auth, report export, and clearer status cards.
- Added root README, software/hardware license notices, CI/release workflows, issue templates, release packaging script, and product journey docs.
