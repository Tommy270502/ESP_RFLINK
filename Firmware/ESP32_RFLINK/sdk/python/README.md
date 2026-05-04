# Wireless Dev Bridge Python SDK

Host-side SDK for the Wireless Dev Bridge firmware.

## Install

HTTP-only usage has no runtime dependencies:

```bash
cd sdk/python
python -m pip install -e .
```

For USB serial and WebSocket support:

```bash
python -m pip install -e ".[all]"
```

## Quick Start

HTTP, when connected to the device AP:

```python
from wireless_dev_bridge import WirelessDevBridge

dev = WirelessDevBridge.http("192.168.4.1")
print(dev.status())
print(dev.rf_send_hex("1234", require_ack=True))
```

USB serial:

```python
from wireless_dev_bridge import WirelessDevBridge

dev = WirelessDevBridge.serial("COM5")
print(dev.self_test())
dev.rf_send_bytes(b"hello", require_ack=True)
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

For Wi-Fi-driven tests, use host arguments instead:

```bash
python examples/rf_ping.py --node1-host 192.168.4.1 --node2-host 192.168.4.2 --skip-rx-check
```

## CLI

```bash
wdb --host 192.168.4.1 status
wdb --host 192.168.4.1 rf-send 1234 --require-ack
wdb --serial COM5 self-test
wdb --serial COM5 rf-config --channel 76 --datarate 1mbps --power low
```

The CLI prints the full device response JSON.
