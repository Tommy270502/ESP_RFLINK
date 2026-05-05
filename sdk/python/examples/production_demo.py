from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import rf_ping
from wireless_dev_bridge import BridgeError, WirelessDevBridge
from wireless_dev_bridge.exceptions import TransportError


DEFAULT_REPORT_DIR = Path("reports")
DEFAULT_DEMO_ID = "wireless-dev-bridge-v1"
DEFAULT_FIRMWARE_DIR = Path(__file__).resolve().parents[3] / "Firmware" / "ESP32_RFLINK"


@dataclass(frozen=True)
class SerialPortCandidate:
    device: str
    description: str
    hwid: str
    manufacturer: str | None
    vid: int | None
    pid: int | None

    @property
    def rank(self) -> tuple[int, str]:
        text = f"{self.device} {self.description} {self.hwid} {self.manufacturer or ''}".lower()
        likely_terms = ("esp", "usb", "serial", "uart", "jtag", "cp210", "ch340", "cdc")
        score = 0 if any(term in text for term in likely_terms) else 1
        return score, natural_port_key(self.device)


@dataclass
class DemoReport:
    demo_id: str
    generated_at: str
    result: str
    elapsed_s: float
    node1_port: str
    node2_port: str
    flashed: bool
    channel: int
    datarate: str
    power: str
    operator: str | None
    lot: str | None
    serial_number: str | None
    steps: list[dict[str, Any]]
    error: str | None = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Flash and validate two Wireless Dev Bridge dongles as a polished "
            "production demo. The test writes a JSON report suitable for demos, "
            "bench logs, or factory records."
        )
    )
    parser.add_argument("--node1-serial", "--node1-port", dest="node1_serial", help="Node 1 COM port")
    parser.add_argument("--node2-serial", "--node2-port", dest="node2_serial", help="Node 2 COM port")
    parser.add_argument(
        "--auto-ports",
        action="store_true",
        help="Auto-select exactly two visible serial ports when node ports are not supplied",
    )
    parser.add_argument("--list-ports", action="store_true", help="List visible serial ports and exit")
    parser.add_argument("--flash", action="store_true", help="Build and upload node1/node2 firmware first")
    parser.add_argument("--erase-first", action="store_true", help="Erase each target before upload")
    parser.add_argument(
        "--firmware-dir",
        type=Path,
        default=DEFAULT_FIRMWARE_DIR,
        help=f"PlatformIO firmware directory, default {DEFAULT_FIRMWARE_DIR}",
    )
    parser.add_argument(
        "--platformio",
        nargs="+",
        help="PlatformIO command override, for example: --platformio python -m platformio",
    )
    parser.add_argument("--timeout", type=float, default=3.0, help="Command timeout in seconds")
    parser.add_argument("--event-timeout", type=float, default=8.0, help="RF packet wait timeout in seconds")
    parser.add_argument("--channel", type=int, default=rf_ping.DEFAULT_CHANNEL)
    parser.add_argument("--datarate", default=rf_ping.DEFAULT_DATARATE, choices=["250kbps", "1mbps", "2mbps"])
    parser.add_argument("--power", default=rf_ping.DEFAULT_POWER, choices=["min", "low", "high", "max"])
    parser.add_argument(
        "--skip-rx-check",
        action="store_true",
        help="Only validate ACK send success; skip receive-event confirmation",
    )
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--demo-id", default=DEFAULT_DEMO_ID)
    parser.add_argument("--operator", help="Operator name or initials for the report")
    parser.add_argument("--lot", help="Build lot or batch identifier for the report")
    parser.add_argument("--serial-number", help="Kit or packaged unit serial number for the report")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print selected ports and PlatformIO commands without flashing or testing hardware",
    )
    parser.add_argument("--json", action="store_true", help="Print the final report JSON to stdout")
    return parser


def natural_port_key(port: str) -> str:
    prefix = port.rstrip("0123456789")
    suffix = port[len(prefix):]
    return f"{prefix}{int(suffix):05d}" if suffix.isdigit() else port


def discover_serial_ports() -> list[SerialPortCandidate]:
    try:
        from serial.tools import list_ports
    except ImportError as exc:
        raise RuntimeError("install the serial extra first: python -m pip install -e \".[serial]\"") from exc

    ports: list[SerialPortCandidate] = []
    for port in list_ports.comports():
        ports.append(
            SerialPortCandidate(
                device=port.device,
                description=port.description or "",
                hwid=port.hwid or "",
                manufacturer=port.manufacturer,
                vid=port.vid,
                pid=port.pid,
            )
        )
    return sorted(ports, key=lambda candidate: candidate.rank)


def print_ports(ports: Sequence[SerialPortCandidate]) -> None:
    if not ports:
        print("No serial ports found.")
        return

    print("Visible serial ports:")
    for port in ports:
        vid_pid = ""
        if port.vid is not None and port.pid is not None:
            vid_pid = f" VID:PID={port.vid:04X}:{port.pid:04X}"
        manufacturer = f" manufacturer={port.manufacturer}" if port.manufacturer else ""
        print(f"- {port.device}: {port.description}{vid_pid}{manufacturer}")


def resolve_node_ports(node1: str | None, node2: str | None, auto_ports: bool) -> tuple[str, str]:
    if node1 and node2:
        if node1 == node2:
            raise ValueError("node1 and node2 serial ports must be different")
        return node1, node2

    if node1 or node2:
        raise ValueError("provide both --node1-serial and --node2-serial, or use --auto-ports")

    if not auto_ports:
        raise ValueError("provide node serial ports or pass --auto-ports")

    ports = discover_serial_ports()
    if len(ports) != 2:
        print_ports(ports)
        raise ValueError(f"--auto-ports requires exactly two visible serial ports; found {len(ports)}")

    return ports[0].device, ports[1].device


def find_platformio_command(override: Sequence[str] | None = None) -> list[str]:
    if override:
        return list(override)

    for name in ("pio", "platformio"):
        executable = shutil.which(name)
        if executable:
            return [executable]

    home = Path.home()
    candidates = [
        home / ".platformio" / "penv" / "Scripts" / "pio.exe",
        home / ".platformio" / "penv" / "Scripts" / "platformio.exe",
        home / ".platformio" / "penv" / "bin" / "pio",
        home / ".platformio" / "penv" / "bin" / "platformio",
    ]
    for path in candidates:
        if path.exists():
            return [str(path)]

    raise RuntimeError("PlatformIO was not found. Install PlatformIO or pass --platformio.")


def run_process(command: Sequence[str], cwd: Path, dry_run: bool = False) -> None:
    printable = " ".join(str(part) for part in command)
    print(f"$ {printable}")
    if dry_run:
        return

    completed = subprocess.run(
        list(command),
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if completed.stdout:
        print(completed.stdout.rstrip())
    if completed.returncode != 0:
        raise RuntimeError(f"command failed with exit code {completed.returncode}: {printable}")


def wait_for_serial_port(port: str, timeout: float = 20.0) -> None:
    try:
        import serial
    except ImportError as exc:
        raise RuntimeError("install the serial extra first: python -m pip install -e \".[serial]\"") from exc

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            handle = serial.Serial(port=port, baudrate=115200, timeout=0.2, write_timeout=0.2)
            handle.close()
            return
        except serial.SerialException:
            time.sleep(0.5)

    raise RuntimeError(f"serial port did not become available: {port}")


def flash_nodes(
    platformio: Sequence[str],
    firmware_dir: Path,
    node1_port: str,
    node2_port: str,
    erase_first: bool,
    dry_run: bool,
) -> None:
    firmware_dir = firmware_dir.resolve()
    if not firmware_dir.exists():
        raise RuntimeError(f"firmware directory does not exist: {firmware_dir}")

    run_process([*platformio, "run", "-e", "node1", "-e", "node2"], firmware_dir, dry_run=dry_run)

    for env, port in (("node1", node1_port), ("node2", node2_port)):
        if erase_first:
            run_process([*platformio, "run", "-e", env, "--target", "erase", "--upload-port", port], firmware_dir, dry_run)
            if not dry_run:
                wait_for_serial_port(port)

        run_process([*platformio, "run", "-e", env, "--target", "upload", "--upload-port", port], firmware_dir, dry_run)
        if not dry_run:
            wait_for_serial_port(port)


def run_two_node_validation(args: argparse.Namespace, node1_port: str, node2_port: str) -> tuple[list[rf_ping.StepResult], str | None]:
    results: list[rf_ping.StepResult] = []
    node1: WirelessDevBridge | None = None
    node2: WirelessDevBridge | None = None

    try:
        node1 = WirelessDevBridge.serial(node1_port, timeout=args.timeout)
        node2 = WirelessDevBridge.serial(node2_port, timeout=args.timeout)
        rf_ping.configure_node("node1", node1, "node1", "NODE1", "NODE2", args.channel, args.datarate, args.power, results)
        rf_ping.configure_node("node2", node2, "node2", "NODE2", "NODE1", args.channel, args.datarate, args.power, results)
        rf_ping.send_and_verify("node1", node1, "node2", node2, rf_ping.NODE1_PAYLOAD, args.event_timeout, args.skip_rx_check, results)
        rf_ping.send_and_verify("node2", node2, "node1", node1, rf_ping.NODE2_PAYLOAD, args.event_timeout, args.skip_rx_check, results)
        return results, None
    except (BridgeError, TransportError, RuntimeError, ValueError) as exc:
        rf_ping.record(results, "production demo", False, str(exc))
        return results, str(exc)
    finally:
        if node1 is not None:
            node1.close()
        if node2 is not None:
            node2.close()


def build_report(
    args: argparse.Namespace,
    node1_port: str,
    node2_port: str,
    flashed: bool,
    elapsed_s: float,
    results: list[rf_ping.StepResult],
    error: str | None,
) -> DemoReport:
    return DemoReport(
        demo_id=args.demo_id,
        generated_at=datetime.now(timezone.utc).isoformat(),
        result="PASS" if error is None else "FAIL",
        elapsed_s=round(elapsed_s, 3),
        node1_port=node1_port,
        node2_port=node2_port,
        flashed=flashed,
        channel=args.channel,
        datarate=args.datarate,
        power=args.power,
        operator=args.operator,
        lot=args.lot,
        serial_number=args.serial_number,
        steps=[asdict(step) for step in results],
        error=error,
    )


def write_report(report: DemoReport, report_dir: Path, dry_run: bool = False) -> Path:
    safe_id = "".join(ch if ch.isalnum() or ch in ("-", "_") else "-" for ch in report.demo_id)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = report_dir / f"{timestamp}-{safe_id}.json"
    print(f"Report: {path}")
    if dry_run:
        return path

    report_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(report), indent=2) + "\n", encoding="utf-8")
    return path


def main() -> int:
    args = build_parser().parse_args()

    if args.list_ports:
        print_ports(discover_serial_ports())
        return 0

    started_at = time.monotonic()
    results: list[rf_ping.StepResult] = []
    error: str | None = None
    flashed = False
    node1_port = args.node1_serial or ""
    node2_port = args.node2_serial or ""

    try:
        node1_port, node2_port = resolve_node_ports(args.node1_serial, args.node2_serial, args.auto_ports)
        print(f"Node 1 port: {node1_port}")
        print(f"Node 2 port: {node2_port}")

        if args.flash:
            platformio = find_platformio_command(args.platformio)
            flash_nodes(platformio, args.firmware_dir, node1_port, node2_port, args.erase_first, args.dry_run)
            flashed = not args.dry_run

        if args.dry_run:
            print("Dry run complete; hardware validation was not executed.")
        else:
            results, error = run_two_node_validation(args, node1_port, node2_port)
            rf_ping.print_summary(results)
    except (RuntimeError, ValueError) as exc:
        error = str(exc)
        print(f"[FAIL] {error}")

    elapsed_s = time.monotonic() - started_at
    report = build_report(args, node1_port, node2_port, flashed, elapsed_s, results, error)
    write_report(report, args.report_dir, dry_run=args.dry_run)

    if args.json:
        print(json.dumps(asdict(report), indent=2))

    if report.result == "PASS":
        print("\nRESULT: PASS production demo completed")
        return 0

    print("\nRESULT: FAIL production demo did not complete")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
