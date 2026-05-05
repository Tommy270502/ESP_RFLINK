from __future__ import annotations

from typing import Any, Dict, Optional, Union

from .exceptions import CommandError, ProtocolError
from .transports import BaseTransport, BleTransport, HttpTransport, SerialTransport, WebSocketTransport

Payload = Union[bytes, bytearray, memoryview]


class WirelessDevBridge:
    def __init__(self, transport: BaseTransport):
        self.transport = transport

    @classmethod
    def http(cls, host: str = "192.168.4.1", timeout: float = 3.0) -> "WirelessDevBridge":
        return cls(HttpTransport(host=host, timeout=timeout))

    @classmethod
    def serial(cls, port: str, baudrate: int = 115200, timeout: float = 2.0) -> "WirelessDevBridge":
        return cls(SerialTransport(port=port, baudrate=baudrate, timeout=timeout))

    @classmethod
    def websocket(cls, host: str = "192.168.4.1", port: int = 81, timeout: float = 3.0) -> "WirelessDevBridge":
        return cls(WebSocketTransport(host=host, port=port, timeout=timeout))

    @classmethod
    def ble(cls, device: str = "WirelessDev-Node1", timeout: float = 5.0) -> "WirelessDevBridge":
        return cls(BleTransport(device=device, timeout=timeout))

    def close(self) -> None:
        self.transport.close()

    def request(self, cmd: str, check: bool = True, **params: Any) -> Dict[str, Any]:
        payload = {"cmd": cmd}
        payload.update({key: value for key, value in params.items() if value is not None})

        response = self.transport.command(payload)
        self._validate_response(response)

        if check and not response["ok"]:
            raise CommandError(response)
        return response

    def command(self, cmd: str, **params: Any) -> Dict[str, Any]:
        return self.request(cmd, **params)["data"]

    def ping(self) -> Dict[str, Any]:
        return self.command("ping")

    def protocol(self) -> Dict[str, Any]:
        return self.command("protocol")

    def capabilities(self) -> Dict[str, Any]:
        return self.command("capabilities")

    def status(self) -> Dict[str, Any]:
        return self.command("status")

    def self_test(self) -> Dict[str, Any]:
        return self.command("self_test")

    def rf_get_config(self) -> Dict[str, Any]:
        return self.command("rf_get_config")

    def rf_config(
        self,
        channel: Optional[int] = None,
        datarate: Optional[str] = None,
        power: Optional[str] = None,
        auto_ack: Optional[bool] = None,
    ) -> Dict[str, Any]:
        return self.command(
            "rf_config",
            channel=channel,
            datarate=datarate,
            power=power,
            auto_ack=auto_ack,
        )

    def rf_send_hex(self, hex_payload: str, require_ack: bool = False) -> Dict[str, Any]:
        return self.command("rf_send", hex=hex_payload, require_ack=require_ack)

    def rf_send_bytes(self, payload: Payload, require_ack: bool = False) -> Dict[str, Any]:
        return self.rf_send_hex(bytes(payload).hex().upper(), require_ack=require_ack)

    def rf_start_listen(self) -> Dict[str, Any]:
        return self.command("rf_start_listen")

    def rf_stop_listen(self) -> Dict[str, Any]:
        return self.command("rf_stop_listen")

    def rf_flush_rx(self) -> Dict[str, Any]:
        return self.command("rf_flush_rx")

    def rf_flush_tx(self) -> Dict[str, Any]:
        return self.command("rf_flush_tx")

    def rf_set_address(
        self,
        pipe: Optional[str] = None,
        address: Optional[str] = None,
        rx: Optional[str] = None,
        tx: Optional[str] = None,
        format: str = "ascii",
    ) -> Dict[str, Any]:
        return self.command(
            "rf_set_address",
            pipe=pipe,
            address=address,
            rx=rx,
            tx=tx,
            format=format,
        )

    def bridge(
        self,
        rf_to_wifi: Optional[bool] = None,
        rf_to_ble: Optional[bool] = None,
    ) -> Dict[str, Any]:
        self._validate_optional_bool("rf_to_wifi", rf_to_wifi)
        self._validate_optional_bool("rf_to_ble", rf_to_ble)
        return self.command("bridge", rf_to_wifi=rf_to_wifi, rf_to_ble=rf_to_ble)

    def read_event(self, timeout: Optional[float] = None):
        return self.transport.read_event(timeout=timeout)

    def iter_events(self, timeout: Optional[float] = None):
        return self.transport.iter_events(timeout=timeout)

    @staticmethod
    def _validate_optional_bool(name: str, value: Optional[bool]) -> None:
        if value is not None and not isinstance(value, bool):
            raise ValueError(f"{name} must be true or false")

    @staticmethod
    def _validate_response(response: Dict[str, Any]) -> None:
        if not isinstance(response.get("ok"), bool):
            raise ProtocolError("missing boolean ok field")
        if "cmd" not in response:
            raise ProtocolError("missing cmd field")
        if "data" not in response:
            raise ProtocolError("missing data field")
        if "error" not in response:
            raise ProtocolError("missing error field")
