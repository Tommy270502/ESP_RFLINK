# Firmware Guide

The firmware lives in `Firmware/ESP32_RFLINK` and uses PlatformIO with the Arduino framework.

## Target

- MCU: ESP32-S3-WROOM-1
- Board profile: `esp32-s3-devkitc-1`
- Flash: 4 MB
- Partition table: `no_ota.csv`
- USB: native USB CDC serial
- RF: nRF24L01+

BLE support requires a larger application partition than the default Arduino OTA layout provides on 4 MB flash, so V1 uses a single no-OTA app slot.

## Build Environments

`node1` is the default environment:

```bash
cd Firmware/ESP32_RFLINK
pio run
```

Two node-specific environments are provided for paired RF validation:

| Environment | RX address | TX address | AP/BLE name |
| --- | --- | --- | --- |
| `node1` | `NODE1` | `NODE2` | `WirelessDev-Node1` |
| `node2` | `NODE2` | `NODE1` | `WirelessDev-Node2` |

Build both:

```bash
pio run -e node1 -e node2
```

## Source Modules

| Module | Responsibility |
| --- | --- |
| `main.cpp` | Boot sequence, service polling, boot JSON message. |
| `Config.h` | Firmware constants, pin map, product names, protocol UUIDs. |
| `CommandService` | Transport-independent command parsing and response envelope. |
| `RadioService` | nRF24 setup, config, TX/RX, FIFO control, packet polling. |
| `BridgeService` | RF packet forwarding to WebSocket and BLE. |
| `WebService` | SoftAP, HTTP API, browser UI, WebSocket server. |
| `BleService` | BLE UART-style command and notification transport. |
| `Utils` | Hex, RF address, datarate, power, and JSON helpers. |

## Pin Map

The V1 firmware defaults are in `include/Config.h`:

| Signal | GPIO |
| --- | --- |
| nRF24 CE | 45 |
| nRF24 CSN | 15 |
| nRF24 SCK | 14 |
| nRF24 MOSI | 13 |
| nRF24 MISO | 12 |
| RX LED | 16 |
| TX LED | 17 |

## Runtime Defaults

| Setting | Default |
| --- | --- |
| RF channel | 76 |
| RF datarate | `1mbps` |
| RF PA level | `low` |
| Auto-ACK | `true` |
| RF-to-Wi-Fi bridge | `true` |
| RF-to-BLE bridge | `true` |
| Protocol version | `1.0` |
| Firmware version | `0.1.0-v1` |

RF channel and datarate must match between peers. TX power can differ by peer.
Runtime RF settings are not persisted and return to build defaults after reboot.

## Release Build Smoke Test

```bash
cd Firmware/ESP32_RFLINK
pio run -e node1 -e node2
```

Then run the SDK tests:

```bash
cd ../../sdk/python
python -m pytest
```

For hardware validation, flash one `node1` and one `node2`, then run:

```bash
python examples/rf_ping.py --node1-serial COM5 --node2-serial COM6
```

The local web workbench can run the same validation manually: keep both serial ports open, apply matching RF config on both nodes, send ACK-required packets in both directions, and watch `rf_tx`/`rf_rx` counters plus WebSocket/BLE packet events.
