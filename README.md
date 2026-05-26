# Wireless Dev Bridge

Wireless Dev Bridge is a USB-C developer kit for ESP32-S3 and nRF24L01+ work. It gives one bench dongle a shared JSON command protocol over USB serial, HTTP, WebSocket, and BLE, plus a Python SDK, CLI, local web workbench, firmware browser dashboard, KiCad hardware source, and manufacturing outputs.

![Wireless Dev Bridge PCB top view](docs/assets/board/PCB-TOP.png)

## Start Here

1. Read [Getting Started](docs/getting-started.md) for firmware build, SDK install, and first RF validation.
2. Use the local web workbench:

   ```bash
   pip install -r application/requirements.txt
   python application/main.py
   ```

3. Or install the SDK and CLI:

   ```bash
   cd sdk/python
   python -m pip install -e ".[all]"
   wdb discover
   wdb --serial COM5 identify
   wdb --serial COM5 diagnostics
   ```

4. For a two-dongle kit, flash one `node1` and one `node2`, then run:

   ```bash
   wdb pair-test --node1-serial COM5 --node2-serial COM6
   ```

## Product Surfaces

| Surface | Location | Description |
| --- | --- | --- |
| Firmware | `Firmware/ESP32_RFLINK` | PlatformIO ESP32-S3 firmware. |
| Local web workbench | `application` | FastAPI/browser host tool at `http://127.0.0.1:5173`. |
| SDK/CLI | `sdk/python` | Python SDK, CLI, examples, and hardware-free tests. |
| Firmware browser dashboard | `http://192.168.4.1` | Served by the dongle SoftAP. |
| Hardware | `hardware/kicad` | KiCad schematic and PCB source. |
| Manufacturing | `manufacturing/gerbers` | Current V1 Gerber/drill export. |

All transports share one command response envelope:

```json
{"ok":true,"cmd":"status","data":{},"error":null}
```

See [Project Overview](project-overview.md) for interfaces, validated bench workflows, and architecture detail.

## Protocol 1.1 Capabilities

- Shared command envelope over USB serial, HTTP, WebSocket, and BLE.
- Runtime RF config, address management, send/listen/flush, and bridge toggles.
- Settings persistence through NVS with `settings_get`, `settings_set`, `settings_save`, and `settings_reset`.
- Diagnostics and identify commands for support and physical device matching.
- Optional token auth for HTTP, WebSocket, and BLE command surfaces.
- Support report export from the CLI and local web workbench.

## Development Checks

```bash
cd Firmware/ESP32_RFLINK
pio run -e node1 -e node2

cd ../../sdk/python
python -m pytest

cd ../..
python -m py_compile application/main.py
python scripts/check_docs_links.py
```

## Documentation

- [Documentation Index](docs/documentation-index.md)
- [Project Overview](project-overview.md)
- [Getting Started](docs/getting-started.md)
- [First Run](docs/first-run.md)
- [API Reference](docs/api-reference.md)
- [Firmware Guide](docs/firmware.md)
- [Hardware Guide](docs/hardware.md)
- [Security Model](docs/security-model.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Release Checklist](docs/release-checklist.md)
- [Local Web Workbench](application/desktop-workbench.md)
- [Python SDK](sdk/python/python-sdk-guide.md)

## V1 Boundaries

- nRF24 payloads are limited to 32 bytes.
- nRF24 address width is fixed at 5 bytes.
- RF configuration is runtime-only until saved with protocol 1.1 settings commands.
- HTTP, WebSocket, and BLE APIs are intended for trusted developer/lab networks.
- OTA, cloud connectivity, packet decoding, persistence, and mesh networking are out of scope for V1.

## License

Software is licensed under the MIT License; see [LICENSE](LICENSE). Hardware source and manufacturing outputs use the hardware license notice in [hardware/LICENSE.md](hardware/LICENSE.md).
