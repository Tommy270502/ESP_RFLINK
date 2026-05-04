from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

try:
    from .client import WirelessDevBridge
    from .exceptions import BridgeError
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from wireless_dev_bridge.client import WirelessDevBridge
    from wireless_dev_bridge.exceptions import BridgeError


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        bridge = make_client(args)
        response = run_command(bridge, args)
        print(json.dumps(response, indent=2, sort_keys=True))
        bridge.close()
        return 0 if response.get("ok", False) else 2
    except BridgeError as exc:
        print(str(exc), file=sys.stderr)
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wdb", description="Wireless Dev Bridge SDK CLI")
    transport = parser.add_mutually_exclusive_group()
    transport.add_argument("--host", default=None, help="HTTP host or URL, default 192.168.4.1")
    transport.add_argument("--serial", default=None, help="USB serial port, for example COM5")
    transport.add_argument("--ws", default=None, help="WebSocket host or URL")
    transport.add_argument("--ble", default=None, help="BLE device name or address")
    parser.add_argument("--timeout", type=float, default=3.0)

    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("ping")
    sub.add_parser("protocol")
    sub.add_parser("status")
    sub.add_parser("self-test")
    sub.add_parser("rf-get-config")

    rf_config = sub.add_parser("rf-config")
    rf_config.add_argument("--channel", type=int)
    rf_config.add_argument("--datarate", choices=["250kbps", "1mbps", "2mbps"])
    rf_config.add_argument("--power", choices=["min", "low", "high", "max"])
    rf_config.add_argument("--auto-ack", choices=["true", "false"])

    rf_send = sub.add_parser("rf-send")
    rf_send.add_argument("payload", help="hex payload by default, or text with --text")
    rf_send.add_argument("--text", action="store_true", help="encode payload as UTF-8 text")
    rf_send.add_argument("--require-ack", action="store_true")

    listen = sub.add_parser("listen")
    listen.add_argument("state", choices=["start", "stop"])

    flush = sub.add_parser("flush")
    flush.add_argument("fifo", choices=["rx", "tx"])

    set_address = sub.add_parser("set-address")
    set_address.add_argument("--pipe", choices=["rx", "tx"])
    set_address.add_argument("--address")
    set_address.add_argument("--rx")
    set_address.add_argument("--tx")
    set_address.add_argument("--format", choices=["ascii", "hex"], default="ascii")

    bridge = sub.add_parser("bridge")
    bridge.add_argument("rf_to_wifi", choices=["on", "off"])

    raw = sub.add_parser("raw")
    raw.add_argument("json_command")

    return parser


def make_client(args: argparse.Namespace) -> WirelessDevBridge:
    if args.serial:
        return WirelessDevBridge.serial(args.serial, timeout=args.timeout)
    if args.ws:
        return WirelessDevBridge.websocket(args.ws, timeout=args.timeout)
    if args.ble:
        return WirelessDevBridge.ble(args.ble, timeout=args.timeout)
    return WirelessDevBridge.http(args.host or "192.168.4.1", timeout=args.timeout)


def run_command(bridge: WirelessDevBridge, args: argparse.Namespace) -> Dict[str, Any]:
    if args.command == "ping":
        return request(bridge, "ping")
    if args.command == "protocol":
        return request(bridge, "protocol")
    if args.command == "status":
        return request(bridge, "status")
    if args.command == "self-test":
        return request(bridge, "self_test")
    if args.command == "rf-get-config":
        return request(bridge, "rf_get_config")
    if args.command == "rf-config":
        auto_ack = None if args.auto_ack is None else args.auto_ack == "true"
        return request(
            bridge,
            "rf_config",
            channel=args.channel,
            datarate=args.datarate,
            power=args.power,
            auto_ack=auto_ack,
        )
    if args.command == "rf-send":
        payload = args.payload.encode("utf-8").hex().upper() if args.text else args.payload
        return request(bridge, "rf_send", hex=payload, require_ack=args.require_ack)
    if args.command == "listen":
        return request(bridge, "rf_start_listen" if args.state == "start" else "rf_stop_listen")
    if args.command == "flush":
        return request(bridge, "rf_flush_rx" if args.fifo == "rx" else "rf_flush_tx")
    if args.command == "set-address":
        return request(
            bridge,
            "rf_set_address",
            pipe=args.pipe,
            address=args.address,
            rx=args.rx,
            tx=args.tx,
            format=args.format,
        )
    if args.command == "bridge":
        return request(bridge, "bridge", rf_to_wifi=args.rf_to_wifi == "on")
    if args.command == "raw":
        payload = json.loads(args.json_command)
        return request(bridge, payload.pop("cmd"), **payload)
    raise AssertionError(args.command)


def request(bridge: WirelessDevBridge, cmd: str, **params: Any) -> Dict[str, Any]:
    return bridge.request(cmd, check=False, **params)


if __name__ == "__main__":
    raise SystemExit(main())
