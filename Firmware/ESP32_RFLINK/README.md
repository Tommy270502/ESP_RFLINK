# Wireless Dev Bridge Firmware V1

Firmware for a USB-C multi-protocol wireless development interface based on an ESP32-S3-WROOM-1 and nRF24L01+.

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
- Browser dashboard at `http://192.168.4.1`
- WebSocket live RF packet stream on port `81`
- RF -> Wi-Fi/WebSocket bridge toggle
- WebSocket -> RF send path through the same command protocol
- Production-oriented `self_test` command

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
    "ap_ip": "192.168.4.1"
  },
  "error": null
}
```

## Known Limitations

- nRF24 payloads are limited to 32 bytes.
- nRF24 addresses are fixed at 5 bytes in this V1 firmware.
- Wi-Fi AP has no authentication beyond the shared AP password.
- HTTP and WebSocket APIs are not authenticated.
- No BLE, OTA, cloud, packet decoding, mesh networking, or persistence yet.
- RF settings are runtime-only and reset after reboot.
