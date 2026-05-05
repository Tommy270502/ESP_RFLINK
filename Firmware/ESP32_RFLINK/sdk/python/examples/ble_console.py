"""Interactive BLE maintenance console for a Wireless Dev Bridge.

Examples:
  python examples/ble_console.py --ble WirelessDev-Node1
  python examples/ble_console.py --ble WirelessDev-Node1 --command status
  python examples/ble_console.py --ble WirelessDev-Node1 --command '{"cmd":"bridge","rf_to_ble":true}'
"""

from __future__ import annotations

import argparse
import json
import shlex
from typing import Any, Dict

from example_common import BridgeError, DEFAULT_BLE_DEVICE, WirelessDevBridge, fail_with_bridge_error, print_error


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run commands against the dongle over BLE")
    parser.add_argument("--ble", default=DEFAULT_BLE_DEVICE, help=f"BLE device name or address, default {DEFAULT_BLE_DEVICE}")
    parser.add_argument("--timeout", type=float, default=5.0, help="command timeout in seconds")
    parser.add_argument("--command", help="single command to run, otherwise start an interactive prompt")
    return parser


def parse_console_command(line: str) -> Dict[str, Any]:
    stripped = line.strip()
    if not stripped:
        raise ValueError("empty command")
    if stripped.startswith("{"):
        payload = json.loads(stripped)
        if not isinstance(payload, dict) or "cmd" not in payload:
            raise ValueError("JSON commands must be objects with a cmd field")
        return payload

    parts = shlex.split(stripped)
    command = parts[0].replace("-", "_")
    if command == "rf_send":
        if len(parts) < 2:
            raise ValueError("rf-send requires a hex payload")
        return {"cmd": "rf_send", "hex": parts[1], "require_ack": "--ack" in parts[2:]}
    if command == "bridge":
        if len(parts) != 3 or parts[1] not in {"rf-to-wifi", "rf-to-ble"} or parts[2] not in {"on", "off"}:
            raise ValueError("bridge usage: bridge rf-to-wifi|rf-to-ble on|off")
        return {"cmd": "bridge", parts[1].replace("-", "_"): parts[2] == "on"}
    return {"cmd": command}


def run_command(dev: WirelessDevBridge, line: str) -> None:
    payload = parse_console_command(line)
    cmd = payload.pop("cmd")
    response = dev.request(cmd, check=False, **payload)
    print(json.dumps(response, indent=2, sort_keys=True))


def main() -> int:
    args = build_parser().parse_args()
    dev = None

    try:
        dev = WirelessDevBridge.ble(args.ble, timeout=args.timeout)
        if args.command:
            run_command(dev, args.command)
            return 0

        print("Enter command names, raw JSON commands, or 'exit'.")
        while True:
            try:
                line = input("wdb-ble> ")
            except EOFError:
                break
            if line.strip().lower() in {"exit", "quit"}:
                break
            try:
                run_command(dev, line)
            except (ValueError, json.JSONDecodeError) as exc:
                print_error(f"invalid command: {exc}")
        return 0
    except BridgeError as exc:
        return fail_with_bridge_error(exc)
    except KeyboardInterrupt:
        return 130
    finally:
        if dev is not None:
            dev.close()


if __name__ == "__main__":
    raise SystemExit(main())
