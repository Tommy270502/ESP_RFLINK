from __future__ import annotations

import json
import queue
import sys
import threading
from pathlib import Path
from typing import Any, Callable

import tkinter as tk
from tkinter import messagebox, ttk


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
    import serial.tools.list_ports
except ImportError:
    serial = None


BAUD_RATE = 115200
DEFAULT_TIMEOUT_SECONDS = 3.0
MAX_NRF24_PAYLOAD_BYTES = 32
RF_ADDRESS_WIDTH = 5

TRANSPORT_SERIAL = "USB serial"
TRANSPORT_HTTP = "HTTP"
TRANSPORT_WEBSOCKET = "WebSocket"
TRANSPORT_BLE = "BLE"
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
        self.active_bridges: dict[tuple[str, str, float], WirelessDevBridge] = {}
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

        quick = ttk.Frame(frame)
        quick.grid(row=1, column=0, columnspan=8, sticky="ew", padx=10, pady=(0, 10))
        for label, command in (
            ("Ping", lambda: self.send_command("ping")),
            ("Status", lambda: self.send_command("status")),
            ("Self Test", lambda: self.send_command("self_test")),
            ("Protocol", lambda: self.send_command("protocol")),
            ("RF Config", lambda: self.send_command("rf_get_config")),
        ):
            self._button(quick, label, command).pack(side="left", padx=(0, 8))

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
            args=(transport, endpoint, timeout, self.event_stop),
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
        stop_event: threading.Event,
    ) -> None:
        bridge = None
        try:
            bridge = self._make_client(transport, endpoint, timeout)
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

        payload = {"cmd": cmd, **{key: value for key, value in params.items() if value is not None}}
        if log:
            self._append_log(f"> {self.transport_var.get()} {endpoint} {json.dumps(payload, separators=(',', ':'))}")
        self._set_busy(True)
        worker = threading.Thread(
            target=self._send_worker,
            args=(self.transport_var.get(), endpoint, timeout, cmd, params, log, refresh_after),
            daemon=True,
        )
        worker.start()

    def _send_worker(
        self,
        transport: str,
        endpoint: str,
        timeout: float,
        cmd: str,
        params: dict[str, Any],
        log: bool,
        refresh_after: bool,
    ) -> None:
        try:
            bridge = self._get_client(transport, endpoint, timeout)
            response = bridge.request(cmd, check=False, **params)
        except BridgeError as exc:
            self._close_client((transport, endpoint, timeout))
            self.result_queue.put(("error", str(exc)))
            return
        except Exception as exc:
            self._close_client((transport, endpoint, timeout))
            self.result_queue.put(("error", f"{type(exc).__name__}: {exc}"))
            return
        finally:
            self.result_queue.put(("busy", False))

        self.result_queue.put(("response", (response, log, refresh_after)))

    def _get_client(self, transport: str, endpoint: str, timeout: float) -> WirelessDevBridge:
        key = (transport, endpoint, timeout)
        bridge = self.active_bridges.get(key)
        if bridge is not None:
            return bridge

        bridge = self._make_client(transport, endpoint, timeout)
        self.active_bridges[key] = bridge
        return bridge

    def _make_client(self, transport: str, endpoint: str, timeout: float) -> WirelessDevBridge:
        if transport == TRANSPORT_SERIAL:
            return WirelessDevBridge.serial(endpoint, baudrate=BAUD_RATE, timeout=timeout)
        if transport == TRANSPORT_HTTP:
            return WirelessDevBridge.http(endpoint, timeout=timeout)
        if transport == TRANSPORT_WEBSOCKET:
            return WirelessDevBridge.websocket(endpoint, timeout=timeout)
        if transport == TRANSPORT_BLE:
            return WirelessDevBridge.ble(endpoint, timeout=timeout)
        raise ValueError(f"unsupported transport: {transport}")

    def _endpoint(self) -> str:
        transport = self.transport_var.get()
        if transport == TRANSPORT_SERIAL:
            selected = self.serial_port_var.get().strip()
            return selected.split(" - ", 1)[0] if selected else ""
        if transport == TRANSPORT_HTTP:
            return self.http_host_var.get().strip()
        if transport == TRANSPORT_WEBSOCKET:
            return self.ws_host_var.get().strip()
        return self.ble_device_var.get().strip()

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

    def _close_client(self, key: tuple[str, str, float]) -> None:
        bridge = self.active_bridges.pop(key, None)
        if bridge is None:
            return

        try:
            bridge.close()
        except Exception:
            pass

    def _close_all_clients(self) -> None:
        keys = list(self.active_bridges)
        for key in keys:
            self._close_client(key)

    def _payload_to_hex(self) -> str:
        value = self.payload_var.get()
        if self.payload_mode_var.get() == "Text":
            payload = value.encode("utf-8")
            if not payload:
                raise ValueError("Payload must not be empty.")
            if len(payload) > MAX_NRF24_PAYLOAD_BYTES:
                raise ValueError("nRF24 payloads are limited to 32 bytes.")
            return payload.hex().upper()

        hex_payload = value.strip()
        if hex_payload.lower().startswith("0x"):
            hex_payload = hex_payload[2:]
        hex_payload = "".join(hex_payload.split())
        if not hex_payload:
            raise ValueError("Payload must not be empty.")
        if len(hex_payload) % 2:
            raise ValueError("Hex payload must contain an even number of characters.")
        try:
            payload = bytes.fromhex(hex_payload)
        except ValueError as exc:
            raise ValueError("Hex payload contains non-hex characters.") from exc
        if len(payload) > MAX_NRF24_PAYLOAD_BYTES:
            raise ValueError("nRF24 payloads are limited to 32 bytes.")
        return payload.hex().upper()

    def _validate_address(self, label: str, value: str, fmt: str) -> None:
        if fmt == "ascii":
            if len(value.encode("ascii", errors="ignore")) != len(value):
                raise ValueError(f"{label} address must contain ASCII characters only.")
            if len(value) != RF_ADDRESS_WIDTH:
                raise ValueError(f"{label} address must be exactly {RF_ADDRESS_WIDTH} ASCII characters.")
            return

        normalized = value.strip()
        if normalized.lower().startswith("0x"):
            normalized = normalized[2:]
        normalized = "".join(normalized.split())
        if len(normalized) != RF_ADDRESS_WIDTH * 2:
            raise ValueError(f"{label} address must be exactly {RF_ADDRESS_WIDTH * 2} hex characters.")
        try:
            bytes.fromhex(normalized)
        except ValueError as exc:
            raise ValueError(f"{label} address contains non-hex characters.") from exc

    def _set_address_preset(self, rx: str, tx: str) -> None:
        self.address_format_var.set("ascii")
        self.rx_address_var.set(rx)
        self.tx_address_var.set(tx)

    def _update_payload_counter(self) -> None:
        try:
            if self.payload_mode_var.get() == "Text":
                count = len(self.payload_var.get().encode("utf-8"))
            else:
                normalized = self.payload_var.get().strip()
                if normalized.lower().startswith("0x"):
                    normalized = normalized[2:]
                normalized = "".join(normalized.split())
                count = len(normalized) // 2 if len(normalized) % 2 == 0 else (len(normalized) + 1) // 2
            self.payload_counter_var.set(f"{count}/{MAX_NRF24_PAYLOAD_BYTES} bytes")
        except tk.TclError:
            pass

    def _poll_results(self) -> None:
        while True:
            try:
                kind, message = self.result_queue.get_nowait()
            except queue.Empty:
                break

            if kind == "busy":
                self._set_busy(bool(message))
            elif kind == "error":
                self._append_log(f"! {message}")
                messagebox.showerror("Command failed", str(message))
            elif kind == "response":
                response, log, refresh_after = message
                self._handle_response(response, log=log, refresh_after=refresh_after)
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

        self.after(100, self._poll_results)

    def _handle_response(self, response: dict[str, Any], log: bool = True, refresh_after: bool = True) -> None:
        if log:
            pretty = json.dumps(response, indent=2, sort_keys=True)
            self._append_log(f"< {pretty}")

        if not response.get("ok", False):
            error = response.get("error") or {}
            self._append_log(f"! {error.get('code', 'command_failed')}: {error.get('message', 'command failed')}")
            return

        cmd = response.get("cmd")
        data = response.get("data") or {}
        if not isinstance(data, dict):
            return

        if cmd in {"status", "self_test"}:
            self._update_overview_from_status(data, self_test=cmd == "self_test")
        elif cmd in {"rf_config", "rf_get_config", "rf_set_address"}:
            self._update_rf_controls(data, update_form=cmd in {"rf_config", "rf_get_config"})
            if cmd in {"rf_config", "rf_get_config"}:
                self._set_rf_config_dirty(False)
        elif cmd == "bridge":
            self._update_bridge_controls(data)

        if refresh_after and cmd not in {"status", "self_test", "protocol", "capabilities", "rf_get_config"}:
            self.after(250, self._refresh_status_if_idle)

    def _update_overview_from_status(self, data: dict[str, Any], self_test: bool = False) -> None:
        if self_test:
            self.summary_vars["role"].set(str(data.get("role", "-")))
            self.summary_vars["fw"].set(str(data.get("fw", "-")))
            self.summary_vars["protocol"].set(str(data.get("protocol", "-")))
            self.summary_vars["uptime"].set(self._format_uptime(data.get("uptime_ms")))
            radio_ok = data.get("radio_initialized") and data.get("radio_chip_connected")
            self.summary_vars["radio"].set("ok" if radio_ok else "check")
            self.summary_vars["wifi"].set(str(data.get("wifi_ap_ip", "-")))
            self.summary_vars["ble"].set(self._format_enabled_connected(data.get("ble_enabled"), data.get("ble_connected")))
            return

        radio = data.get("radio") if isinstance(data.get("radio"), dict) else {}
        wifi = data.get("wifi") if isinstance(data.get("wifi"), dict) else {}
        bridge = data.get("bridge") if isinstance(data.get("bridge"), dict) else {}
        ble = data.get("ble") if isinstance(data.get("ble"), dict) else {}
        stats = data.get("stats") if isinstance(data.get("stats"), dict) else {}

        self.summary_vars["role"].set(str(data.get("role", "-")))
        self.summary_vars["fw"].set(str(data.get("fw", "-")))
        self.summary_vars["protocol"].set(str(data.get("protocol", "-")))
        self.summary_vars["uptime"].set(self._format_uptime(data.get("uptime_ms")))
        self._update_rf_controls(radio, update_form=not self.rf_config_dirty)
        self._update_bridge_controls(bridge)
        self.summary_vars["wifi"].set(f"{wifi.get('ip', '-')} ({wifi.get('clients', 0)} clients)")
        self.summary_vars["ble"].set(self._format_enabled_connected(ble.get("enabled"), ble.get("connected")))
        self.summary_vars["stats"].set(
            f"RX {stats.get('rf_rx', 0)} / TX {stats.get('rf_tx', 0)} / fail {stats.get('rf_tx_fail', 0)}"
        )

    def _update_rf_controls(self, data: dict[str, Any], update_form: bool = True) -> None:
        self.loading_rf_controls = True
        try:
            self._update_rf_controls_inner(data, update_form=update_form)
        finally:
            self.loading_rf_controls = False

    def _update_rf_controls_inner(self, data: dict[str, Any], update_form: bool = True) -> None:
        if "channel" in data:
            if update_form:
                self.channel_var.set(str(data["channel"]))
            self.summary_vars["channel"].set(str(data["channel"]))
        if "datarate" in data:
            if update_form:
                self.datarate_var.set(str(data["datarate"]))
            self.summary_vars["datarate"].set(str(data["datarate"]))
        if "power" in data:
            if update_form:
                self.power_var.set(str(data["power"]))
            self.summary_vars["power"].set(str(data["power"]))
        if "auto_ack" in data:
            if update_form:
                self.auto_ack_var.set(bool(data["auto_ack"]))
        if "listening" in data:
            self.summary_vars["listening"].set("yes" if data["listening"] else "no")
        if "initialized" in data or "chip_connected" in data:
            initialized = data.get("initialized")
            connected = data.get("chip_connected")
            self.summary_vars["radio"].set("ok" if initialized and connected else "check")

        rx_address = data.get("rx_address_ascii") or data.get("rx_address_hex")
        tx_address = data.get("tx_address_ascii") or data.get("tx_address_hex")
        if data.get("rx_address_ascii") or data.get("tx_address_ascii"):
            self.address_format_var.set("ascii")
        elif data.get("rx_address_hex") or data.get("tx_address_hex"):
            self.address_format_var.set("hex")
        if rx_address:
            self.rx_address_var.set(str(rx_address))
            self.summary_vars["rx_address"].set(str(rx_address))
        if tx_address:
            self.tx_address_var.set(str(tx_address))
            self.summary_vars["tx_address"].set(str(tx_address))

    def _mark_rf_config_dirty(self) -> None:
        if not self.loading_rf_controls:
            self._set_rf_config_dirty(True)

    def _set_rf_config_dirty(self, dirty: bool) -> None:
        self.rf_config_dirty = dirty
        if dirty:
            self.rf_config_state_var.set("Unsaved RF config edits. Click Apply Config to send them.")
        else:
            self.rf_config_state_var.set("RF config matches last device read.")

    def _update_bridge_controls(self, data: dict[str, Any]) -> None:
        if "rf_to_wifi" in data:
            self.rf_to_wifi_var.set(bool(data["rf_to_wifi"]))
        if "rf_to_ble" in data:
            self.rf_to_ble_var.set(bool(data["rf_to_ble"]))

        wifi = "wifi on" if self.rf_to_wifi_var.get() else "wifi off"
        ble = "ble on" if self.rf_to_ble_var.get() else "ble off"
        self.summary_vars["bridge"].set(f"{wifi}, {ble}")

    def _format_enabled_connected(self, enabled: Any, connected: Any) -> str:
        if enabled is None:
            return "-"
        if not enabled:
            return "disabled"
        return "connected" if connected else "advertising"

    def _format_uptime(self, uptime_ms: Any) -> str:
        if not isinstance(uptime_ms, (int, float)):
            return "-"
        seconds = int(uptime_ms // 1000)
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours:
            return f"{hours}h {minutes}m {seconds}s"
        if minutes:
            return f"{minutes}m {seconds}s"
        return f"{seconds}s"

    def _set_busy(self, busy: bool) -> None:
        self.busy = busy
        state = "disabled" if busy else "normal"
        for button in self.command_buttons:
            try:
                button.configure(state=state)
            except tk.TclError:
                pass

    def _append_log(self, message: str) -> None:
        self.log.configure(state="normal")
        self.log.insert(tk.END, message + "\n")
        self.log.see(tk.END)
        self.log.configure(state="disabled")

    def _handle_event(self, event: dict[str, Any]) -> None:
        self.event_count += 1
        event_type = event.get("type")

        if event_type == "packet":
            self.event_packet_count += 1
            data = event.get("data") if isinstance(event.get("data"), dict) else {}
            self._append_event_log(
                f"< packet len={data.get('len', '-')} hex={data.get('hex', '-')} uptime_ms={data.get('uptime_ms', '-')}"
            )
        elif event_type == "status":
            data = event.get("data") if isinstance(event.get("data"), dict) else {}
            self._append_event_log("< status event")
            self._update_overview_from_status(data)
        else:
            self._append_event_log(f"< event {json.dumps(event, separators=(',', ':'))}")

        self.event_status_var.set(f"Streaming ({self.event_packet_count} packets, {self.event_count} events)")

    def _append_event_log(self, message: str) -> None:
        self.event_log.configure(state="normal")
        self.event_log.insert(tk.END, message + "\n")
        self.event_log.see(tk.END)
        self.event_log.configure(state="disabled")

    def _clear_log(self) -> None:
        self.log.configure(state="normal")
        self.log.delete("1.0", tk.END)
        self.log.configure(state="disabled")

    def _clear_event_log(self) -> None:
        self.event_log.configure(state="normal")
        self.event_log.delete("1.0", tk.END)
        self.event_log.configure(state="disabled")
        self.event_count = 0
        self.event_packet_count = 0
        if self.event_running:
            self.event_status_var.set("Streaming (0 packets, 0 events)")
        else:
            self.event_status_var.set("Stopped")

    def _refresh_status_if_idle(self) -> None:
        if not self.busy and self._endpoint():
            self._start_command("status", {}, log=False, refresh_after=False)

    def _auto_refresh_status(self) -> None:
        if self.auto_status_var.get():
            self._refresh_status_if_idle()
        self.after(3000, self._auto_refresh_status)

    def _on_close(self) -> None:
        self.stop_event_stream()
        self._close_all_clients()
        self.destroy()


if __name__ == "__main__":
    app = WirelessDevBridgeApp()
    app.mainloop()
