# Getting Started

This guide takes a new developer from clone to a working Wireless Dev Bridge dongle.

## Requirements

- ESP32-S3 Wireless Dev Bridge hardware.
- USB-C cable with data support.
- PlatformIO Core or the PlatformIO IDE extension.
- Python 3.9 or newer.
- Optional transport packages for USB serial, WebSocket, BLE, and MQTT examples.

## 1. Build Firmware

```bash
cd Firmware/ESP32_RFLINK
pio run -e node1
```

The default firmware target is `node1`. For paired RF testing, build both node roles:

```bash
pio run -e node1 -e node2
```

## 2. Flash A Dongle

List connected serial ports:

```bash
pio device list
```

Upload to a specific port:

```bash
pio run -e node1 --target upload --upload-port COM5
```

If the device was previously flashed with a different partition layout, erase once:

```bash
pio run -e node1 --target erase --upload-port COM5
pio run -e node1 --target upload --upload-port COM5
```

## 3. Install The SDK

From the repository root:

```bash
cd sdk/python
python -m pip install -e ".[all]"
```

HTTP-only SDK usage has no runtime dependencies, but `.[all]` installs the optional serial, WebSocket, BLE, and MQTT transports used by the examples.

## 4. Run A Smoke Test

USB serial:

```bash
wdb --serial COM5 self-test
wdb --serial COM5 status
```

Wi-Fi:

```bash
wdb --host 192.168.4.1 status
```

BLE:

```bash
wdb --ble WirelessDev-Node1 status
```

## 5. Use The Browser Dashboard

Connect your computer to the dongle access point, then open:

```text
http://192.168.4.1
```

Default node SSIDs:

- `WirelessDev-Node1`
- `WirelessDev-Node2`

Default AP password:

```text
12345678
```

## 6. Run A Two-Dongle RF Test

Flash one dongle as `node1` and the other as `node2`, then run:

```bash
cd sdk/python
python examples/rf_ping.py --node1-serial COM5 --node2-serial COM6
```

The test verifies role, radio health, RF config, complementary addresses, and ACK-required traffic in both directions.

## Common Workflows

Monitor RF packets over WebSocket:

```bash
python examples/packet_monitor.py --ws 192.168.4.1 --count 10
```

Bridge RF packet events to BLE:

```bash
wdb --ble WirelessDev-Node1 bridge rf-to-ble on
python examples/packet_monitor.py --ble WirelessDev-Node1 --count 10
```

Bridge RF packet events to MQTT:

```bash
python -m pip install -e ".[mqtt]"
python examples/bridge_to_mqtt.py --ws 192.168.4.1 --broker localhost --topic-prefix lab/bridge1
```

Inventory a bench before a test run:

```bash
python examples/device_inventory.py --device serial:COM5 --device serial:COM6
```
