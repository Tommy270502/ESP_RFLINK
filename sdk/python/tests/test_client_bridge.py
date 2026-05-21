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


def test_protocol_11_helpers_send_expected_commands():
    transport = FakeTransport()
    dev = WirelessDevBridge(transport)

    dev.identify()
    dev.diagnostics()
    dev.settings_get()
    dev.settings_set(rf={"channel": 42}, security={"auth_required": True})
    dev.settings_save()
    dev.settings_reset()

    assert [payload["cmd"] for payload in transport.payloads] == [
        "identify",
        "diagnostics",
        "settings_get",
        "settings_set",
        "settings_save",
        "settings_reset",
    ]
    assert transport.payloads[3]["rf"] == {"channel": 42}
    assert transport.payloads[3]["security"] == {"auth_required": True}


def test_auth_token_is_added_to_non_http_command_payloads():
    transport = FakeTransport()
    dev = WirelessDevBridge(transport, auth_token="secret")

    dev.status()

    assert transport.payloads[-1]["auth"] == "secret"
