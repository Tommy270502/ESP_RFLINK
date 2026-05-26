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

    settings_response = bridge.request("settings_get", check=False)
    report["settings_response"] = settings_response
    report["settings"] = settings_response.get("data", {})

    rf_metrics_response = bridge.request("rf_metrics", check=False)
    report["rf_metrics_response"] = rf_metrics_response
    report["rf_metrics"] = rf_metrics_response.get("data", {})

    event_log_response = bridge.request("event_log", check=False)
    report["event_log_response"] = event_log_response
    report["event_log"] = event_log_response.get("data", {})

    return report


def summarize_report(report: Dict[str, Any]) -> Dict[str, Optional[Any]]:
    status = report.get("status") if isinstance(report.get("status"), dict) else {}
    self_test = report.get("self_test") if isinstance(report.get("self_test"), dict) else {}
    radio = status.get("radio") if isinstance(status.get("radio"), dict) else {}
    stats = status.get("stats") if isinstance(status.get("stats"), dict) else {}
    diagnostics = report.get("diagnostics") if isinstance(report.get("diagnostics"), dict) else {}
    build = diagnostics.get("build") if isinstance(diagnostics.get("build"), dict) else {}
    storage = status.get("storage") if isinstance(status.get("storage"), dict) else {}
    return {
        "fw": status.get("fw") or self_test.get("fw"),
        "protocol": status.get("protocol") or self_test.get("protocol"),
        "role": status.get("role") or self_test.get("role"),
        "radio_ok": bool(radio.get("initialized") and radio.get("chip_connected")),
        "rf_rx": stats.get("rf_rx"),
        "rf_tx": stats.get("rf_tx"),
        "rf_tx_fail": stats.get("rf_tx_fail"),
        "rf_tx_attempts": stats.get("rf_tx_attempts"),
        "ack_failure_rate": stats.get("ack_failure_rate"),
        "build_profile": build.get("profile"),
        "build_date": build.get("date"),
        "settings_dirty": storage.get("dirty"),
        "settings_schema_version": storage.get("schema_version"),
    }
