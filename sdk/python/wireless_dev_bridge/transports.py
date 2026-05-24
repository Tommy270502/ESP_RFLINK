from __future__ import annotations

import json
import asyncio
import threading
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
    def __init__(self, host: str = "192.168.4.1", timeout: float = 3.0, auth_token: Optional[str] = None):
        if host.startswith("http://") or host.startswith("https://"):
            self.base_url = host.rstrip("/")
        else:
            self.base_url = f"http://{host.strip('/')}"
        self.timeout = timeout
        self.auth_token = auth_token

    def command(self, payload: JsonDict) -> JsonDict:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["X-WDB-Token"] = self.auth_token

        request = urllib.request.Request(
            f"{self.base_url}/api/command",
            data=body,
            headers=headers,
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


class BleTransport(BaseTransport):
    SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
    RX_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
    TX_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"

    def __init__(self, device: str = "WirelessDev-Node1", timeout: float = 5.0):
        try:
            from bleak import BleakClient, BleakScanner
        except ImportError as exc:
            raise TransportError("install bleak or use HTTP/serial/WebSocket transport") from exc

        self.BleakClient = BleakClient
        self.BleakScanner = BleakScanner
        self.device = device
        self.timeout = timeout
        self.rx_buffer = bytearray()
        self.pending_events: List[JsonDict] = []
        self.loop = asyncio.new_event_loop()
        self.queue: Optional[asyncio.Queue[JsonDict]] = None
        self.client = None
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        self._run(self._connect(), timeout + 5.0)

    def command(self, payload: JsonDict) -> JsonDict:
        return self._run(self._command(payload), self.timeout)

    def read_event(self, timeout: Optional[float] = None) -> JsonDict:
        if self.pending_events:
            return self.pending_events.pop(0)
        return self._run(self._read_message(timeout or self.timeout), (timeout or self.timeout) + 1.0)

    def iter_events(self, timeout: Optional[float] = None) -> Iterator[JsonDict]:
        while True:
            yield self.read_event(timeout)

    def close(self) -> None:
        try:
            self._run(self._disconnect(), self.timeout)
        finally:
            self.loop.call_soon_threadsafe(self.loop.stop)
            self.thread.join(timeout=1.0)

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self.loop)
        self.queue = asyncio.Queue()
        self.loop.run_forever()

    def _run(self, coroutine, timeout: float):
        future = asyncio.run_coroutine_threadsafe(coroutine, self.loop)
        try:
            return future.result(timeout)
        except Exception as exc:
            raise TransportError(str(exc)) from exc

    async def _connect(self) -> None:
        target = self.device
        if ":" not in target and not target.startswith("{"):
            discovered = await self.BleakScanner.discover(timeout=self.timeout)
            match = next((d for d in discovered if d.name == target), None)
            if match is None:
                raise TransportError(f"BLE device not found: {target}")
            target = match.address

        self.client = self.BleakClient(target)
        await self.client.connect(timeout=self.timeout)
        await self.client.start_notify(self.TX_UUID, self._on_notify)

    async def _disconnect(self) -> None:
        if self.client is not None and self.client.is_connected:
            await self.client.disconnect()

    async def _command(self, payload: JsonDict) -> JsonDict:
        if self.client is None or not self.client.is_connected:
            raise TransportError("BLE client is not connected")

        cmd = str(payload.get("cmd", ""))
        line = json.dumps(payload, separators=(",", ":")).encode("utf-8") + b"\n"
        await self.client.write_gatt_char(self.RX_UUID, line, response=False)

        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            message = await self._read_message(max(0.1, deadline - time.monotonic()))
            if _is_command_response(message, cmd):
                return message
            self.pending_events.append(message)

        raise TransportError(f"timeout waiting for BLE response to {cmd}")

    async def _read_message(self, timeout: float) -> JsonDict:
        if self.queue is None:
            raise TransportError("BLE queue is not initialized")

        try:
            return await asyncio.wait_for(self.queue.get(), timeout=timeout)
        except asyncio.TimeoutError as exc:
            raise TransportError("timeout waiting for BLE JSON") from exc

    def _on_notify(self, _sender: int, data: bytearray) -> None:
        self.rx_buffer.extend(data)

        while b"\n" in self.rx_buffer:
            line, _, remainder = self.rx_buffer.partition(b"\n")
            self.rx_buffer = bytearray(remainder)
            if not line.strip():
                continue
            try:
                message = json.loads(line.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            if isinstance(message, dict) and self.queue is not None:
                self.queue.put_nowait(message)


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
