# Wireless Dev Bridge

![Wireless Dev Bridge PCB top view](docs/assets/board/PCB-TOP.png)

Wireless Dev Bridge is a compact USB-C developer dongle for engineers who need one bench interface for Wi-Fi, BLE, and nRF24L01-based 2.4 GHz RF systems. It combines an ESP32-S3, native USB CDC serial, a browser dashboard, BLE GATT, WebSocket streaming, and an nRF24L01+ radio path behind one JSON command protocol.

This repository is organized as a V1 external developer launch package: firmware, host tools, hardware source, board renders, and manufacturing outputs are all included.

## What You Can Do

- Bridge nRF24 packets to USB serial, Wi-Fi/WebSocket, or BLE notifications.
- Send and receive 32-byte nRF24 payloads from scripts, the CLI, the desktop workbench, or the browser UI.
- Configure RF channel, datarate, power, auto-ACK, listen state, and 5-byte pipe addresses.
- Watch live RF packet events over WebSocket or BLE while controlling devices over USB serial.
- Run two-dongle RF ping and production-style self-test workflows.
- Use the Python SDK, CLI, or desktop workbench without writing embedded code.

## Quick Start

Build and flash firmware:

```bash
cd Firmware/ESP32_RFLINK
pio run -e node1
pio run -e node1 --target upload
```

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

Launch the desktop workbench:

```bash
# from the repository root
python application/main.py
```

Use the desktop workbench to configure both node roles, send ACK-required RF packets in both directions, watch counters, and stream RF packet events over WebSocket or BLE.

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
| `application` | Tkinter desktop workbench for the shared command protocol. |
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

The desktop workbench and Python SDK can use these same transports from the host side.

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

In the desktop workbench, use USB serial for reliable command control. The app keeps open connections per endpoint so switching between COM ports does not reset the boards. `status` counters should show `rf_tx` increasing on the sender and `rf_rx` increasing on the peer.

To prove wireless event streaming, use the **Live Events** tab:

- WebSocket: connect the PC to a dongle AP, stream from `192.168.4.1`, and send RF from the peer.
- BLE: stream from `WirelessDev-Node1` or `WirelessDev-Node2`, then send RF from the peer.

## Documentation

- [Documentation Index](docs/documentation-index.md)
- [Getting Started](docs/getting-started.md)
- [API Reference](docs/api-reference.md)
- [Firmware Guide](docs/firmware.md)
- [Hardware Guide](docs/hardware.md)
- [Release Checklist](docs/release-checklist.md)
- [Desktop Workbench](application/desktop-workbench.md)
- [Python SDK](sdk/python/python-sdk-guide.md)

## V1 Boundaries

- nRF24 payloads are limited to 32 bytes.
- nRF24 address width is fixed at 5 bytes.
- RF configuration is runtime-only until saved with protocol `1.1` settings commands.
- HTTP, WebSocket, and BLE APIs are intended for trusted developer/lab networks.
- OTA, cloud connectivity, packet decoding, persistence, and mesh networking are out of scope for V1.

## License

Software is licensed under the MIT License. Hardware source and manufacturing outputs carry the hardware license notice in `hardware/LICENSE.md`.
