# Wireless Dev Bridge Workbench

`main.py` is a Tkinter desktop workbench for the V1 command protocol. It imports
the local Python SDK from `sdk/python`, so it can be run from a repository
checkout without packaging the app separately.

## Run

From the repository root:

```bash
python application/main.py
```

HTTP mode has no optional runtime dependency. USB serial, WebSocket, and BLE use
the same optional SDK dependencies as the CLI:

```bash
cd sdk/python
python -m pip install -e ".[all]"
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
