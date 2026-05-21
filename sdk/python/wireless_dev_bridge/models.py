from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping


def _copy(data: Mapping[str, Any]) -> Dict[str, Any]:
    return dict(data)


@dataclass(frozen=True)
class StatusModel:
    data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_data(cls, data: Mapping[str, Any]) -> "StatusModel":
        return cls(_copy(data))

    @property
    def role(self) -> str:
        return str(self.data.get("role", ""))

    @property
    def firmware(self) -> str:
        return str(self.data.get("fw", ""))

    @property
    def protocol(self) -> str:
        return str(self.data.get("protocol", ""))

    @property
    def radio_ok(self) -> bool:
        radio = self.data.get("radio") if isinstance(self.data.get("radio"), dict) else {}
        return bool(radio.get("initialized") and radio.get("chip_connected"))


@dataclass(frozen=True)
class RfConfigModel:
    data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_data(cls, data: Mapping[str, Any]) -> "RfConfigModel":
        return cls(_copy(data))

    @property
    def channel(self) -> int:
        return int(self.data.get("channel", 0))

    @property
    def datarate(self) -> str:
        return str(self.data.get("datarate", ""))

    @property
    def rx_address(self) -> str:
        return str(self.data.get("rx_address_ascii") or self.data.get("rx_address_hex") or "")

    @property
    def tx_address(self) -> str:
        return str(self.data.get("tx_address_ascii") or self.data.get("tx_address_hex") or "")


@dataclass(frozen=True)
class SettingsModel:
    data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_data(cls, data: Mapping[str, Any]) -> "SettingsModel":
        return cls(_copy(data))

    @property
    def dirty(self) -> bool:
        return bool(self.data.get("dirty"))

    @property
    def persisted(self) -> bool:
        return bool(self.data.get("loaded_from_nvs"))

    @property
    def reboot_required(self) -> bool:
        return bool(self.data.get("reboot_required"))


@dataclass(frozen=True)
class DiagnosticsModel:
    data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_data(cls, data: Mapping[str, Any]) -> "DiagnosticsModel":
        return cls(_copy(data))

    @property
    def reset_reason(self) -> str:
        return str(self.data.get("reset_reason", ""))

    @property
    def free_heap(self) -> int:
        return int(self.data.get("free_heap", 0))

    @property
    def radio_ok(self) -> bool:
        self_test = self.data.get("self_test") if isinstance(self.data.get("self_test"), dict) else {}
        return bool(self_test.get("radio_initialized") and self_test.get("radio_chip_connected"))
