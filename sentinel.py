# sentinel.py - The Sentinel: Visual Process Reaper
"""
A cinematic TUI process manager with:
- Targeting reticules
- Health bars for CPU/RAM
- Kill animations
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical, Horizontal, Container
from textual.widgets import Static, DataTable, Input, Footer
from textual.binding import Binding
from textual.reactive import reactive
from textual import events
from rich.text import Text
from rich.table import Table
from rich.panel import Panel
import psutil
import asyncio


class ProcessRow:
    """Data class for a process"""
    def __init__(self, proc):
        self.pid = proc.info['pid']
        self.name = proc.info['name'] or "Unknown"
        self.cpu = proc.info['cpu_percent'] or 0.0
        self.memory = proc.info['memory_percent'] or 0.0
        self.status = proc.info['status'] or "unknown"
    
    def cpu_bar(self, width=10):
        filled = int(min(self.cpu, 100) / 100 * width)
        bar = '█' * filled + '░' * (width - filled)
        if self.cpu > 80:
            return f"[bold red]{bar}[/]"
        elif self.cpu > 50:
            return f"[yellow]{bar}[/]"
        return f"[green]{bar}[/]"
    
    def mem_bar(self, width=10):
        filled = int(min(self.memory, 100) / 100 * width)
        bar = '█' * filled + '░' * (width - filled)
        if self.memory > 80:
            return f"[bold red]{bar}[/]"
        elif self.memory > 50:
            return f"[yellow]{bar}[/]"
        return f"[cyan]{bar}[/]"


class KillOverlay(Static):
    """Targeting/Kill confirmation overlay"""
    
    def __init__(self, pid: int, name: str):
        super().__init__()
        self.target_pid = pid
        self.target_name = name
    
    def compose(self) -> ComposeResult:
        yield Static(id="kill_content", markup=True)
    
    def on_mount(self):
        content = self.query_one("#kill_content", Static)
        content.update(f"""
[bold red]╔══════════════════════════════════════╗[/]
[bold red]║[/]       [bold white]◎ TARGET LOCKED ◎[/]            [bold red]║[/]
[bold red]╠══════════════════════════════════════╣[/]
[bold red]║[/]  PID:  [bold yellow]{self.target_pid:<10}[/]                 [bold red]║[/]
[bold red]║[/]  NAME: [bold cyan]{self.target_name[:20]:<20}[/]     [bold red]║[/]
[bold red]╠══════════════════════════════════════╣[/]
[bold red]║[/]  [dim]Press [bold]ENTER[/] to TERMINATE[/]          [bold red]║[/]
[bold red]║[/]  [dim]Press [bold]ESC[/] to cancel[/]               [bold red]║[/]
[bold red]╚══════════════════════════════════════╝[/]
""")


class SentinelScreen(Screen):
    """The Sentinel: Visual Process Reaper"""
    
    CSS = """
    SentinelScreen {
        background: #050505;
    }
    
    #header {
        dock: top;
        height: 5;
        background: #0a0505;
        border-bottom: heavy #aa0000;
        padding: 0 2;
    }
    
    #process_table {
        height: 1fr;
        background: #050505;
        border: round #330000;
        scrollbar-background: #0a0a0a;
        scrollbar-color: #330000;
    }
    
    #process_table > .datatable--header {
        background: #1a0505;
        color: #ff4444;
        text-style: bold;
    }
    
    #process_table > .datatable--cursor {
        background: #331111;
    }
    
    #filter_bar {
        dock: bottom;
        height: 3;
        background: #0a0505;
        border-top: solid #550000;
        padding: 0 1;
    }
    
    #filter_input {
        width: 1fr;
        background: transparent;
        border: none;
        color: #ff6666;
    }
    
    #stats_bar {
        dock: bottom;
        height: 1;
        background: #1a0505;
        color: #aa4444;
        text-align: center;
    }
    
    #kill_overlay {
        layer: overlay;
        width: 100%;
        height: 100%;
        background: rgba(10, 0, 0, 0.85);
        align: center middle;
        display: none;
    }
    
    #kill_overlay.visible {
        display: block;
    }
    
    KillOverlay {
        width: auto;
        height: auto;
    }
    """
    
    BINDINGS = [
        Binding("escape", "close_or_cancel", "Close/Cancel", show=True),
        Binding("k", "target_kill", "Kill", show=True),
        Binding("space", "target_kill", "Target", show=False),
        Binding("enter", "confirm_kill", "Confirm", show=False),
        Binding("r", "refresh", "Refresh", show=True),
        Binding("f", "focus_filter", "Filter", show=True),
    ]
    
    filter_text = reactive("")
    targeting = reactive(False)
    target_pid = reactive(0)
    target_name = reactive("")
    
    def compose(self) -> ComposeResult:
        yield Static(id="header", markup=True)
        yield DataTable(id="process_table", cursor_type="row", zebra_stripes=True)
        with Horizontal(id="filter_bar"):
            yield Static("[bold red]◈ FILTER:[/] ", markup=True)
            yield Input(id="filter_input", placeholder="Type to filter processes...")
        yield Static(id="stats_bar", markup=True)
        
        # Kill overlay (hidden by default)
        with Container(id="kill_overlay"):
            yield KillOverlay(0, "")
    
    def on_mount(self):
        # Header
        header = self.query_one("#header", Static)
        header.update("""
[bold red]╔════════════════════════════════════════════════════════════════════════════════╗[/]
[bold red]║[/]                          [bold white]THE SENTINEL: PROCESS REAPER[/]                        [bold red]║[/]
[bold red]╚════════════════════════════════════════════════════════════════════════════════╝[/]
""")
        
        # Setup table
        table = self.query_one("#process_table", DataTable)
        table.add_column("◎", width=3)  # Targeting reticule
        table.add_column("PID", width=8)
        table.add_column("NAME", width=30)
        table.add_column("CPU", width=15)
        table.add_column("RAM", width=15)
        table.add_column("STATUS", width=12)
        
        # Load processes
        self._refresh_processes()
        
        # Auto-refresh
        self.set_interval(2.0, self._refresh_processes)
    
    def _refresh_processes(self):
        table = self.query_one("#process_table", DataTable)
        
        # Remember cursor position
        try:
            cursor_row = table.cursor_row
        except:
            cursor_row = 0
        
        table.clear()
        
        try:
            procs = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
                try:
                    procs.append(ProcessRow(proc))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Sort by CPU usage descending
            procs.sort(key=lambda p: p.cpu, reverse=True)
            
            # Filter
            filter_text = self.filter_text.lower()
            if filter_text:
                procs = [p for p in procs if filter_text in p.name.lower() or filter_text in str(p.pid)]
            
            # Limit to top 100 for performance
            procs = procs[:100]
            
            for proc in procs:
                reticule = "[dim]○[/]"
                if self.target_pid == proc.pid:
                    reticule = "[bold red]◉[/]"
                
                table.add_row(
                    Text.from_markup(reticule),
                    str(proc.pid),
                    proc.name[:28],
                    Text.from_markup(f"{proc.cpu_bar()} {proc.cpu:5.1f}%"),
                    Text.from_markup(f"{proc.mem_bar()} {proc.memory:5.1f}%"),
                    proc.status,
                    key=str(proc.pid)
                )
            
            # Update stats
            cpu_total = psutil.cpu_percent()
            mem = psutil.virtual_memory()
            stats = self.query_one("#stats_bar", Static)
            stats.update(f"[bold red]◈[/] PROCESSES: {len(procs)} | CPU: {cpu_total:.1f}% | RAM: {mem.percent:.1f}% | [dim]K=Kill R=Refresh F=Filter ESC=Exit[/]")
            
            # Restore cursor
            if cursor_row < len(procs):
                table.move_cursor(row=cursor_row)
                
        except Exception as e:
            pass
    
    def on_input_changed(self, event: Input.Changed):
        if event.input.id == "filter_input":
            self.filter_text = event.value
            self._refresh_processes()
    
    def action_close_or_cancel(self):
        if self.targeting:
            self._hide_kill_overlay()
        else:
            self.app.pop_screen()
    
    def action_target_kill(self):
        if self.targeting:
            return
        
        table = self.query_one("#process_table", DataTable)
        try:
            row_key = table.get_row_at(table.cursor_row)
            pid = int(table.get_cell_at((table.cursor_row, 1)))
            name = str(table.get_cell_at((table.cursor_row, 2)))
            
            self.target_pid = pid
            self.target_name = name
            self._show_kill_overlay(pid, name)
        except:
            pass
    
    def _show_kill_overlay(self, pid: int, name: str):
        self.targeting = True
        overlay = self.query_one("#kill_overlay", Container)
        overlay.add_class("visible")
        
        # Update overlay content
        kill_widget = overlay.query_one(KillOverlay)
        kill_widget.target_pid = pid
        kill_widget.target_name = name
        kill_widget.on_mount()  # Refresh content
    
    def _hide_kill_overlay(self):
        self.targeting = False
        self.target_pid = 0
        self.target_name = ""
        overlay = self.query_one("#kill_overlay", Container)
        overlay.remove_class("visible")
    
    def action_confirm_kill(self):
        if not self.targeting or self.target_pid == 0:
            return
        
        try:
            proc = psutil.Process(self.target_pid)
            proc.terminate()
            
            # Visual feedback
            log = f"[bold green]✓ TERMINATED:[/] {self.target_name} (PID {self.target_pid})"
        except psutil.NoSuchProcess:
            log = f"[yellow]Process already terminated[/]"
        except psutil.AccessDenied:
            log = f"[bold red]ACCESS DENIED:[/] Cannot terminate {self.target_name}"
        except Exception as e:
            log = f"[red]Error: {e}[/]"
        
        self._hide_kill_overlay()
        self._refresh_processes()
    
    def action_refresh(self):
        self._refresh_processes()
    
    def action_focus_filter(self):
        self.query_one("#filter_input", Input).focus()
