# Security

Wireless Dev Bridge V1 is intended for trusted developer benches and lab networks.

## V1 Security Model

- The Wi-Fi SoftAP uses a shared AP password.
- HTTP, WebSocket, USB serial, and BLE command APIs are not authenticated.
- RF packet data is treated as lab/test traffic and is not encrypted by the dongle.

Do not expose the Wi-Fi, WebSocket, HTTP, or BLE control surfaces to untrusted networks or untrusted physical environments.

## Reporting

Open a private security report or contact the maintainer before disclosing vulnerabilities publicly.
