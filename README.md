# Wireless Dev Bridge

![Wireless Dev Bridge PCB top view](docs/assets/board/PCB-TOP.png)

Wireless Dev Bridge is a compact USB-C developer dongle for engineers who need one bench interface for Wi-Fi, BLE, and nRF24L01-based 2.4 GHz RF systems. It combines an ESP32-S3, native USB CDC serial, a browser dashboard, BLE GATT, WebSocket streaming, and an nRF24L01+ radio path behind one JSON command protocol.

This repository is organized as a V1 external developer launch package: firmware, Python SDK, hardware source, board renders, and manufacturing outputs are all included.

## What You Can Do

- Bridge nRF24 packets to USB serial, Wi-Fi/WebSocket, or BLE notifications.
- Send and receive 32-byte nRF24 payloads from scripts, the CLI, or the browser UI.
- Configure RF channel, datarate, power, auto-ACK, listen state, and 5-byte pipe addresses.
- Run two-dongle RF ping and production-style self-test workflows.
- Build lab tools around the Python SDK without writing embedded code.

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
| `sdk/python` | Python SDK, CLI, examples, and hardware-free tests. |
| `hardware/kicad` | KiCad schematic and PCB source. |
| `hardware/3d-models` | Bundled 3D model assets used by the KiCad project. |
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

All transports share the same command response envelope:

```json
{"ok":true,"cmd":"status","data":{},"error":null}
```

## Documentation

- [Getting Started](docs/getting-started.md)
- [API Reference](docs/api-reference.md)
- [Firmware Guide](docs/firmware.md)
- [Hardware Guide](docs/hardware.md)
- [Release Checklist](docs/release-checklist.md)
- [Python SDK](sdk/python/README.md)

## V1 Boundaries

- nRF24 payloads are limited to 32 bytes.
- nRF24 address width is fixed at 5 bytes.
- RF configuration is runtime-only and resets on reboot.
- HTTP, WebSocket, and BLE APIs are intended for trusted developer/lab networks.
- OTA, cloud connectivity, packet decoding, persistence, and mesh networking are out of scope for V1.

## License

No license file is currently included. Add one before publishing this repository publicly so external developers know their usage rights.
