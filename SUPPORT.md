# Support

For V1 developer support, include:

- Firmware version from `status` or `self_test`.
- Host tool and transport used: CLI, SDK, desktop workbench, browser dashboard; USB serial, HTTP, WebSocket, or BLE.
- Host OS and Python version when using the SDK.
- Hardware role: `node1`, `node2`, or custom build flags.
- Relevant command JSON and full response JSON.
- RF config: channel, datarate, power, auto-ACK, RX address, and TX address.

For hardware issues, include clear photos of the board, power symptoms, USB enumeration behavior, and whether the KiCad/Gerber release was modified.

Preferred report command:

```bash
wdb --serial <port> report --output wireless-dev-bridge-report.json
```

The desktop workbench can export the same support report from the selected connection.
