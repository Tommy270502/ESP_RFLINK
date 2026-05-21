# Security Model

Wireless Dev Bridge is designed for trusted developer benches and lab networks.

## Default Behavior

- USB serial is treated as the trusted setup path.
- Wi-Fi SoftAP uses the configured AP password.
- HTTP, WebSocket, and BLE command APIs are unauthenticated by default for fast bench bring-up.
- RF traffic is not encrypted by the dongle.

## Optional Command Auth

Protocol `1.1` adds optional token auth for non-USB command surfaces:

- HTTP: send `X-WDB-Token`.
- WebSocket and BLE: include top-level JSON field `auth`.
- `ping`, `protocol`, and `capabilities` remain available without auth for discovery.

Example:

```bash
wdb --serial COM5 setup --auth-required --device-auth-token lab-secret --save
wdb --host 192.168.4.1 --auth-token lab-secret diagnostics
```

If auth is required and the token is missing or wrong, commands return:

```json
{"ok":false,"cmd":"status","data":{},"error":{"code":"auth_required","message":"valid auth token required"}}
```

## Operational Guidance

- Do not expose the AP, HTTP, WebSocket, or BLE command surfaces to untrusted networks.
- Rotate the token before sharing hardware outside a trusted bench.
- Use `settings_reset` over USB serial to clear persisted settings and auth state.
