from __future__ import annotations

import asyncio
import json
<<<<<<< HEAD
=======
import platform
import queue
>>>>>>> 05d28c834b179d240a117645e267be65919b6695
import sys
import threading
import webbrowser
from contextlib import asynccontextmanager
from pathlib import Path
<<<<<<< HEAD
from typing import Any
=======
from datetime import datetime, timezone
from typing import Any, Callable

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

>>>>>>> 05d28c834b179d240a117645e267be65919b6695

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
<<<<<<< HEAD
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

=======
TRANSPORTS = (TRANSPORT_SERIAL, TRANSPORT_HTTP, TRANSPORT_WEBSOCKET, TRANSPORT_BLE)
EVENT_TRANSPORTS = (TRANSPORT_WEBSOCKET, TRANSPORT_BLE)

DATARATES = ("250kbps", "1mbps", "2mbps")
POWER_LEVELS = ("min", "low", "high", "max")
ADDRESS_FORMATS = ("ascii", "hex")


class WirelessDevBridgeApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()

        self.title("Wireless Dev Bridge Workbench")
        self.geometry("1040x760")
        self.minsize(920, 680)

        self.result_queue: queue.Queue[tuple[str, Any]] = queue.Queue()
        self.busy = False
        self.command_buttons: list[ttk.Button] = []
        self.active_bridges: dict[tuple[str, str, float, str], WirelessDevBridge] = {}
        self.event_thread: threading.Thread | None = None
        self.event_stop: threading.Event | None = None
        self.event_bridge: WirelessDevBridge | None = None
        self.event_running = False
        self.event_count = 0
        self.event_packet_count = 0
        self.rf_config_dirty = False
        self.loading_rf_controls = False

        self.transport_var = tk.StringVar(value=TRANSPORT_SERIAL)
        self.serial_port_var = tk.StringVar()
        self.http_host_var = tk.StringVar(value="192.168.4.1")
        self.ws_host_var = tk.StringVar(value="192.168.4.1")
        self.ble_device_var = tk.StringVar(value="WirelessDev-Node1")
        self.timeout_var = tk.StringVar(value=str(DEFAULT_TIMEOUT_SECONDS))
        self.auth_token_var = tk.StringVar()
        self.endpoint_label_var = tk.StringVar(value="Port")
        self.auto_status_var = tk.BooleanVar(value=True)
        self.event_transport_var = tk.StringVar(value=TRANSPORT_WEBSOCKET)
        self.event_host_var = tk.StringVar(value="192.168.4.1")
        self.event_ble_device_var = tk.StringVar(value="WirelessDev-Node1")
        self.event_endpoint_label_var = tk.StringVar(value="Host")
        self.event_status_var = tk.StringVar(value="Stopped")

        self.channel_var = tk.StringVar(value="76")
        self.datarate_var = tk.StringVar(value="1mbps")
        self.power_var = tk.StringVar(value="low")
        self.auto_ack_var = tk.BooleanVar(value=True)
        self.rf_config_state_var = tk.StringVar(value="RF config matches last device read.")
        self.payload_mode_var = tk.StringVar(value="Text")
        self.payload_var = tk.StringVar(value="hello")
        self.require_ack_var = tk.BooleanVar(value=False)
        self.address_format_var = tk.StringVar(value="ascii")
        self.rx_address_var = tk.StringVar(value="NODE1")
        self.tx_address_var = tk.StringVar(value="NODE2")
        self.rf_to_wifi_var = tk.BooleanVar(value=True)
        self.rf_to_ble_var = tk.BooleanVar(value=True)

        self.summary_vars: dict[str, tk.StringVar] = {}

        self._configure_style()
        self._build_ui()
        self.transport_var.trace_add("write", lambda *_: self._sync_transport_controls())
        self.event_transport_var.trace_add("write", lambda *_: self._sync_event_transport_controls())
        for variable in (self.channel_var, self.datarate_var, self.power_var, self.auto_ack_var):
            variable.trace_add("write", lambda *_: self._mark_rf_config_dirty())
        self.payload_var.trace_add("write", lambda *_: self._update_payload_counter())
        self.payload_mode_var.trace_add("write", lambda *_: self._update_payload_counter())

        self._sync_transport_controls()
        self._sync_event_transport_controls()
        self.refresh_ports(show_error=False)
        self._update_payload_counter()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(100, self._poll_results)
        self.after(3000, self._auto_refresh_status)

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Status.TLabel", font=("Segoe UI", 10, "bold"))
        style.configure("Muted.TLabel", foreground="#5f6b75")

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self._build_connection_bar().grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 8))
        self._build_overview().grid(row=1, column=0, sticky="ew", padx=12, pady=8)
        self._build_workspace().grid(row=2, column=0, sticky="nsew", padx=12, pady=(8, 12))

    def _build_connection_bar(self) -> ttk.LabelFrame:
        frame = ttk.LabelFrame(self, text="Connection")
        frame.columnconfigure(3, weight=1)

        ttk.Label(frame, text="Transport").grid(row=0, column=0, sticky="w", padx=(10, 6), pady=10)
        transport = ttk.Combobox(
            frame,
            textvariable=self.transport_var,
            values=TRANSPORTS,
            state="readonly",
            width=14,
        )
        transport.grid(row=0, column=1, sticky="w", padx=(0, 12), pady=10)

        ttk.Label(frame, textvariable=self.endpoint_label_var).grid(row=0, column=2, sticky="w", padx=(0, 6), pady=10)
        self.endpoint_frame = ttk.Frame(frame)
        self.endpoint_frame.grid(row=0, column=3, sticky="ew", padx=(0, 12), pady=10)
        self.endpoint_frame.columnconfigure(0, weight=1)

        self.serial_combo = ttk.Combobox(self.endpoint_frame, textvariable=self.serial_port_var)
        self.serial_refresh_button = ttk.Button(self.endpoint_frame, text="Refresh", command=self.refresh_ports)
        self.http_entry = ttk.Entry(self.endpoint_frame, textvariable=self.http_host_var)
        self.ws_entry = ttk.Entry(self.endpoint_frame, textvariable=self.ws_host_var)
        self.ble_entry = ttk.Entry(self.endpoint_frame, textvariable=self.ble_device_var)

        ttk.Label(frame, text="Timeout").grid(row=0, column=4, sticky="w", padx=(0, 6), pady=10)
        ttk.Entry(frame, textvariable=self.timeout_var, width=6).grid(row=0, column=5, sticky="w", padx=(0, 10), pady=10)
        ttk.Checkbutton(frame, text="Auto status", variable=self.auto_status_var).grid(
            row=0,
            column=6,
            sticky="w",
            padx=(0, 10),
            pady=10,
        )
        ttk.Button(frame, text="Disconnect", command=self.disconnect).grid(
            row=0,
            column=7,
            sticky="w",
            padx=(0, 10),
            pady=10,
        )

        ttk.Label(frame, text="Auth token").grid(row=1, column=0, sticky="w", padx=(10, 6), pady=(0, 10))
        ttk.Entry(frame, textvariable=self.auth_token_var, show="*", width=28).grid(
            row=1,
            column=1,
            columnspan=2,
            sticky="ew",
            padx=(0, 12),
            pady=(0, 10),
        )

        quick = ttk.Frame(frame)
        quick.grid(row=2, column=0, columnspan=8, sticky="ew", padx=10, pady=(0, 10))
        for label, command in (
            ("Ping", lambda: self.send_command("ping")),
            ("Status", lambda: self.send_command("status")),
            ("Self Test", lambda: self.send_command("self_test")),
            ("Identify", lambda: self.send_command("identify")),
            ("Diagnostics", lambda: self.send_command("diagnostics")),
            ("Protocol", lambda: self.send_command("protocol")),
            ("RF Config", lambda: self.send_command("rf_get_config")),
            ("Settings", lambda: self.send_command("settings_get")),
            ("Save Settings", lambda: self.send_command("settings_save")),
        ):
            self._button(quick, label, command).pack(side="left", padx=(0, 8))
        self._button(quick, "Export Support Report", self.export_support_report).pack(side="left", padx=(0, 8))

        return frame

    def _build_overview(self) -> ttk.LabelFrame:
        frame = ttk.LabelFrame(self, text="Device Overview")
        for column in range(6):
            frame.columnconfigure(column, weight=1 if column % 2 else 0)

        fields = (
            ("Role", "role"),
            ("Firmware", "fw"),
            ("Protocol", "protocol"),
            ("Uptime", "uptime"),
            ("Radio", "radio"),
            ("RF Channel", "channel"),
            ("Datarate", "datarate"),
            ("Power", "power"),
            ("RX Address", "rx_address"),
            ("TX Address", "tx_address"),
            ("Listening", "listening"),
            ("Bridge", "bridge"),
            ("BLE", "ble"),
            ("Wi-Fi", "wifi"),
            ("Counters", "stats"),
        )

        for index, (label, key) in enumerate(fields):
            row = index // 3
            column = (index % 3) * 2
            self.summary_vars[key] = tk.StringVar(value="-")
            ttk.Label(frame, text=label).grid(row=row, column=column, sticky="w", padx=(10, 6), pady=4)
            ttk.Label(frame, textvariable=self.summary_vars[key], style="Status.TLabel").grid(
                row=row,
                column=column + 1,
                sticky="w",
                padx=(0, 12),
                pady=4,
            )

        return frame

    def _build_workspace(self) -> ttk.PanedWindow:
        pane = ttk.PanedWindow(self, orient=tk.VERTICAL)
        upper = ttk.Frame(pane)
        lower = ttk.Frame(pane)
        upper.columnconfigure(0, weight=1)
        lower.columnconfigure(0, weight=1)
        lower.rowconfigure(0, weight=1)
        pane.add(upper, weight=2)
        pane.add(lower, weight=3)

        notebook = ttk.Notebook(upper)
        notebook.grid(row=0, column=0, sticky="nsew")
        upper.rowconfigure(0, weight=1)
        notebook.add(self._build_rf_config_tab(notebook), text="RF Config")
        notebook.add(self._build_send_tab(notebook), text="Send Packet")
        notebook.add(self._build_addresses_tab(notebook), text="Addresses")
        notebook.add(self._build_bridge_tab(notebook), text="Bridge")
        notebook.add(self._build_events_tab(notebook), text="Live Events")
        notebook.add(self._build_raw_tab(notebook), text="Raw JSON")

        log_frame = ttk.LabelFrame(lower, text="Command Log")
        log_frame.grid(row=0, column=0, sticky="nsew")
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log = tk.Text(log_frame, wrap="word", height=14, state="disabled", font=("Consolas", 10))
        self.log.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=10)
        scrollbar = ttk.Scrollbar(log_frame, command=self.log.yview)
        scrollbar.grid(row=0, column=1, sticky="ns", padx=(0, 10), pady=10)
        self.log.configure(yscrollcommand=scrollbar.set)

        actions = ttk.Frame(log_frame)
        actions.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))
        ttk.Button(actions, text="Clear Log", command=self._clear_log).pack(side="right")

        return pane

    def _build_rf_config_tab(self, parent: ttk.Notebook) -> ttk.Frame:
        frame = ttk.Frame(parent, padding=12)
        for column in range(4):
            frame.columnconfigure(column, weight=1)

        ttk.Label(frame, text="Channel").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Spinbox(frame, from_=0, to=125, textvariable=self.channel_var, width=8).grid(
            row=1,
            column=0,
            sticky="w",
            pady=(0, 12),
        )

        ttk.Label(frame, text="Datarate").grid(row=0, column=1, sticky="w", pady=4)
        ttk.Combobox(frame, textvariable=self.datarate_var, values=DATARATES, state="readonly", width=12).grid(
            row=1,
            column=1,
            sticky="w",
            pady=(0, 12),
        )

        ttk.Label(frame, text="Power").grid(row=0, column=2, sticky="w", pady=4)
        ttk.Combobox(frame, textvariable=self.power_var, values=POWER_LEVELS, state="readonly", width=10).grid(
            row=1,
            column=2,
            sticky="w",
            pady=(0, 12),
        )

        ttk.Checkbutton(frame, text="Auto ACK", variable=self.auto_ack_var).grid(
            row=1,
            column=3,
            sticky="w",
            pady=(0, 12),
        )

        buttons = ttk.Frame(frame)
        buttons.grid(row=2, column=0, columnspan=4, sticky="ew")
        self._button(buttons, "Read Config", lambda: self.send_command("rf_get_config")).pack(side="left", padx=(0, 8))
        self._button(buttons, "Apply Config", self.send_rf_config).pack(side="left", padx=(0, 8))
        self._button(buttons, "Start Listen", lambda: self.send_command("rf_start_listen")).pack(side="left", padx=(0, 8))
        self._button(buttons, "Stop Listen", lambda: self.send_command("rf_stop_listen")).pack(side="left", padx=(0, 8))
        self._button(buttons, "Flush RX", lambda: self.send_command("rf_flush_rx")).pack(side="left", padx=(0, 8))
        self._button(buttons, "Flush TX", lambda: self.send_command("rf_flush_tx")).pack(side="left")

        ttk.Label(
            frame,
            textvariable=self.rf_config_state_var,
            style="Muted.TLabel",
        ).grid(row=3, column=0, columnspan=4, sticky="w", pady=(14, 0))

        ttk.Label(
            frame,
            text="Runtime settings reset when the dongle reboots. Both RF peers need matching channel and datarate.",
            style="Muted.TLabel",
        ).grid(row=4, column=0, columnspan=4, sticky="w", pady=(4, 0))

        return frame

    def _build_events_tab(self, parent: ttk.Notebook) -> ttk.Frame:
        frame = ttk.Frame(parent, padding=12)
        frame.columnconfigure(3, weight=1)
        frame.rowconfigure(2, weight=1)

        ttk.Label(frame, text="Source").grid(row=0, column=0, sticky="w", padx=(0, 6), pady=4)
        ttk.Combobox(
            frame,
            textvariable=self.event_transport_var,
            values=EVENT_TRANSPORTS,
            state="readonly",
            width=12,
        ).grid(row=0, column=1, sticky="w", padx=(0, 12), pady=4)

        ttk.Label(frame, textvariable=self.event_endpoint_label_var).grid(row=0, column=2, sticky="w", padx=(0, 6), pady=4)
        self.event_endpoint_frame = ttk.Frame(frame)
        self.event_endpoint_frame.grid(row=0, column=3, sticky="ew", padx=(0, 12), pady=4)
        self.event_endpoint_frame.columnconfigure(0, weight=1)
        self.event_ws_entry = ttk.Entry(self.event_endpoint_frame, textvariable=self.event_host_var)
        self.event_ble_entry = ttk.Entry(self.event_endpoint_frame, textvariable=self.event_ble_device_var)

        self.event_start_button = ttk.Button(frame, text="Start Stream", command=self.start_event_stream)
        self.event_start_button.grid(row=0, column=4, sticky="w", padx=(0, 8), pady=4)
        self.event_stop_button = ttk.Button(frame, text="Stop Stream", command=self.stop_event_stream, state="disabled")
        self.event_stop_button.grid(row=0, column=5, sticky="w", pady=4)

        actions = ttk.Frame(frame)
        actions.grid(row=1, column=0, columnspan=6, sticky="ew", pady=(8, 8))
        self._button(actions, "Enable WebSocket Events", lambda: self.send_command("bridge", rf_to_wifi=True)).pack(
            side="left",
            padx=(0, 8),
        )
        self._button(actions, "Enable BLE Events", lambda: self.send_command("bridge", rf_to_ble=True)).pack(
            side="left",
            padx=(0, 8),
        )
        ttk.Button(actions, text="Clear Events", command=self._clear_event_log).pack(side="right")
        ttk.Label(actions, textvariable=self.event_status_var, style="Status.TLabel").pack(side="right", padx=(0, 14))

        self.event_log = tk.Text(frame, wrap="word", height=8, state="disabled", font=("Consolas", 10))
        self.event_log.grid(row=2, column=0, columnspan=6, sticky="nsew")
        scrollbar = ttk.Scrollbar(frame, command=self.event_log.yview)
        scrollbar.grid(row=2, column=6, sticky="ns")
        self.event_log.configure(yscrollcommand=scrollbar.set)

        ttk.Label(
            frame,
            text="Start the stream, then send an RF packet from the peer dongle. WebSocket requires your PC on the dongle AP; BLE requires the bleak optional dependency and a BLE adapter.",
            style="Muted.TLabel",
        ).grid(row=3, column=0, columnspan=6, sticky="w", pady=(8, 0))

        return frame

    def _build_send_tab(self, parent: ttk.Notebook) -> ttk.Frame:
        frame = ttk.Frame(parent, padding=12)
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Payload mode").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Combobox(
            frame,
            textvariable=self.payload_mode_var,
            values=("Text", "Hex"),
            state="readonly",
            width=10,
        ).grid(row=0, column=1, sticky="w", padx=(10, 0), pady=4)

        ttk.Label(frame, text="Payload").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=self.payload_var).grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=4)

        self.payload_counter_var = tk.StringVar()
        ttk.Label(frame, textvariable=self.payload_counter_var, style="Muted.TLabel").grid(
            row=2,
            column=1,
            sticky="w",
            padx=(10, 0),
            pady=(0, 8),
        )

        ttk.Checkbutton(frame, text="Require ACK", variable=self.require_ack_var).grid(
            row=3,
            column=1,
            sticky="w",
            padx=(10, 0),
            pady=4,
        )

        self._button(frame, "Send RF Packet", self.send_rf_packet).grid(
            row=4,
            column=1,
            sticky="e",
            padx=(10, 0),
            pady=(10, 0),
        )

        return frame

    def _build_addresses_tab(self, parent: ttk.Notebook) -> ttk.Frame:
        frame = ttk.Frame(parent, padding=12)
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Format").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Combobox(
            frame,
            textvariable=self.address_format_var,
            values=ADDRESS_FORMATS,
            state="readonly",
            width=10,
        ).grid(row=0, column=1, sticky="w", padx=(10, 0), pady=4)

        ttk.Label(frame, text="RX address").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=self.rx_address_var).grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=4)

        ttk.Label(frame, text="TX address").grid(row=2, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=self.tx_address_var).grid(row=2, column=1, sticky="ew", padx=(10, 0), pady=4)

        buttons = ttk.Frame(frame)
        buttons.grid(row=3, column=1, sticky="e", padx=(10, 0), pady=(10, 0))
        ttk.Button(buttons, text="Node 1 Preset", command=lambda: self._set_address_preset("NODE1", "NODE2")).pack(
            side="left",
            padx=(0, 8),
        )
        ttk.Button(buttons, text="Node 2 Preset", command=lambda: self._set_address_preset("NODE2", "NODE1")).pack(
            side="left",
            padx=(0, 8),
        )
        self._button(buttons, "Set Addresses", self.send_addresses).pack(side="left")

        ttk.Label(
            frame,
            text="ASCII addresses must be 5 characters. Hex addresses must be 10 hex characters.",
            style="Muted.TLabel",
        ).grid(row=4, column=0, columnspan=2, sticky="w", pady=(14, 0))

        return frame

    def _build_bridge_tab(self, parent: ttk.Notebook) -> ttk.Frame:
        frame = ttk.Frame(parent, padding=12)
        frame.columnconfigure(0, weight=1)

        ttk.Checkbutton(frame, text="Forward RF packets to Wi-Fi/WebSocket", variable=self.rf_to_wifi_var).grid(
            row=0,
            column=0,
            sticky="w",
            pady=4,
        )
        ttk.Checkbutton(frame, text="Forward RF packets to BLE notifications", variable=self.rf_to_ble_var).grid(
            row=1,
            column=0,
            sticky="w",
            pady=4,
        )
        self._button(frame, "Apply Bridge State", self.send_bridge).grid(row=2, column=0, sticky="w", pady=(10, 0))

        ttk.Label(
            frame,
            text="The V1 control surfaces are intended for trusted developer benches and lab networks.",
            style="Muted.TLabel",
        ).grid(row=3, column=0, sticky="w", pady=(14, 0))

        return frame

    def _build_raw_tab(self, parent: ttk.Notebook) -> ttk.Frame:
        frame = ttk.Frame(parent, padding=12)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        self.raw_json = tk.Text(frame, height=8, wrap="word", font=("Consolas", 10))
        self.raw_json.insert("1.0", '{\n  "cmd": "status"\n}')
        self.raw_json.grid(row=0, column=0, sticky="nsew")

        self._button(frame, "Send Raw Command", self.send_raw_command).grid(row=1, column=0, sticky="e", pady=(10, 0))

        return frame

    def _button(self, parent: tk.Misc, text: str, command: Callable[[], None]) -> ttk.Button:
        button = ttk.Button(parent, text=text, command=command)
        self.command_buttons.append(button)
        return button

    def _sync_transport_controls(self) -> None:
        for widget in (self.serial_combo, self.serial_refresh_button, self.http_entry, self.ws_entry, self.ble_entry):
            widget.grid_forget()

        transport = self.transport_var.get()
        if transport == TRANSPORT_SERIAL:
            self.endpoint_label_var.set("Port")
            self.serial_combo.grid(row=0, column=0, sticky="ew")
            self.serial_refresh_button.grid(row=0, column=1, sticky="w", padx=(8, 0))
        elif transport == TRANSPORT_HTTP:
            self.endpoint_label_var.set("Host")
            self.http_entry.grid(row=0, column=0, columnspan=2, sticky="ew")
        elif transport == TRANSPORT_WEBSOCKET:
            self.endpoint_label_var.set("Host/URL")
            self.ws_entry.grid(row=0, column=0, columnspan=2, sticky="ew")
        else:
            self.endpoint_label_var.set("Device")
            self.ble_entry.grid(row=0, column=0, columnspan=2, sticky="ew")

    def _sync_event_transport_controls(self) -> None:
        for widget in (self.event_ws_entry, self.event_ble_entry):
            widget.grid_forget()

        if self.event_transport_var.get() == TRANSPORT_WEBSOCKET:
            self.event_endpoint_label_var.set("Host/URL")
            self.event_ws_entry.grid(row=0, column=0, sticky="ew")
        else:
            self.event_endpoint_label_var.set("Device")
            self.event_ble_entry.grid(row=0, column=0, sticky="ew")

    def refresh_ports(self, show_error: bool = True) -> None:
        if serial is None:
            if show_error:
                messagebox.showerror(
                    "Missing dependency",
                    "pyserial is required for USB serial. Install sdk/python with the serial or all extra.",
                )
            self.serial_combo["values"] = ()
            return

        ports = list(serial.tools.list_ports.comports())
        values = [f"{port.device} - {port.description}" for port in ports]
        self.serial_combo["values"] = values

        if values and not self.serial_port_var.get():
            self.serial_combo.current(0)
        elif not values:
            self.serial_port_var.set("")
            self._append_log("No serial ports found.")

    def send_rf_config(self) -> None:
        try:
            channel = int(self.channel_var.get())
        except ValueError:
            messagebox.showwarning("Invalid channel", "Channel must be an integer from 0 to 125.")
            return

        if not 0 <= channel <= 125:
            messagebox.showwarning("Invalid channel", "Channel must be between 0 and 125.")
            return

        self.send_command(
            "rf_config",
            channel=channel,
            datarate=self.datarate_var.get(),
            power=self.power_var.get(),
            auto_ack=self.auto_ack_var.get(),
        )

    def send_rf_packet(self) -> None:
        try:
            hex_payload = self._payload_to_hex()
        except ValueError as exc:
            messagebox.showwarning("Invalid payload", str(exc))
            return

        self.send_command("rf_send", hex=hex_payload, require_ack=self.require_ack_var.get())

    def send_addresses(self) -> None:
        fmt = self.address_format_var.get()
        rx = self.rx_address_var.get().strip()
        tx = self.tx_address_var.get().strip()

        if not rx or not tx:
            messagebox.showwarning("Missing address", "Enter both RX and TX addresses.")
            return

        try:
            self._validate_address("RX", rx, fmt)
            self._validate_address("TX", tx, fmt)
        except ValueError as exc:
            messagebox.showwarning("Invalid address", str(exc))
            return

        self.send_command("rf_set_address", rx=rx, tx=tx, format=fmt)

    def send_bridge(self) -> None:
        self.send_command(
            "bridge",
            rf_to_wifi=self.rf_to_wifi_var.get(),
            rf_to_ble=self.rf_to_ble_var.get(),
        )

    def send_raw_command(self) -> None:
        raw = self.raw_json.get("1.0", tk.END).strip()
        if not raw:
            messagebox.showwarning("Missing command", "Enter a JSON command object.")
            return

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            messagebox.showerror("Invalid JSON", f"Raw command JSON is invalid: {exc}")
            return

        if not isinstance(payload, dict):
            messagebox.showwarning("Invalid command", "Raw command must be a JSON object.")
            return
        cmd = payload.pop("cmd", None)
        if not isinstance(cmd, str) or not cmd.strip():
            messagebox.showwarning("Missing command", "Raw command must include a non-empty cmd string.")
            return

        self.send_command(cmd.strip(), **payload)

    def send_command(self, cmd: str, **params: Any) -> None:
        self._start_command(cmd, params, log=True, refresh_after=True)

    def export_support_report(self) -> None:
        if self.busy:
            self._append_log("Command already in progress.")
            return

        endpoint = self._endpoint()
        if not endpoint:
            messagebox.showwarning("Missing endpoint", self._missing_endpoint_message())
            return

        try:
            timeout = float(self.timeout_var.get())
        except ValueError:
            messagebox.showwarning("Invalid timeout", "Timeout must be a number of seconds.")
            return

        default_name = f"wireless-dev-bridge-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        path = filedialog.asksaveasfilename(
            title="Export support report",
            initialfile=default_name,
            defaultextension=".json",
            filetypes=(("JSON reports", "*.json"), ("All files", "*.*")),
        )
        if not path:
            return

        auth_token = self.auth_token_var.get().strip()
        self._append_log(f"> export support report {path}")
        self._set_busy(True)
        worker = threading.Thread(
            target=self._support_report_worker,
            args=(self.transport_var.get(), endpoint, timeout, auth_token, path),
            daemon=True,
        )
        worker.start()

    def _support_report_worker(
        self,
        transport: str,
        endpoint: str,
        timeout: float,
        auth_token: str,
        path: str,
    ) -> None:
        try:
            bridge = self._get_client(transport, endpoint, timeout, auth_token)
            report = {
                "schema": "wireless-dev-bridge-support-report-v1",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "source": "desktop-workbench",
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
                "responses": {},
            }
            for cmd in ("status", "self_test", "diagnostics", "settings_get"):
                report["responses"][cmd] = bridge.request(cmd, check=False)

            Path(path).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            self.result_queue.put(("report_saved", path))
        except BridgeError as exc:
            self._close_client((transport, endpoint, timeout, auth_token))
            self.result_queue.put(("error", str(exc)))
        except Exception as exc:
            self._close_client((transport, endpoint, timeout, auth_token))
            self.result_queue.put(("error", f"{type(exc).__name__}: {exc}"))
        finally:
            self.result_queue.put(("busy", False))

    def start_event_stream(self) -> None:
        if self.event_running:
            return

        transport = self.event_transport_var.get()
        endpoint = self._event_endpoint()
        if not endpoint:
            messagebox.showwarning("Missing event endpoint", "Enter a WebSocket host/URL or BLE device name.")
            return

        try:
            timeout = float(self.timeout_var.get())
        except ValueError:
            messagebox.showwarning("Invalid timeout", "Timeout must be a number of seconds.")
            return
        if timeout <= 0:
            messagebox.showwarning("Invalid timeout", "Timeout must be greater than zero.")
            return

        if transport == TRANSPORT_BLE:
            timeout = max(timeout, 5.0)

        auth_token = self.auth_token_var.get().strip()
        self.event_count = 0
        self.event_packet_count = 0
        self.event_stop = threading.Event()
        self.event_running = True
        self.event_status_var.set(f"Connecting {transport} {endpoint}...")
        self.event_start_button.configure(state="disabled")
        self.event_stop_button.configure(state="normal")
        self._append_event_log(f"> stream {transport} {endpoint}")
        self.event_thread = threading.Thread(
            target=self._event_stream_worker,
            args=(transport, endpoint, timeout, auth_token, self.event_stop),
            daemon=True,
        )
        self.event_thread.start()

    def stop_event_stream(self) -> None:
        if self.event_stop is not None:
            self.event_stop.set()
            self.event_status_var.set("Stopping stream...")

    def _event_endpoint(self) -> str:
        if self.event_transport_var.get() == TRANSPORT_WEBSOCKET:
            return self.event_host_var.get().strip()
        return self.event_ble_device_var.get().strip()

    def _event_stream_worker(
        self,
        transport: str,
        endpoint: str,
        timeout: float,
        auth_token: str,
        stop_event: threading.Event,
    ) -> None:
        bridge = None
        try:
            bridge = self._make_client(transport, endpoint, timeout, auth_token)
            self.event_bridge = bridge
            self.result_queue.put(("event_state", f"Streaming {transport} {endpoint}"))

            while not stop_event.is_set():
                try:
                    event = bridge.read_event(timeout=1.0)
                except Exception as exc:
                    if stop_event.is_set():
                        break
                    if self._is_event_timeout(exc):
                        continue
                    self.result_queue.put(("event_error", f"{transport} {endpoint}: {exc}"))
                    break

                self.result_queue.put(("event", event))
        except Exception as exc:
            self.result_queue.put(("event_error", f"{transport} {endpoint}: {exc}"))
        finally:
            if bridge is not None:
                try:
                    bridge.close()
                except Exception:
                    pass
            self.event_bridge = None
            self.result_queue.put(("event_stopped", None))

    def _is_event_timeout(self, exc: Exception) -> bool:
        text = str(exc).lower()
        return "timeout" in text or "timed out" in text

    def _start_command(
        self,
        cmd: str,
        params: dict[str, Any],
        log: bool,
        refresh_after: bool,
    ) -> None:
        if self.busy:
            self._append_log("Command already in progress.")
            return

        endpoint = self._endpoint()
        if not endpoint:
            messagebox.showwarning("Missing endpoint", self._missing_endpoint_message())
            return

        try:
            timeout = float(self.timeout_var.get())
        except ValueError:
            messagebox.showwarning("Invalid timeout", "Timeout must be a number of seconds.")
            return
        if timeout <= 0:
            messagebox.showwarning("Invalid timeout", "Timeout must be greater than zero.")
            return

        auth_token = self.auth_token_var.get().strip()
        payload = {"cmd": cmd, **{key: value for key, value in params.items() if value is not None}}
        if log:
            self._append_log(f"> {self.transport_var.get()} {endpoint} {json.dumps(payload, separators=(',', ':'))}")
        self._set_busy(True)
        worker = threading.Thread(
            target=self._send_worker,
            args=(self.transport_var.get(), endpoint, timeout, auth_token, cmd, params, log, refresh_after),
            daemon=True,
        )
        worker.start()

    def _send_worker(
        self,
        transport: str,
        endpoint: str,
        timeout: float,
        auth_token: str,
        cmd: str,
        params: dict[str, Any],
        log: bool,
        refresh_after: bool,
    ) -> None:
        try:
            bridge = self._get_client(transport, endpoint, timeout, auth_token)
            response = bridge.request(cmd, check=False, **params)
        except BridgeError as exc:
            self._close_client((transport, endpoint, timeout, auth_token))
            self.result_queue.put(("error", str(exc)))
            return
        except Exception as exc:
            self._close_client((transport, endpoint, timeout, auth_token))
            self.result_queue.put(("error", f"{type(exc).__name__}: {exc}"))
            return
        finally:
            self.result_queue.put(("busy", False))

        self.result_queue.put(("response", (response, log, refresh_after)))

    def _get_client(self, transport: str, endpoint: str, timeout: float, auth_token: str) -> WirelessDevBridge:
        key = (transport, endpoint, timeout, auth_token)
        bridge = self.active_bridges.get(key)
        if bridge is not None:
            return bridge

        bridge = self._make_client(transport, endpoint, timeout, auth_token)
        self.active_bridges[key] = bridge
        return bridge

    def _make_client(self, transport: str, endpoint: str, timeout: float, auth_token: str = "") -> WirelessDevBridge:
        token = auth_token or None
        if transport == TRANSPORT_SERIAL:
            return WirelessDevBridge.serial(endpoint, baudrate=BAUD_RATE, timeout=timeout, auth_token=token)
        if transport == TRANSPORT_HTTP:
            return WirelessDevBridge.http(endpoint, timeout=timeout, auth_token=token)
        if transport == TRANSPORT_WEBSOCKET:
            return WirelessDevBridge.websocket(endpoint, timeout=timeout, auth_token=token)
        if transport == TRANSPORT_BLE:
            return WirelessDevBridge.ble(endpoint, timeout=timeout, auth_token=token)
        raise ValueError(f"unsupported transport: {transport}")
>>>>>>> 05d28c834b179d240a117645e267be65919b6695

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

<<<<<<< HEAD
=======
    def _missing_endpoint_message(self) -> str:
        if self.transport_var.get() == TRANSPORT_SERIAL:
            return "Select a USB serial port first."
        if self.transport_var.get() == TRANSPORT_BLE:
            return "Enter a BLE device name or address."
        return "Enter a host, IP address, or URL."

    def disconnect(self, log: bool = True) -> None:
        self.stop_event_stream()
        self._close_all_clients()
        if log:
            self._append_log("Disconnected all open devices.")

    def _close_client(self, key: tuple[str, str, float, str]) -> None:
        bridge = self.active_bridges.pop(key, None)
        if bridge is None:
            return
>>>>>>> 05d28c834b179d240a117645e267be65919b6695

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


<<<<<<< HEAD
def _push(msg: dict) -> None:
    if _event_loop and not _event_loop.is_closed():
        _event_loop.call_soon_threadsafe(_broadcast, msg)
=======
            if kind == "busy":
                self._set_busy(bool(message))
            elif kind == "error":
                self._append_log(f"! {message}")
                messagebox.showerror("Command failed", str(message))
            elif kind == "response":
                response, log, refresh_after = message
                self._handle_response(response, log=log, refresh_after=refresh_after)
            elif kind == "report_saved":
                self._append_log(f"< support report saved: {message}")
                messagebox.showinfo("Support report exported", f"Report saved to:\n{message}")
            elif kind == "event_state":
                self.event_status_var.set(str(message))
                self._append_event_log(f"* {message}")
            elif kind == "event_error":
                self.event_status_var.set("Stream error")
                self._append_event_log(f"! {message}")
            elif kind == "event":
                self._handle_event(message)
            elif kind == "event_stopped":
                self.event_running = False
                self.event_stop = None
                self.event_start_button.configure(state="normal")
                self.event_stop_button.configure(state="disabled")
                self.event_status_var.set(f"Stopped ({self.event_packet_count} packets, {self.event_count} events)")
                self._append_event_log("< stream stopped")
>>>>>>> 05d28c834b179d240a117645e267be65919b6695


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


<<<<<<< HEAD
app = FastAPI(title="Wireless Dev Bridge Workbench", lifespan=_lifespan)
_STATIC = APP_DIR / "static"
app.mount("/static", StaticFiles(directory=str(_STATIC)), name="static")
=======
        if cmd in {"status", "self_test"}:
            self._update_overview_from_status(data, self_test=cmd == "self_test")
        elif cmd == "diagnostics":
            status = data.get("status") if isinstance(data.get("status"), dict) else {}
            if status:
                self._update_overview_from_status(status)
        elif cmd in {"settings_get", "settings_set", "settings_save", "settings_reset"}:
            effective = data.get("effective") if isinstance(data.get("effective"), dict) else {}
            rf = effective.get("rf") if isinstance(effective.get("rf"), dict) else {}
            bridge = effective.get("bridge") if isinstance(effective.get("bridge"), dict) else {}
            if rf:
                self._update_rf_controls(rf, update_form=not self.rf_config_dirty)
            if bridge:
                self._update_bridge_controls(bridge)
        elif cmd in {"rf_config", "rf_get_config", "rf_set_address"}:
            self._update_rf_controls(data, update_form=cmd in {"rf_config", "rf_get_config"})
            if cmd in {"rf_config", "rf_get_config"}:
                self._set_rf_config_dirty(False)
        elif cmd == "bridge":
            self._update_bridge_controls(data)
>>>>>>> 05d28c834b179d240a117645e267be65919b6695


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
