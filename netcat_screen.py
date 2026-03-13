"""
netcat_screen.py - Nextral Netcat Module

A user-friendly interface for Netcat (nc) networking tool.
Supports both client mode (connect to remote) and listen mode (wait for connections).
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical, Horizontal, Container, ScrollableContainer
from textual.widgets import Header, Footer, Static, Button, Input, RichLog, TextArea, Label
from textual.binding import Binding
from textual.reactive import reactive
from textual import work
import asyncio
import sys

sys.path.insert(0, '.')
from tools_locator import is_tool_installed, run_tool


class NetcatScreen(Screen):
    """Netcat Client/Server Interface"""
    
    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("c", "toggle_mode", "Toggle Mode"),
        Binding("r", "start_operation", "Run"),
        Binding("x", "stop_operation", "Stop"),
        Binding("c", "clear_terminal", "Clear"),
    ]
    
    CSS = """
    NetcatScreen {
        background: #0a0a12;
    }
    
    Header {
        background: #0a1a1a;
        color: #4db6ac;
    }
    
    #nc_title {
        width: 100%;
        height: 3;
        content-align: center middle;
        background: #0d2a2a;
        color: #4db6ac;
        text-style: bold;
        border-bottom: solid #00796b;
    }
    
    #main_container {
        height: 1fr;
        layout: grid;
        grid-size: 2 1;
        grid-columns: 1fr 1fr;
    }
    
    #left_panel {
        border: solid #00796b;
        margin: 1;
        padding: 1;
        background: #051515;
    }
    
    #right_panel {
        border: solid #004d40;
        margin: 1;
        padding: 1;
        background: #0a1515;
    }
    
    .panel_title {
        color: #80cbc4;
        text-style: bold;
        margin-bottom: 1;
    }
    
    .input_label {
        color: #4db6ac;
        margin-bottom: 0;
    }
    
    .input_field {
        background: #0d2020;
        border: solid #00695c;
        color: #b2dfdb;
    }
    
    #output_area {
        height: 1fr;
        background: #030a0a;
        border: solid #004d40;
        margin-top: 1;
    }
    
    #output_log {
        height: 100%;
        background: #030a0a;
    }
    
    #status_bar {
        dock: bottom;
        height: 2;
        background: #0a1a1a;
        color: #4db6ac;
    }
    
    #button_row {
        height: auto;
        padding: 1;
        background: #051515;
    }
    
    .action_btn {
        background: #00695c;
        color: #b2dfdb;
    }
    
    .action_btn:hover {
        background: #00897b;
    }
    
    #mode_indicator {
        width: 100%;
        height: 2;
        content-align: center middle;
        background: #004d40;
        color: #b2dfdb;
    }
    
    Footer {
        background: #0a1a1a;
        color: #4db6ac;
    }
    
    #terminal_input {
        height: 3;
        background: #0d2020;
        border: solid #00695c;
    }
    
    #terminal_output {
        height: 1fr;
        background: #030a0a;
        border: solid #004d40;
        margin: 1;
    }
    """
    
    mode = reactive("connect")  # "connect" or "listen"
    is_active = reactive(False)
    
    def __init__(self, target: str = "", port: int = 0, mode: str = "connect"):
        super().__init__()
        self.target = target
        self.port = port
        self.mode = mode
        self.process = None
        self._reader_task = None
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        yield Static("◈ NETCAT NETWORK TOOL ◈", id="nc_title")
        
        with Container(id="main_container"):
            with Container(id="left_panel"):
                yield Static("📡 CONNECTION SETTINGS", classes="panel_title")
                
                yield Label("MODE:", classes="input_label")
                with Horizontal(id="mode_buttons"):
                    yield Button("Connect (Client)", id="mode_connect", variant="primary")
                    yield Button("Listen (Server)", id="mode_listen", variant="default")
                
                yield Label("TARGET HOST:", classes="input_label")
                yield Input(
                    id="target_input",
                    placeholder="e.g., 192.168.1.1, example.com",
                    classes="input_field"
                )
                
                yield Label("PORT:", classes="input_label")
                yield Input(
                    id="port_input",
                    placeholder="e.g., 4444, 80, 22",
                    classes="input_field"
                )
                
                yield Label("ADDITIONAL OPTIONS:", classes="input_label")
                yield Input(
                    id="options_input",
                    placeholder="-v -n -z (optional flags)",
                    classes="input_field"
                )
                
                with Horizontal(id="button_row"):
                    yield Button("▶ CONNECT / LISTEN", id="action_btn", variant="success")
                    yield Button("■ STOP", id="stop_btn", variant="error")
            
            with Container(id="right_panel"):
                yield Static("📟 TERMINAL OUTPUT", classes="panel_title")
                
                yield RichLog(id="terminal_output", markup=True, wrap=True)
                
                yield Label("SEND DATA:", classes="input_label")
                yield Input(
                    id="send_input",
                    placeholder="Type message and press Enter to send...",
                    classes="input_field"
                )
        
        yield Static(id="status_bar")
        yield Footer()
    
    def on_mount(self) -> None:
        self._update_status("[cyan]Ready. Select mode and enter target/port, then press [bold]RUN[/]")
        
        if self.target:
            self.query_one("#target_input", Input).value = self.target
        if self.port:
            self.query_one("#port_input", Input).value = str(self.port)
        
        log = self.query_one("#terminal_output", RichLog)
        log.write("[bold cyan]╔══════════════════════════════════════════════════════════════╗[/]")
        log.write("[bold cyan]║[/]                  [bold white]NETCAT TERMINAL v1.0[/]                     [bold cyan]║[/]")
        log.write("[bold cyan]╚══════════════════════════════════════════════════════════════╝[/]")
        log.write("")
        
        installed, path = is_tool_installed("netcat")
        if not installed:
            log.write("[bold red]⚠ NETCAT NOT FOUND![/]")
            log.write("[dim]Please install netcat or configure path in Settings.[/]")
        else:
            log.write(f"[green]✓ Netcat found: {path}[/]")
            log.write("")
            log.write("[dim]Mode: [yellow]CONNECT[/] - Connect to remote host")
            log.write("[dim]Mode: [yellow]LISTEN[/] - Wait for incoming connections")
            log.write("")
        
        self._update_mode_indicator()
    
    def _update_status(self, text: str) -> None:
        try:
            self.query_one("#status_bar", Static).update(text)
        except:
            pass
    
    def _update_mode_indicator(self) -> None:
        if self.mode == "connect":
            self._update_status("[cyan]MODE: CONNECT - Ready to connect to remote host[/]")
        else:
            self._update_status("[cyan]MODE: LISTEN - Waiting for incoming connections[/]")
    
    def action_close(self) -> None:
        self._stop_operation()
        self.app.pop_screen()
    
    def action_toggle_mode(self) -> None:
        self.mode = "listen" if self.mode == "connect" else "connect"
        self._update_mode_indicator()
    
    def action_start_operation(self) -> None:
        if self.is_active:
            return
        
        target = self.query_one("#target_input", Input).value.strip()
        port_str = self.query_one("#port_input", Input).value.strip()
        options = self.query_one("#options_input", Input).value.strip()
        
        if not port_str:
            self._update_status("[red]Error: Please enter a port number![/]")
            return
        
        try:
            port = int(port_str)
        except ValueError:
            self._update_status("[red]Error: Port must be a number![/]")
            return
        
        if self.mode == "connect" and not target:
            self._update_status("[red]Error: Please enter a target host for connect mode![/]")
            return
        
        installed, path = is_tool_installed("netcat")
        if not installed:
            log = self.query_one("#terminal_output", RichLog)
            log.write("[bold red]Error: Netcat is not installed or not found in PATH![/]")
            return
        
        self.target = target
        self.port = port
        self.is_active = True
        
        asyncio.create_task(self._run_operation(target, port, options))
    
    async def _run_operation(self, target: str, port: int, options: str) -> None:
        log = self.query_one("#terminal_output", RichLog)
        
        tool_path = find_tool("netcat")
        
        if self.mode == "connect":
            log.write(f"[yellow]>>> Connecting to {target}:{port}...[/]")
            args = [target, str(port)]
        else:
            log.write(f"[yellow]>>> Listening on port {port}...[/]")
            args = ["-l", "-p", str(port)]
        
        if options:
            args.extend(options.split())
        
        try:
            self.process = await asyncio.create_subprocess_exec(
                tool_path,
                *args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            
            self._reader_task = asyncio.create_task(self._read_output(log))
            
            if self.mode == "connect":
                self._update_status(f"[green]Connected to {target}:{port} - Type to send data[/]")
            else:
                self._update_status(f"[green]Listening on port {port} - Waiting for connections...[/]")
                
        except Exception as e:
            log.write(f"[red]Error: {e}[/]")
            self.is_active = False
    
    async def _read_output(self, log: RichLog) -> None:
        buffer = ""
        while True:
            try:
                if not self.process or not self.process.stdout:
                    break
                
                chunk = await self.process.stdout.read(1024)
                if not chunk:
                    break
                
                text = chunk.decode('utf-8', errors='replace')
                buffer += text
                
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line.strip():
                        log.write(f"[white]{line}[/]")
                
            except asyncio.CancelledError:
                break
            except Exception:
                break
        
        if buffer and buffer.strip():
            log.write(f"[white]{buffer}[/]")
        
        log.write("[yellow]>>> Connection closed[/]")
        self.is_active = False
        self._update_status("[cyan]Connection closed. Ready for new operation.[/]")
    
    def action_stop_operation(self) -> None:
        self._stop_operation()
    
    def _stop_operation(self) -> None:
        if self.process:
            try:
                self.process.terminate()
            except:
                pass
        if self._reader_task:
            self._reader_task.cancel()
        self.is_active = False
        self._update_status("[yellow]Operation stopped.[/]")
    
    def action_clear_terminal(self) -> None:
        log = self.query_one("#terminal_output", RichLog)
        log.clear()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        
        if btn_id == "mode_connect":
            self.mode = "connect"
            self._update_mode_indicator()
        elif btn_id == "mode_listen":
            self.mode = "listen"
            self._update_mode_indicator()
        elif btn_id == "action_btn":
            self.action_start_operation()
        elif btn_id == "stop_btn":
            self.action_stop_operation()
    
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "send_input" and self.is_active:
            if self.process and self.process.stdin:
                data = event.input.value + "\n"
                self.process.stdin.write(data.encode('utf-8'))
                await self.process.stdin.drain()
                event.input.value = ""


def find_tool(name: str):
    """Find tool path - local import to avoid issues"""
    import shutil
    import os
    
    tool_key = name.lower()
    commands = {"netcat": "nc", "nmap": "nmap"}
    
    cmd = commands.get(tool_key, tool_key)
    path = shutil.which(cmd)
    
    if path:
        return path
    
    common_paths = {
        "nc": ["/usr/bin/nc", "/usr/local/bin/nc", "/bin/nc"],
        "nmap": ["/usr/bin/nmap", "/usr/local/bin/nmap"]
    }
    
    for p in common_paths.get(cmd, []):
        if os.path.exists(p):
            return p
    
    return cmd
