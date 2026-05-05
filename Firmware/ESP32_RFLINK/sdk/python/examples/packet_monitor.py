"""Monitor RF packet events from a Wireless Dev Bridge.

Examples:
  python examples/packet_monitor.py --ws 192.168.4.1 --count 10
  python examples/packet_monitor.py --ble WirelessDev-Node1 --count 10
  python examples/packet_monitor.py --serial COM5 --json
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from typing import Any, Dict

from example_common import (
    BridgeError,
    add_transport_args,
    connect_bridge,
    enable_rf_event_bridge,
    fail_with_bridge_error,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Print RF packet events from a dongle")
    add_transport_args(parser, include_http=False, default_transport="ws")
    parser.add_argument("--channel", type=int, help="optional RF channel to apply before monitoring")
    parser.add_argument("--datarate", choices=["250kbps", "1mbps", "2mbps"], help="optional RF data rate")
    parser.add_argument("--power", choices=["min", "low", "high", "max"], help="optional RF power")
    parser.add_argument("--count", type=int, default=0, help="number of packets to print, 0 means forever")
    parser.add_argument("--event-timeout", type=float, default=10.0, help="event read timeout in seconds")
    parser.add_argument("--no-listen", action="store_true", help="do not send rf_start_listen first")
    parser.add_argument("--json", action="store_true", help="print complete packet event JSON")
    return parser


def format_packet(event: Dict[str, Any]) -> str:
    data = event.get("data") or {}
    host_time = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return (
        f"{host_time} uptime_ms={data.get('uptime_ms')} "
        f"len={data.get('len')} hex={data.get('hex')}"
    )


def main() -> int:
    args = build_parser().parse_args()
    dev = None

    try:
        dev, transport, _target = connect_bridge(args)
        enable_rf_event_bridge(dev, transport)

        if args.channel is not None or args.datarate is not None or args.power is not None:
            dev.rf_config(channel=args.channel, datarate=args.datarate, power=args.power)
        if not args.no_listen:
            dev.rf_start_listen()

        printed = 0
        while args.count == 0 or printed < args.count:
            event = dev.read_event(timeout=args.event_timeout)
            if event.get("type") != "packet":
                continue

            if args.json:
                print(json.dumps(event, separators=(",", ":"), sort_keys=True))
            else:
                print(format_packet(event))
            printed += 1
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
