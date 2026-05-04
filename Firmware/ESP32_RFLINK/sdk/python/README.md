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

## CLI

```bash
wdb --host 192.168.4.1 status
wdb --host 192.168.4.1 rf-send 1234 --require-ack
wdb --serial COM5 self-test
wdb --serial COM5 rf-config --channel 76 --datarate 1mbps --power low
```

The CLI prints the full device response JSON.
