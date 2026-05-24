# Wireless Dev Bridge Workbench

`main.py` is a local browser-hosted workbench for the V1 command protocol. It
starts a FastAPI/Uvicorn server on `http://127.0.0.1:5173`, opens a browser
window automatically, serves the static UI from `application/static`, and wraps
the local Python SDK from `sdk/python`.

This is a host-side tool. The local workbench URL is different from the dongle's
firmware browser dashboard at `http://192.168.4.1`.

## Install

Install web dependencies (one time):

```bash
python -m pip install -r application/requirements.txt
```

Install SDK transport dependencies (one time):

```bash
cd sdk/python
python -m pip install -e ".[all]"
```

HTTP transport does not need SDK extras, but USB serial, WebSocket, and BLE use
the SDK optional dependencies installed by `.[all]`.

## Run

From the repository root:

```bash
python application/main.py
```

The browser opens automatically. If it does not, open:

```text
http://127.0.0.1:5173
```

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | >=0.111 | REST API and SSE |
| uvicorn | >=0.29  | ASGI server |

## Architecture

- `application/main.py` is the entry point and backend.
- `application/static/index.html` contains the local HTML, CSS, and JavaScript UI.
- The backend imports the local SDK from `sdk/python` when running from a checkout.
- Blocking SDK calls run through worker threads so the web server can continue
  serving the UI and Server-Sent Events.
- SDK clients are kept open by `(transport, endpoint, timeout)` to avoid USB CDC
  reconnect resets while switching between devices.
- Live packet events use a dedicated WebSocket or BLE SDK connection and are
  broadcast to the browser over Server-Sent Events.
- Active clients and event streams are closed on **Disconnect** and during server
  shutdown.

## Local API

The browser uses these local endpoints. They are intended for the bundled UI and
bench automation, not as a stable public API.

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Local server health check. |
| `GET` | `/api/ports` | List USB serial ports when `pyserial` is installed. |
| `POST` | `/api/command` | Send one JSON command through USB serial, HTTP, WebSocket, or BLE. |
| `POST` | `/api/disconnect` | Stop live events and close all open SDK clients. |
| `POST` | `/api/events/start` | Start a live event reader over WebSocket or BLE. |
| `POST` | `/api/events/stop` | Ask the live event reader to stop. |
| `GET` | `/api/events/stream` | Browser SSE stream for event status, packets, and errors. |

Command request shape:

```json
{
  "transport": "USB serial",
  "endpoint": "COM5",
  "timeout": 3.0,
  "cmd": "status",
  "params": {}
}
```

Live event start request shape:

```json
{
  "transport": "WebSocket",
  "endpoint": "192.168.4.1",
  "timeout": 3.0
}
```

## Workflows

- Send `ping`, `status`, `self_test`, `protocol`, and `rf_get_config`.
- Keep SDK transports open between commands and endpoints to avoid USB CDC reconnect resets during two-dongle work.
- Refresh `status` automatically so counters, Wi-Fi clients, BLE connection state, and uptime stay current.
- Configure channel, datarate, power, auto-ACK, listen state, and FIFOs.
- Send text or hex nRF24 payloads with the 32-byte V1 limit enforced.
- Set 5-byte RX/TX addresses with Node 1 and Node 2 presets.
- Toggle RF-to-Wi-Fi/WebSocket and RF-to-BLE bridge forwarding.
- Stream live RF packet events over WebSocket or BLE while sending commands through another transport.
- Send raw top-level JSON commands for firmware features not surfaced by a form.

Use **Disconnect** before opening the same serial ports in another tool.

BLE mode connects to the dongle's UART-style GATT service. It is intended for
custom host tools, mobile apps, or the SDK examples to send JSON commands and
receive command responses or RF packet notifications.

## Two-Dongle RF Bring-Up

1. Flash one dongle as `node1` and the other as `node2`.
2. Select COM port for node 1, click **Status**, and confirm RX `NODE1`, TX `NODE2`.
3. Select COM port for node 2, click **Status**, and confirm RX `NODE2`, TX `NODE1`.
4. Set the same channel, datarate, and auto-ACK state on both dongles with **Apply Config**.
5. Send a packet from each side with **Require ACK** enabled.
6. Confirm `rf_tx` increments on the sender and `rf_rx` increments on the receiver.

The app keeps separate open SDK clients for each endpoint. This avoids USB CDC
reconnect resets when switching between COM ports.

## RF Config Notes

- Channel must match on both RF peers.
- Datarate must match on both RF peers: `250kbps`, `1mbps`, or `2mbps`.
- Power can differ by peer: `min`, `low`, `high`, or `max`.
- Runtime RF settings reset when a dongle reboots.
- The app protects in-progress RF config edits from automatic status refreshes.

## Live Events

Use the **Live Events** tab to prove the wireless bridge paths:

- WebSocket: connect the PC to one dongle AP, start a WebSocket stream to
  `192.168.4.1`, then send an RF packet from the other dongle.
- BLE: start a BLE stream to `WirelessDev-Node1` or `WirelessDev-Node2`, then
  send an RF packet from the peer. BLE streaming requires `bleak` from the
  SDK's `.[all]` or `.[ble]` extra.

For packet events, the matching bridge toggle must be enabled:

- WebSocket uses `rf_to_wifi`.
- BLE uses `rf_to_ble`.

Expected packet event shape:

```json
{"type":"packet","source":"rf","data":{"len":5,"hex":"68656C6C6F","uptime_ms":12345}}
```

## Troubleshooting

- **FastAPI/Uvicorn missing:** run `python -m pip install -r application/requirements.txt`.
- **No serial ports:** install the SDK serial extra with `python -m pip install -e "sdk/python[serial]"`, reconnect the dongle, then click **Refresh**.
- **Port 5173 already in use:** stop the other process before running `python application/main.py`.
- **WebSocket live events fail:** connect the PC to the dongle AP or otherwise route to `192.168.4.1`.
- **BLE commands or events fail:** install the BLE extra, confirm a working BLE adapter, and use the advertised device name or address.
- **Another tool cannot open the COM port:** click **Disconnect** or stop the workbench first.
