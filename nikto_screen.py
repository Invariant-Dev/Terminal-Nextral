"""
nikto_screen.py - Nextral Nikto Web Scanner Module

A user-friendly interface for Nikto web server scanner.
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical, Horizontal, Container
from textual.widgets import Header, Footer, Static, Button, Input, RichLog, Label
from textual.binding import Binding
from textual.reactive import reactive
import asyncio
import sys

sys.path.insert(0, '.')
from tools_locator import is_tool_installed, run_tool, find_tool


class NiktoScreen(Screen):
    """Nikto Web Vulnerability Scanner Interface"""
    
    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("r", "start_scan", "Run Scan"),
        Binding("c", "clear_results", "Clear"),
    ]
    
    CSS = """
    NiktoScreen {
        background: #0c0c0c;
    }
    
    #header_bar {
        dock: top;
        height: 3;
        background: #1a1a0a;
        border-bottom: solid #4a4a1a;
    }

    #header_title {
        color: #cccc44;
        text-style: bold;
        padding: 0 2;
    }

    #header_info {
        color: #888833;
        padding: 0 2;
    }

    #main_container {
        height: 1fr;
    }

    #input_section {
        width: 35%;
        border-right: solid #333311;
        padding: 1;
    }

    #output_section {
        width: 65%;
        padding: 1;
    }
    
    .input_label {
        color: #aaaa55;
        margin-bottom: 0;
        text-style: bold;
    }
    
    .input_field {
        background: #0a0a00;
        border: solid #444422;
        color: #cccc88;
    }
    
    .input_field:focus {
        border: solid #cccc44;
        background: #111100;
    }
    
    #scan_options {
        height: auto;
        border-bottom: solid #f57f17;
        padding: 1 2;
        background: #0d0d02;
    }
    
    #results_section {
        height: 1fr;
        background: #050503;
    }
    
    #results_log {
        height: 1fr;
        background: #080805;
        border: solid #f57f17;
        margin: 1;
        padding: 1;
    }
    
    #status_bar {
        dock: bottom;
        height: 1;
        background: #1a1a05;
        color: #ffd54f;
        text-align: center;
    }
    
    #button_row {
        height: auto;
        padding: 1 2;
        background: #0d0d02;
        border-top: solid #f57f17;
    }
    
    .scan_btn {
        background: #f9a825;
        color: #0a0a02;
        text-style: bold;
    }
    
    .scan_btn:hover {
        background: #ffca28;
    }
    
    Button {
        margin-right: 1;
    }
    
    Footer {
        background: #1a1a05;
        color: #ffd54f;
    }
    """
    
    scanning = reactive(False)
    
    def __init__(self, target: str = ""):
        super().__init__()
        self.target = target
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        yield Static("◈ NIKTO WEB VULNERABILITY SCANNER ◈", id="nikto_title")
        
        with Container(id="main_container"):
            with Container(id="input_section"):
                yield Label("🎯 TARGET URL:", classes="input_label")
                yield Input(
                    id="target_input",
                    placeholder="e.g., http://192.168.1.1, https://example.com",
                    classes="input_field"
                )
                
                yield Label("SCAN PROFILE:", classes="input_label")
                with Horizontal(id="preset_buttons"):
                    yield Button("Quick Scan", id="preset_quick", variant="primary")
                    yield Button("Full Scan", id="preset_full", variant="default")
                    yield Button("SSL Only", id="preset_ssl", variant="default")
                
                yield Label("ADDITIONAL OPTIONS:", classes="input_label")
                yield Input(
                    id="options_input",
                    placeholder="-Plugins cgi,sql -timeout 30",
                    classes="input_field"
                )
            
            with Container(id="results_section"):
                yield RichLog(id="results_log", markup=True, wrap=True)
            
            with Horizontal(id="button_row"):
                yield Button("▶ START SCAN", id="scan_btn", variant="success")
                yield Button("↺ CLEAR", id="clear_btn", variant="default")
                yield Button("✕ CLOSE", id="close_btn", variant="error")
        
        yield Static(id="status_bar")
        yield Footer()
    
    def on_mount(self) -> None:
        self._update_status("[cyan]Ready to scan. Enter target URL and press [bold]RUN[/]")
        
        if self.target:
            self.query_one("#target_input", Input).value = self.target
        
        log = self.query_one("#results_log", RichLog)
        log.write("[bold cyan]╔══════════════════════════════════════════════════════════════╗[/]")
        log.write("[bold cyan]║[/]           [bold white]NIKTO WEB VULNERABILITY SCANNER[/]                [bold cyan]║[/]")
        log.write("[bold cyan]╚══════════════════════════════════════════════════════════════╝[/]")
        log.write("")
        log.write("[dim]Nikto is a web server scanner that detects dangerous files/CGIs,[/]")
        log.write("[dim]outdated software, and other security issues.[/]")
        log.write("")
        
        installed, path = is_tool_installed("nikto")
        if not installed:
            log.write("[bold red]⚠ NIKTO NOT FOUND![/]")
            log.write("[dim]Please install nikto or configure path in Settings.[/]")
        else:
            log.write(f"[green]✓ Nikto found: {path}[/]")
    
    def _update_status(self, text: str) -> None:
        try:
            self.query_one("#status_bar", Static).update(text)
        except:
            pass
    
    def action_close(self) -> None:
        self.app.pop_screen()
    
    def action_start_scan(self) -> None:
        target = self.query_one("#target_input", Input).value.strip()
        
        if not target:
            self._update_status("[red]Error: Please enter a target URL![/]")
            return
        
        if self.scanning:
            return
        
        installed, path = is_tool_installed("nikto")
        if not installed:
            log = self.query_one("#results_log", RichLog)
            log.write("[bold red]Error: Nikto is not installed or not found![/]")
            log.write("[dim]Please install nikto or configure path in Settings.[/]")
            return
        
        self.scanning = True
        self._update_status(f"[yellow]◐ Scanning {target}...[/]")
        
        log = self.query_one("#results_log", RichLog)
        log.write("")
        log.write(f"[bold yellow]>>> Starting Nikto scan on: {target}[/]")
        log.write("")
        
        asyncio.create_task(self._run_scan(target))
    
    async def _run_scan(self, target: str) -> None:
        log = self.query_one("#results_log", RichLog)
        
        args = ["-h", target]
        
        options = self.query_one("#options_input", Input).value.strip()
        if options:
            args.extend(options.split())
        
        args.extend(["-Format", "txt", "-v"])
        
        returncode, stdout, stderr = await run_tool("nikto", args, timeout=600)
        
        if returncode == 0:
            log.write("[green]✓ Scan completed![/]")
            log.write("")
            log.write(stdout)
        elif returncode == -1:
            log.write(f"[red]✗ {stderr}[/]")
        else:
            log.write(f"[yellow]⚠ Scan finished with code {returncode}[/]")
            if stdout:
                log.write(stdout)
            if stderr:
                log.write(f"[dim]{stderr}[/]")
        
        self.scanning = False
        self._update_status("[green]✓ Scan complete. Ready for next scan.[/]")
    
    def action_clear_results(self) -> None:
        log = self.query_one("#results_log", RichLog)
        log.clear()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        
        if btn_id == "scan_btn" or btn_id == "preset_quick":
            self.action_start_scan()
        elif btn_id == "preset_full":
            self.query_one("#options_input", Input).value = "-Plugins all"
            self._update_status("[cyan]Preset: Full Scan - Press RUN to start[/]")
        elif btn_id == "preset_ssl":
            self.query_one("#options_input", Input).value = "-ssl -ports 443"
            self._update_status("[cyan]Preset: SSL Only - Press RUN to start[/]")
        elif btn_id == "clear_btn":
            self.action_clear_results()
        elif btn_id == "close_btn":
            self.action_close()
