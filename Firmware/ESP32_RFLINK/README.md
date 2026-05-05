# Wireless Dev Bridge Firmware V1

Firmware for a USB-C multi-protocol wireless development interface based on an ESP32-S3-WROOM-1 and nRF24L01+.

For the full product launch package, start at the repository root `README.md`.

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
- Wi-Fi AP mode
- BLE GATT JSON command transport
- Browser dashboard at `http://192.168.4.1`
- WebSocket live RF packet stream on port `81`
- RF -> Wi-Fi/WebSocket bridge toggle
- RF -> BLE notification bridge toggle
- WebSocket -> RF send path through the same command protocol
- Production-oriented `self_test` command
- Python host SDK in repository root `sdk/python`

## Host SDK

A Python SDK is included for application and test development. HTTP mode works with the Python standard library. USB serial, WebSocket, and BLE modes use optional dependencies.

Install the SDK:

```bash
cd ../../sdk/python
python -m pip install -e .
```

Install all transport extras:

```bash
python -m pip install -e ".[all]"
```

Use the CLI over Wi-Fi:

```bash
wdb --host 192.168.4.1 status
wdb --host 192.168.4.1 rf-send 1234 --require-ack
```

Use the CLI over USB serial:

```bash
wdb --serial COM5 self-test
wdb --serial COM5 rf-config --channel 76 --datarate 1mbps --power low
```

Use the CLI over BLE:

```bash
wdb --ble WirelessDev-Node1 status
wdb --ble WirelessDev-Node1 bridge rf-to-ble on
wdb --ble WirelessDev-Node1 rf-send 1234 --require-ack
```

Use it from Python:

```python
from wireless_dev_bridge import WirelessDevBridge

dev = WirelessDevBridge.serial("COM5")
print(dev.status())
dev.rf_send_bytes(b"hello", require_ack=True)
```

BLE from Python:

```python
from wireless_dev_bridge import WirelessDevBridge

dev = WirelessDevBridge.ble("WirelessDev-Node1")
dev.bridge(rf_to_ble=True)
print(dev.protocol())
```

Run the bundled two-device production test:

```bash
cd ../../sdk/python
python examples/rf_ping.py --node1-serial COM8 --node2-serial COM11
```

Additional launch examples are included in repository root `sdk/python/examples`:

- `packet_monitor.py`: stream RF packet events over WebSocket, BLE, or serial.
- `bridge_to_mqtt.py`: publish RF packet events to MQTT for lab automation. Requires `paho-mqtt` or `.[mqtt]`.
- `ble_console.py`: run interactive or one-shot maintenance commands over BLE.
- `latency_benchmark.py`: measure command or optional RF send latency.
- `device_inventory.py`: inventory firmware, role, heap, radio health, and RF config across devices.

## Getting Started By Workflow

Monitor RF packets from a dongle when bringing up RF firmware or debugging packet flow:

```bash
cd ../../sdk/python
python examples/packet_monitor.py --ws 192.168.4.1 --count 10
```

Expected output shape:

```text
2026-05-05T12:00:00+00:00 uptime_ms=12345 len=2 hex=1234
```

Bridge RF events to BLE when a BLE host or mobile app should receive nRF24 packet events:

```bash
wdb --ble WirelessDev-Node1 bridge rf-to-ble on
python examples/packet_monitor.py --ble WirelessDev-Node1 --count 10
```

Bridge RF events to MQTT for bench automation or dashboards:

```bash
python -m pip install -e ".[mqtt]"
python examples/bridge_to_mqtt.py --ws 192.168.4.1 --broker localhost --topic-prefix lab/bridge1
```

Run a bench inventory/self-test before test execution:

```bash
python examples/device_inventory.py --device serial:COM5 --device serial:COM6
```

Measure transport latency across HTTP, USB serial, WebSocket, or BLE:

```bash
python examples/latency_benchmark.py --host 192.168.4.1 --count 50
python examples/latency_benchmark.py --ble WirelessDev-Node1 --count 50 --json
```

Use the CLI for quick validation:

```bash
wdb --serial COM5 self-test
wdb --host 192.168.4.1 status
wdb --ws 192.168.4.1 bridge rf-to-wifi on
wdb --ble WirelessDev-Node1 bridge rf-to-ble on
```

Expected command responses use the standard JSON shape described below with `ok`, `cmd`, `data`, and `error`.

## Product Applications

- nRF24 manufacturing tester: one dongle acts as the fixture controller while another or a known-good device acts as the golden peer.
- BLE-to-nRF24 bridge for mobile apps: a phone or tablet talks BLE to the ESP32-S3, then the dongle drives nRF24 test devices.
- RF regression harness: CI or bench scripts replay known packet patterns through the SDK.
- Classroom wireless lab tool: one USB-C dongle exposes serial, Wi-Fi, BLE, and 2.4 GHz RF workflows.
- Portable field diagnostic bridge: a laptop or BLE host inspects nearby nRF24-based nodes without a custom adapter.
- Interactive protocol workbench: combine WebSocket events with a browser UI for packet watch, send, and config changes.
- Sensor gateway prototype: nRF24 edge nodes report to the dongle while applications consume data through HTTP, WebSocket, or BLE.

## Build And Upload

1. Open this folder in PlatformIO.
2. Review hardware values in `include/Config.h`.
3. Build the default environment. The default is `node1`:

```bash
pio run
```

4. Upload the default environment:

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

Upload node 1:

```bash
pio run -e node1 --target upload
```

Upload node 2:

```bash
pio run -e node2 --target upload
```

If both boards are connected, list ports first:

```bash
pio device list
```

Then upload to a specific port:

```bash
pio run -e node1 --target upload --upload-port COM5
pio run -e node2 --target upload --upload-port COM6
```

Monitor a specific port:

```bash
pio device monitor -p COM5 -b 115200
pio device monitor -p COM6 -b 115200
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

For paired testing, prefer the `node1` and `node2` PlatformIO environments above so the addresses are complementary at build time.

## Wi-Fi AP

- SSID: `WirelessDev-Bridge`
- Node 1 SSID: `WirelessDev-Node1`
- Node 2 SSID: `WirelessDev-Node2`
- Password: `12345678`
- Dashboard: `http://192.168.4.1`
- WebSocket: `ws://192.168.4.1:81/`

## BLE GATT

The firmware advertises as the node-specific BLE name:

- Node 1: `WirelessDev-Node1`
- Node 2: `WirelessDev-Node2`

BLE uses a UART-style GATT profile with newline-delimited JSON framing:

- Service UUID: `6e400001-b5a3-f393-e0a9-e50e24dcca9e`
- RX write UUID: `6e400002-b5a3-f393-e0a9-e50e24dcca9e`
- TX notify UUID: `6e400003-b5a3-f393-e0a9-e50e24dcca9e`

Write command JSON to the RX characteristic. Subscribe to TX notifications for command responses and RF packet events. Responses are newline-terminated and may be split across multiple BLE notifications.

## Command Response Format

All command responses use this shape:

```json
{
  "ok": true,
  "cmd": "status",
  "data": {},
  "error": null
}
```

Errors use a code and message:

```json
{
  "ok": false,
  "cmd": "rf_send",
  "data": {},
  "error": {
    "code": "payload_too_large",
    "message": "payload must be 32 bytes or less"
  }
}
```

## Serial Commands

Each command is one newline-delimited JSON object.

```json
{"cmd":"ping"}
```

```json
{"cmd":"status"}
```

```json
{"cmd":"self_test"}
```

```json
{"cmd":"rf_get_config"}
```

```json
{"cmd":"rf_config","channel":76,"datarate":"1mbps","power":"low"}
```

```json
{"cmd":"rf_config","auto_ack":true}
```

```json
{"cmd":"rf_send","hex":"68656C6C6F"}
```

By default `rf_send` transmits a no-ACK payload. Use `require_ack` when a peer radio is expected to acknowledge the packet:

```json
{"cmd":"rf_send","hex":"68656C6C6F","require_ack":true}
```

```json
{"cmd":"rf_start_listen"}
```

```json
{"cmd":"rf_stop_listen"}
```

```json
{"cmd":"rf_flush_rx"}
```

```json
{"cmd":"rf_flush_tx"}
```

Set a printable 5-byte address:

```json
{"cmd":"rf_set_address","pipe":"rx","address":"NODE1","format":"ascii"}
```

Set a 5-byte hex address:

```json
{"cmd":"rf_set_address","pipe":"tx","address":"4E4F444532","format":"hex"}
```

Set both addresses:

```json
{"cmd":"rf_set_address","rx":"NODE1","tx":"NODE2","format":"ascii"}
```

Bridge toggle:

```json
{"cmd":"bridge","rf_to_wifi":true}
```

Bridge RF packets to BLE notifications:

```json
{"cmd":"bridge","rf_to_ble":true}
```

## HTTP API Examples

Status:

```http
GET /api/status
```

Self-test:

```http
GET /api/self_test
```

Generic command endpoint:

```http
POST /api/command
Content-Type: application/json

{"cmd":"rf_get_config"}
```

RF config:

```http
POST /api/rf/config
Content-Type: application/json

{"channel":76,"datarate":"1mbps","power":"low"}
```

RF send:

```http
POST /api/rf/send
Content-Type: application/json

{"hex":"68656C6C6F"}
```

Bridge toggle:

```http
POST /api/bridge
Content-Type: application/json

{"rf_to_wifi":true}
```

Additional routes:

- `GET /api/rf/config`
- `POST /api/rf/listen/start`
- `POST /api/rf/listen/stop`
- `POST /api/rf/flush_rx`
- `POST /api/rf/flush_tx`

## WebSocket Messages

Connect to:

```text
ws://192.168.4.1:81/
```

Incoming RF packet event:

```json
{
  "type": "packet",
  "source": "rf",
  "data": {
    "len": 5,
    "hex": "68656C6C6F",
    "uptime_ms": 12345
  }
}
```

Status event:

```json
{
  "type": "status",
  "data": {
    "fw": "0.1.0-v1",
    "uptime_ms": 12345,
    "radio": {},
    "wifi": {},
    "bridge": {},
    "stats": {}
  }
}
```

You can send command JSON over WebSocket too:

```json
{"cmd":"rf_send","hex":"68656C6C6F"}
```

## BLE Messages

BLE uses the same command response format as USB serial, HTTP, and WebSocket. Packet events use the same event object:

```json
{"type":"packet","source":"rf","data":{"len":2,"hex":"1234","uptime_ms":12345}}
```

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

## Known Limitations

- nRF24 payloads are limited to 32 bytes.
- nRF24 addresses are fixed at 5 bytes in this V1 firmware.
- Wi-Fi AP has no authentication beyond the shared AP password.
- HTTP, WebSocket, and BLE APIs are not authenticated.
- No OTA, cloud, packet decoding, mesh networking, or persistence yet.
- RF settings are runtime-only and reset after reboot.
