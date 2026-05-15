# SDK

Host-side SDKs and automation tools for Wireless Dev Bridge.

The V1 Python SDK, CLI, tests, and examples live in:

```text
sdk/python
```

Install from the repository root:

```bash
cd sdk/python
python -m pip install -e ".[all]"
```

See [Python SDK README](python/README.md) for examples, optional transports, and test instructions.

The desktop workbench in [`../application`](../application/README.md) uses this SDK instead of duplicating the command protocol. It exposes serial, HTTP, WebSocket, BLE, RF config, packet send, bridge toggles, and live WebSocket/BLE packet events.
