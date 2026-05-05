"""Run self-test and RF config checks across one or more dongles.

Examples:
  python examples/device_inventory.py --device serial:COM5 --device serial:COM6
  python examples/device_inventory.py --device http:192.168.4.1 --json
  python examples/device_inventory.py --device ble:WirelessDev-Node1
"""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict, Tuple

from example_common import BridgeError, WirelessDevBridge, print_error

VALID_DEVICE_SCHEMES = {"http", "serial", "ws", "ble"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inventory attached or network-reachable dongles")
    parser.add_argument(
        "--device",
        action="append",
        required=True,
        help="device spec: serial:COM5, http:192.168.4.1, ws:192.168.4.1, or ble:WirelessDev-Node1",
    )
    parser.add_argument("--timeout", type=float, default=3.0, help="command timeout in seconds")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    return parser


def parse_device_spec(spec: str) -> Tuple[str, str]:
    if ":" not in spec:
        raise ValueError("device spec must use scheme:target, for example serial:COM5")

    scheme, target = spec.split(":", 1)
    if scheme not in VALID_DEVICE_SCHEMES:
        raise ValueError(f"unsupported device scheme {scheme}")
    if not target:
        raise ValueError("device target must not be empty")
    return scheme, target


def connect_device(scheme: str, target: str, timeout: float) -> WirelessDevBridge:
    if scheme == "serial":
        return WirelessDevBridge.serial(target, timeout=timeout)
    if scheme == "ws":
        return WirelessDevBridge.websocket(target, timeout=timeout)
    if scheme == "ble":
        return WirelessDevBridge.ble(target, timeout=timeout)
    return WirelessDevBridge.http(target, timeout=timeout)


def collect_inventory(spec: str, timeout: float) -> Dict[str, Any]:
    scheme, target = parse_device_spec(spec)
    dev = connect_device(scheme, target, timeout)
    try:
        self_test = dev.self_test()
        rf_config = dev.rf_get_config()
        return {
            "spec": spec,
            "transport": scheme,
            "target": target,
            "ok": True,
            "role": self_test.get("role"),
            "fw": self_test.get("fw"),
            "ble_name": self_test.get("ble_name"),
            "radio_initialized": self_test.get("radio_initialized"),
            "radio_chip_connected": self_test.get("radio_chip_connected"),
            "free_heap": self_test.get("free_heap"),
            "channel": rf_config.get("channel"),
            "datarate": rf_config.get("datarate"),
            "power": rf_config.get("power"),
            "rx_address": rf_config.get("rx_address_ascii") or rf_config.get("rx_address_hex"),
            "tx_address": rf_config.get("tx_address_ascii") or rf_config.get("tx_address_hex"),
        }
    finally:
        dev.close()


def print_table(rows: list[Dict[str, Any]]) -> None:
    header = (
        "SPEC",
        "OK",
        "ROLE",
        "FW",
        "BLE",
        "RADIO",
        "CH",
        "RATE",
        "RX",
        "TX",
    )
    print("{:<24} {:<3} {:<8} {:<10} {:<18} {:<5} {:<3} {:<7} {:<8} {:<8}".format(*header))
    for row in rows:
        radio = "yes" if row.get("radio_initialized") and row.get("radio_chip_connected") else "no"
        print(
            "{:<24} {:<3} {:<8} {:<10} {:<18} {:<5} {:<3} {:<7} {:<8} {:<8}".format(
                row.get("spec", ""),
                "yes" if row.get("ok") else "no",
                row.get("role") or "",
                row.get("fw") or "",
                row.get("ble_name") or "",
                radio,
                row.get("channel") if row.get("channel") is not None else "",
                row.get("datarate") or "",
                row.get("rx_address") or "",
                row.get("tx_address") or "",
            )
        )


def main() -> int:
    args = build_parser().parse_args()
    rows = []

    for spec in args.device:
        try:
            rows.append(collect_inventory(spec, args.timeout))
        except (BridgeError, ValueError) as exc:
            rows.append({"spec": spec, "ok": False, "error": str(exc)})

    if args.json:
        print(json.dumps(rows, indent=2, sort_keys=True))
    else:
        print_table(rows)
        failures = [row for row in rows if not row.get("ok")]
        for row in failures:
            print_error(f"{row['spec']}: {row.get('error', 'inventory failed')}")

    return 1 if any(not row.get("ok") for row in rows) else 0


if __name__ == "__main__":
    raise SystemExit(main())
