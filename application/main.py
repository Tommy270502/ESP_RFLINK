from __future__ import annotations

import asyncio
import json
import sys
import threading
import webbrowser
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any


APP_DIR = Path(__file__).resolve().parent
REPO_ROOT = APP_DIR.parent
SDK_DIR = REPO_ROOT / "sdk" / "python"
if SDK_DIR.exists() and str(SDK_DIR) not in sys.path:
    sys.path.insert(0, str(SDK_DIR))

try:
    from wireless_dev_bridge import BridgeError, WirelessDevBridge
except ImportError as exc:
    raise SystemExit(
        "Unable to import the Wireless Dev Bridge SDK. Run this app from the "
        "repository checkout or install sdk/python with: python -m pip install -e sdk/python"
    ) from exc

try:
    import serial.tools.list_ports  # type: ignore[import]
except ImportError:
    serial = None  # type: ignore[assignment]

try:
    import uvicorn
    from fastapi import FastAPI, Request
    from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
    from fastapi.staticfiles import StaticFiles
except ImportError as exc:
    raise SystemExit(
        "FastAPI and Uvicorn are required. Install with:\n"
        "  pip install -r application/requirements.txt"
    ) from exc

# ── Constants ─────────────────────────────────────────────────────────────────

BAUD_RATE = 115200
DEFAULT_TIMEOUT = 3.0
MAX_PAYLOAD_BYTES = 32
RF_ADDRESS_WIDTH = 5

TRANSPORT_SERIAL = "USB serial"
TRANSPORT_HTTP = "HTTP"
TRANSPORT_WEBSOCKET = "WebSocket"
TRANSPORT_BLE = "BLE"
COMMAND_TRANSPORTS = {TRANSPORT_SERIAL, TRANSPORT_HTTP, TRANSPORT_WEBSOCKET, TRANSPORT_BLE}
EVENT_TRANSPORTS = {TRANSPORT_WEBSOCKET, TRANSPORT_BLE}

HOST = "127.0.0.1"
PORT = 5173

# ── Application state ─────────────────────────────────────────────────────────

_lock = threading.Lock()
_active_bridges: dict[tuple[str, str, float], WirelessDevBridge] = {}
_sse_queues: list[asyncio.Queue] = []
_event_loop: asyncio.AbstractEventLoop | None = None
_event_thread: threading.Thread | None = None
_event_stop: threading.Event | None = None

# ── Validation helpers ────────────────────────────────────────────────────────

def payload_to_hex(value: str, mode: str) -> str:
    if mode == "text":
        data = value.encode("utf-8")
        if not data:
            raise ValueError("Payload must not be empty.")
        if len(data) > MAX_PAYLOAD_BYTES:
            raise ValueError(f"nRF24 payloads are limited to {MAX_PAYLOAD_BYTES} bytes.")
        return data.hex().upper()
    normalized = value.strip()
    if normalized.lower().startswith("0x"):
        normalized = normalized[2:]
    normalized = "".join(normalized.split())
    if not normalized:
        raise ValueError("Payload must not be empty.")
    if len(normalized) % 2:
        raise ValueError("Hex payload must have an even number of characters.")
    try:
        data = bytes.fromhex(normalized)
    except ValueError as exc:
        raise ValueError("Hex payload contains non-hex characters.") from exc
    if len(data) > MAX_PAYLOAD_BYTES:
        raise ValueError(f"nRF24 payloads are limited to {MAX_PAYLOAD_BYTES} bytes.")
    return data.hex().upper()


def validate_address(label: str, value: str, fmt: str) -> None:
    if fmt == "ascii":
        if len(value.encode("ascii", errors="ignore")) != len(value):
            raise ValueError(f"{label} must contain ASCII characters only.")
        if len(value) != RF_ADDRESS_WIDTH:
            raise ValueError(f"{label} must be exactly {RF_ADDRESS_WIDTH} ASCII characters.")
        return
    normalized = value.strip()
    if normalized.lower().startswith("0x"):
        normalized = normalized[2:]
    normalized = "".join(normalized.split())
    if len(normalized) != RF_ADDRESS_WIDTH * 2:
        raise ValueError(f"{label} must be exactly {RF_ADDRESS_WIDTH * 2} hex characters.")
    try:
        bytes.fromhex(normalized)
    except ValueError as exc:
        raise ValueError(f"{label} contains non-hex characters.") from exc


# ── Client pool ───────────────────────────────────────────────────────────────

def _get_client(transport: str, endpoint: str, timeout: float) -> WirelessDevBridge:
    key = (transport, endpoint, timeout)
    with _lock:
        bridge = _active_bridges.get(key)
        if bridge is not None:
            return bridge
        bridge = _make_client(transport, endpoint, timeout)
        _active_bridges[key] = bridge
        return bridge


def _make_client(transport: str, endpoint: str, timeout: float) -> WirelessDevBridge:
    if transport == TRANSPORT_SERIAL:
        return WirelessDevBridge.serial(endpoint, baudrate=BAUD_RATE, timeout=timeout)
    if transport == TRANSPORT_HTTP:
        return WirelessDevBridge.http(endpoint, timeout=timeout)
    if transport == TRANSPORT_WEBSOCKET:
        return WirelessDevBridge.websocket(endpoint, timeout=timeout)
    if transport == TRANSPORT_BLE:
        return WirelessDevBridge.ble(endpoint, timeout=timeout)
    raise ValueError(f"unsupported transport: {transport}")


def _close_client(key: tuple[str, str, float]) -> None:
    with _lock:
        bridge = _active_bridges.pop(key, None)
    if bridge is not None:
        try:
            bridge.close()
        except Exception:
            pass


def _close_all_clients() -> None:
    with _lock:
        keys = list(_active_bridges)
    for key in keys:
        _close_client(key)


# ── SSE broadcast ─────────────────────────────────────────────────────────────

def _broadcast(msg: dict) -> None:
    for q in list(_sse_queues):
        try:
            q.put_nowait(msg)
        except Exception:
            pass


def _push(msg: dict) -> None:
    if _event_loop and not _event_loop.is_closed():
        _event_loop.call_soon_threadsafe(_broadcast, msg)


# ── FastAPI ───────────────────────────────────────────────────────────────────

@asynccontextmanager
async def _lifespan(application: "FastAPI"):
    global _event_loop
    _event_loop = asyncio.get_running_loop()
    try:
        yield
    finally:
        if _event_stop is not None:
            _event_stop.set()
        await asyncio.to_thread(_close_all_clients)
        if _event_thread and _event_thread.is_alive():
            await asyncio.to_thread(_event_thread.join, 2.0)


app = FastAPI(title="Wireless Dev Bridge Workbench", lifespan=_lifespan)
_STATIC = APP_DIR / "static"
app.mount("/static", StaticFiles(directory=str(_STATIC)), name="static")


@app.get("/", response_class=HTMLResponse)
async def root() -> HTMLResponse:
    return HTMLResponse((_STATIC / "index.html").read_text(encoding="utf-8"))


@app.get("/health")
async def health() -> dict:
    return {"ok": True}


@app.get("/api/ports")
async def list_ports() -> dict:
    if serial is None:
        return {"ports": [], "error": "pyserial not installed — install sdk/python with the serial or all extra"}
    ports = [{"device": p.device, "description": p.description} for p in serial.tools.list_ports.comports()]
    return {"ports": ports}


@app.post("/api/command")
async def run_command(body: dict) -> Any:
    transport = body.get("transport", "")
    endpoint = body.get("endpoint", "")
    cmd = body.get("cmd", "")
    params_body = body.get("params") or {}
    if not isinstance(params_body, dict):
        return JSONResponse({"ok": False, "error": "params must be a JSON object"}, status_code=400)
    params: dict = {k: v for k, v in params_body.items() if v is not None}
    try:
        timeout = float(body.get("timeout", DEFAULT_TIMEOUT))
    except (TypeError, ValueError):
        return JSONResponse({"ok": False, "error": "timeout must be a number"}, status_code=400)

    if not transport or not endpoint or not cmd:
        return JSONResponse({"ok": False, "error": "transport, endpoint, and cmd are required"}, status_code=400)
    if transport not in COMMAND_TRANSPORTS:
        return JSONResponse({"ok": False, "error": f"unsupported transport: {transport}"}, status_code=400)

    def _run() -> tuple[dict | None, str | None]:
        try:
            bridge = _get_client(transport, endpoint, timeout)
            return bridge.request(cmd, check=False, **params), None
        except BridgeError as exc:
            _close_client((transport, endpoint, timeout))
            return None, str(exc)
        except Exception as exc:
            _close_client((transport, endpoint, timeout))
            return None, f"{type(exc).__name__}: {exc}"

    response, error = await asyncio.to_thread(_run)
    if error:
        return {"ok": False, "error": error, "cmd": cmd, "data": {}}
    return response


@app.post("/api/disconnect")
async def disconnect() -> dict:
    global _event_stop
    if _event_stop is not None:
        _event_stop.set()
    await asyncio.to_thread(_close_all_clients)
    return {"ok": True}


@app.post("/api/events/start")
async def start_events(body: dict) -> Any:
    global _event_thread, _event_stop
    transport = body.get("transport", TRANSPORT_WEBSOCKET)
    endpoint = body.get("endpoint", "")
    try:
        timeout = float(body.get("timeout", DEFAULT_TIMEOUT))
    except (TypeError, ValueError):
        return JSONResponse({"ok": False, "error": "timeout must be a number"}, status_code=400)
    if transport == TRANSPORT_BLE:
        timeout = max(timeout, 5.0)
    if not endpoint:
        return JSONResponse({"ok": False, "error": "endpoint required"}, status_code=400)
    if transport not in EVENT_TRANSPORTS:
        return JSONResponse({"ok": False, "error": f"unsupported event transport: {transport}"}, status_code=400)
    if _event_thread and _event_thread.is_alive():
        return JSONResponse({"ok": False, "error": "event stream already running"}, status_code=409)
    _event_stop = threading.Event()
    _event_thread = threading.Thread(
        target=_event_worker, args=(transport, endpoint, timeout, _event_stop), daemon=True
    )
    _event_thread.start()
    return {"ok": True}


@app.post("/api/events/stop")
async def stop_events() -> dict:
    if _event_stop is not None:
        _event_stop.set()
    return {"ok": True}


@app.get("/api/events/stream")
async def event_stream(request: Request) -> StreamingResponse:
    q: asyncio.Queue = asyncio.Queue(maxsize=512)
    _sse_queues.append(q)

    async def generate():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    msg = await asyncio.wait_for(q.get(), timeout=15.0)
                    yield f"data: {json.dumps(msg)}\n\n"
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            try:
                _sse_queues.remove(q)
            except ValueError:
                pass

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── Event worker ──────────────────────────────────────────────────────────────

def _event_worker(transport: str, endpoint: str, timeout: float, stop: threading.Event) -> None:
    bridge = None
    try:
        bridge = _make_client(transport, endpoint, timeout)
        _push({"type": "event_state", "status": f"Streaming {transport} {endpoint}"})
        while not stop.is_set():
            try:
                event = bridge.read_event(timeout=1.0)
            except Exception as exc:
                if stop.is_set():
                    break
                low = str(exc).lower()
                if "timeout" in low or "timed out" in low:
                    continue
                _push({"type": "event_error", "message": f"{transport} {endpoint}: {exc}"})
                break
            _push({"type": "event", "data": event})
    except Exception as exc:
        _push({"type": "event_error", "message": f"{transport} {endpoint}: {exc}"})
    finally:
        if bridge is not None:
            try:
                bridge.close()
            except Exception:
                pass
        _push({"type": "event_stopped"})


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    def _open_browser():
        import time
        time.sleep(1.2)
        webbrowser.open(f"http://{HOST}:{PORT}")

    threading.Thread(target=_open_browser, daemon=True).start()
    print(f"Wireless Dev Bridge Workbench: http://{HOST}:{PORT}")
    try:
        uvicorn.run(app, host=HOST, port=PORT, log_level="warning")
    finally:
        if _event_stop is not None:
            _event_stop.set()
        _close_all_clients()


if __name__ == "__main__":
    main()
