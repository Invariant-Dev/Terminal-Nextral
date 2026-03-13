"""
WhatsApp IP Tracer - Fixed Version
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container
from textual.widgets import Header, Footer, Static, Button, RichLog
from textual.binding import Binding
from textual.reactive import reactive
import subprocess
import threading
import socket
import os


class WhatsAppIPTracerScreen(Screen):
    """WhatsApp IP Tracer"""
    
    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("r", "start_capture", "Start"),
        Binding("s", "stop_capture", "Stop"),
    ]
    
    CSS = """
    WhatsAppIPTracerScreen { background: #0d1117; }
    Header { background: #161b22; color: #58a6ff; }
    #title { width: 100%; height: 3; content-align: center; background: #161b22; color: #f0883e; text-style: bold; }
    #results { height: 1fr; background: #0d1117; }
    #log { height: 100%; background: #0d1117; border: none; }
    #buttons { dock: bottom; height: 3; background: #161b22; }
    #status { dock: bottom; height: 2; background: #161b22; color: #8b949e; }
    Button { margin: 1; }
    """
    
    capturing = reactive(False)
    
    def compose(self):
        yield Header()
        yield Static("◈ WHATSAPP IP TRACER ◈", id="title")
        with Container(id="results"):
            yield RichLog(id="log", markup=True)
        with Container(id="buttons"):
            yield Button("▶ START", id="start", variant="success")
            yield Button("■ STOP", id="stop", variant="error")
            yield Button("✕ CLOSE", id="close")
        yield Static("Ready", id="status")
        yield Footer()
    
    def on_mount(self):
        self.running = False
        self.proc = None
        self.seen_ips = set()
        self.logger = self.query_one("#log", RichLog)
        self.status = self.query_one("#status", Static)
        
        self.logger.write("[bold #f0883e]================================================[/]")
        self.logger.write("[bold #f0883e]         WHATSAPP IP TRACER               [/]")
        self.logger.write("[bold #f0883e]================================================[/]")
        self.logger.write("")
        self.logger.write("[yellow]>>> INSTRUCTIONS:[/yellow]")
        self.logger.write("1. Make a WhatsApp voice/video call")
        self.logger.write("2. Click START and keep the call active")
        self.logger.write("3. Watch for IPs below...")
        self.logger.write("")
        self.logger.write("[dim]Note: Run as Administrator for packet capture[/]")
    
    def on_button_pressed(self, event):
        if event.button.id == "start":
            self.start_capture()
        elif event.button.id == "stop":
            self.stop_capture()
        elif event.button.id == "close":
            self.stop_capture()
            self.app.pop_screen()
    
    def get_interface(self):
        """Get the best network interface for capture."""
        import subprocess
        
        # Find tshark
        tshark_path = r"C:\Program Files\Wireshark\tshark.exe"
        if not os.path.exists(tshark_path):
            tshark_path = "tshark"
        
        try:
            result = subprocess.run(
                [tshark_path, '-D'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                lines = result.stdout.splitlines()
                for line in lines:
                    line = line.strip()
                    # Look for Wi-Fi interface
                    if 'Wi-Fi' in line or 'Wireless' in line:
                        # Extract interface name like "\Device\NPF_{...} (Wi-Fi)"
                        if '.' in line:
                            return line.split('. ', 1)[1].split(' ')[0]
                
                # If no Wi-Fi, return first ethernet interface
                for line in lines:
                    line = line.strip()
                    if 'Local Area Connection' in line or 'Ethernet' in line:
                        if '.' in line:
                            return line.split('. ', 1)[1].split(' ')[0]
                
                # Return first available interface
                if lines:
                    first = lines[0].strip()
                    if '.' in first:
                        return first.split('. ', 1)[1].split(' ')[0]
        except:
            pass
        
        # Fallback to common names
        return r"\Device\NPF_{945CEE4B-7D59-4565-8E5E-1AF3B0418334}"  # Wi-Fi on this machine
    
    def start_capture(self):
        if self.capturing:
            return
        
        self.capturing = True
        self.running = True
        self.seen_ips = set()
        
        self.status.update("[green]● CAPTURING...")
        self.logger.write("")
        self.logger.write("[bold green]▶ CAPTURE STARTED[/]")
        self.logger.write("[yellow]Make WhatsApp call NOW![/]")
        self.logger.write("-" * 50)
        
        # Start capture thread
        self.thread = threading.Thread(target=self._capture, daemon=True)
        self.thread.start()
    
    def stop_capture(self):
        self.running = False
        self.capturing = False
        
        if self.proc:
            try:
                self.proc.terminate()
            except:
                pass
        
        self.status.update("[yellow]■ STOPPED")
        self.logger.write("")
        self.logger.write("[bold yellow]■ CAPTURE STOPPED[/]")
        self.logger.write(f"[cyan]Unique IPs found: {len(self.seen_ips)}[/]")
    
    def _capture(self):
        # Get local IP
        local_ip = "192.168.1.1"
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except:
            pass
        
        # Find tshark
        tshark_path = r"C:\Program Files\Wireshark\tshark.exe"
        if not os.path.exists(tshark_path):
            tshark_path = "tshark"
        
        # Find available interface
        iface = self.get_interface()
        
        # Simpler filter - STUN packets from your IP
        filter_str = f'ip.addr == {local_ip} && stun'
        
        self.logger.write(f"[dim]Local IP: {local_ip}[/]")
        self.logger.write(f"[dim]Using interface: {iface}[/]")
        self.logger.write(f"[dim]Filter: {filter_str}[/]")
        
        cmd = [
            tshark_path,
            "-i", iface,
            "-Y", filter_str,
            "-T", "fields",
            "-e", "ip.src",
            "-e", "ip.dst",
            "-e", "frame.len",
            "-e", "stun.type.method",
            "-E", "separator=|",
        ]
        
        self.logger.write(f"[dim]Running: {' '.join(cmd)}[/]")
        
        try:
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            self.proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                startupinfo=startupinfo
            )
            
            self.logger.write("[green]✓ tshark started![/]")
            
            while self.running:
                line = self.proc.stdout.readline()
                if not line:
                    if self.proc.poll() is not None:
                        break
                    continue
                
                line = line.strip()
                if not line:
                    continue
                
                # Show raw output for debugging
                self.logger.write(f"[dim]→ {line}[/]")
                
                parts = line.split('|')
                if len(parts) >= 2:
                    src = parts[0].strip()
                    dst = parts[1].strip()
                    
                    # Show destination IP (STUN server)
                    if dst and dst != local_ip and "." in dst:
                        if dst not in self.seen_ips:
                            self.seen_ips.add(dst)
                            self.logger.write("")
                            self.logger.write(f"[bold yellow][!] IP OBTAINED: {dst}[/bold yellow]")
                            self.logger.write(f"    Source: {src}")
                            self.logger.write(f"    Total unique: {len(self.seen_ips)}")
                            self.logger.write("")
            
        except Exception as e:
            self.logger.write(f"[bold red]Error: {e}[/]")
        
        self.capturing = False
        self.status.update("[yellow]Done")
