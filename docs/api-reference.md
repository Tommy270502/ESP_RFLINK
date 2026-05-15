# API Reference

Wireless Dev Bridge uses the same JSON command model over USB serial, HTTP, WebSocket, and BLE.

## Response Envelope

Successful commands:

```json
{
  "ok": true,
  "cmd": "status",
  "data": {},
  "error": null
}
```

Errors:

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

## Transports

| Transport | Framing | Endpoint |
| --- | --- | --- |
| USB CDC serial | Newline-delimited JSON | 115200 baud |
| HTTP | JSON request/response | `http://192.168.4.1` |
| WebSocket | JSON messages | `ws://192.168.4.1:81/` |
| BLE GATT | Newline-delimited JSON | UART-style service |

## Commands

| Command | Purpose |
| --- | --- |
| `ping` | Basic liveness check. |
| `protocol` | Capability and protocol metadata. |
| `capabilities` | Alias for `protocol`. |
| `status` | Runtime status, radio config, bridge state, BLE state, Wi-Fi state, and counters. |
| `self_test` | Production-oriented radio, Wi-Fi, BLE, heap, and role check. |
| `rf_get_config` | Read current RF config. |
| `rf_config` | Set channel, datarate, power, and auto-ACK. |
| `rf_send` | Send a hex payload over nRF24. |
| `rf_start_listen` | Enter receive/listen mode. |
| `rf_stop_listen` | Stop receive/listen mode. |
| `rf_flush_rx` | Flush nRF24 RX FIFO. |
| `rf_flush_tx` | Flush nRF24 TX FIFO. |
| `rf_set_address` | Set RX and/or TX pipe addresses. |
| `bridge` | Enable or disable RF-to-Wi-Fi and RF-to-BLE event forwarding. |

## Status Data

`status` returns the current runtime state. Useful fields:

| Field | Meaning |
| --- | --- |
| `radio.channel` | nRF24 channel, `0..125`. |
| `radio.datarate` | nRF24 datarate: `250kbps`, `1mbps`, or `2mbps`. Both RF peers must match. |
| `radio.power` | TX power: `min`, `low`, `high`, or `max`. |
| `radio.listening` | Whether the radio is in RX/listen mode. |
| `radio.rx_address_ascii` / `radio.tx_address_ascii` | Printable 5-byte pipe addresses when available. |
| `wifi.clients` | Number of stations associated to the SoftAP. |
| `ble.connected` | Whether a BLE central is connected. |
| `stats.rf_tx` / `stats.rf_rx` | RF packets transmitted and received. |
| `stats.rf_tx_fail` | RF send failures, including ACK timeouts. |

## Command Examples

```json
{"cmd":"status"}
```

```json
{"cmd":"rf_config","channel":76,"datarate":"1mbps","power":"low","auto_ack":true}
```

```json
{"cmd":"rf_send","hex":"68656C6C6F","require_ack":true}
```

```json
{"cmd":"rf_set_address","rx":"NODE1","tx":"NODE2","format":"ascii"}
```

```json
{"cmd":"bridge","rf_to_wifi":true,"rf_to_ble":true}
```

## HTTP Routes

| Route | Method | Purpose |
| --- | --- | --- |
| `/api/status` | `GET` | Runtime status. |
| `/api/self_test` | `GET` | Self-test response. |
| `/api/command` | `POST` | Generic command endpoint. |
| `/api/rf/config` | `GET` | Read RF config. |
| `/api/rf/config` | `POST` | Apply RF config. |
| `/api/rf/send` | `POST` | Send RF payload. |
| `/api/rf/listen/start` | `POST` | Start listening. |
| `/api/rf/listen/stop` | `POST` | Stop listening. |
| `/api/rf/flush_rx` | `POST` | Flush RX FIFO. |
| `/api/rf/flush_tx` | `POST` | Flush TX FIFO. |
| `/api/bridge` | `POST` | Set bridge state. |

## RF Packet Event

RF packet events are emitted on USB serial, WebSocket when `rf_to_wifi` is enabled, and BLE notifications when `rf_to_ble` is enabled.

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

## Status Event

```json
{
  "type": "status",
  "data": {
    "fw": "0.1.0-v1",
    "protocol": "1.0",
    "role": "node1",
    "uptime_ms": 12345,
    "radio": {},
    "wifi": {},
    "bridge": {},
    "ble": {},
    "stats": {}
  }
}
```

## BLE GATT

BLE advertises with the node-specific device name:

- `WirelessDev-Node1`
- `WirelessDev-Node2`

UART-style service:

| Item | UUID |
| --- | --- |
| Service | `6e400001-b5a3-f393-e0a9-e50e24dcca9e` |
| RX write | `6e400002-b5a3-f393-e0a9-e50e24dcca9e` |
| TX notify | `6e400003-b5a3-f393-e0a9-e50e24dcca9e` |

Subscribe to TX notifications before writing commands to RX. Responses are newline-terminated and may be split across multiple notifications.

BLE is a GATT command/event transport, not classic Bluetooth serial. A BLE central writes JSON commands to RX and receives command responses or packet events on TX.
