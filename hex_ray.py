# hex_ray.py - Hex-Ray: Binary TUI Visualizer
"""
A sophisticated hex editor/viewer with:
- Offset | Hex | ASCII columns
- File header detection
- Color-coded bytes
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical, Horizontal, Container
from textual.widgets import Static, Footer
from textual.binding import Binding
from textual.reactive import reactive
from rich.text import Text
import os


# Common file signatures for identification
FILE_SIGNATURES = {
    b'\x4D\x5A': ('EXE/DLL', 'Windows Executable'),
    b'\x50\x4B\x03\x04': ('ZIP', 'ZIP Archive'),
    b'\x50\x4B\x05\x06': ('ZIP', 'Empty ZIP Archive'),
    b'\x89\x50\x4E\x47': ('PNG', 'PNG Image'),
    b'\xFF\xD8\xFF': ('JPEG', 'JPEG Image'),
    b'\x47\x49\x46\x38': ('GIF', 'GIF Image'),
    b'\x25\x50\x44\x46': ('PDF', 'PDF Document'),
    b'\x7F\x45\x4C\x46': ('ELF', 'Linux Executable'),
    b'\xCA\xFE\xBA\xBE': ('CLASS', 'Java Class File'),
    b'\x52\x61\x72\x21': ('RAR', 'RAR Archive'),
    b'\x1F\x8B': ('GZIP', 'GZIP Compressed'),
    b'\x42\x5A\x68': ('BZ2', 'BZIP2 Compressed'),
    b'\x37\x7A\xBC\xAF': ('7Z', '7-Zip Archive'),
    b'\x00\x00\x00\x1C\x66\x74\x79\x70': ('MP4', 'MP4 Video'),
    b'\x49\x44\x33': ('MP3', 'MP3 Audio'),
    b'\x52\x49\x46\x46': ('WAV/AVI', 'RIFF Container'),
}


def identify_file(data: bytes) -> tuple:
    for sig, (short, desc) in FILE_SIGNATURES.items():
        if data.startswith(sig):
            return short, desc
    return 'UNKNOWN', 'Unknown File Type'


class HexView(Static):    
    offset = reactive(0)
    bytes_per_row = 16
    rows_visible = 20
    
    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path
        self.file_data = b''
        self.file_size = 0
        
    def on_mount(self):
        self._load_file()
        self._render_hex()
    
    def _load_file(self):
        try:
            with open(self.file_path, 'rb') as f:
                self.file_data = f.read()
            self.file_size = len(self.file_data)
        except Exception as e:
            self.file_data = b''
            self.file_size = 0
    
    def _render_hex(self):
        if not self.file_data:
            self.update("[red]Error: Could not load file[/]")
            return
        
        lines = []
        start = self.offset
        end = min(start + (self.bytes_per_row * self.rows_visible), self.file_size)
        
        # Header
        header = "[bold cyan]  OFFSET  [/]│[bold cyan]  "
        header += "  ".join(f"{i:02X}" for i in range(self.bytes_per_row))
        header += "  [/]│[bold cyan]    ASCII         [/]"
        lines.append(header)
        lines.append("[dim]──────────┼─────────────────────────────────────────────────────────┼──────────────────[/]")
        
        for row_start in range(start, end, self.bytes_per_row):
            row_end = min(row_start + self.bytes_per_row, self.file_size)
            row_bytes = self.file_data[row_start:row_end]
            
            # Offset column
            line = f"[yellow]{row_start:08X}[/] │ "
            
            # Hex bytes
            hex_parts = []
            for b in row_bytes:
                if b == 0x00:
                    hex_parts.append(f"[dim]{b:02X}[/]")
                elif 0x20 <= b <= 0x7E:
                    hex_parts.append(f"[green]{b:02X}[/]")
                else:
                    hex_parts.append(f"[cyan]{b:02X}[/]")
            
            # Pad if row is incomplete
            while len(hex_parts) < self.bytes_per_row:
                hex_parts.append("  ")
            
            line += "  ".join(hex_parts) + "  │ "
            
            # ASCII representation
            ascii_part = ""
            for b in row_bytes:
                if 0x20 <= b <= 0x7E:
                    ascii_part += f"[white]{chr(b)}[/]"
                else:
                    ascii_part += "[dim].[/]"
            
            line += ascii_part
            lines.append(line)
        
        # Status line
        lines.append("")
        pct = int((self.offset / max(1, self.file_size - (self.bytes_per_row * self.rows_visible))) * 100) if self.file_size > 0 else 0
        pct = max(0, min(100, pct))
        lines.append(f"[dim]Showing bytes {start:,} - {end:,} of {self.file_size:,} ({pct}%)[/]")
        
        self.update("\n".join(lines))
    
    def scroll_down(self):
        max_offset = max(0, self.file_size - (self.bytes_per_row * self.rows_visible))
        self.offset = min(self.offset + (self.bytes_per_row * 5), max_offset)
        self._render_hex()
    
    def scroll_up(self):
        self.offset = max(0, self.offset - (self.bytes_per_row * 5))
        self._render_hex()
    
    def page_down(self):
        max_offset = max(0, self.file_size - (self.bytes_per_row * self.rows_visible))
        self.offset = min(self.offset + (self.bytes_per_row * self.rows_visible), max_offset)
        self._render_hex()
    
    def page_up(self):
        self.offset = max(0, self.offset - (self.bytes_per_row * self.rows_visible))
        self._render_hex()


class HeaderPanel(Static):
    """File header analysis panel"""
    
    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path
    
    def on_mount(self):
        self._analyze()
    
    def _analyze(self):
        try:
            with open(self.file_path, 'rb') as f:
                header_bytes = f.read(64)
            
            file_size = os.path.getsize(self.file_path)
            file_name = os.path.basename(self.file_path)
            short_type, desc = identify_file(header_bytes)
            
            content = f"""
[bold white]╔════════════════════════════════════════╗[/]
[bold white]║[/]           [bold cyan]FILE ANALYSIS[/]                [bold white]║[/]
[bold white]╚════════════════════════════════════════╝[/]

[bold]Name:[/] [white]{file_name[:30]}[/]
[bold]Size:[/] [yellow]{file_size:,} bytes[/]
[bold]Type:[/] [green]{short_type}[/]
[bold]Desc:[/] [dim]{desc}[/]

[bold cyan]─── HEADER BYTES ───[/]
"""
            # Show first 16 bytes in a nice format
            hex_line = " ".join(f"{b:02X}" for b in header_bytes[:16])
            content += f"[dim]{hex_line}[/]\n"
            
            # Magic bytes detection
            content += "\n[bold cyan]─── MAGIC BYTES ───[/]\n"
            if header_bytes[:4]:
                magic = " ".join(f"{b:02X}" for b in header_bytes[:4])
                content += f"[yellow]{magic}[/]\n"
            
            self.update(content)
            
        except Exception as e:
            self.update(f"[red]Error: {e}[/]")


class HexScreen(Screen):
    """Hex-Ray: Binary Visualizer Screen"""
    
    CSS = """
    HexScreen {
        background: #050510;
    }
    
    #header {
        dock: top;
        height: 3;
        background: #0a0a20;
        border-bottom: heavy #4444aa;
        padding: 0 2;
        content-align: center middle;
    }
    
    #hex_container {
        width: 1fr;
        height: 1fr;
    }
    
    #hex_view {
        width: 1fr;
        height: 1fr;
        background: #080810;
        border: round #333366;
        padding: 1;
        overflow-y: auto;
    }
    
    #sidebar {
        dock: right;
        width: 42;
        background: #0a0a15;
        border-left: heavy #4444aa;
        padding: 1;
    }
    
    #stats {
        dock: bottom;
        height: 1;
        background: #0a0a20;
        color: #6666aa;
        text-align: center;
    }
    """
    
    BINDINGS = [
        Binding("escape", "close", "Close", show=True),
        Binding("up", "scroll_up", "Scroll Up", show=False),
        Binding("down", "scroll_down", "Scroll Down", show=False),
        Binding("pageup", "page_up", "Page Up", show=True),
        Binding("pagedown", "page_down", "Page Down", show=True),
        Binding("home", "go_start", "Start", show=True),
        Binding("end", "go_end", "End", show=True),
    ]
    
    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path
    
    def compose(self) -> ComposeResult:
        yield Static(
            "[bold blue]╔════════════════════════════════════════════════════════════════════════════════╗[/]\n"
            "[bold blue]║[/]                       [bold white]HEX-RAY: BINARY VISUALIZER[/]                       [bold blue]║[/]\n"
            "[bold blue]╚════════════════════════════════════════════════════════════════════════════════╝[/]",
            id="header", markup=True
        )
        yield HeaderPanel(self.file_path, id="sidebar")
        with Container(id="hex_container"):
            yield HexView(self.file_path, id="hex_view")
        yield Static(id="stats", markup=True)
    
    def on_mount(self):
        stats = self.query_one("#stats", Static)
        stats.update("[bold blue]◈[/] ↑↓=Scroll PgUp/PgDn=Page Home/End=Jump ESC=Exit")
    
    def action_close(self):
        self.app.pop_screen()
    
    def action_scroll_up(self):
        self.query_one("#hex_view", HexView).scroll_up()
    
    def action_scroll_down(self):
        self.query_one("#hex_view", HexView).scroll_down()
    
    def action_page_up(self):
        self.query_one("#hex_view", HexView).page_up()
    
    def action_page_down(self):
        self.query_one("#hex_view", HexView).page_down()
    
    def action_go_start(self):
        hv = self.query_one("#hex_view", HexView)
        hv.offset = 0
        hv._render_hex()
    
    def action_go_end(self):
        hv = self.query_one("#hex_view", HexView)
        hv.offset = max(0, hv.file_size - (hv.bytes_per_row * hv.rows_visible))
        hv._render_hex()
