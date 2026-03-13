"""
Nextral Metasploit RPC Bridge — msf_bridge.py
Provides a Textual UI for interacting with a running msfrpcd instance.
Requires pymetasploit3: pip install pymetasploit3
"""

import os
import subprocess
import socket
import base64
import time
import asyncio
from pathlib import Path
from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical, Horizontal, Container, ScrollableContainer
from textual.widgets import Header, Footer, Static, Button, RichLog, Label, Input, ListView, ListItem, DataTable
from textual.binding import Binding
from textual.reactive import reactive
from textual.worker import Worker, get_current_worker

try:
    from pymetasploit3.msfrpc import MsfRpcClient
    MSF_AVAILABLE = True
except ImportError:
    MSF_AVAILABLE = False

class MSFBridgeScreen(Screen):
    """Metasploit RPC Bridge Interface"""

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Close"),
        Binding("r", "refresh_data", "Refresh Sessions/Jobs"),
        Binding("ctrl+c", "disconnect", "Disconnect"),
    ]

    CSS = """
    MSFBridgeScreen {
        background: #050508;
    }
    
    #msf_header {
        dock: top;
        height: 5;
        background: #0a0a12;
        border-bottom: heavy #ff0055;
        padding: 0 1;
    }
    
    .msf-title {
        color: #ff0055;
        text-style: bold;
        font-size: 140%;
    }
    
    .msf-subtitle {
        color: #8888aa;
    }
    
    #connect_panel {
        layout: horizontal;
        height: 3;
        margin-top: 1;
        align: left middle;
    }
    
    .msf-input {
        background: #0a0a12;
        border: solid #1a1a2e;
        color: #ff3377;
        width: 30;
        transition: border 0.3s;
    }
    
    .msf-input:focus {
        border: solid #ff0055;
    }
    
    .msf-btn {
        background: #1a1a2e;
        border: solid #1a1a2e;
        color: #bbbbbb;
        min-width: 15;
        transition: background 0.3s, color 0.3s, border 0.3s;
    }
    
    .msf-btn:hover {
        background: #ff0055;
        color: #ffffff;
        border: solid #ff0055;
    }
    
    #main_split {
        height: 1fr;
        layout: horizontal;
    }
    
    #left_panel {
        width: 50%;
        border-right: heavy #1a1a2e;
        padding: 1;
    }
    
    #right_panel {
        width: 50%;
        padding: 1;
    }
    
    .section-label {
        color: #00e5ff;
        text-style: bold;
        background: #0a0a12;
        padding: 0 1;
        margin-bottom: 1;
        border-left: thick #00e5ff;
    }
    
    DataTable {
        height: 10;
        border: solid #1a1a2e;
        background: #050508;
    }
    
    #console_log {
        height: 1fr;
        border: solid #1a1a2e;
        background: #050508;
    }
    
    #console_input {
        dock: bottom;
        height: 3;
        background: #0a0a12;
        border: solid #1a1a2e;
        color: #00e5ff;
        transition: border 0.3s;
    }
    
    #console_input:focus {
        border: solid #00e5ff;
    }
    """

    connected = reactive(False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = None
        self.current_console_id = 0
        self.last_activity = time.time()
        self.reader_timer = None

    def _schedule_next_read(self, override_interval=None) -> None:
        if not self.connected:
            return
            
        interval = override_interval
        if interval is None:
            if time.time() - self.last_activity < 10.0:
                interval = 0.2
            else:
                interval = 3.0
                
        self.reader_timer = self.set_timer(interval, self._read_console, name="msf_console_reader")


    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Container(id="msf_header"):
            yield Static("☠ METASPLOIT RPC BRIDGE ☠", classes="msf-title")
            yield Static("Connect to msfrpcd to manage sessions, jobs, and execute modules remotely.", classes="msf-subtitle")
            
            with Horizontal(id="connect_panel"):
                yield Input(value="127.0.0.1", id="msf_host", placeholder="Host", classes="msf-input")
                yield Input(value="55553", id="msf_port", placeholder="Port", classes="msf-input")
                yield Input(password=True, value="msf", id="msf_pass", placeholder="Password", classes="msf-input")
                yield Button("CONNECT", id="btn_connect", classes="msf-btn")
                yield Button("START RPC", id="btn_start_rpc", classes="msf-btn", variant="warning")
                yield Button("⚡ QUICK HANDLER", id="btn_quick_handler", classes="msf-btn", variant="primary")

        if not MSF_AVAILABLE:
            with Vertical(classes="msf-missing-pkg", style="padding: 2; align: center middle; height: 1fr;"):
                yield Static("[bold red]pymetasploit3 is not installed.[/]")
                yield Static("Please run: [bold cyan]pip install pymetasploit3[/]")
            yield Footer()
            return

        with Horizontal(id="main_split"):
            with Vertical(id="left_panel"):
                yield Label("ACTIVE SESSIONS", classes="section-label")
                yield DataTable(id="dt_sessions")
                
                yield Label("BACKGROUND JOBS", classes="section-label")
                yield DataTable(id="dt_jobs")
                
                yield Label("MODULE SEARCH", classes="section-label")
                yield Input(id="module_search", placeholder="Search modules... (e.g. ms17_010)")
                yield RichLog(id="module_results", markup=True, max_lines=50, height=8)

            with Container(id="right_panel"):
                yield Label("CONSOLE INTERACTION", classes="section-label")
                yield RichLog(id="console_log", markup=True, max_lines=2000)
                yield Input(id="console_input", placeholder="Enter MSF console command here... (connected required)")

        yield Footer()

    def on_mount(self) -> None:
        if MSF_AVAILABLE:
            dt_sessions = self.query_one("#dt_sessions", DataTable)
            dt_sessions.add_columns("ID", "Type", "Info", "Tunnel")
            dt_sessions.cursor_type = "row"

            dt_jobs = self.query_one("#dt_jobs", DataTable)
            dt_jobs.add_columns("ID", "Name", "Start Time")
            dt_jobs.cursor_type = "row"
            
            self.query_one("#console_input", Input).disabled = True

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_connect":
            if self.connected:
                self.action_disconnect()
            else:
                self.connect_to_msf()
        elif event.button.id == "btn_start_rpc":
            await self.auto_start_msfrpcd()
        elif event.button.id == "btn_quick_handler":
            await self._quick_handler()

    async def auto_start_msfrpcd(self) -> None:
        """Attempt to launch msfrpcd in the background via asyncio."""
        host = self.query_one("#msf_host", Input).value
        port = self.query_one("#msf_port", Input).value
        password = self.query_one("#msf_pass", Input).value
        
        log = self.query_one("#console_log", RichLog)
        log.write("[bold yellow]Attempting to auto-launch msfrpcd...[/]")
        
        try:
            # Check if msfrpcd is in PATH
            import shutil
            msf_path = shutil.which("msfrpcd")
            if not msf_path:
                log.write("[bold red]Error: 'msfrpcd' not found in system PATH.[/]")
                log.write("[dim]Please install Metasploit or add it to your PATH.[/]")
                return

            # Launch in background using asyncio
            cmd = [msf_path, "-P", password, "-n", "-a", host, "-p", port]
            
            await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            log.write(f"[bold green]msfrpcd process spawned.[/] Waiting 5s for initialization...")
            # We'll try to connect after a short delay
            self.set_timer(5.0, self.connect_to_msf)
            
        except Exception as e:
            log.write(f"[bold red]Failed to launch msfrpcd: {e}[/]")

    def connect_to_msf(self) -> None:
        host = self.query_one("#msf_host", Input).value
        port = self.query_one("#msf_port", Input).value
        password = self.query_one("#msf_pass", Input).value
        
        log = self.query_one("#console_log", RichLog)
        log.write(f"[dim]Attempting connection to {host}:{port}...[/]")
        
        self.run_worker(self._connect_worker(host, port, password), exclusive=True)

    async def _connect_worker(self, host: str, port: str, password: str) -> None:
        try:
            # pymetasploit3 blocks, so doing it in a worker thread is good
            worker = get_current_worker()
            client = MsfRpcClient(password, server=host, port=int(port), ssl=True)
            
            if not worker.is_cancelled:
                self.app.call_from_thread(self._on_connect_success, client)
        except Exception as e:
            if not worker.is_cancelled:
                self.app.call_from_thread(self._on_connect_failure, str(e))

    def _on_connect_success(self, client) -> None:
        self.client = client
        self.connected = True
        
        btn = self.query_one("#btn_connect", Button)
        btn.label = "DISCONNECT"
        btn.variant = "error"
        
        self.query_one("#msf_host", Input).disabled = True
        self.query_one("#msf_port", Input).disabled = True
        self.query_one("#msf_pass", Input).disabled = True
        self.query_one("#console_input", Input).disabled = False
        
        log = self.query_one("#console_log", RichLog)
        log.write("[bold green]Successfully connected to msfrpcd.[/]")
        
        # Create a console
        res = self.client.call('console.create')
        if 'id' in res:
            self.current_console_id = res['id']
            log.write(f"[dim]Attached to MSF Console ID: {self.current_console_id}[/]")
            # Start a read loop for the console with adaptive heartbeat
            self._schedule_next_read(0.2)

        self.action_refresh_data()

    def _on_connect_failure(self, err: str) -> None:
        self.connected = False
        log = self.query_one("#console_log", RichLog)
        log.write(f"[bold red]Connection failed:[/] {err}")
        log.write("[dim]Ensure msfrpcd is running. Example: msfrpcd -P msf -n -a 127.0.0.1[/]")

    def action_disconnect(self) -> None:
        if not self.connected:
            return
            
        try:
            if self.client and hasattr(self, 'current_console_id') and self.current_console_id:
                self.client.call('console.destroy', [self.current_console_id])
        except:
            pass
            
        self.client = None
        self.connected = False
        
        btn = self.query_one("#btn_connect", Button)
        btn.label = "CONNECT"
        btn.variant = "default"
        
        self.query_one("#msf_host", Input).disabled = False
        self.query_one("#msf_port", Input).disabled = False
        self.query_one("#msf_pass", Input).disabled = False
        self.query_one("#console_input", Input).disabled = True
        
        log = self.query_one("#console_log", RichLog)
        log.write("[bold yellow]Disconnected from msfrpcd.[/]")
        
        dt_sessions = self.query_one("#dt_sessions", DataTable)
        dt_jobs = self.query_one("#dt_jobs", DataTable)
        dt_sessions.clear()
        dt_jobs.clear()

    def action_refresh_data(self) -> None:
        if not self.connected or not self.client:
            return
            
        self.run_worker(self._refresh_worker())

    async def _refresh_worker(self) -> None:
        if not self.client: return
        
        try:
            sessions = self.client.sessions.list
            jobs = self.client.jobs.list
            self.app.call_from_thread(self._update_tables, sessions, jobs)
        except Exception as e:
            self.app.call_from_thread(self._on_connect_failure, f"RPC Error: {e}")
            self.app.call_from_thread(self.action_disconnect)

    def _update_tables(self, sessions: dict, jobs: dict) -> None:
        dt_sessions = self.query_one("#dt_sessions", DataTable)
        dt_jobs = self.query_one("#dt_jobs", DataTable)
        
        dt_sessions.clear()
        dt_jobs.clear()
        
        for s_id, s_info in sessions.items():
            dt_sessions.add_row(
                s_id, 
                s_info.get('type', 'N/A'),
                s_info.get('info', 'N/A'),
                s_info.get('tunnel_peer', 'N/A')
            )
            
        for j_id, j_name in jobs.items():
            dt_jobs.add_row(j_id, j_name, "Running")

    def _read_console(self) -> None:
        if not self.connected or not self.client or not self.current_console_id:
            return
            
        try:
            # Only call if we are connected and not busy
            res = self.client.call('console.read', [self.current_console_id])
            if res and res.get('data'):
                line = res['data'].strip()
                if line:
                    log = self.query_one("#console_log", RichLog)
                    log.write(line)
                    self.last_activity = time.time()
        except:
            # Basic error handling to prevent crash on timeout/disconnect
            pass
        finally:
            self._schedule_next_read()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "console_input" and self.connected and self.client:
            cmd = event.value.strip()
            if cmd:
                log = self.query_one("#console_log", RichLog)
                log.write(f"[bold cyan]msf6 >[/] {cmd}")
                try:
                    self.client.call('console.write', [self.current_console_id, f"{cmd}\n"])
                    
                    # Adaptive Heartbeat: spike polling speed after command
                    self.last_activity = time.time()
                    if self.reader_timer:
                        self.reader_timer.stop()
                    self._schedule_next_read(0.2)
                    
                except Exception as e:
                    log.write(f"[bold red]RPC Error:[/] {e}")
            event.input.value = ""

    def on_input_changed(self, event) -> None:
        """Live module search as user types."""
        if event.input.id != "module_search":
            return
        query = event.value.strip().lower()
        try:
            results_log = self.query_one("#module_results", RichLog)
        except Exception:
            return
        results_log.clear()
        if not query or not self.connected or not self.client:
            if not self.connected:
                results_log.write("[dim]Connect to MSF to search modules.[/]")
            return
        try:
            # Use console search command via RPC for lightweight query
            res = self.client.call('module.search', [query])
            count = 0
            for m in (res or []):
                name = m.get('fullname') or m.get('name', '')
                rank = m.get('rank', '')
                if name:
                    results_log.write(f"[cyan]{name}[/] [dim]{rank}[/]")
                    count += 1
                if count >= 30:
                    results_log.write("[dim]... (more results, narrow your search)[/]")
                    break
            if count == 0:
                results_log.write("[yellow]No modules found.[/]")
        except Exception as ex:
            results_log.write(f"[red]Search error: {ex}[/]")

    async def _quick_handler(self) -> None:
        """Spin up a multi/handler for common reverse payloads."""
        log = self.query_one("#console_log", RichLog)
        if not self.connected or not self.client:
            log.write("[red]⚠ Not connected to MSF. Connect first.[/]")
            return

        # Use host from the MSF connection as default LHOST
        lhost = self.query_one("#msf_host", Input).value.strip() or "0.0.0.0"
        lport = "4444"

        cmds = [
            "use exploit/multi/handler",
            "set PAYLOAD windows/meterpreter/reverse_tcp",
            f"set LHOST {lhost}",
            f"set LPORT {lport}",
            "set ExitOnSession false",
            "exploit -j -z",
        ]

        log.write(f"[bold yellow]⚡ Launching Quick Handler ({lhost}:{lport})...[/]")
        try:
            for cmd in cmds:
                self.client.call('console.write', [self.current_console_id, f"{cmd}\n"])
                await asyncio.sleep(0.1)
            self.last_activity = time.time()
            self._schedule_next_read(0.5)
            log.write("[green]✓ Handler started in background (job). Check BACKGROUND JOBS.[/]")
            self.action_refresh_data()
        except Exception as ex:
            log.write(f"[red]Handler error: {ex}[/]")

    def on_unmount(self) -> None:
        self.action_disconnect()

