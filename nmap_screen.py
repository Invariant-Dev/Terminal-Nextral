"""
nmap_screen.py - Nextral Nmap Scanner Module

A clean, professional interface for Nmap network scanning.
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical, Horizontal, Container, ScrollableContainer
from textual.widgets import Header, Footer, Static, Button, Input, RichLog, Switch, Label
from textual.binding import Binding
from textual.reactive import reactive
import asyncio
import sys

sys.path.insert(0, '.')
from tools_locator import is_tool_installed, run_tool, find_tool


class NmapScreen(Screen):
    """Nmap Network Scanner Interface - Professional Edition"""
    
    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("r", "start_scan", "Run Scan"),
        Binding("c", "clear_results", "Clear"),
    ]
    
    CSS = """
NmapScreen {
    background: #0c0c0c;
}

#header_bar {
    dock: top;
    height: 3;
    background: #1a0a1a;
    border-bottom: solid #4a1a4a;
}

#header_title {
    color: #cc44cc;
    text-style: bold;
    padding: 0 2;
}

#header_info {
    color: #884488;
    padding: 0 2;
}

#main_area {
    height: 1fr;
}

#input_panel {
    width: 40%;
    border-right: solid #331133;
    padding: 1;
}

#output_panel {
    width: 60%;
    padding: 1;
}

.input-label {
    color: #aa66aa;
    text-style: bold;
    margin-bottom: 0;
}

.input-field {
    background: #0a000a;
    border: solid #441144;
    color: #cc88cc;
    margin-bottom: 1;
}

.input-field:focus {
    border: solid #cc44cc;
    background: #100010;
}

.preset-btn {
    width: 100%;
    height: 3;
    margin-bottom: 1;
    background: #1a0a1a;
    border: solid #331133;
    color: #aa66aa;
}

.preset-btn:hover {
    background: #2a1a2a;
    border: solid #cc44cc;
}

.preset-btn.active {
    background: #331133;
    border: solid #cc44cc;
    color: #cc88cc;
}

.option-switch {
    margin: 0 2;
}

#results_log {
    height: 1fr;
    background: #050005;
    border: solid #331133;
    padding: 1;
}

#status_bar {
    dock: bottom;
    height: 2;
    background: #1a0a1a;
    color: #884488;
    padding: 0 2;
}

.action-btn {
    width: 100%;
    height: 3;
    margin: 0 1;
    background: #2a1a2a;
    border: solid #441144;
    color: #cc88cc;
}

.action-btn:hover {
    background: #3a2a3a;
    border: solid #cc44cc;
}

Button {
    background: #1a0a1a;
    border: solid #331133;
    color: #aa66aa;
}

Button:hover {
    background: #2a1a2a;
    border: solid #cc44cc;
}

Input {
    background: #0a000a;
    border: solid #331133;
    color: #cc88cc;
}

Input:focus {
    border: solid #cc44cc;
    color: #eeaaee;
}

Header {
    background: #1a0a1a;
    color: #cc44cc;
}

Footer {
    background: #1a0a1a;
    color: #884488;
}
"""
    
    scanning = reactive(False)
    
    def __init__(self, target: str = ""):
        super().__init__()
        self.target = target
        self.scan_type = "-sV"
        self.preset = "quick"
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        with Container(id="header_bar"):
            yield Static("[bold #cc44cc]NMAP SCANNER[/] | Network Discovery & Port Scanning", id="header_title")
            yield Static("[dim]Keys: [bold]R[/]=Run  [bold]C[/]=Clear  [bold]Esc[/]=Close", id="header_info")
        
        with Horizontal(id="main_area"):
            with Vertical(id="input_panel"):
                yield Label("TARGET HOST / NETWORK:", classes="input-label")
                yield Input(
                    id="target_input",
                    placeholder="e.g., 192.168.1.1, 10.0.0.0/24",
                    classes="input-field"
                )
                
                yield Label("SCAN PRESETS:", classes="input-label")
                yield Button("Quick Scan (TCP SYN)", id="preset_quick", classes="preset-btn active")
                yield Button("Full Scan (+UDP)", id="preset_full", classes="preset-btn")
                yield Button("Stealth Scan", id="preset_stealth", classes="preset-btn")
                yield Button("Aggressive Scan", id="preset_aggressive", classes="preset-btn")
                
                yield Label("OPTIONS:", classes="input-label")
                with Horizontal():
                    yield Switch(id="opt_service", value=True)
                    yield Label("Service Ver", id="label_service")
                with Horizontal():
                    yield Switch(id="opt_os", value=False)
                    yield Label("OS Detect", id="label_os")
                
                yield Label("ACTIONS:", classes="input-label")
                with Horizontal():
                    yield Button("RUN SCAN", id="scan_btn", variant="success")
                    yield Button("CLEAR", id="clear_btn")
            
            with Vertical(id="output_panel"):
                yield RichLog(id="results_log", markup=True, wrap=True, max_lines=2000)
        
        yield Static(id="status_bar")
        yield Footer()
    
    def on_mount(self) -> None:
        self._update_status("Ready. Enter target and click RUN or press R")
        
        if self.target:
            self.query_one("#target_input", Input).value = self.target
        
        log = self.query_one("#results_log", RichLog)
        log.write("[bold #cc44cc]== NMAP NETWORK SCANNER ==[/]")
        log.write("")
        log.write("[dim]Enter target IP/hostname and select scan preset.[/]")
        log.write("[dim]Press [bold]R[/] or click [bold]RUN SCAN[/] to begin.[/]")
        log.write("")
        
        installed, path = is_tool_installed("nmap")
        if not installed:
            log.write("[bold red]WARNING: Nmap not found![/]")
            log.write("[dim]Please install nmap or configure path in Settings.[/]")
        else:
            log.write(f"[green]Nmap found:[/] {path}")
    
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
            self._update_status("Error: Please enter a target!")
            return
        
        if self.scanning:
            return
        
        installed, path = is_tool_installed("nmap")
        if not installed:
            log = self.query_one("#results_log", RichLog)
            log.write("[bold red]Error: Nmap not installed![/]")
            return
        
        self.scanning = True
        self._update_status(f"Scanning {target}...")
        
        log = self.query_one("#results_log", RichLog)
        log.write("")
        log.write(f"[bold #cc44cc]>> Scanning:[/] {target}")
        log.write(f"[dim]Preset: {self.preset} | Flags: {self.scan_type}[/]")
        log.write("")
        
        asyncio.create_task(self._run_scan(target))
    
    async def _run_scan(self, target: str) -> None:
        log = self.query_one("#results_log", RichLog)
        
        args = [target]
        args.extend(self.scan_type.split())
        
        if self.query_one("#opt_os", Switch).value:
            args.append("-O")
        
        args.append("-v")
        
        returncode, stdout, stderr = await run_tool("nmap", args, timeout=300)
        
        if returncode == 0:
            log.write("[green]Scan completed successfully![/]")
            log.write("")
            log.write(stdout)
        elif returncode == -1:
            log.write(f"[red]Error: {stderr}[/]")
        else:
            log.write(f"[yellow]Scan finished with code {returncode}[/]")
            log.write("")
            if stdout:
                log.write(stdout)
            if stderr:
                log.write(f"[dim]{stderr}[/]")
        
        self.scanning = False
        self._update_status("Scan complete. Ready for next scan.")
    
    def action_clear_results(self) -> None:
        log = self.query_one("#results_log", RichLog)
        log.clear()
        log.write("[dim]Results cleared.[/]")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        
        if btn_id == "scan_btn":
            self.action_start_scan()
        elif btn_id == "clear_btn":
            self.action_clear_results()
        elif btn_id == "preset_quick":
            self.scan_type = "-sV"
            self.preset = "Quick"
            self._update_preset_buttons("preset_quick")
        elif btn_id == "preset_full":
            self.scan_type = "-sS -sU -T4 -A -O"
            self.preset = "Full"
            self._update_preset_buttons("preset_full")
        elif btn_id == "preset_stealth":
            self.scan_type = "-sS -T2 -f"
            self.preset = "Stealth"
            self._update_preset_buttons("preset_stealth")
        elif btn_id == "preset_aggressive":
            self.scan_type = "-sS -sV -sC -O -T4"
            self.preset = "Aggressive"
            self._update_preset_buttons("preset_aggressive")
    
    def _update_preset_buttons(self, active_id: str):
        for btn_id in ["preset_quick", "preset_full", "preset_stealth", "preset_aggressive"]:
            btn = self.query_one(f"#{btn_id}", Button)
            if btn_id == active_id:
                btn.add_class("active")
            else:
                btn.remove_class("active")
        self._update_status(f"Preset: {self.preset} - Press R to run")
