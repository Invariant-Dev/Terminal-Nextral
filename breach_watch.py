# breach_watch.py - Breach Watch: Real-time Security Event Stream
"""
A live security monitor that detects:
- New processes starting
- Network connections
- Critical events
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical, Horizontal, Container
from textual.widgets import Static, RichLog, Input
from textual.binding import Binding
from textual.reactive import reactive
from rich.text import Text
import psutil
import asyncio
import socket
from datetime import datetime


class EventEntry:
    """A single security event"""
    TYPES = {
        "PROCESS": ("[bold green]PROC[/]", "green"),
        "NETWORK": ("[bold cyan]NET[/]", "cyan"),
        "WARNING": ("[bold yellow]WARN[/]", "yellow"),
        "ALERT": ("[bold red]ALERT[/]", "red"),
    }
    
    def __init__(self, event_type: str, message: str):
        self.time = datetime.now().strftime("%H:%M:%S")
        self.type = event_type
        self.message = message
    
    def render(self):
        type_badge, color = self.TYPES.get(self.type, ("[dim]???[/]", "white"))
        return f"[dim]{self.time}[/] {type_badge} [{color}]{self.message}[/]"


class BreachWatchScreen(Screen):
    """Breach Watch: Security Event Monitor"""
    
    CSS = """
    BreachWatchScreen {
        background: #050005;
    }
    
    #header {
        dock: top;
        height: 5;
        background: #100005;
        border-bottom: heavy #aa0044;
        padding: 0 2;
    }
    
    #event_log {
        height: 1fr;
        background: #050005;
        border: round #440022;
        scrollbar-background: #0a0a0a;
        scrollbar-color: #440022;
    }
    
    #legend_bar {
        dock: bottom;
        height: 3;
        background: #100010;
        border-top: solid #330022;
        padding: 0 2;
    }
    
    #stats_bar {
        dock: bottom;
        height: 1;
        background: #100005;
        color: #aa4466;
        text-align: center;
    }
    
    #status_panels {
        dock: right;
        width: 35;
        height: 100%;
        background: #080008;
        border-left: heavy #440022;
    }
    
    .status-panel {
        height: auto;
        padding: 1;
        margin: 1;
        border: round #330022;
    }
    """
    
    BINDINGS = [
        Binding("escape", "close", "Close", show=True),
        Binding("c", "clear_log", "Clear", show=True),
        Binding("p", "toggle_pause", "Pause/Resume", show=True),
    ]
    
    paused = reactive(False)
    event_count = reactive(0)
    alert_count = reactive(0)
    
    def __init__(self):
        super().__init__()
        self._known_pids = set()
        self._known_connections = set()
        self._monitoring = False
    
    def compose(self) -> ComposeResult:
        yield Static(id="header", markup=True)
        with Horizontal():
            yield RichLog(id="event_log", markup=True, wrap=True, highlight=True)
            with Vertical(id="status_panels"):
                yield Static(id="process_panel", classes="status-panel", markup=True)
                yield Static(id="network_panel", classes="status-panel", markup=True)
                yield Static(id="threat_panel", classes="status-panel", markup=True)
        yield Static(id="legend_bar", markup=True)
        yield Static(id="stats_bar", markup=True)
    
    def on_mount(self):
        # Header
        header = self.query_one("#header", Static)
        header.update("""[bold #ff0066]
   ██████╗ ██████╗ ███████╗ █████╗  ██████╗██╗  ██╗    ██╗    ██╗ █████╗ ████████╗ ██████╗██╗  ██╗
   ██╔══██╗██╔══██╗██╔════╝██╔══██╗██╔════╝██║  ██║    ██║    ██║██╔══██╗╚══██╔══╝██╔════╝██║  ██║
   ██████╔╝██████╔╝█████╗  ███████║██║     ███████║    ██║ █╗ ██║███████║   ██║   ██║     ███████║
   ██╔══██╗██╔══██╗██╔══╝  ██╔══██║██║     ██╔══██║    ██║███╗██║██╔══██║   ██║   ██║     ██╔══██║
   ██████╔╝██║  ██║███████╗██║  ██║╚██████╗██║  ██║    ╚███╔███╔╝██║  ██║   ██║   ╚██████╗██║  ██║
   ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝     ╚══╝╚══╝ ╚═╝  ╚═╝   ╚═╝    ╚═════╝╚═╝  ╚═╝
[/]""")
        
        # Legend
        legend = self.query_one("#legend_bar", Static)
        legend.update("""[bold #ff0066]◈ EVENT TYPES:[/]  [green]█ PROC[/] Process activity  [cyan]█ NET[/] Network connection  [yellow]█ WARN[/] Warning  [red]█ ALERT[/] Security alert
[dim]All events are monitored in real-time. Press P to pause, C to clear.[/]""")
        
        # Initialize known processes and connections
        self._init_baseline()
        
        # Start monitoring
        self._monitoring = True
        self.set_interval(1.0, self._monitor_cycle)
        self._update_panels()
        self.set_interval(2.0, self._update_panels)
    
    def _init_baseline(self):
        """Initialize baseline of known processes and connections"""
        log = self.query_one("#event_log", RichLog)
        log.write("[bold #ff0066]>>> BREACH WATCH INITIALIZING <<<[/]")
        log.write("[dim]Establishing baseline...[/]")
        
        # Get current processes
        for proc in psutil.process_iter(['pid']):
            try:
                self._known_pids.add(proc.info['pid'])
            except:
                pass
        
        # Get current connections
        try:
            for conn in psutil.net_connections(kind='inet'):
                if conn.status == 'ESTABLISHED' and conn.raddr:
                    self._known_connections.add((conn.laddr, conn.raddr))
        except:
            pass
        
        log.write(f"[dim]Baseline: {len(self._known_pids)} processes, {len(self._known_connections)} connections[/]")
        log.write("[bold green]>>> MONITORING ACTIVE <<<[/]")
        log.write("")
    
    def _monitor_cycle(self):
        """Single monitoring cycle"""
        if self.paused or not self._monitoring:
            return
        
        log = self.query_one("#event_log", RichLog)
        
        # Check for new processes
        current_pids = set()
        for proc in psutil.process_iter(['pid', 'name', 'username']):
            try:
                pid = proc.info['pid']
                current_pids.add(pid)
                
                if pid not in self._known_pids:
                    name = proc.info['name'] or "Unknown"
                    user = proc.info['username'] or "N/A"
                    
                    # Check if it's a suspicious process
                    suspicious = any(s in name.lower() for s in ['powershell', 'cmd', 'python', 'nc', 'netcat', 'mimikatz'])
                    
                    if suspicious:
                        event = EventEntry("ALERT", f"SUSPICIOUS: {name} (PID: {pid}) by {user}")
                        self.alert_count += 1
                    else:
                        event = EventEntry("PROCESS", f"Started: {name} (PID: {pid})")
                    
                    log.write(event.render())
                    self.event_count += 1
            except:
                pass
        
        # Check for terminated processes (optional - can be noisy)
        terminated = self._known_pids - current_pids
        for pid in list(terminated)[:3]:  # Limit to 3 per cycle
            event = EventEntry("PROCESS", f"Terminated: PID {pid}")
            log.write(event.render())
            self.event_count += 1
        
        self._known_pids = current_pids
        
        # Check for new network connections
        try:
            current_connections = set()
            for conn in psutil.net_connections(kind='inet'):
                if conn.status == 'ESTABLISHED' and conn.raddr:
                    conn_tuple = (conn.laddr, conn.raddr)
                    current_connections.add(conn_tuple)
                    
                    if conn_tuple not in self._known_connections:
                        remote_ip = conn.raddr.ip
                        remote_port = conn.raddr.port
                        local_port = conn.laddr.port
                        
                        # Common suspicious ports
                        suspicious_ports = [4444, 5555, 6666, 1337, 31337]
                        if remote_port in suspicious_ports or local_port in suspicious_ports:
                            event = EventEntry("ALERT", f"SUSPICIOUS PORT: {remote_ip}:{remote_port}")
                            self.alert_count += 1
                        else:
                            event = EventEntry("NETWORK", f"Connection: {remote_ip}:{remote_port}")
                        
                        log.write(event.render())
                        self.event_count += 1
            
            self._known_connections = current_connections
        except:
            pass
        
        # Update stats
        self._update_stats()
    
    def _update_panels(self):
        """Update status panels"""
        # Process panel
        proc_panel = self.query_one("#process_panel", Static)
        proc_count = len(self._known_pids)
        cpu = psutil.cpu_percent()
        proc_panel.update(f"""[bold green]◈ PROCESSES[/]
[cyan]Active:[/] {proc_count}
[cyan]CPU:[/] {cpu:.1f}%""")
        
        # Network panel
        net_panel = self.query_one("#network_panel", Static)
        conn_count = len(self._known_connections)
        try:
            io = psutil.net_io_counters()
            sent_mb = io.bytes_sent / (1024*1024)
            recv_mb = io.bytes_recv / (1024*1024)
        except:
            sent_mb = recv_mb = 0
        net_panel.update(f"""[bold cyan]◈ NETWORK[/]
[cyan]Connections:[/] {conn_count}
[cyan]Sent:[/] {sent_mb:.1f} MB
[cyan]Recv:[/] {recv_mb:.1f} MB""")
        
        # Threat panel
        threat_panel = self.query_one("#threat_panel", Static)
        threat_level = "LOW" if self.alert_count == 0 else ("MEDIUM" if self.alert_count < 5 else "HIGH")
        threat_color = "green" if threat_level == "LOW" else ("yellow" if threat_level == "MEDIUM" else "red")
        threat_panel.update(f"""[bold red]◈ THREAT LEVEL[/]
[{threat_color}]█ {threat_level}[/]
[cyan]Alerts:[/] {self.alert_count}
[cyan]Events:[/] {self.event_count}""")
    
    def _update_stats(self):
        """Update stats bar"""
        stats = self.query_one("#stats_bar", Static)
        status = "[yellow]PAUSED[/]" if self.paused else "[green]MONITORING[/]"
        stats.update(f"[bold #ff0066]◈[/] STATUS: {status} | EVENTS: {self.event_count} | ALERTS: {self.alert_count} | [dim]P=Pause C=Clear ESC=Exit[/]")
    
    def action_close(self):
        self._monitoring = False
        self.app.pop_screen()
    
    def action_clear_log(self):
        log = self.query_one("#event_log", RichLog)
        log.clear()
        self.event_count = 0
        log.write("[dim]Log cleared[/]")
    
    def action_toggle_pause(self):
        self.paused = not self.paused
        log = self.query_one("#event_log", RichLog)
        if self.paused:
            log.write("[yellow]>>> MONITORING PAUSED <<<[/]")
        else:
            log.write("[green]>>> MONITORING RESUMED <<<[/]")
        self._update_stats()
