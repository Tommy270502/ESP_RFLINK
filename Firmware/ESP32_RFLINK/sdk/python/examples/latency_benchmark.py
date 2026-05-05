"""Measure command and optional RF send latency across SDK transports.

Examples:
  python examples/latency_benchmark.py --host 192.168.4.1 --count 50
  python examples/latency_benchmark.py --serial COM5 --rf-payload 1234 --require-ack
  python examples/latency_benchmark.py --ble WirelessDev-Node1 --json
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from typing import Iterable, List

from example_common import BridgeError, add_transport_args, connect_bridge, fail_with_bridge_error


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Measure Wireless Dev Bridge command latency")
    add_transport_args(parser, include_http=True, default_transport="http")
    parser.add_argument("--count", type=int, default=20, help="number of measured iterations")
    parser.add_argument("--warmup", type=int, default=2, help="warmup iterations before measuring")
    parser.add_argument("--rf-payload", help="optional hex payload for rf_send timing instead of ping")
    parser.add_argument("--require-ack", action="store_true", help="require RF ACK when using --rf-payload")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    return parser


def summarize_latencies(samples_ms: Iterable[float]) -> dict[str, float]:
    values = sorted(float(sample) for sample in samples_ms)
    if not values:
        raise ValueError("at least one latency sample is required")

    p95_index = min(len(values) - 1, int(round((len(values) - 1) * 0.95)))
    return {
        "count": len(values),
        "min_ms": values[0],
        "avg_ms": statistics.fmean(values),
        "p95_ms": values[p95_index],
        "max_ms": values[-1],
    }


def measure(dev, args: argparse.Namespace) -> List[float]:
    samples: List[float] = []
    total = args.warmup + args.count

    for index in range(total):
        start = time.perf_counter()
        if args.rf_payload:
            dev.rf_send_hex(args.rf_payload, require_ack=args.require_ack)
        else:
            dev.ping()
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        if index >= args.warmup:
            samples.append(elapsed_ms)

    return samples


def main() -> int:
    args = build_parser().parse_args()
    dev = None

    try:
        dev, transport, target = connect_bridge(args)
        samples = measure(dev, args)
        summary = summarize_latencies(samples)
        result = {
            "transport": transport,
            "target": target,
            "operation": "rf_send" if args.rf_payload else "ping",
            "summary": summary,
        }

        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print(f"{result['transport']} {result['target']} {result['operation']}")
            print(
                "count={count:.0f} min={min_ms:.2f}ms avg={avg_ms:.2f}ms "
                "p95={p95_ms:.2f}ms max={max_ms:.2f}ms".format(**summary)
            )
        return 0
    except BridgeError as exc:
        return fail_with_bridge_error(exc)
    except ValueError as exc:
        print(str(exc))
        return 1
    except KeyboardInterrupt:
        return 130
    finally:
        if dev is not None:
            dev.close()


if __name__ == "__main__":
    raise SystemExit(main())
