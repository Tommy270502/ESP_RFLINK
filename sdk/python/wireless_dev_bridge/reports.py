from __future__ import annotations

import platform
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .client import WirelessDevBridge


def collect_support_report(
    bridge: WirelessDevBridge,
    *,
    transport: str,
    endpoint: str,
    include_diagnostics: bool = True,
) -> Dict[str, Any]:
    report: Dict[str, Any] = {
        "schema": "wireless-dev-bridge-support-report-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "host": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python": platform.python_version(),
        },
        "connection": {
            "transport": transport,
            "endpoint": endpoint,
        },
    }

    status_response = bridge.request("status", check=False)
    report["status_response"] = status_response
    report["status"] = status_response.get("data", {})

    self_test_response = bridge.request("self_test", check=False)
    report["self_test_response"] = self_test_response
    report["self_test"] = self_test_response.get("data", {})

    if include_diagnostics:
        diagnostics_response = bridge.request("diagnostics", check=False)
        report["diagnostics_response"] = diagnostics_response
        report["diagnostics"] = diagnostics_response.get("data", {})

    return report


def summarize_report(report: Dict[str, Any]) -> Dict[str, Optional[Any]]:
    status = report.get("status") if isinstance(report.get("status"), dict) else {}
    self_test = report.get("self_test") if isinstance(report.get("self_test"), dict) else {}
    radio = status.get("radio") if isinstance(status.get("radio"), dict) else {}
    stats = status.get("stats") if isinstance(status.get("stats"), dict) else {}
    return {
        "fw": status.get("fw") or self_test.get("fw"),
        "protocol": status.get("protocol") or self_test.get("protocol"),
        "role": status.get("role") or self_test.get("role"),
        "radio_ok": bool(radio.get("initialized") and radio.get("chip_connected")),
        "rf_rx": stats.get("rf_rx"),
        "rf_tx": stats.get("rf_tx"),
        "rf_tx_fail": stats.get("rf_tx_fail"),
    }
