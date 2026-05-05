from __future__ import annotations

import pytest

from wireless_dev_bridge import WirelessDevBridge


class FakeTransport:
    def __init__(self):
        self.payloads = []

    def command(self, payload):
        self.payloads.append(dict(payload))
        return {
            "ok": True,
            "cmd": payload["cmd"],
            "data": {key: value for key, value in payload.items() if key != "cmd"},
            "error": None,
        }


def test_bridge_preserves_legacy_rf_to_wifi_positional_call():
    transport = FakeTransport()
    dev = WirelessDevBridge(transport)

    response = dev.bridge(True)

    assert response["rf_to_wifi"] is True
    assert transport.payloads[-1] == {"cmd": "bridge", "rf_to_wifi": True}


def test_bridge_supports_rf_to_ble():
    transport = FakeTransport()
    dev = WirelessDevBridge(transport)

    response = dev.bridge(rf_to_ble=True)

    assert response["rf_to_ble"] is True
    assert transport.payloads[-1] == {"cmd": "bridge", "rf_to_ble": True}


def test_bridge_can_configure_both_modes_together():
    transport = FakeTransport()
    dev = WirelessDevBridge(transport)

    response = dev.bridge(rf_to_wifi=False, rf_to_ble=True)

    assert response == {"rf_to_wifi": False, "rf_to_ble": True}
    assert transport.payloads[-1] == {
        "cmd": "bridge",
        "rf_to_wifi": False,
        "rf_to_ble": True,
    }


def test_bridge_rejects_non_bool_modes():
    dev = WirelessDevBridge(FakeTransport())

    with pytest.raises(ValueError, match="rf_to_ble"):
        dev.bridge(rf_to_ble="yes")
