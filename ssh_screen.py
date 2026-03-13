"""
ssh_screen.py — Nextral SSH Client

Features:
  • Connection manager with saved hosts (stored in ssh_hosts.json)
  • Interactive terminal session via paramiko channels
  • Integrates with TerminalScreen's PassthroughMode on connect / disconnect
  • Full keyboard passthrough once connected
"""

from __future__ import annotations

import asyncio
import json
import os
import socket
import threading
from pathlib import Path
from typing import Callable, Optional

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Button, Input, Label, ListItem, ListView, RichLog, Static

# ---------------------------------------------------------------------------
# Saved-hosts persistence
# ---------------------------------------------------------------------------
HOSTS_FILE = Path(__file__).parent / "ssh_hosts.json"


def _load_hosts() -> list[dict]:
    if HOSTS_FILE.exists():
        try:
            return json.loads(HOSTS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def _save_hosts(hosts: list[dict]) -> None:
    try:
        HOSTS_FILE.write_text(json.dumps(hosts, indent=2), encoding="utf-8")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# SSHScreen
# ---------------------------------------------------------------------------
class SSHScreen(Screen):
    """Interactive SSH client with connection manager."""

    BINDINGS = [
        Binding("escape", "close", "Close / Disconnect"),
        Binding("ctrl+d", "disconnect", "Disconnect", show=False),
    ]

    CSS = """
    SSHScreen {
        background: #040a10;
    }

    /* ── Title bar ── */
    #ssh_title {
        width: 100%;
        height: 3;
        content-align: center middle;
        background: #061825;
        color: #38bdf8;
        text-style: bold;
        border-bottom: solid #0ea5e9;
    }

    /* ── Layout containers ── */
    #main_area {
        height: 1fr;
        width: 100%;
    }

    /* ── Saved-hosts sidebar ── */
    #host_panel {
        width: 30;
        height: 100%;
        background: #050d14;
        border-right: solid #0c4a6e;
    }

    #host_panel_title {
        height: 1;
        background: #0c2130;
        color: #38bdf8;
        text-style: bold;
        text-align: center;
        padding: 0 1;
    }

    #host_list {
        height: 1fr;
        background: #050d14;
        scrollbar-background: #040a10;
        scrollbar-color: #0c4a6e;
    }

    #host_list > ListItem {
        padding: 0 1;
        height: 1;
        color: #94a3b8;
    }

    #host_list > ListItem:hover {
        background: #0c2130;
        color: #38bdf8;
    }

    #host_list > ListItem.-highlighted {
        background: #0c3048;
        color: #38bdf8;
    }

    /* ── Right side (form + terminal log) ── */
    #right_panel {
        width: 1fr;
        height: 100%;
    }

    /* ── Connection form ── */
    #conn_form {
        height: auto;
        padding: 1 2;
        background: #050d14;
        border-bottom: solid #0c4a6e;
    }

    .form_row {
        height: auto;
        margin-bottom: 1;
    }

    .form_label {
        width: 14;
        height: 3;
        align-vertical: middle;
        color: #7dd3fc;
        text-style: bold;
    }

    .form_input {
        width: 1fr;
        height: 3;
        background: #061825;
        border: tall #0c4a6e;
        color: #e2e8f0;
    }

    .form_input:focus {
        border: tall #38bdf8;
        background: #082030;
    }

    #btn_row {
        height: auto;
        margin-top: 1;
        align-horizontal: left;
    }

    .ssh_btn {
        margin-right: 1;
        text-style: bold;
    }

    /* ── Terminal log ── */
    #terminal_log {
        height: 1fr;
        background: #020810;
        color: #94a3b8;
        padding: 0 1;
        border: none;
        scrollbar-background: #040a10;
        scrollbar-color: #0c4a6e;
    }

    /* ── Passthrough input row ── */
    #passthrough_row {
        height: 3;
        background: #040a10;
        border-top: solid #0c4a6e;
        padding: 0 1;
    }

    #pt_label {
        width: auto;
        align-vertical: middle;
        padding-right: 1;
        color: #0ea5e9;
        text-style: bold;
    }

    #pt_input {
        width: 1fr;
        height: 3;
        background: transparent;
        border: none;
        color: #38bdf8;
    }

    /* ── Status bar ── */
    #ssh_status {
        dock: bottom;
        height: 1;
        background: #0c2130;
        color: #38bdf8;
        text-align: center;
    }

    /* ── Connected state ── */
    SSHScreen.connected #conn_form {
        display: none;
    }

    SSHScreen.connected #passthrough_row {
        border-top: solid #22c55e;
    }

    SSHScreen.connected #pt_label {
        color: #22c55e;
    }

    SSHScreen.connected #pt_input {
        color: #86efac;
    }

    SSHScreen.connected #ssh_status {
        background: #052e16;
        color: #22c55e;
    }

    #tunnel_row {
        height: auto;
        padding: 1;
        background: #040d18;
        border-top: solid #0c2d48;
    }
    """

    # Track connection state reactively so CSS responds automatically
    connected: reactive[bool] = reactive(False)

    def __init__(self, host: str = "") -> None:
        super().__init__()
        self._prefill_host = host
        self._paramiko_client = None
        self._channel: Optional[object] = None   # paramiko.Channel
        self._reader_thread: Optional[threading.Thread] = None
        self._running = False
        self._hosts: list[dict] = _load_hosts()
        self._tunnels: dict = {}  # maps "label" -> (server, thread)
        # Callback so TerminalScreen can toggle its own passthrough mode
        self._on_connect_cb: Optional[Callable[[bool], None]] = None

    def set_passthrough_callback(self, cb: Callable[[bool], None]) -> None:
        """
        Register a callback that TerminalScreen uses to know when
        to enable/disable its own passthrough lock.

        cb(True)  → SSH session opened  → TerminalScreen enter passthrough
        cb(False) → SSH session closed  → TerminalScreen exit passthrough
        """
        self._on_connect_cb = cb

    # ------------------------------------------------------------------
    # Compose
    # ------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Static("◈  NEXTRAL  //  SSH  CLIENT  ◈", id="ssh_title")

        with Horizontal(id="main_area"):
            # ── Saved-hosts sidebar ──
            with Vertical(id="host_panel"):
                yield Static("── SAVED HOSTS ──", id="host_panel_title")
                yield ListView(id="host_list")

            # ── Right panel ──
            with Vertical(id="right_panel"):
                # Connection form
                with Container(id="conn_form"):
                    with Horizontal(classes="form_row"):
                        yield Label("Host / IP", classes="form_label")
                        yield Input(
                            id="f_host",
                            placeholder="192.168.1.1 or hostname",
                            classes="form_input",
                        )
                    with Horizontal(classes="form_row"):
                        yield Label("Port", classes="form_label")
                        yield Input(
                            id="f_port",
                            placeholder="22",
                            value="22",
                            classes="form_input",
                        )
                    with Horizontal(classes="form_row"):
                        yield Label("Username", classes="form_label")
                        yield Input(
                            id="f_user",
                            placeholder="root",
                            classes="form_input",
                        )
                    with Horizontal(classes="form_row"):
                        yield Label("Password", classes="form_label")
                        yield Input(
                            id="f_pass",
                            placeholder="(leave empty for key auth)",
                            password=True,
                            classes="form_input",
                        )
                    with Horizontal(classes="form_row"):
                        yield Label("Key File", classes="form_label")
                        yield Input(
                            id="f_key",
                            placeholder="~/.ssh/id_rsa  (optional)",
                            classes="form_input",
                        )
                    with Horizontal(id="btn_row"):
                        yield Button("⚡ Connect", id="btn_connect", variant="success", classes="ssh_btn")
                        yield Button("💾 Save Host", id="btn_save", variant="default", classes="ssh_btn")
                        yield Button("🗑 Delete", id="btn_del", variant="error", classes="ssh_btn")
                        yield Button("✕ Close", id="btn_close", variant="default", classes="ssh_btn")

                # Live terminal output
                yield RichLog(id="terminal_log", markup=True, wrap=True, highlight=False, max_lines=2000)

                # Passthrough input (shown always, active when connected)
                with Horizontal(id="passthrough_row"):
                    yield Label("SSH ❯", id="pt_label")
                    yield Input(id="pt_input", placeholder="Disconnected — connect first…")

                # Tunnel controls (always visible)
                with Container(id="tunnel_row"):
                    yield Static("[bold cyan]PORT FORWARDER:[/] ", markup=True)
                    with Horizontal():
                        yield Input(id="tun_lport", placeholder="Local Port", classes="form_input")
                        yield Input(id="tun_rhost", placeholder="Remote Host", classes="form_input")
                        yield Input(id="tun_rport", placeholder="Remote Port", classes="form_input")
                    with Horizontal():
                        from textual.widgets import Select as _Sel
                        yield _Sel(
                            [("Local (-L)", "L"), ("Remote (-R)", "R"), ("Dynamic SOCKS (-D)", "D")],
                            id="tun_type", value="L"
                        )
                        yield Button("▶ START TUNNEL", id="btn_tunnel_start", variant="success")
                        yield Button("■ STOP ALL", id="btn_tunnel_stop", variant="error")

        yield Static(id="ssh_status")

    # ------------------------------------------------------------------
    # Mount
    # ------------------------------------------------------------------

    def on_mount(self) -> None:
        self._update_status("[dim]Ready. Fill in connection details or select a saved host.[/]")
        self._refresh_host_list()
        self.query_one("#pt_input", Input).disabled = True

        log = self.query_one("#terminal_log", RichLog)
        log.write("[bold cyan]╔══════════════════════════════════════════════════════╗[/]")
        log.write("[bold cyan]║[/]          [bold white]NEXTRAL  //  SSH  CLIENT[/]              [bold cyan]║[/]")
        log.write("[bold cyan]╚══════════════════════════════════════════════════════╝[/]")
        log.write("")
        log.write("[dim]Supports password & key-based authentication via paramiko.[/]")
        log.write("[dim]Once connected, all input is forwarded directly to the remote shell.[/]")
        log.write("[dim]Press [bold]Ctrl+D[/] or [bold]Escape[/] to disconnect and return.[/]")
        log.write("")

        # Pre-fill host field if launched with a host argument
        if self._prefill_host:
            self.query_one("#f_host", Input).value = self._prefill_host

    # ------------------------------------------------------------------
    # Host list management
    # ------------------------------------------------------------------

    def _refresh_host_list(self) -> None:
        lv = self.query_one("#host_list", ListView)
        lv.clear()
        for i, h in enumerate(self._hosts):
            label = f"{h.get('user', 'user')}@{h.get('host', '?')}:{h.get('port', 22)}"
            lv.append(ListItem(Label(label), id=f"host_{i}"))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Populate form from saved host selection."""
        idx_str = event.item.id or ""
        if not idx_str.startswith("host_"):
            return
        try:
            idx = int(idx_str.split("_", 1)[1])
            h = self._hosts[idx]
            self.query_one("#f_host", Input).value = h.get("host", "")
            self.query_one("#f_port", Input).value = str(h.get("port", 22))
            self.query_one("#f_user", Input).value = h.get("user", "")
            self.query_one("#f_pass", Input).value = h.get("password", "")
            self.query_one("#f_key", Input).value = h.get("key_file", "")
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Button dispatch
    # ------------------------------------------------------------------

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn = event.button.id
        if btn == "btn_connect":
            asyncio.create_task(self._do_connect())
        elif btn == "btn_save":
            self._save_current_host()
        elif btn == "btn_del":
            self._delete_selected_host()
        elif btn == "btn_close":
            self.action_close()
        elif btn == "btn_tunnel_start":
            self._start_tunnel()
        elif btn == "btn_tunnel_stop":
            self._stop_tunnels()

    # ------------------------------------------------------------------
    # Passthrough input — send to SSH channel
    # ------------------------------------------------------------------

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != "pt_input":
            return
        if not self.connected or self._channel is None:
            return
        text = event.value + "\n"
        event.input.value = ""
        try:
            self._channel.send(text.encode("utf-8", errors="replace"))
        except Exception as ex:
            log = self.query_one("#terminal_log", RichLog)
            log.write(f"[red]Send error: {ex}[/]")

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    async def _do_connect(self) -> None:
        host = self.query_one("#f_host", Input).value.strip()
        port_str = self.query_one("#f_port", Input).value.strip() or "22"
        user = self.query_one("#f_user", Input).value.strip()
        password = self.query_one("#f_pass", Input).value
        key_file = self.query_one("#f_key", Input).value.strip()

        log = self.query_one("#terminal_log", RichLog)

        if not host or not user:
            self._update_status("[red]⚠ Host and Username are required.[/]")
            return

        try:
            port = int(port_str)
        except ValueError:
            self._update_status("[red]⚠ Port must be an integer.[/]")
            return

        self._update_status(f"[yellow]◐ Connecting to {user}@{host}:{port}…[/]")
        log.write(f"[bold yellow]>>> Initiating SSH to {user}@{host}:{port}…[/]")

        try:
            import paramiko  # imported here so the rest of the app still works if not installed
        except ImportError:
            log.write("[bold red]✕ paramiko not installed! Run: pip install paramiko[/]")
            self._update_status("[red]paramiko missing — pip install paramiko[/]")
            return

        # Run the blocking paramiko connect in a thread executor
        loop = asyncio.get_event_loop()
        err = await loop.run_in_executor(None, self._connect_sync, host, port, user, password, key_file)

        if err:
            log.write(f"[bold red]✕ Connection failed: {err}[/]")
            self._update_status(f"[red]Connection failed: {err}[/]")
            return

        # Connected — switch to terminal mode
        self.connected = True
        self.add_class("connected")
        pt = self.query_one("#pt_input", Input)
        pt.disabled = False
        pt.placeholder = f"Send command to {user}@{host}…"
        pt.focus()

        self._update_status(f"[green]✓ Connected to {user}@{host}:{port}  |  Ctrl+D / Esc to disconnect[/]")
        log.write(f"[bold green]✓ SSH session established — {user}@{host}:{port}[/]")
        log.write("[dim]─────────────────────────────────────────────────[/]")

        # Notify TerminalScreen to enter passthrough lock
        if self._on_connect_cb:
            self._on_connect_cb(True)

        # Start reader thread
        self._running = True
        self._reader_thread = threading.Thread(
            target=self._channel_reader, daemon=True
        )
        self._reader_thread.start()

    def _connect_sync(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        key_file: str,
    ) -> Optional[str]:
        """Blocking connect — run in executor. Returns error string or None."""
        import paramiko

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            connect_kwargs: dict = {
                "hostname": host,
                "port": port,
                "username": user,
                "timeout": 15,
                "banner_timeout": 15,
                "auth_timeout": 20,
            }
            if key_file:
                expanded = os.path.expanduser(key_file)
                if os.path.exists(expanded):
                    connect_kwargs["key_filename"] = expanded
            if password:
                connect_kwargs["password"] = password

            client.connect(**connect_kwargs)
        except Exception as ex:
            return str(ex)

        self._paramiko_client = client
        # Request an interactive PTY channel
        transport = client.get_transport()
        channel = transport.open_session()
        channel.get_pty(term="xterm-256color", width=200, height=50)
        channel.invoke_shell()
        self._channel = channel
        return None

    def _channel_reader(self) -> None:
        """Background thread: read from SSH channel and post to log."""
        import paramiko

        channel: paramiko.Channel = self._channel  # type: ignore[assignment]
        while self._running:
            try:
                if channel.recv_ready():
                    data = channel.recv(4096).decode("utf-8", errors="replace")
                    # Strip ANSI control sequences for clean RichLog display
                    clean = _strip_ansi(data)
                    if clean.strip():
                        self.app.call_from_thread(self._append_output, clean)
                if channel.recv_stderr_ready():
                    edata = channel.recv_stderr(4096).decode("utf-8", errors="replace")
                    clean_err = _strip_ansi(edata)
                    if clean_err.strip():
                        self.app.call_from_thread(
                            self._append_output, f"[red]{clean_err}[/]"
                        )
                if channel.exit_status_ready():
                    self.app.call_from_thread(self._on_remote_exit)
                    break
            except Exception:
                break

    def _append_output(self, text: str) -> None:
        log = self.query_one("#terminal_log", RichLog)
        # Write each line individually so RichLog scrolls nicely
        for line in text.splitlines():
            log.write(line)

    def _on_remote_exit(self) -> None:
        log = self.query_one("#terminal_log", RichLog)
        log.write("")
        log.write("[bold yellow]>>> Remote shell exited.[/]")
        self._disconnect_cleanup()

    # ------------------------------------------------------------------
    # Tunneling
    # ------------------------------------------------------------------

    def _start_tunnel(self) -> None:
        """Start a port forwarding tunnel over the current SSH session."""
        log = self.query_one("#terminal_log", RichLog)
        if not self.connected or self._channel is None:
            log.write("[red]\u26a0 Not connected. Connect to SSH first.[/]")
            return

        from textual.widgets import Select
        tun_type = self.query_one("#tun_type", Select).value
        lport_str = self.query_one("#tun_lport", Input).value.strip()
        rhost = self.query_one("#tun_rhost", Input).value.strip()
        rport_str = self.query_one("#tun_rport", Input).value.strip()

        try:
            lport = int(lport_str) if lport_str else 0
            rport = int(rport_str) if rport_str else 0
        except ValueError:
            log.write("[red]\u26a0 Invalid port values.[/]")
            return

        transport = self._paramiko_client.get_transport() if self._paramiko_client else None
        if not transport:
            log.write("[red]\u26a0 No active transport.[/]")
            return

        try:
            if tun_type == "L":
                # Local forwarding: tunnel localhost:lport -> rhost:rport
                import socketserver
                class _Handler(socketserver.BaseRequestHandler):
                    def handle(self):
                        try:
                            chan = transport.open_channel("direct-tcpip", (rhost, rport), self.request.getpeername())
                            if chan is None: return
                            while True:
                                import select as _sel
                                r, _, _ = _sel.select([self.request, chan], [], [], 1)
                                if self.request in r:
                                    d = self.request.recv(1024)
                                    if not d: break
                                    chan.send(d)
                                if chan in r:
                                    d = chan.recv(1024)
                                    if not d: break
                                    self.request.send(d)
                        except Exception: pass

                class _Server(socketserver.ThreadingTCPServer):
                    daemon_threads = True
                    allow_reuse_address = True

                server = _Server(("127.0.0.1", lport), _Handler)
                t = threading.Thread(target=server.serve_forever, daemon=True)
                t.start()
                label = f"L:127.0.0.1:{lport}->{rhost}:{rport}"
                self._tunnels[label] = (server, t)
                log.write(f"[green]\u2713 Local tunnel: {label}[/]")

            elif tun_type == "R":
                transport.request_port_forward("", rport)
                label = f"R:remote:{rport}->{rhost}:{lport}"
                self._tunnels[label] = (None, None)
                log.write(f"[green]\u2713 Remote tunnel requested: {label}[/]")

            elif tun_type == "D":
                # Dynamic SOCKS proxy via local port
                import socks_server  # optional; show note if missing
                log.write(f"[yellow]\u26a0 SOCKS proxy on 127.0.0.1:{lport} - implement with socks_server or similar.[/]")

        except Exception as ex:
            log.write(f"[red]\u26a0 Tunnel error: {ex}[/]")

    def _stop_tunnels(self) -> None:
        log = self.query_one("#terminal_log", RichLog)
        for label, (server, _) in list(self._tunnels.items()):
            try:
                if server: server.shutdown()
            except Exception: pass
        self._tunnels.clear()
        log.write("[yellow]All tunnels stopped.[/]")

    # ------------------------------------------------------------------
    # Disconnect
    # ------------------------------------------------------------------

    def action_disconnect(self) -> None:
        if self.connected:
            self._disconnect_cleanup()

    def _disconnect_cleanup(self) -> None:
        self._running = False
        try:
            if self._channel:
                self._channel.close()
            if self._paramiko_client:
                self._paramiko_client.close()
        except Exception:
            pass
        self._channel = None
        self._paramiko_client = None
        self.connected = False
        self.remove_class("connected")

        pt = self.query_one("#pt_input", Input)
        pt.disabled = True
        pt.placeholder = "Disconnected — connect first…"

        log = self.query_one("#terminal_log", RichLog)
        log.write("[dim]─────────────────────── disconnected ───────────────────────[/]")
        self._update_status("[dim]Disconnected.[/]")

        # Notify TerminalScreen to exit passthrough lock
        if self._on_connect_cb:
            self._on_connect_cb(False)

    # ------------------------------------------------------------------
    # Saved-host helpers
    # ------------------------------------------------------------------

    def _save_current_host(self) -> None:
        h = {
            "host": self.query_one("#f_host", Input).value.strip(),
            "port": int(self.query_one("#f_port", Input).value.strip() or "22"),
            "user": self.query_one("#f_user", Input).value.strip(),
            "password": self.query_one("#f_pass", Input).value,
            "key_file": self.query_one("#f_key", Input).value.strip(),
        }
        if not h["host"]:
            self._update_status("[red]Cannot save — Host is empty.[/]")
            return

        # Avoid duplicates by host+port+user
        for existing in self._hosts:
            if (
                existing.get("host") == h["host"]
                and existing.get("port") == h["port"]
                and existing.get("user") == h["user"]
            ):
                # Update existing entry
                existing.update(h)
                _save_hosts(self._hosts)
                self._refresh_host_list()
                self._update_status(f"[green]✓ Updated: {h['user']}@{h['host']}[/]")
                return

        self._hosts.append(h)
        _save_hosts(self._hosts)
        self._refresh_host_list()
        self._update_status(f"[green]✓ Saved: {h['user']}@{h['host']}:{h['port']}[/]")

    def _delete_selected_host(self) -> None:
        lv = self.query_one("#host_list", ListView)
        highlighted = lv.highlighted_child
        if highlighted is None:
            self._update_status("[yellow]Select a host to delete.[/]")
            return
        idx_str = highlighted.id or ""
        if not idx_str.startswith("host_"):
            return
        try:
            idx = int(idx_str.split("_", 1)[1])
            removed = self._hosts.pop(idx)
            _save_hosts(self._hosts)
            self._refresh_host_list()
            self._update_status(f"[green]Deleted: {removed.get('user')}@{removed.get('host')}[/]")
        except Exception as ex:
            self._update_status(f"[red]Delete failed: {ex}[/]")

    # ------------------------------------------------------------------
    # Close / Escape
    # ------------------------------------------------------------------

    def action_close(self) -> None:
        if self.connected:
            self._disconnect_cleanup()
        self.app.pop_screen()

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def _update_status(self, text: str) -> None:
        try:
            self.query_one("#ssh_status", Static).update(text)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# ANSI strip helper (keeps RichLog clean)
# ---------------------------------------------------------------------------
import re as _re

_ANSI_RE = _re.compile(r"\x1B[@-Z\\-_]|\x1B\[.*?[@-~]|\x1B\(.")


def _strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from a string."""
    return _ANSI_RE.sub("", text)
