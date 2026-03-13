"""
stun_analyzer_screen.py - WhatsApp STUN Analyzer TUI Module

A Textual-based TUI for the STUN Binding Request analyzer.
Part of the Nextral network analysis toolkit.
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical, Horizontal, Container
from textual.widgets import Header, Footer, Static, Button, Input, RichLog, Label, Select
from textual.binding import Binding
from textual.reactive import reactive
import asyncio
import re
import subprocess
import sys
import threading
from datetime import datetime

sys.path.insert(0, '.')
from tools_locator import is_tool_installed, find_tool


class StunAnalyzerScreen(Screen):
    """WhatsApp IP Tracer Interface"""
    
    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("r", "start_capture", "Start"),
        Binding("s", "stop_capture", "Stop"),
        Binding("c", "clear_results", "Clear"),
        Binding("l", "list_interfaces", "List Ifaces"),
    ]
    
    CSS = """
    StunAnalyzerScreen {
        background: #0a0a12;
    }
    
    Header {
        background: #0a1a2e;
        color: #64b5f6;
    }
    
    #stun_title {
        width: 100%;
        height: 3;
        content-align: center middle;
        background: #0d1f3a;
        color: #4db6ac;
        text-style: bold;
        border-bottom: solid #00796b;
    }
    
    #main_container {
        height: 1fr;
        border: solid #00796b;
        margin: 1;
    }
    
    #input_section {
        height: auto;
        border-bottom: solid #00695c;
        padding: 1 2;
        background: #050d18;
    }
    
    .input_label {
        color: #80cbc4;
        margin-bottom: 0;
        text-style: bold;
    }
    
    .input_field, Select {
        background: #0a1525;
        border: solid #00796b;
        color: #b2dfdb;
        height: 1;
    }
    
    #results_section {
        height: 1fr;
        border: solid #00796b;
        background: #020508;
    }
    
    #results_log {
        height: 1fr;
        background: #030810;
        border: solid #00695c;
        margin: 1;
        padding: 1;
    }
    
    #status_bar {
        dock: bottom;
        height: 2;
        background: #0a1a2e;
        color: #4db6ac;
        text-align: center;
    }
    
    #button_row {
        height: auto;
        padding: 1 2;
        background: #050d18;
        border-top: solid #00695c;
    }
    
    .action_btn {
        background: #00796b;
        color: #e0f2f1;
    }
    
    .action_btn:hover {
        background: #00897b;
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
    
    .info_text {
        color: #80cbc4;
    }
    """
    
    capturing = reactive(False)
    process = None
    seen_ips = set()
    packet_count = 0
    _stop_event = threading.Event()
    
    FILTER = 'stun && frame.len == 86 && stun.type.method == 0x0001'
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        yield Static("◈ WHATSAPP IP TRACER ◈", id="stun_title")
        
        with Container(id="main_container"):
            with Container(id="input_section"):
                yield Label("NETWORK INTERFACE:", classes="input_label")
                yield Select(
                    [],
                    id="iface_select",
                )
                
                yield Label("OR PCAP FILE (optional):", classes="input_label")
                yield Input(
                    id="pcap_input",
                    placeholder="path/to/capture.pcap",
                    classes="input_field"
                )
                
                yield Label("OUTPUT FORMAT:", classes="input_label")
                with Horizontal(id="format_options"):
                    yield Select(
                        [(("Terminal", "term")), (("JSON", "json"))],
                        id="format_select",
                        value="term"
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
        self._update_status("[cyan]Ready. Select interface and press [bold]START[/]")
        
        log = self.query_one("#results_log", RichLog)
        log.write("[bold cyan]╔══════════════════════════════════════════════════════════════╗")
        log.write("[bold cyan]║                   WHATSAPP IP TRACER                      ║")
        log.write("[bold cyan]╚══════════════════════════════════════════════════════════════╝")
        log.write("")
        log.write("[bold yellow]▸ INSTRUCTIONS:[/bold yellow]")
        log.write("[dim]1. Make a WhatsApp voice/video call to the target[/dim]")
        log.write("[dim]2. Click START to begin packet capture[/dim]")
        log.write("[dim]3. Watch for WhatsApp server IPs in the output[/dim]")
        log.write("")
        
        self._populate_interfaces()
    
    def _populate_interfaces(self) -> None:
        """Populate interface dropdown."""
        try:
            log = self.query_one("#results_log", RichLog)
        except:
            log = None
        
        interfaces = self._list_interfaces()
        select = self.query_one("#iface_select", Select)
        
        if not interfaces:
            # Fallback to common Windows interface names
            interfaces = ["Ethernet", "Wi-Fi", "Local Area Connection"]
        
        if interfaces:
            options = [(iface, iface) for iface in interfaces]
            select.set_options(options)
            select.value = interfaces[0]
            if log:
                log.write(f"[green]✓ Interface selected: {interfaces[0]}[/green]")
        
        if log:
            self._check_tshark()
    
    def _list_interfaces(self) -> list:
        """List available network interfaces."""
        interfaces = []
        
        # Try tshark -D first
        try:
            result = subprocess.run(
                ['tshark', '-D'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    # Handle format: "1. eth0" or "1. \Device\NPF_{...}"
                    line = line.strip()
                    if line and line[0].isdigit():
                        parts = line.split('. ', 1)
                        if len(parts) > 1:
                            iface = parts[1].strip()
                            if iface:
                                interfaces.append(iface)
                if interfaces:
                    return interfaces
        except:
            pass
        
        # Try dumpcap -D
        try:
            result = subprocess.run(
                ['dumpcap', '-D'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    line = line.strip()
                    if line and line[0].isdigit():
                        parts = line.split('. ', 1)
                        if len(parts) > 1:
                            iface = parts[1].strip()
                            if iface:
                                interfaces.append(iface)
                if interfaces:
                    return interfaces
        except:
            pass
        
        # Fallback: common Windows interface names
        import platform
        if platform.system() == "Windows":
            common = ["Ethernet", "Wi-Fi", "Local Area Connection", "eth0", "en0"]
            for iface in common:
                interfaces.append(iface)
        
        return interfaces[:5]  # Return up to 5
    
    def _check_tshark(self) -> None:
        """Check if tshark is available."""
        try:
            log = self.query_one("#results_log", RichLog)
        except:
            return
        
        try:
            result = subprocess.run(
                ['tshark', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                log.write("[green]✓ tshark found and ready[/]")
                log.write("[dim]Note: Capturing packets may require elevated privileges.[/]")
            else:
                log.write("[bold red]⚠ tshark returned error[/]")
        except FileNotFoundError:
            log.write("[bold red]⚠ TSHARK NOT FOUND![/]")
            log.write("[dim]Please install Wireshark (includes tshark).[/]")
        except Exception as e:
            log.write(f"[red]Error checking tshark: {e}[/]")
    
    def _update_status(self, text: str) -> None:
        try:
            self.query_one("#status_bar", Static).update(text)
        except:
            pass
    
    def action_close(self) -> None:
        self._stop_capture()
        self.app.pop_screen()
    
    def action_list_interfaces(self) -> None:
        """List available network interfaces."""
        log = self.query_one("#results_log", RichLog)
        log.write("")
        log.write("[bold cyan]Available Network Interfaces:[/bold cyan]")
        
        try:
            result = subprocess.run(
                ['tshark', '-D'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    log.write(f"[white]{line}[/]")
            else:
                log.write("[red]Failed to list interfaces[/]")
        except Exception as e:
            log.write(f"[red]Error: {e}[/]")
    
    def action_start_capture(self) -> None:
        if self.capturing:
            return
        
        iface_select = self.query_one("#iface_select", Select)
        iface_input = str(iface_select.value) if iface_select.value else ""
        pcap_input = self.query_one("#pcap_input", Input).value.strip()
        
        if not iface_input or iface_input == "none":
            log = self.query_one("#results_log", RichLog)
            log.write("[bold red]Error: Select a network interface[/]")
            return
        
        self.capturing = True
        self.seen_ips = set()
        self.packet_count = 0
        self._stop_event.clear()
        
        self._update_status("[green]● CAPTURING - Press S to stop[/]")
        
        log = self.query_one("#results_log", RichLog)
        log.write("")
        log.write("[bold green]>>> Starting WhatsApp IP Tracer capture...[/]")
        log.write("")
        log.write("[bold yellow]▸ INSTRUCTION: Make a WhatsApp call to the target now![/bold yellow]")
        log.write("[dim]  STUN packets will reveal WhatsApp server IPs[/dim]")
        log.write("")
        
        asyncio.create_task(self._run_capture(iface_input, pcap_input))
    
    async def _run_capture(self, iface: str, pcap: str) -> None:
        import shutil
        log = self.query_one("#results_log", RichLog)
        
        tool_path = find_tool("tshark")
        if not tool_path:
            tool_path = "tshark"
        
        cmd = ['tshark']
        
        if pcap:
            cmd.extend(['-r', pcap])
        elif iface:
            cmd.extend(['-i', iface])
        
        cmd.extend([
            '-Y', self.FILTER,
            '-T', 'fields',
            '-e', 'frame.time_epoch',
            '-e', 'ip.src',
            '-e', 'ip.dst',
            '-e', 'frame.interface_name',
            '-E', 'separator=|',
        ])
        
        format_select = self.query_one("#format_select", Select)
        format_type = str(format_select.value) if format_select.value else "term"
        
        try:
            self.capture_process = await asyncio.create_subprocess_exec(
                tool_path,
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            
            asyncio.create_task(self._read_output(log, format_type))
            
        except FileNotFoundError:
            log.write("[bold red]Error: tshark not found![/]")
            log.write("[dim]Please install Wireshark to use this tool.[/]")
            self.capturing = False
            self._update_status("[red]Error: tshark not found[/]")
        except PermissionError:
            log.write("[bold red]Error: Permission denied[/]")
            log.write("[dim]Try running as Administrator or with elevated privileges.[/]")
            self.capturing = False
            self._update_status("[red]Permission denied[/]")
        except Exception as e:
            log.write(f"[red]Error: {e}[/]")
            self.capturing = False
    
    async def _read_output(self, log: RichLog, format_type: str) -> None:
        buffer = ""
        while True:
            try:
                if not self.capture_process or not self.capture_process.stdout:
                    break
                
                chunk = await self.capture_process.stdout.read(1024)
                if not chunk:
                    break
                
                text = chunk.decode('utf-8', errors='replace')
                buffer += text
                
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line.strip():
                        self._process_line(line.strip(), log, format_type)
                
            except asyncio.CancelledError:
                break
            except Exception:
                break
        
        if buffer and buffer.strip():
            self._process_line(buffer.strip(), log, format_type)
        
        self.capturing = False
        self._update_status("[yellow]Capture stopped or completed.[/]")
    
    def _process_line(self, line: str, log: RichLog, format_type: str) -> None:
        """Process a single tshark output line."""
        parts = line.split('|')
        if len(parts) < 4:
            return
        
        try:
            timestamp_epoch = float(parts[0])
            timestamp = datetime.fromtimestamp(timestamp_epoch).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        except:
            timestamp = parts[0]
        
        src_ip = parts[1]
        dst_ip = parts[2]
        interface = parts[3]
        
        self.packet_count += 1
        self.seen_ips.add(src_ip)
        
        if format_type == "term":
            log.write("")
            log.write(f"[bold yellow][!] POTENTIAL IP ADDRESS OBTAINED:[/bold yellow] [bold yellow]{src_ip}[/bold yellow] [dim]AT[/dim] [cyan]{timestamp}[/cyan]")
            log.write(f"[dim]    → External STUN server: {dst_ip}[/dim]")
            log.write(f"[dim]    → Interface: {interface}[/dim]")
            log.write(f"[dim]    Packets: {self.packet_count} | Unique Peers: {len(self.seen_ips)}[/]")
        else:
            import json
            output = {
                "timestamp": timestamp,
                "source_ip": src_ip,
                "destination_ip": dst_ip,
                "interface": interface,
                "stats": {
                    "total_packets": self.packet_count,
                    "unique_peers": len(self.seen_ips)
                }
            }
            log.write(json.dumps(output))
    
    def action_stop_capture(self) -> None:
        self._stop_capture()
    
    def _stop_capture(self) -> None:
        self._stop_event.set()
        if hasattr(self, 'capture_process') and self.capture_process:
            try:
                self.capture_process.terminate()
            except:
                pass
        self.capturing = False
        self._update_status("[yellow]Capture stopped.[/]")
    
    def action_clear_results(self) -> None:
        log = self.query_one("#results_log", RichLog)
        log.clear()
        self.seen_ips = set()
        self.packet_count = 0
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        
        if btn_id == "start_btn":
            self.action_start_capture()
        elif btn_id == "stop_btn":
            self.action_stop_capture()
        elif btn_id == "clear_btn":
            self.action_clear_results()
        elif btn_id == "list_btn":
            self.action_list_interfaces()
        elif btn_id == "close_btn":
            self.action_close()
