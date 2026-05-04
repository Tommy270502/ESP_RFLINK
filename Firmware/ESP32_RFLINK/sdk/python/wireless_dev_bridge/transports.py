from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Iterator, List, Optional

from .exceptions import TransportError

JsonDict = Dict[str, Any]


class BaseTransport:
    def command(self, payload: JsonDict) -> JsonDict:
        raise NotImplementedError

    def close(self) -> None:
        pass

    def read_event(self, timeout: Optional[float] = None) -> JsonDict:
        raise NotImplementedError("this transport does not support single-event reads")

    def iter_events(self, timeout: Optional[float] = None) -> Iterator[JsonDict]:
        raise NotImplementedError("this transport does not support event streaming")


class HttpTransport(BaseTransport):
    def __init__(self, host: str = "192.168.4.1", timeout: float = 3.0):
        if host.startswith("http://") or host.startswith("https://"):
            self.base_url = host.rstrip("/")
        else:
            self.base_url = f"http://{host.strip('/')}"
        self.timeout = timeout

    def command(self, payload: JsonDict) -> JsonDict:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/api/command",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return _loads_response(response.read())
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            try:
                return _loads_response(raw)
            except TransportError:
                raise TransportError(f"HTTP {exc.code}: {raw.decode('utf-8', errors='replace')}") from exc
        except OSError as exc:
            raise TransportError(str(exc)) from exc


class SerialTransport(BaseTransport):
    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 2.0):
        try:
            import serial
        except ImportError as exc:
            raise TransportError("install pyserial or use the HTTP transport") from exc

        self.timeout = timeout
        self.pending_events: List[JsonDict] = []
        self.serial = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=min(timeout, 0.2),
            write_timeout=timeout,
        )
        time.sleep(0.1)

    def command(self, payload: JsonDict) -> JsonDict:
        cmd = str(payload.get("cmd", ""))
        line = json.dumps(payload, separators=(",", ":")) + "\n"
        self.serial.write(line.encode("utf-8"))
        self.serial.flush()

        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            message = self._read_message(deadline)
            if _is_command_response(message, cmd):
                return message
            self.pending_events.append(message)

        raise TransportError(f"timeout waiting for response to {cmd}")

    def read_event(self, timeout: Optional[float] = None) -> JsonDict:
        if self.pending_events:
            return self.pending_events.pop(0)

        deadline = time.monotonic() + (self.timeout if timeout is None else timeout)
        return self._read_message(deadline)

    def iter_events(self, timeout: Optional[float] = None) -> Iterator[JsonDict]:
        while True:
            yield self.read_event(timeout)

    def close(self) -> None:
        self.serial.close()

    def _read_message(self, deadline: float) -> JsonDict:
        while time.monotonic() < deadline:
            raw = self.serial.readline()
            if not raw:
                continue

            line = raw.decode("utf-8", errors="replace").strip()
            if not line:
                continue

            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                continue

            if isinstance(message, dict):
                return message

        raise TransportError("timeout waiting for serial JSON")


class WebSocketTransport(BaseTransport):
    def __init__(self, host: str = "192.168.4.1", port: int = 81, timeout: float = 3.0):
        try:
            import websocket
        except ImportError as exc:
            raise TransportError("install websocket-client or use HTTP/serial transport") from exc

        url = host if host.startswith("ws://") or host.startswith("wss://") else f"ws://{host}:{port}/"
        self.timeout = timeout
        self.ws = websocket.create_connection(url, timeout=timeout)

    def command(self, payload: JsonDict) -> JsonDict:
        cmd = str(payload.get("cmd", ""))
        self.ws.send(json.dumps(payload, separators=(",", ":")))
        deadline = time.monotonic() + self.timeout

        while time.monotonic() < deadline:
            raw = self.ws.recv()
            message = json.loads(raw)
            if isinstance(message, dict) and _is_command_response(message, cmd):
                return message

        raise TransportError(f"timeout waiting for response to {cmd}")

    def iter_events(self, timeout: Optional[float] = None) -> Iterator[JsonDict]:
        if timeout is not None:
            self.ws.settimeout(timeout)
        while True:
            message = json.loads(self.ws.recv())
            if isinstance(message, dict):
                yield message

    def read_event(self, timeout: Optional[float] = None) -> JsonDict:
        if timeout is not None:
            self.ws.settimeout(timeout)
        while True:
            message = json.loads(self.ws.recv())
            if isinstance(message, dict):
                return message

    def close(self) -> None:
        self.ws.close()


def _loads_response(raw: bytes) -> JsonDict:
    try:
        message = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TransportError("transport returned invalid JSON") from exc

    if not isinstance(message, dict):
        raise TransportError("transport returned non-object JSON")
    return message


def _is_command_response(message: JsonDict, cmd: str) -> bool:
    if "ok" not in message or "cmd" not in message:
        return False
    return not cmd or message.get("cmd") == cmd
