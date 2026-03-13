"""
hydra_screen.py - Nextral Hydra Password Cracker Module

A user-friendly interface for Hydra online password cracking tool.
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical, Horizontal, Container
from textual.widgets import Header, Footer, Static, Button, Input, RichLog, Label, Select
from textual.binding import Binding
from textual.reactive import reactive
import asyncio
import sys

sys.path.insert(0, '.')
from tools_locator import is_tool_installed, run_tool


class HydraScreen(Screen):
    """Hydra Password Attack Tool Interface"""
    
    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("r", "start_attack", "Run Attack"),
        Binding("c", "clear_results", "Clear"),
    ]
    
    CSS = """
    HydraScreen {
        background: #0a0a12;
    }
    
    Header {
        background: #1a0a0a;
        color: #ef5350;
    }
    
    #hydra_title {
        width: 100%;
        height: 3;
        content-align: center middle;
        background: #2a0a0a;
        color: #ef5350;
        text-style: bold;
        border-bottom: solid #c62828;
    }
    
    #main_container {
        height: 1fr;
        border: solid #c62828;
        margin: 1;
    }
    
    #input_section {
        height: auto;
        border: solid #b71c1c;
        padding: 1;
        background: #0d0505;
    }
    
    .input_label {
        color: #ef9a9a;
        margin-bottom: 0;
    }
    
    .input_field {
        background: #1a0a0a;
        border: solid #c62828;
        color: #ffcdd2;
    }
    
    #service_select {
        margin-bottom: 1;
    }
    
    #results_section {
        height: 1fr;
        border: solid #c62828;
        background: #050505;
    }
    
    #results_log {
        height: 1fr;
        background: #0a0505;
        border: solid #b71c1c;
        margin: 1;
        padding: 1;
    }
    
    #status_bar {
        dock: bottom;
        height: 2;
        background: #1a0a0a;
        color: #ef5350;
        text-align: center;
    }
    
    #button_row {
        height: auto;
        padding: 1;
        background: #0d0505;
    }
    
    .action_btn {
        background: #c62828;
        color: #ffcdd2;
    }
    
    .action_btn:hover {
        background: #e53935;
    }
    
    Footer {
        background: #1a0a0a;
        color: #ef5350;
    }
    
    .warning {
        color: #ff9800;
    }
    """
    
    scanning = reactive(False)
    
    SERVICES = [
        ("SSH", "ssh"),
        ("Telnet", "telnet"),
        ("FTP", "ftp"),
        ("HTTP/HTTPS Form", "http-get"),
        ("HTTP/HTTPS Post", "http-post"),
        ("MySQL", "mysql"),
        ("PostgreSQL", "postgresql"),
        ("RDP", "rdp"),
        ("SMB", "smb"),
        ("VNC", "vnc"),
        ("LDAP", "ldap"),
        ("SMTP", "smtp"),
    ]
    
    def __init__(self, target: str = "", service: str = ""):
        super().__init__()
        self.target = target
        self.service = service
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        yield Static("◈ HYDRA PASSWORD ATTACK TOOL ◈", id="hydra_title")
        
        with Container(id="main_container"):
            with Container(id="input_section"):
                yield Label("⚠ LEGAL WARNING: Only use on systems you own or have explicit permission to test!", classes="warning")
                
                yield Label("TARGET SERVICE:", classes="input_label")
                yield Select(self.SERVICES, id="service_select", value="ssh")
                
                yield Label("TARGET HOST:", classes="input_label")
                yield Input(
                    id="target_input",
                    placeholder="e.g., 192.168.1.1, example.com",
                    classes="input_field"
                )
                
                yield Label("PORT:", classes="input_label")
                yield Input(
                    id="port_input",
                    placeholder="Leave empty for default port",
                    classes="input_field"
                )
                
                yield Label("USERNAME:", classes="input_label")
                yield Input(
                    id="username_input",
                    placeholder="e.g., admin, root",
                    classes="input_field"
                )
                
                yield Label("PASSWORD LIST:", classes="input_label")
                yield Input(
                    id="wordlist_input",
                    placeholder="/usr/share/wordlists/passwords.txt",
                    classes="input_field"
                )
                
                yield Label("ADDITIONAL OPTIONS:", classes="input_label")
                yield Input(
                    id="options_input",
                    placeholder="-t 4 -V (threads, verbose)",
                    classes="input_field"
                )
            
            with Container(id="results_section"):
                yield RichLog(id="results_log", markup=True, wrap=True)
            
            with Horizontal(id="button_row"):
                yield Button("▶ START ATTACK", id="attack_btn", variant="error")
                yield Button("↺ CLEAR", id="clear_btn", variant="default")
                yield Button("✕ CLOSE", id="close_btn", variant="default")
        
        yield Static(id="status_bar")
        yield Footer()
    
    def on_mount(self) -> None:
        self._update_status("[red]WARNING: Only use on systems you own or have permission to test!")
        
        if self.target:
            self.query_one("#target_input", Input).value = self.target
        if self.service:
            self.query_one("#service_select", Select).value = self.service
        
        log = self.query_one("#results_log", RichLog)
        log.write("[bold red]╔══════════════════════════════════════════════════════════════╗[/]")
        log.write("[bold red]║[/]              [bold white]HYDRA PASSWORD ATTACK TOOL[/]                    [bold red]║[/]")
        log.write("[bold red]╚══════════════════════════════════════════════════════════════╝[/]")
        log.write("")
        log.write("[bold red]⚠ LEGAL WARNING:[/]")
        log.write("[dim]This tool should only be used on systems you own or have[/]")
        log.write("[dim]explicit written permission to test. Unauthorized access is illegal.[/]")
        log.write("")
        
        installed, path = is_tool_installed("hydra")
        if not installed:
            log.write("[bold red]⚠ HYDRA NOT FOUND![/]")
            log.write("[dim]Please install hydra or configure path in Settings.[/]")
        else:
            log.write(f"[green]✓ Hydra found: {path}[/]")
            log.write("")
    
    def _update_status(self, text: str) -> None:
        try:
            self.query_one("#status_bar", Static).update(text)
        except:
            pass
    
    def action_close(self) -> None:
        self.app.pop_screen()
    
    def action_start_attack(self) -> None:
        target = self.query_one("#target_input", Input).value.strip()
        port = self.query_one("#port_input", Input).value.strip()
        username = self.query_one("#username_input", Input).value.strip()
        wordlist = self.query_one("#wordlist_input", Input).value.strip()
        
        if not target:
            self._update_status("[red]Error: Please enter a target host![/]")
            return
        if not username:
            self._update_status("[red]Error: Please enter a username![/]")
            return
        if not wordlist:
            self._update_status("[red]Error: Please enter a wordlist path![/]")
            return
        
        service = self.query_one("#service_select", Select).value
        if not service:
            self._update_status("[red]Error: Please select a service![/]")
            return
        
        if self.scanning:
            return
        
        installed, path = is_tool_installed("hydra")
        if not installed:
            log = self.query_one("#results_log", RichLog)
            log.write("[bold red]Error: Hydra is not installed or not found![/]")
            return
        
        self.scanning = True
        self._update_status(f"[yellow]◐ Running Hydra attack on {target}...[/]")
        
        log = self.query_one("#results_log", RichLog)
        log.write("")
        log.write(f"[bold red]>>> Starting Hydra attack[/]")
        log.write(f"[dim]Target: {target} | Service: {service} | User: {username}[/]")
        log.write("")
        
        asyncio.create_task(self._run_attack(target, service, port, username, wordlist))
    
    async def _run_attack(self, target: str, service: str, port: str, username: str, wordlist: str) -> None:
        log = self.query_one("#results_log", RichLog)
        
        if service in ["http-get", "http-post"]:
            args = ["-l", username, "-P", wordlist, f"{service}://{target}"]
        else:
            args = ["-l", username, "-P", wordlist, "-o", target]
            if port:
                args.extend(["-s", port])
        
        options = self.query_one("#options_input", Input).value.strip()
        if options:
            args.extend(options.split())
        
        returncode, stdout, stderr = await run_tool("hydra", args, timeout=3600)
        
        if returncode == 0:
            log.write("[green]✓ Attack completed![/]")
            log.write("")
            log.write(stdout)
        elif returncode == -1:
            log.write(f"[red]✗ {stderr}[/]")
        else:
            if stdout:
                log.write(stdout)
            if stderr:
                log.write(f"[dim]{stderr}[/]")
        
        self.scanning = False
        self._update_status("[green]✓ Attack complete.[/]")
    
    def action_clear_results(self) -> None:
        log = self.query_one("#results_log", RichLog)
        log.clear()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        
        if btn_id == "attack_btn":
            self.action_start_attack()
        elif btn_id == "clear_btn":
            self.action_clear_results()
        elif btn_id == "close_btn":
            self.action_close()
