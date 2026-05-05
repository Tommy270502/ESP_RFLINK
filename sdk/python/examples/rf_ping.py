from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from wireless_dev_bridge import BridgeError, WirelessDevBridge


DEFAULT_CHANNEL = 76
DEFAULT_DATARATE = "1mbps"
DEFAULT_POWER = "low"
NODE1_PAYLOAD = "1234"
NODE2_PAYLOAD = "ABCD"


@dataclass
class StepResult:
    label: str
    passed: bool
    detail: str


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Two-device production test for the Wireless Dev Bridge"
    )
    parser.add_argument("--node1-serial", help="Node 1 serial port, for example COM8")
    parser.add_argument("--node2-serial", help="Node 2 serial port, for example COM11")
    parser.add_argument("--node1-host", help="Node 1 HTTP host, default 192.168.4.1")
    parser.add_argument("--node2-host", help="Node 2 HTTP host, default 192.168.4.1")
    parser.add_argument("--timeout", type=float, default=3.0, help="Command timeout in seconds")
    parser.add_argument("--event-timeout", type=float, default=8.0, help="Packet wait timeout in seconds")
    parser.add_argument("--channel", type=int, default=DEFAULT_CHANNEL)
    parser.add_argument("--datarate", default=DEFAULT_DATARATE, choices=["250kbps", "1mbps", "2mbps"])
    parser.add_argument("--power", default=DEFAULT_POWER, choices=["min", "low", "high", "max"])
    parser.add_argument(
        "--skip-rx-check",
        action="store_true",
        help="Only validate ACK send success, skip receive-event confirmation",
    )
    return parser


def make_device(role: str, serial_port: str | None, host: str | None, timeout: float) -> WirelessDevBridge:
    if serial_port:
        return WirelessDevBridge.serial(serial_port, timeout=timeout)
    if host:
        return WirelessDevBridge.http(host, timeout=timeout)
    raise ValueError(f"{role} requires either a serial port or a host")


def log(title: str, payload: Any) -> None:
    print(f"{title}: {json.dumps(payload, separators=(',', ':'))}")


def record(results: list[StepResult], label: str, passed: bool, detail: str) -> None:
    results.append(StepResult(label, passed, detail))
    prefix = "PASS" if passed else "FAIL"
    print(f"[{prefix}] {label}: {detail}")


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def configure_node(label: str, dev: WirelessDevBridge, expected_role: str, expected_rx: str, expected_tx: str,
                   channel: int, datarate: str, power: str, results: list[StepResult]) -> None:
    self_test = dev.self_test()
    log(f"{label} self_test", self_test)
    expect(self_test["role"] == expected_role, f"expected role {expected_role}, got {self_test['role']}")
    expect(self_test["radio_initialized"], "radio not initialized")
    expect(self_test["radio_chip_connected"], "radio chip not connected")
    record(results, f"{label} self-test", True, f"role={self_test['role']} heap={self_test['free_heap']}")

    rf_state = dev.rf_set_address(rx=expected_rx, tx=expected_tx, format="ascii")
    log(f"{label} rf_set_address", rf_state)
    expect(rf_state["rx_address_ascii"] == expected_rx, "rx address mismatch")
    expect(rf_state["tx_address_ascii"] == expected_tx, "tx address mismatch")
    record(results, f"{label} address", True, f"{expected_rx}->{expected_tx}")

    rf_state = dev.rf_config(channel=channel, datarate=datarate, power=power, auto_ack=True)
    log(f"{label} rf_config", rf_state)
    expect(rf_state["channel"] == channel, "channel mismatch")
    expect(rf_state["datarate"] == datarate, "datarate mismatch")
    expect(rf_state["power"] == power, "power mismatch")
    expect(rf_state["auto_ack"] is True, "auto_ack mismatch")
    record(results, f"{label} radio config", True, f"ch={channel} rate={datarate} power={power}")

    dev.rf_start_listen()
    dev.rf_flush_rx()
    dev.rf_flush_tx()
    record(results, f"{label} listen", True, "rx/tx FIFOs flushed and listening enabled")


def wait_for_packet(label: str, dev: WirelessDevBridge, expected_hex: str, timeout: float) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        event = dev.read_event(timeout=max(0.1, deadline - time.monotonic()))
        log(f"{label} event", event)
        data = event.get("data") or {}
        if event.get("type") == "packet" and data.get("hex") == expected_hex:
            return event
    raise RuntimeError(f"expected RF packet {expected_hex} was not observed")


def send_and_verify(tx_label: str, tx_dev: WirelessDevBridge, rx_label: str, rx_dev: WirelessDevBridge,
                    payload_hex: str, event_timeout: float, skip_rx_check: bool, results: list[StepResult]) -> None:
    response = tx_dev.rf_send_hex(payload_hex, require_ack=True)
    log(f"{tx_label} rf_send", response)
    expect(response["sent"] is True, "rf_send returned sent=false")
    record(results, f"{tx_label} ACK send", True, f"payload={payload_hex}")

    if skip_rx_check:
        record(results, f"{rx_label} RX confirm", True, "skipped by option")
        return

    packet = wait_for_packet(rx_label, rx_dev, payload_hex, event_timeout)
    record(results, f"{rx_label} RX confirm", True, f"payload={packet['data']['hex']}")


def print_summary(results: list[StepResult]) -> None:
    print("\nSummary")
    for result in results:
      status = "PASS" if result.passed else "FAIL"
      print(f"- {status} {result.label}: {result.detail}")


def main() -> int:
    args = build_parser().parse_args()
    results: list[StepResult] = []

    node1 = make_device("node1", args.node1_serial, args.node1_host, args.timeout)
    node2 = make_device("node2", args.node2_serial, args.node2_host, args.timeout)

    try:
        configure_node("node1", node1, "node1", "NODE1", "NODE2", args.channel, args.datarate, args.power, results)
        configure_node("node2", node2, "node2", "NODE2", "NODE1", args.channel, args.datarate, args.power, results)

        send_and_verify("node1", node1, "node2", node2, NODE1_PAYLOAD, args.event_timeout, args.skip_rx_check, results)
        send_and_verify("node2", node2, "node1", node1, NODE2_PAYLOAD, args.event_timeout, args.skip_rx_check, results)

        print_summary(results)
        print("\nRESULT: PASS two-way RF production test completed")
        return 0
    except (BridgeError, RuntimeError, ValueError) as exc:
        record(results, "test run", False, str(exc))
        print_summary(results)
        print("\nRESULT: FAIL")
        return 1
    finally:
        node1.close()
        node2.close()


if __name__ == "__main__":
    raise SystemExit(main())
