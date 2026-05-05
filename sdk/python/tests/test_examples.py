from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

EXAMPLES_DIR = Path(__file__).resolve().parents[1] / "examples"
sys.path.insert(0, str(EXAMPLES_DIR))


@pytest.mark.parametrize(
    "module_name",
    [
        "packet_monitor",
        "bridge_to_mqtt",
        "ble_console",
        "latency_benchmark",
        "device_inventory",
    ],
)
def test_examples_import_without_hardware(module_name):
    importlib.import_module(module_name)


def test_latency_summary_is_deterministic():
    benchmark = importlib.import_module("latency_benchmark")

    summary = benchmark.summarize_latencies([3.0, 1.0, 2.0])

    assert summary["count"] == 3
    assert summary["min_ms"] == 1.0
    assert summary["avg_ms"] == 2.0
    assert summary["max_ms"] == 3.0


def test_device_inventory_parses_device_specs():
    inventory = importlib.import_module("device_inventory")

    assert inventory.parse_device_spec("serial:COM5") == ("serial", "COM5")
    assert inventory.parse_device_spec("ble:WirelessDev-Node1") == ("ble", "WirelessDev-Node1")


def test_device_inventory_rejects_invalid_scheme():
    inventory = importlib.import_module("device_inventory")

    with pytest.raises(ValueError, match="unsupported"):
        inventory.parse_device_spec("ftp:192.168.4.1")
