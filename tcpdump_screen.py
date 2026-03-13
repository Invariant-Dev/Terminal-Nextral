"""
tcpdump_screen.py - Nextral TCPDump Packet Capture Module

A user-friendly interface for tcpdump packet analyzer.
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical, Horizontal, Container
from textual.widgets import Header, Footer, Static, Button, Input, RichLog, Label, Switch
from textual.binding import Binding
from textual.reactive import reactive
import asyncio
import sys

sys.path.insert(0, '.')
from tools_locator import is_tool_installed, find_tool


class TcpdumpScreen(Screen):
    """TCPDump Packet Capture Interface"""
    
    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("r", "start_capture", "Start"),
        Binding("s", "stop_capture", "Stop"),
        Binding("c", "clear_results", "Clear"),
    ]
    
    CSS = """
    TcpdumpScreen {
        background: #0a0a12;
    }
    
    Header {
        background: #0a1a2e;
        color: #64b5f6;
    }
    
    #tcpdump_title {
        width: 100%;
        height: 3;
        content-align: center middle;
        background: #0d1f3a;
        color: #64b5f6;
        text-style: bold;
        border-bottom: solid #1565c0;
    }
    
    #main_container {
        height: 1fr;
        border: solid #1565c0;
        margin: 1;
    }
    
    #input_section {
        height: auto;
        border-bottom: solid #0d47a1;
        padding: 1 2;
        background: #050d18;
    }
    
    .input_label {
        color: #90caf9;
        margin-bottom: 0;
        text-style: bold;
    }
    
    .input_field {
        background: #0a1525;
        border: solid #1565c0;
        color: #bbdefb;
    }
    
    #interface_section {
        height: auto;
        border-bottom: solid #0d47a1;
        padding: 1 2;
        background: #050d18;
    }
    
    #results_section {
        height: 1fr;
        border: solid #1565c0;
        background: #020508;
    }
    
    #results_log {
        height: 1fr;
        background: #030810;
        border: solid #0d47a1;
        margin: 1;
        padding: 1;
    }
    
    #status_bar {
        dock: bottom;
        height: 2;
        background: #0a1a2e;
        color: #64b5f6;
        text-align: center;
    }
    
    #button_row {
        height: auto;
        padding: 1 2;
        background: #050d18;
        border-top: solid #0d47a1;
    }
    
    .action_btn {
        background: #1565c0;
        color: #bbdefb;
    }
    
    .action_btn:hover {
        background: #1976d2;
    }
    
    Footer {
        background: #0a1a2e;
        color: #64b5f6;
    }
    
    .running_indicator {
        color: #4caf50;
    }
    
    .stopped_indicator {
        color: #f44336;
    }
    """
    
    capturing = reactive(False)
    process = None
    
    def __init__(self, interface: str = ""):
        super().__init__()
        self.interface = interface
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        yield Static("◈ TCPDUMP PACKET CAPTURE ◈", id="tcpdump_title")
        
        with Container(id="main_container"):
            with Container(id="input_section"):
                yield Label("CAPTURE FILTER (BPF):", classes="input_label")
                yield Input(
                    id="filter_input",
                    placeholder="e.g., tcp, udp, port 80, host 192.168.1.1",
                    classes="input_field"
                )
                
                yield Label("CAPTURE OPTIONS:", classes="input_label")
                with Horizontal(id="option_toggles"):
                    yield Switch(id="opt_promisc", value=True, classes="option_toggle")
                    yield Label("Promiscuous", id="label_promisc")
                    yield Switch(id="opt_resolve", value=False, classes="option_toggle")
                    yield Label("Resolve DNS", id="label_resolve")
                    yield Switch(id="opt_hex", value=False, classes="option_toggle")
                    yield Label("Hex Dump", id="label_hex")
                
                yield Label("PACKET COUNT (0 = infinite):", classes="input_label")
                yield Input(
                    id="count_input",
                    placeholder="0",
                    classes="input_field"
                )
            
            with Container(id="results_section"):
                yield RichLog(id="results_log", markup=True, wrap=True)
            
            with Horizontal(id="button_row"):
                yield Button("▶ START CAPTURE", id="start_btn", variant="success")
                yield Button("■ STOP", id="stop_btn", variant="error")
                yield Button("↺ CLEAR", id="clear_btn", variant="default")
                yield Button("✕ CLOSE", id="close_btn", variant="default")
        
        yield Static(id="status_bar")
        yield Footer()
    
    def on_mount(self) -> None:
        self._update_status("[cyan]Ready to capture. Configure filter and press [bold]START[/]")
        
        log = self.query_one("#results_log", RichLog)
        log.write("[bold cyan]╔══════════════════════════════════════════════════════════════╗[/]")
        log.write("[bold cyan]║[/]               [bold white]TCPDUMP PACKET ANALYZER[/]                     [bold cyan]║[/]")
        log.write("[bold cyan]╚══════════════════════════════════════════════════════════════╝[/]")
        log.write("")
        log.write("[dim]TCPDump is a powerful packet analyzer that captures network traffic.[/]")
        log.write("[dim]Use BPF (Berkeley Packet Filter) syntax for capture filters.[/]")
        log.write("")
        
        installed, path = is_tool_installed("tcpdump")
        if not installed:
            log.write("[bold red]⚠ TCPDUMP NOT FOUND![/]")
            log.write("[dim]Please install tcpdump or configure path in Settings.[/]")
            log.write("[dim]On Linux, you may need root privileges to capture packets.[/]")
        else:
            log.write(f"[green]✓ TCPDump found: {path}[/]")
            log.write("")
            log.write("[yellow]Note: Capturing packets typically requires root privileges.[/]")
    
    def _update_status(self, text: str) -> None:
        try:
            self.query_one("#status_bar", Static).update(text)
        except:
            pass
    
    def action_close(self) -> None:
        self._stop_capture()
        self.app.pop_screen()
    
    def action_start_capture(self) -> None:
        if self.capturing:
            return
        
        installed, path = is_tool_installed("tcpdump")
        if not installed:
            log = self.query_one("#results_log", RichLog)
            log.write("[bold red]Error: TCPDump is not installed or not found![/]")
            return
        
        self.capturing = True
        self._update_status("[green]● CAPTURING - Press S to stop[/]")
        
        log = self.query_one("#results_log", RichLog)
        log.write("")
        log.write("[bold green]>>> Starting packet capture...[/]")
        log.write("")
        
        asyncio.create_task(self._run_capture())
    
    async def _run_capture(self) -> None:
        import shutil
        log = self.query_one("#results_log", RichLog)
        
        tool_path = find_tool("tcpdump")
        if not tool_path:
            tool_path = "tcpdump"
        
        args = ["-l"]
        
        if self.query_one("#opt_promisc", Switch).value:
            args.append("-p")
        
        if not self.query_one("#opt_resolve", Switch).value:
            args.append("-n")
        
        if self.query_one("#opt_hex", Switch).value:
            args.append("-X")
        
        count = self.query_one("#count_input", Input).value.strip()
        if count and count != "0":
            try:
                c = int(count)
                args.extend(["-c", str(c)])
            except:
                pass
        
        filter_expr = self.query_one("#filter_input", Input).value.strip()
        if filter_expr:
            args.extend(["-f", filter_expr])
        
        try:
            self.process = await asyncio.create_subprocess_exec(
                tool_path,
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            
            asyncio.create_task(self._read_output(log))
            
        except Exception as e:
            log.write(f"[red]Error: {e}[/]")
            self.capturing = False
    
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
        
        self.capturing = False
        self._update_status("[yellow]Capture stopped or completed.[/]")
    
    def action_stop_capture(self) -> None:
        self._stop_capture()
    
    def _stop_capture(self) -> None:
        if self.process:
            try:
                self.process.terminate()
            except:
                pass
        self.capturing = False
        self._update_status("[yellow]Capture stopped.[/]")
    
    def action_clear_results(self) -> None:
        log = self.query_one("#results_log", RichLog)
        log.clear()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        
        if btn_id == "start_btn":
            self.action_start_capture()
        elif btn_id == "stop_btn":
            self.action_stop_capture()
        elif btn_id == "clear_btn":
            self.action_clear_results()
        elif btn_id == "close_btn":
            self.action_close()
