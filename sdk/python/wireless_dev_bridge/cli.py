from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

try:
    from .client import WirelessDevBridge
    from .exceptions import BridgeError
    from .reports import collect_support_report, summarize_report
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from wireless_dev_bridge.client import WirelessDevBridge
    from wireless_dev_bridge.exceptions import BridgeError
    from wireless_dev_bridge.reports import collect_support_report, summarize_report

BRIDGE_MODE_FIELDS = {
    "rf-to-wifi": "rf_to_wifi",
    "wifi": "rf_to_wifi",
    "rf-to-ble": "rf_to_ble",
    "ble": "rf_to_ble",
}


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    bridge = None

    try:
        validate_args(args)
        if command_requires_client(args):
            bridge = make_client(args)
        response = run_command(bridge, args)
        print(json.dumps(response, indent=2, sort_keys=True))
        return 0 if response.get("ok", False) else 2
    except (BridgeError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    finally:
        if bridge is not None:
            bridge.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wdb", description="Wireless Dev Bridge SDK CLI")
    transport = parser.add_mutually_exclusive_group()
    transport.add_argument("--host", default=None, help="HTTP host or URL, default 192.168.4.1")
    transport.add_argument("--serial", default=None, help="USB serial port, for example COM5")
    transport.add_argument("--ws", default=None, help="WebSocket host or URL")
    transport.add_argument("--ble", default=None, help="BLE device name or address")
    parser.add_argument("--timeout", type=float, default=3.0)
    parser.add_argument("--auth-token", default=os.environ.get("WDB_AUTH_TOKEN"), help="auth token for protected Wi-Fi/BLE commands")

    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("discover")
    sub.add_parser("ping")
    sub.add_parser("protocol")
    sub.add_parser("status")
    sub.add_parser("self-test")
    sub.add_parser("identify")
    sub.add_parser("diagnostics")
    sub.add_parser("rf-get-config")
    sub.add_parser("settings-get")
    sub.add_parser("settings-save")
    sub.add_parser("settings-reset")

    sub.add_parser("rf-metrics")
    sub.add_parser("rf-profiles")
    rf_apply_profile = sub.add_parser("rf-apply-profile")
    rf_apply_profile.add_argument("name", help="profile name: lab, low_power, range_test, production_test")
    sub.add_parser("event-log")

    settings_set = sub.add_parser("settings-set")
    settings_set.add_argument("--json", default="{}", help="settings object with optional rf, bridge, device, and security keys")

    setup = sub.add_parser("setup", help="apply common first-run settings")
    setup.add_argument("--ap-ssid")
    setup.add_argument("--ap-pass")
    setup.add_argument("--ble-name")
    setup.add_argument("--device-name")
    setup.add_argument("--auth-required", action="store_true")
    setup.add_argument("--device-auth-token", help="token to store on the device")
    setup.add_argument("--save", action="store_true", help="persist settings after applying")

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

    bridge = sub.add_parser("bridge", help="enable or disable RF event bridge modes")
    bridge.add_argument(
        "mode",
        choices=["rf-to-wifi", "rf-to-ble", "wifi", "ble", "on", "off"],
        help="bridge mode, or legacy on/off for rf-to-wifi",
    )
    bridge.add_argument("state", nargs="?", choices=["on", "off"], help="desired state")

    raw = sub.add_parser("raw")
    raw.add_argument("json_command")

    pair_test = sub.add_parser("pair-test", help="run a basic two-dongle serial RF validation")
    pair_test.add_argument("--node1-serial", required=True)
    pair_test.add_argument("--node2-serial", required=True)
    pair_test.add_argument("--channel", type=int, default=76)
    pair_test.add_argument("--datarate", choices=["250kbps", "1mbps", "2mbps"], default="1mbps")
    pair_test.add_argument("--power", choices=["min", "low", "high", "max"], default="low")

    report = sub.add_parser("report", help="collect a support report from the selected device")
    report.add_argument("--output", help="write report JSON to this path")
    report.add_argument("--no-diagnostics", action="store_true", help="skip diagnostics command")

    firmware = sub.add_parser("firmware", help="firmware utility commands")
    firmware_sub = firmware.add_subparsers(dest="firmware_command", required=True)
    flash = firmware_sub.add_parser("flash", help="flash a merged firmware image with esptool")
    flash.add_argument("--port", required=True)
    flash.add_argument("--image", required=True)
    flash.add_argument("--chip", default="esp32s3")
    flash.add_argument("--baud", default="460800")
    flash.add_argument("--offset", default="0x0")

    return parser


def make_client(args: argparse.Namespace) -> WirelessDevBridge:
    if args.serial:
        return WirelessDevBridge.serial(args.serial, timeout=args.timeout, auth_token=args.auth_token)
    if args.ws:
        return WirelessDevBridge.websocket(args.ws, timeout=args.timeout, auth_token=args.auth_token)
    if args.ble:
        return WirelessDevBridge.ble(args.ble, timeout=args.timeout, auth_token=args.auth_token)
    return WirelessDevBridge.http(args.host or "192.168.4.1", timeout=args.timeout, auth_token=args.auth_token)


def command_requires_client(args: argparse.Namespace) -> bool:
    if args.command in {"discover", "pair-test"}:
        return False
    if args.command == "firmware":
        return False
    return True


def validate_args(args: argparse.Namespace) -> None:
    if args.command == "bridge":
        parse_bridge_args(args.mode, args.state)


def run_command(bridge: WirelessDevBridge, args: argparse.Namespace) -> Dict[str, Any]:
    if args.command == "discover":
        return discover_devices()
    if args.command == "ping":
        return request(bridge, "ping")
    if args.command == "protocol":
        return request(bridge, "protocol")
    if args.command == "status":
        return request(bridge, "status")
    if args.command == "self-test":
        return request(bridge, "self_test")
    if args.command == "identify":
        return request(bridge, "identify")
    if args.command == "diagnostics":
        return request(bridge, "diagnostics")
    if args.command == "rf-get-config":
        return request(bridge, "rf_get_config")
    if args.command == "rf-metrics":
        return request(bridge, "rf_metrics")
    if args.command == "rf-profiles":
        return request(bridge, "rf_profiles")
    if args.command == "rf-apply-profile":
        return request(bridge, "rf_apply_profile", name=args.name)
    if args.command == "event-log":
        return request(bridge, "event_log")
    if args.command == "settings-get":
        return request(bridge, "settings_get")
    if args.command == "settings-set":
        return run_settings_set(bridge, args)
    if args.command == "settings-save":
        return request(bridge, "settings_save")
    if args.command == "settings-reset":
        return request(bridge, "settings_reset")
    if args.command == "setup":
        return run_setup(bridge, args)
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
        return request(bridge, "bridge", **parse_bridge_args(args.mode, args.state))
    if args.command == "raw":
        payload = json.loads(args.json_command)
        return request(bridge, payload.pop("cmd"), **payload)
    if args.command == "pair-test":
        return run_pair_test(args)
    if args.command == "report":
        return run_report(bridge, args)
    if args.command == "firmware":
        return run_firmware(args)
    raise AssertionError(args.command)


def discover_devices() -> Dict[str, Any]:
    serial_ports = []
    try:
        import serial.tools.list_ports

        serial_ports = [
            {
                "device": port.device,
                "description": port.description,
                "hwid": port.hwid,
            }
            for port in serial.tools.list_ports.comports()
        ]
    except ImportError:
        pass

    return {
        "ok": True,
        "cmd": "discover",
        "data": {
            "serial_ports": serial_ports,
            "default_http": "192.168.4.1",
            "default_ble_names": ["WirelessDev-Node1", "WirelessDev-Node2"],
        },
        "error": None,
    }


def run_settings_set(bridge: WirelessDevBridge, args: argparse.Namespace) -> Dict[str, Any]:
    payload = parse_json_object(args.json, "settings JSON")
    return request(
        bridge,
        "settings_set",
        rf=payload.get("rf"),
        bridge=payload.get("bridge"),
        device=payload.get("device"),
        security=payload.get("security"),
    )


def run_setup(bridge: WirelessDevBridge, args: argparse.Namespace) -> Dict[str, Any]:
    device = {}
    if args.device_name:
        device["name"] = args.device_name
    if args.ap_ssid:
        device["ap_ssid"] = args.ap_ssid
    if args.ap_pass:
        device["ap_pass"] = args.ap_pass
    if args.ble_name:
        device["ble_name"] = args.ble_name

    security = {}
    if args.auth_required:
        security["auth_required"] = True
    if args.device_auth_token:
        security["auth_token"] = args.device_auth_token

    response = request(
        bridge,
        "settings_set",
        device=device or None,
        security=security or None,
    )
    if args.save and response.get("ok"):
        return request(bridge, "settings_save")
    return response


def run_pair_test(args: argparse.Namespace) -> Dict[str, Any]:
    node1 = WirelessDevBridge.serial(args.node1_serial, timeout=args.timeout, auth_token=args.auth_token)
    node2 = WirelessDevBridge.serial(args.node2_serial, timeout=args.timeout, auth_token=args.auth_token)
    steps = []
    try:
        for name, dev, rx, tx in (
            ("node1", node1, "NODE1", "NODE2"),
            ("node2", node2, "NODE2", "NODE1"),
        ):
            steps.append({"device": name, "self_test": dev.request("self_test", check=False)})
            steps.append({"device": name, "address": dev.request("rf_set_address", check=False, rx=rx, tx=tx, format="ascii")})
            steps.append(
                {
                    "device": name,
                    "rf_config": dev.request(
                        "rf_config",
                        check=False,
                        channel=args.channel,
                        datarate=args.datarate,
                        power=args.power,
                        auto_ack=True,
                    ),
                }
            )
            steps.append({"device": name, "flush_rx": dev.request("rf_flush_rx", check=False)})
            steps.append({"device": name, "flush_tx": dev.request("rf_flush_tx", check=False)})
            steps.append({"device": name, "listen": dev.request("rf_start_listen", check=False)})

        tx1 = node1.request("rf_send", check=False, hex="50494E4731", require_ack=True)
        tx2 = node2.request("rf_send", check=False, hex="50494E4732", require_ack=True)
        status1 = node1.request("status", check=False)
        status2 = node2.request("status", check=False)
        ok = (
            all(
                next(value for key, value in step.items() if key != "device").get("ok", False)
                for step in steps
            )
            and tx1.get("ok")
            and tx2.get("ok")
        )
        return {
            "ok": bool(ok),
            "cmd": "pair-test",
            "data": {
                "steps": steps,
                "node1_tx": tx1,
                "node2_tx": tx2,
                "node1_status": status1,
                "node2_status": status2,
            },
            "error": None if ok else {"code": "pair_test_failed", "message": "one or more pair-test steps failed"},
        }
    finally:
        node1.close()
        node2.close()


def run_report(bridge: WirelessDevBridge, args: argparse.Namespace) -> Dict[str, Any]:
    transport, endpoint = selected_transport(args)
    report = collect_support_report(
        bridge,
        transport=transport,
        endpoint=endpoint,
        include_diagnostics=not args.no_diagnostics,
    )
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return {
        "ok": True,
        "cmd": "report",
        "data": {
            "summary": summarize_report(report),
            "output": args.output,
            "report": report if not args.output else None,
        },
        "error": None,
    }


def run_firmware(args: argparse.Namespace) -> Dict[str, Any]:
    if args.firmware_command != "flash":
        raise AssertionError(args.firmware_command)

    command = [
        sys.executable,
        "-m",
        "esptool",
        "--chip",
        args.chip,
        "--port",
        args.port,
        "--baud",
        str(args.baud),
        "write_flash",
        args.offset,
        args.image,
    ]
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    ok = result.returncode == 0
    return {
        "ok": ok,
        "cmd": "firmware flash",
        "data": {
            "command": command,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        },
        "error": None if ok else {"code": "flash_failed", "message": "esptool returned a non-zero exit code"},
    }


def parse_json_object(raw: str, label: str) -> Dict[str, Any]:
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def selected_transport(args: argparse.Namespace) -> tuple[str, str]:
    if args.serial:
        return "serial", args.serial
    if args.ws:
        return "websocket", args.ws
    if args.ble:
        return "ble", args.ble
    return "http", args.host or "192.168.4.1"


def parse_bridge_args(mode: str, state: str | None) -> Dict[str, bool]:
    if mode in {"on", "off"}:
        if state is not None:
            raise BridgeError("legacy bridge on/off form does not accept a bridge mode")
        return {"rf_to_wifi": mode == "on"}

    if state is None:
        raise BridgeError(f"bridge mode {mode} requires state on/off")

    return {BRIDGE_MODE_FIELDS[mode]: state == "on"}


def request(dev: WirelessDevBridge, cmd: str, **params: Any) -> Dict[str, Any]:
    return dev.request(cmd, check=False, **params)


if __name__ == "__main__":
    raise SystemExit(main())
