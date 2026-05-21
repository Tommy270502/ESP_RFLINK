# Troubleshooting

## Start With A Report

Collect a support report before changing multiple variables:

```bash
wdb --serial COM5 report --output reports/device-report.json
```

Attach the report when opening an issue.

## USB Serial

- Use a USB-C cable with data support.
- Run `wdb discover` to list serial ports.
- Use **Disconnect** in the desktop workbench before opening the same port in another tool.
- If serial output contains boot messages before command responses, the SDK filters events and waits for the matching command response.

## RF Pairing

- Both peers must use the same channel and datarate.
- `node1` defaults to RX `NODE1`, TX `NODE2`.
- `node2` defaults to RX `NODE2`, TX `NODE1`.
- Use ACK-required sends for validation because ACK failures increment `stats.rf_tx_fail`.

## Wi-Fi And Browser Dashboard

- Connect the host computer to the dongle AP before opening `http://192.168.4.1`.
- If optional auth is enabled, enter the token in the browser dashboard settings area.
- AP SSID and password changes require reboot after `settings_save`.

## BLE

- BLE uses GATT, not classic serial.
- Install the SDK `ble` or `all` extra for Python BLE tools.
- BLE notifications may split JSON lines; use the SDK or buffer until newline.

## Reset Settings

Use USB serial:

```bash
wdb --serial COM5 settings-reset
```

This clears persisted settings and restores defaults. Device/AP/BLE name changes may require reboot to be fully reflected by active services.
