from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from wireless_dev_bridge import BridgeError, WirelessDevBridge

DEFAULT_HTTP_HOST = "192.168.4.1"
DEFAULT_WS_HOST = "192.168.4.1"
DEFAULT_BLE_DEVICE = "WirelessDev-Node1"


def add_transport_args(
    parser: argparse.ArgumentParser,
    *,
    include_http: bool = True,
    default_transport: str = "http",
) -> None:
    group = parser.add_mutually_exclusive_group()
    if include_http:
        group.add_argument("--host", help=f"HTTP host or URL, default {DEFAULT_HTTP_HOST}")
    group.add_argument("--serial", help="USB serial port, for example COM5")
    group.add_argument("--ws", help=f"WebSocket host or URL, default {DEFAULT_WS_HOST}")
    group.add_argument("--ble", help=f"BLE device name or address, default {DEFAULT_BLE_DEVICE}")
    parser.add_argument("--timeout", type=float, default=3.0, help="command timeout in seconds")
    parser.set_defaults(default_transport=default_transport)


def selected_transport(args: argparse.Namespace) -> Tuple[str, str]:
    if getattr(args, "serial", None):
        return "serial", args.serial
    if getattr(args, "ws", None):
        return "ws", args.ws
    if getattr(args, "ble", None):
        return "ble", args.ble
    if getattr(args, "host", None):
        return "http", args.host

    default_transport = getattr(args, "default_transport", "http")
    if default_transport == "ws":
        return "ws", DEFAULT_WS_HOST
    if default_transport == "ble":
        return "ble", DEFAULT_BLE_DEVICE
    return "http", DEFAULT_HTTP_HOST


def connect_bridge(args: argparse.Namespace) -> Tuple[WirelessDevBridge, str, str]:
    transport, target = selected_transport(args)
    timeout = getattr(args, "timeout", 3.0)

    if transport == "serial":
        return WirelessDevBridge.serial(target, timeout=timeout), transport, target
    if transport == "ws":
        return WirelessDevBridge.websocket(target, timeout=timeout), transport, target
    if transport == "ble":
        return WirelessDevBridge.ble(target, timeout=timeout), transport, target
    return WirelessDevBridge.http(target, timeout=timeout), transport, target


def enable_rf_event_bridge(dev: WirelessDevBridge, transport: str) -> None:
    if transport == "ws":
        dev.bridge(rf_to_wifi=True)
    elif transport == "ble":
        dev.bridge(rf_to_ble=True)


def print_error(message: str) -> None:
    print(message, file=sys.stderr)


def fail_with_bridge_error(exc: BridgeError) -> int:
    print_error(f"device communication failed: {exc}")
    return 1
