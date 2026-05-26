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
| `settings_get` | Read effective runtime settings and persisted-settings state. |
| `settings_set` | Apply partial RF, bridge, device, or security settings. |
| `settings_save` | Persist current settings to NVS. |
| `settings_reset` | Clear persisted settings and restore defaults. |
| `diagnostics` | Return self-test, status, settings, reset reason, chip, heap, counters, and last error data. |
| `identify` | Blink the LED and return identity fields for matching a physical dongle. |

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
| `device.id` | MAC-derived identity used for support and physical device matching. |
| `storage.dirty` | Runtime settings differ from saved NVS settings. |
| `security.auth_required` | Whether non-USB command surfaces require a token. |
| `reset_reason` | Last reset reason reported by the ESP32 runtime. |
| `last_error` | Last command error object, or `null` when no command error has been recorded. |

## CLI Command Mapping

| CLI command | Firmware command | Notes |
| --- | --- | --- |
| `wdb discover` | — | Host-side serial port discovery, no firmware command. |
| `wdb ping` | `ping` | |
| `wdb protocol` | `protocol` | |
| `wdb status` | `status` | |
| `wdb self-test` | `self_test` | |
| `wdb identify` | `identify` | |
| `wdb diagnostics` | `diagnostics` | |
| `wdb rf-get-config` | `rf_get_config` | |
| `wdb rf-config` | `rf_config` | `--channel`, `--datarate`, `--power`, `--auto-ack` |
| `wdb rf-send` | `rf_send` | `--hex`, `--require-ack` |
| `wdb listen` | `rf_start_listen` / `rf_stop_listen` | `--start` or `--stop` |
| `wdb flush` | `rf_flush_rx` / `rf_flush_tx` | `--rx` or `--tx` |
| `wdb set-address` | `rf_set_address` | `--rx`, `--tx`, `--format` |
| `wdb bridge` | `bridge` | `--rf-to-wifi`, `--rf-to-ble` |
| `wdb settings-get` | `settings_get` | |
| `wdb settings-set` | `settings_set` | `--json` with partial settings object |
| `wdb settings-save` | `settings_save` | |
| `wdb settings-reset` | `settings_reset` | |
| `wdb setup` | `settings_set` + `settings_save` | Applies common first-run settings. |
| `wdb raw` | any | Sends raw JSON via `--json`. |
| `wdb pair-test` | multiple | Two-dongle serial RF validation sequence. |
| `wdb report` | multiple | Collects status, self-test, diagnostics, settings into a JSON report. |
| `wdb firmware flash` | — | Host-side esptool flash, no firmware command. |

## Command Request Fields

| Command | Required fields | Optional fields |
| --- | --- | --- |
| `ping` | — | — |
| `protocol` | — | — |
| `status` | — | — |
| `self_test` | — | — |
| `identify` | — | — |
| `diagnostics` | — | — |
| `rf_get_config` | — | — |
| `rf_config` | — | `channel` (int 0-125), `datarate` (string), `power` (string), `auto_ack` (bool) |
| `rf_send` | `hex` (string) | `require_ack` (bool) |
| `rf_start_listen` | — | — |
| `rf_stop_listen` | — | — |
| `rf_flush_rx` | — | — |
| `rf_flush_tx` | — | — |
| `rf_set_address` | — | `rx` (string), `tx` (string), `format` (`ascii`/`hex`), `pipe` + `address` |
| `bridge` | — | `rf_to_wifi` (bool), `rf_to_ble` (bool) |
| `settings_get` | — | — |
| `settings_set` | — | `rf` (object), `bridge` (object), `device` (object), `security` (object) |
| `settings_save` | — | — |
| `settings_reset` | — | — |

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

```json
{"cmd":"settings_set","rf":{"channel":76,"datarate":"1mbps","power":"low","rx":"NODE1","tx":"NODE2","address_format":"ascii"},"bridge":{"rf_to_wifi":true,"rf_to_ble":true}}
```

```json
{"cmd":"settings_save"}
```

```json
{"cmd":"diagnostics"}
```

```json
{"cmd":"identify"}
```

## Settings And Auth

Protocol `1.1` adds NVS-backed settings. `settings_set` accepts partial objects:

| Object | Fields |
| --- | --- |
| `rf` | `channel`, `datarate`, `power`, `auto_ack`, `rx`, `tx`, `address_format` |
| `bridge` | `rf_to_wifi`, `rf_to_ble` |
| `device` | `name`, `ap_ssid`, `ap_pass`, `ble_name` |
| `security` | `auth_required`, `auth_token` |

HTTP uses the `X-WDB-Token` header when auth is required. WebSocket and BLE use top-level JSON field `auth`. USB serial remains the trusted setup path.

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

The generic `/api/command` route is the canonical route for protocol `1.1` commands such as `settings_get`, `settings_set`, `diagnostics`, and `identify`.

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
    "protocol": "1.1",
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

## Error Taxonomy

Error responses include a `code` and `message`. Codes are stable across firmware versions.

| Code | Commands | Meaning |
| --- | --- | --- |
| `unknown_cmd` | any | Command name not recognized. |
| `missing_cmd` | — | Request JSON has no `cmd` field. |
| `invalid_json` | — | Request is not valid JSON. |
| `line_too_long` | — | Serial line exceeds maximum length. |
| `auth_required` | any | Non-USB transport requires a valid token. |
| `invalid_arg` | multiple | Argument has wrong type or format. |
| `missing_arg` | `rf_send`, `rf_set_address` | Required field is absent. |
| `invalid_channel` | `rf_config` | Channel outside 0-125 range. |
| `invalid_datarate` | `rf_config` | Datarate not `250kbps`, `1mbps`, or `2mbps`. |
| `invalid_power` | `rf_config` | Power not `min`, `low`, `high`, or `max`. |
| `empty_payload` | `rf_send` | Hex payload is empty. |
| `invalid_hex` | `rf_send` | Payload contains non-hex characters or odd length. |
| `payload_too_large` | `rf_send` | Payload exceeds 32 bytes. |
| `invalid_address` | `rf_set_address`, `settings_set` | Address not 5 ASCII chars or 10 hex chars. |
| `invalid_pipe` | `rf_set_address` | Pipe must be `rx` or `tx`. |
| `invalid_setting` | `settings_set` | Setting value out of range (name length, password length, token length). |
| `radio_not_initialized` | RF commands | nRF24L01+ failed initialization. |
| `nvs_error` | `settings_save`, `settings_reset` | NVS write/erase failed. |
| `send_failed` | `rf_send` | nRF24 TX failed (no ACK or hardware error). |

## Auth Behavior

USB serial is always trusted and never requires authentication.

When `security.auth_required` is `true`:

- **HTTP**: include the token as `X-WDB-Token` header.
- **WebSocket**: include `"auth": "<token>"` in each command JSON.
- **BLE**: include `"auth": "<token>"` in each command JSON.

Commands without a valid token receive an `auth_required` error. Set `security.auth_token` through `settings_set` over USB serial, then `settings_save` to persist.
