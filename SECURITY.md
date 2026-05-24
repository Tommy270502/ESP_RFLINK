# Security

Wireless Dev Bridge V1 is intended for trusted developer benches and lab networks.

## V1 Security Model

- The Wi-Fi SoftAP uses a shared AP password.
- USB serial is treated as the trusted setup path.
- HTTP, WebSocket, and BLE command APIs are unauthenticated by default for fast lab bring-up, but protocol `1.1` supports optional token auth.
- RF packet data is treated as lab/test traffic and is not encrypted by the dongle.

Do not expose the Wi-Fi, WebSocket, HTTP, or BLE control surfaces to untrusted networks or untrusted physical environments.

See [docs/security-model.md](docs/security-model.md) for the optional auth workflow.

## Reporting

Open a private security report or contact the maintainer before disclosing vulnerabilities publicly.
