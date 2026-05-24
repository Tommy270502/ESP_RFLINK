# Wireless Dev Bridge

Wireless Dev Bridge is a USB-C developer kit for ESP32-S3 and nRF24L01+ work. It gives one bench dongle a shared JSON command protocol over USB serial, HTTP, WebSocket, and BLE, plus a Python SDK, CLI, desktop workbench, embedded browser dashboard, KiCad hardware source, and manufacturing outputs.

![Wireless Dev Bridge PCB top view](docs/assets/board/PCB-TOP.png)

## Start Here

1. Read [Getting Started](docs/getting-started.md) for firmware build, SDK install, and first RF validation.
2. Use the desktop workbench:

   ```bash
   python application/main.py
   ```

<<<<<<< HEAD
- Bridge nRF24 packets to USB serial, Wi-Fi/WebSocket, or BLE notifications.
- Send and receive 32-byte nRF24 payloads from scripts, the CLI, the local web workbench, or the firmware browser UI.
- Configure RF channel, datarate, power, auto-ACK, listen state, and 5-byte pipe addresses.
- Watch live RF packet events over WebSocket or BLE while controlling devices over USB serial.
- Run two-dongle RF ping and production-style self-test workflows.
- Use the Python SDK, CLI, or local web workbench without writing embedded code.
=======
3. Or install the SDK and CLI:
>>>>>>> 05d28c834b179d240a117645e267be65919b6695

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

- Firmware: PlatformIO ESP32-S3 firmware in `Firmware/ESP32_RFLINK`.
- Desktop app: Tkinter workbench in `application`.
- SDK/CLI: Python package in `sdk/python`.
- Browser dashboard: served by the dongle SoftAP at `http://192.168.4.1`.
- Hardware: KiCad source in `hardware/kicad`.
- Manufacturing: current V1 Gerber/drill export in `manufacturing/gerbers`.

## V1.1 Capabilities

- Shared command envelope over USB serial, HTTP, WebSocket, and BLE.
- Runtime RF config, address management, send/listen/flush, and bridge toggles.
- Settings persistence through NVS with `settings_get`, `settings_set`, `settings_save`, and `settings_reset`.
- Diagnostics and identify commands for support and physical device matching.
- Optional token auth for HTTP, WebSocket, and BLE command surfaces.
- Support report export from the CLI and desktop workbench.

## Development Checks

```bash
cd Firmware/ESP32_RFLINK
pio run -e node1 -e node2

cd ../../sdk/python
python -m pytest

cd ../..
python -m py_compile application/main.py
```

<<<<<<< HEAD
Install the Python SDK:

```bash
cd sdk/python
python -m pip install -e ".[all]"
```

Validate a dongle over USB serial:

```bash
wdb --serial COM5 self-test
wdb --serial COM5 status
```

Launch the local web workbench:

```bash
# from the repository root
python -m pip install -r application/requirements.txt
python application/main.py
```

Use the local web workbench at `http://127.0.0.1:5173` to configure both node
roles, send ACK-required RF packets in both directions, watch counters, and
stream RF packet events over WebSocket or BLE.

Run the two-dongle production demo with flashing and a JSON report:

```bash
python examples/production_demo.py --node1-serial COM5 --node2-serial COM6 --flash
```

Use Wi-Fi after connecting your computer to the dongle AP:

```bash
wdb --host 192.168.4.1 status
```

Open the browser dashboard at:

```text
http://192.168.4.1
```

## Repository Layout

| Path | Purpose |
| --- | --- |
| `Firmware/ESP32_RFLINK` | PlatformIO firmware for the ESP32-S3 dongle. |
| `application` | Local FastAPI/browser workbench for the shared command protocol. |
| `sdk/python` | Python SDK, CLI, examples, and hardware-free tests. |
| `hardware/kicad` | KiCad schematic and PCB source. |
| `manufacturing/gerbers` | Current V1 Gerber/drill export. |
| `docs` | Product, API, hardware, and launch documentation. |
| `docs/assets/board` | Board images used by the docs. |

## Developer Interfaces

| Interface | Default endpoint | Use case |
| --- | --- | --- |
| USB CDC serial | 115200 baud JSONL | Reliable bench automation and flashing-adjacent validation. |
| HTTP JSON | `http://192.168.4.1` | Simple host scripts and browser UI control. |
| WebSocket JSON | `ws://192.168.4.1:81/` | Live packet monitor and RF event streaming. |
| BLE GATT | `WirelessDev-Node1` or `WirelessDev-Node2` | Mobile, field, and BLE-host workflows. |

The local web workbench and Python SDK can use these same transports from the host side.

All transports share the same command response envelope:

```json
{"ok":true,"cmd":"status","data":{},"error":null}
```

## Validated Bench Workflow

For a two-dongle RF bench, flash one dongle as `node1` and one as `node2`. Keep their RF channel, datarate, and auto-ACK settings matched. The default addresses are complementary:

| Role | RX address | TX address |
| --- | --- | --- |
| `node1` | `NODE1` | `NODE2` |
| `node2` | `NODE2` | `NODE1` |

In the local web workbench, use USB serial for reliable command control. The app keeps open connections per endpoint so switching between COM ports does not reset the boards. `status` counters should show `rf_tx` increasing on the sender and `rf_rx` increasing on the peer.

To prove wireless event streaming, use the **Live Events** tab:

- WebSocket: connect the PC to a dongle AP, stream from `192.168.4.1`, and send RF from the peer.
- BLE: stream from `WirelessDev-Node1` or `WirelessDev-Node2`, then send RF from the peer.

=======
>>>>>>> 05d28c834b179d240a117645e267be65919b6695
## Documentation

- [Documentation Index](docs/documentation-index.md)
- [First Run](docs/first-run.md)
- [API Reference](docs/api-reference.md)
- [Security Model](docs/security-model.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Release Checklist](docs/release-checklist.md)
<<<<<<< HEAD
- [Local Web Workbench](application/README.md)
- [Python SDK](sdk/python/README.md)

## V1 Boundaries

- nRF24 payloads are limited to 32 bytes.
- nRF24 address width is fixed at 5 bytes.
- RF configuration is runtime-only and resets on reboot.
- HTTP, WebSocket, and BLE APIs are intended for trusted developer/lab networks.
- OTA, cloud connectivity, packet decoding, persistence, and mesh networking are out of scope for V1.
=======
>>>>>>> 05d28c834b179d240a117645e267be65919b6695

## License

Software is licensed under the MIT License; see [LICENSE](LICENSE). Hardware source and manufacturing outputs use the hardware license notice in [hardware/LICENSE.md](hardware/LICENSE.md).
