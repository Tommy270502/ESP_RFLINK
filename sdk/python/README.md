# Wireless Dev Bridge Python SDK

Host-side SDK for the Wireless Dev Bridge firmware.

## Install

HTTP-only usage has no runtime dependencies:

```bash
# from the repository root
cd sdk/python
python -m pip install -e .
```

Install transport extras for USB serial, WebSocket, BLE, and MQTT examples:

```bash
python -m pip install -e ".[all]"
```

For tests only:

```bash
python -m pip install -e ".[test]"
```

## Quick Start

Minimal Wi-Fi connection, when your computer is connected to the dongle AP:

```python
from wireless_dev_bridge import BridgeError, WirelessDevBridge

dev = WirelessDevBridge.http("192.168.4.1", timeout=3.0)
try:
    print(dev.status())
    print(dev.rf_send_hex("1234", require_ack=False))
except BridgeError as exc:
    print(f"device request failed: {exc}")
finally:
    dev.close()
```

USB serial:

```python
from wireless_dev_bridge import WirelessDevBridge

dev = WirelessDevBridge.serial("COM5")
try:
    print(dev.self_test())
    dev.rf_send_bytes(b"hello", require_ack=True)
finally:
    dev.close()
```

BLE:

```python
from wireless_dev_bridge import WirelessDevBridge

dev = WirelessDevBridge.ble("WirelessDev-Node1")
try:
    dev.bridge(rf_to_ble=True)
    print(dev.protocol())
finally:
    dev.close()
```

## Getting Started By Workflow

Monitor RF packets from a dongle.
Use this when you need a live packet log during firmware bring-up or RF troubleshooting.

```bash
python examples/packet_monitor.py --ws 192.168.4.1 --count 10
python examples/packet_monitor.py --ble WirelessDev-Node1 --count 10
```

Expected output shape:

```text
2026-05-05T12:00:00+00:00 uptime_ms=12345 len=2 hex=1234
```

Bridge RF events to BLE.
Use this when a BLE host, phone app, or field tool should receive nRF24 packet events from the dongle.

```bash
wdb --ble WirelessDev-Node1 bridge rf-to-ble on
python examples/packet_monitor.py --ble WirelessDev-Node1 --count 10
```

Expected command response shape:

```json
{"ok":true,"cmd":"bridge","data":{"rf_to_ble":true},"error":null}
```

Bridge RF events to MQTT.
Use this for test benches, lab automation, or dashboards that already consume MQTT.

```bash
python -m pip install -e ".[mqtt]"
python examples/bridge_to_mqtt.py --ws 192.168.4.1 --broker localhost --topic-prefix lab/bridge1
```

Expected MQTT payload shape:

```json
{"type":"packet","source":"rf","data":{"len":2,"hex":"1234","uptime_ms":12345}}
```

Run a bench inventory/self-test.
Use this before a test run to verify firmware version, role, heap, radio health, and RF config.

```bash
python examples/device_inventory.py --device serial:COM5 --device serial:COM6
```

Expected output shape:

```text
SPEC                     OK  ROLE     FW         BLE                RADIO CH  RATE    RX       TX
serial:COM5              yes node1    0.1.0-v1   WirelessDev-Node1  yes   76  1mbps   NODE1    NODE2
```

Measure transport latency.
Use this to compare HTTP, USB serial, WebSocket, and BLE command round trips.

```bash
python examples/latency_benchmark.py --host 192.168.4.1 --count 50
python examples/latency_benchmark.py --ble WirelessDev-Node1 --count 50 --json
```

Expected output shape:

```text
http 192.168.4.1 ping
count=50 min=12.20ms avg=18.40ms p95=28.10ms max=31.80ms
```

Use the CLI for quick validation.
Use this when you want a fast smoke check without writing Python code.

```bash
wdb --serial COM5 self-test
wdb --host 192.168.4.1 status
wdb --ws 192.168.4.1 bridge rf-to-wifi on
wdb --ble WirelessDev-Node1 bridge rf-to-ble on
```

## Production Test

Run the bundled two-device production test over USB serial:

```bash
python examples/rf_ping.py --node1-serial COM8 --node2-serial COM11
```

This script:

- verifies each device role and radio health
- sets complementary RF addresses
- applies a known RF config
- flushes FIFOs and enables listening
- sends an ACK-required payload in each direction
- confirms the opposite device received the expected RF packet

For network-driven tests, pass the reachable HTTP host for each dongle. A dongle in SoftAP mode normally serves HTTP at `192.168.4.1`; if you are testing two SoftAP dongles, your host must connect to the correct AP or provide separate reachable routes for each device. USB serial is the simplest two-node path:

```bash
python examples/rf_ping.py --node1-serial COM8 --node2-serial COM11
```

## Examples

- `examples/packet_monitor.py`: stream RF packet events over WebSocket, BLE, or serial.
- `examples/bridge_to_mqtt.py`: publish RF packet events to MQTT. Requires `paho-mqtt` or `.[mqtt]`.
- `examples/ble_console.py`: run interactive or one-shot maintenance commands over BLE.
- `examples/latency_benchmark.py`: measure command or optional RF send latency.
- `examples/device_inventory.py`: run `self_test` and RF config reads across multiple devices.
- `examples/rf_ping.py`: two-device RF production test.

All examples support `--help`.

## CLI

```bash
wdb --host 192.168.4.1 status
wdb --host 192.168.4.1 rf-send 1234 --require-ack
wdb --serial COM5 self-test
wdb --serial COM5 rf-config --channel 76 --datarate 1mbps --power low
wdb --ws 192.168.4.1 bridge rf-to-wifi on
wdb --ble WirelessDev-Node1 bridge rf-to-ble on
wdb --ble WirelessDev-Node1 rf-send 1234 --require-ack
```

The legacy bridge form still controls RF-to-Wi-Fi:

```bash
wdb --ws 192.168.4.1 bridge on
wdb --ws 192.168.4.1 bridge off
```

The CLI prints the full device response JSON.

## BLE GATT Details

BLE uses newline-delimited JSON over a UART-style GATT service:

- Service UUID: `6e400001-b5a3-f393-e0a9-e50e24dcca9e`
- RX write UUID: `6e400002-b5a3-f393-e0a9-e50e24dcca9e`
- TX notify UUID: `6e400003-b5a3-f393-e0a9-e50e24dcca9e`

Subscribe to TX notifications before writing commands to RX. Notifications may contain partial JSON lines, so clients should buffer until `\n`.

## Tests

The SDK test suite does not require hardware:

```bash
# from the repository root
cd sdk/python
python -m pytest
```

## Product Applications

- nRF24 manufacturing tester: one dongle acts as the fixture controller while another or a known-good device acts as the golden peer.
- BLE-to-nRF24 bridge for mobile apps: a phone or tablet talks BLE to the ESP32-S3, then the dongle drives nRF24 test devices.
- RF regression harness: CI or bench scripts replay known packet patterns through the SDK.
- Classroom wireless lab tool: one USB-C dongle exposes serial, Wi-Fi, BLE, and 2.4 GHz RF workflows.
- Portable field diagnostic bridge: a laptop or BLE host inspects nearby nRF24-based nodes without a custom adapter.
- Interactive protocol workbench: combine WebSocket events with a browser UI for packet watch, send, and config changes.
- Sensor gateway prototype: nRF24 edge nodes report to the dongle while applications consume data through HTTP, WebSocket, or BLE.
