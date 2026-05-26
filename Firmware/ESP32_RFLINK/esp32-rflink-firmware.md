# Wireless Dev Bridge Firmware V1

Firmware for a USB-C multi-protocol wireless development interface based on an ESP32-S3-WROOM-1 and nRF24L01+.

For the full product launch package, start at the repository root [Project Overview](../../project-overview.md). For the complete command protocol, see [API Reference](../../docs/api-reference.md).

## Target

- Framework: PlatformIO + Arduino
- Board profile: `esp32-s3-devkitc-1`
- MCU: ESP32-S3-WROOM-1
- Flash target: 4 MB
- RF: nRF24L01+
- USB: native USB CDC serial

## Features

- Newline-delimited USB serial JSON command API
- nRF24L01+ send, receive, configure, listen control, FIFO flush, and address configuration
- Wi-Fi AP mode with firmware browser dashboard at `http://192.168.4.1`
- BLE GATT JSON command transport
- WebSocket live RF packet stream on port `81`
- RF-to-WiFi/WebSocket and RF-to-BLE bridge toggles
- Production-oriented `self_test` command
- Protocol 1.1 settings persistence, diagnostics, identify, optional auth, and support metadata

## Build And Upload

1. Open this folder in PlatformIO.
2. Review hardware values in `include/Config.h`.
3. Build the default environment (`node1`):

```bash
pio run
```

4. Upload:

```bash
pio run --target upload
```

If the device was previously flashed with an 8 MB image or shows core dump CRC warnings, erase once before uploading:

```bash
pio run --target erase
pio run --target upload
```

BLE support requires a larger app partition than the Arduino default OTA layout provides on 4 MB flash. This firmware uses `no_ota.csv`, giving one larger app slot and no OTA slot.

5. Monitor serial:

```bash
pio device monitor -b 115200
```

## Node-Specific Builds

Two PlatformIO environments are provided for RF pair testing:

- `node1`: RX `NODE1`, TX `NODE2`, Wi-Fi AP `WirelessDev-Node1`
- `node2`: RX `NODE2`, TX `NODE1`, Wi-Fi AP `WirelessDev-Node2`

Build both:

```bash
pio run -e node1 -e node2
```

Upload to specific ports when both boards are connected:

```bash
pio device list
pio run -e node1 --target upload --upload-port COM5
pio run -e node2 --target upload --upload-port COM6
```

## Pin Configuration

Edit `include/Config.h` for the final PCB:

- `PIN_NRF_CE`
- `PIN_NRF_CSN`
- `PIN_NRF_SCK`
- `PIN_NRF_MOSI`
- `PIN_NRF_MISO`
- `PIN_LED_Rx`
- `PIN_LED_Tx`
- `PIN_LED`

The default nRF24 address width is 5 bytes. The fallback generic defaults are printable developer values:

- RX: `NODE1`
- TX: `NODE2`

For paired testing, prefer the `node1` and `node2` PlatformIO environments so the addresses are complementary at build time.

## Wi-Fi AP

- SSID: `WirelessDev-Bridge`
- Node 1 SSID: `WirelessDev-Node1`
- Node 2 SSID: `WirelessDev-Node2`
- Password: `12345678`
- Firmware browser dashboard: `http://192.168.4.1`
- WebSocket: `ws://192.168.4.1:81/`

## Boot Log

On startup the firmware emits a serial boot JSON message:

```json
{
  "type": "boot",
  "ok": true,
  "cmd": "boot",
  "data": {
    "product": "WirelessDevBridge",
    "fw": "0.1.0-v1",
    "uptime_ms": 1000,
    "radio_initialized": true,
    "radio_chip_connected": true,
    "ap_ssid": "WirelessDev-Bridge",
    "ap_ip": "192.168.4.1",
    "ble_enabled": true,
    "ble_name": "WirelessDev-Node1"
  },
  "error": null
}
```

## Getting Started By Workflow

Monitor RF packets from a dongle:

```bash
cd ../../sdk/python
python examples/packet_monitor.py --ws 192.168.4.1 --count 10
```

The local web workbench **Live Events** tab provides the same WebSocket/BLE packet visibility while USB serial remains available for command control.

Bridge RF events to BLE:

```bash
wdb --ble WirelessDev-Node1 bridge rf-to-ble on
python examples/packet_monitor.py --ble WirelessDev-Node1 --count 10
```

Run a bench inventory/self-test:

```bash
python examples/device_inventory.py --device serial:COM5 --device serial:COM6
```

## Product Applications

- nRF24 manufacturing tester: one dongle acts as the fixture controller while another or a known-good device acts as the golden peer.
- BLE-to-nRF24 bridge for mobile apps: a phone or tablet talks BLE to the ESP32-S3, then the dongle drives nRF24 test devices.
- RF regression harness: CI or bench scripts replay known packet patterns through the SDK.
- Classroom wireless lab tool: one USB-C dongle exposes serial, Wi-Fi, BLE, and 2.4 GHz RF workflows.
- Portable field diagnostic bridge: a laptop or BLE host inspects nearby nRF24-based nodes without a custom adapter.
- Interactive protocol workbench: combine WebSocket events with a browser UI for packet watch, send, and config changes.
- Sensor gateway prototype: nRF24 edge nodes report to the dongle while applications consume data through HTTP, WebSocket, or BLE.

## Known Limitations

- nRF24 payloads are limited to 32 bytes.
- nRF24 addresses are fixed at 5 bytes in this V1 firmware.
- Wi-Fi AP has no authentication beyond the configured AP password.
- HTTP, WebSocket, and BLE APIs are unauthenticated by default, with optional token auth in protocol 1.1.
- No OTA, cloud, packet decoding, or mesh networking yet.

## Canonical Documentation

- Command protocol, HTTP routes, WebSocket events, BLE UUIDs, and error codes: [API Reference](../../docs/api-reference.md)
- Firmware build environments and module guide: [Firmware Guide](../../docs/firmware.md)
- System architecture diagrams: [Architecture](../../docs/architecture.md)
