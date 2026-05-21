# First Run

This guide is the product path for a new two-dongle developer kit.

## 1. Install Host Tools

```bash
cd sdk/python
python -m pip install -e ".[all]"
```

Check what the host can see:

```bash
wdb discover
```

## 2. Identify Each Dongle

Use USB serial for first setup. It remains the trusted setup path even when Wi-Fi/BLE auth is enabled.

```bash
wdb --serial COM5 identify
wdb --serial COM6 identify
```

The `identify` command blinks the device LED and returns firmware, role, AP SSID, BLE name, and device identity.

## 3. Run Diagnostics

```bash
wdb --serial COM5 diagnostics
```

Diagnostics includes self-test output, reset reason, heap, chip information, status, settings, counters, and recent command error state.

## 4. Pair-Test Two Dongles

Flash one dongle as `node1` and one as `node2`, then run:

```bash
wdb pair-test --node1-serial COM5 --node2-serial COM6
```

The pair test configures complementary addresses, applies matching RF config, flushes FIFOs, starts listening, and sends ACK-required packets in both directions.

## 5. Save Bench Settings

Apply settings through the CLI or desktop workbench, then save them:

```bash
wdb --serial COM5 settings-set --json '{"rf":{"channel":76,"datarate":"1mbps","power":"low"},"bridge":{"rf_to_wifi":true,"rf_to_ble":true}}'
wdb --serial COM5 settings-save
```

Device name, AP SSID, AP password, and BLE name changes are persisted but require a reboot before every service advertises the new value.

## 6. Export A Support Report

```bash
wdb --serial COM5 report --output reports/node1-report.json
```

The desktop workbench has the same export under **Export Support Report**.
