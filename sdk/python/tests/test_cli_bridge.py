from __future__ import annotations

import pytest

from wireless_dev_bridge.cli import build_parser, parse_bridge_args, run_command
from wireless_dev_bridge.exceptions import BridgeError


class FakeBridge:
    def __init__(self):
        self.calls = []

    def request(self, cmd, check=False, **params):
        self.calls.append((cmd, check, params))
        return {"ok": True, "cmd": cmd, "data": params, "error": None}


def test_parse_bridge_args_supports_rf_to_ble():
    assert parse_bridge_args("rf-to-ble", "on") == {"rf_to_ble": True}
    assert parse_bridge_args("ble", "off") == {"rf_to_ble": False}


def test_parse_bridge_args_preserves_legacy_rf_to_wifi_form():
    assert parse_bridge_args("on", None) == {"rf_to_wifi": True}
    assert parse_bridge_args("off", None) == {"rf_to_wifi": False}


def test_parse_bridge_args_requires_state_for_explicit_mode():
    with pytest.raises(BridgeError, match="requires state"):
        parse_bridge_args("rf-to-ble", None)


def test_run_command_maps_bridge_mode_to_client_request():
    parser = build_parser()
    args = parser.parse_args(["bridge", "rf-to-ble", "on"])
    bridge = FakeBridge()

    response = run_command(bridge, args)

    assert response["ok"] is True
    assert bridge.calls == [("bridge", False, {"rf_to_ble": True})]


def test_bridge_help_mentions_rf_to_ble(capsys):
    parser = build_parser()

    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["bridge", "--help"])

    assert exc.value.code == 0
    assert "rf-to-ble" in capsys.readouterr().out


def test_run_command_maps_identify():
    parser = build_parser()
    args = parser.parse_args(["identify"])
    bridge = FakeBridge()

    run_command(bridge, args)

    assert bridge.calls == [("identify", False, {})]


def test_run_command_maps_settings_set_json():
    parser = build_parser()
    args = parser.parse_args(["settings-set", "--json", '{"rf":{"channel":42},"security":{"auth_required":true}}'])
    bridge = FakeBridge()

    run_command(bridge, args)

    assert bridge.calls == [
        (
            "settings_set",
            False,
            {
                "rf": {"channel": 42},
                "bridge": None,
                "device": None,
                "security": {"auth_required": True},
            },
        )
    ]


def test_discover_does_not_require_bridge():
    parser = build_parser()
    args = parser.parse_args(["discover"])

    response = run_command(None, args)

    assert response["ok"] is True
    assert response["cmd"] == "discover"
