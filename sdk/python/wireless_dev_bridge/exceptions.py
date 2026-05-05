from __future__ import annotations

from typing import Any, Mapping


class BridgeError(RuntimeError):
    """Base class for SDK errors."""


class TransportError(BridgeError):
    """Raised when the selected host transport fails."""


class ProtocolError(BridgeError):
    """Raised when the device returns malformed protocol data."""


class CommandError(BridgeError):
    """Raised when the device returns ok=false."""

    def __init__(self, response: Mapping[str, Any]):
        self.response = dict(response)
        error = self.response.get("error") or {}
        self.code = error.get("code", "command_failed")
        self.message = error.get("message", "command failed")
        cmd = self.response.get("cmd", "")
        super().__init__(f"{cmd}: {self.code}: {self.message}")
