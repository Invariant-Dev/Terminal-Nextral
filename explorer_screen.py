# explorer_screen.py - TUI File Navigator for Nextral Terminal
from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, ListView, ListItem, Label
from textual.binding import Binding
from textual.reactive import reactive
from textual import events
import os
import subprocess
import sys

# File type icons for that "hacker database" aesthetic
FILE_ICONS = {
    '.py': '🐍',
    '.js': '📜',
    '.ts': '📘',
    '.json': '📋',
    '.md': '📝',
    '.txt': '📄',
    '.html': '🌐',
    '.css': '🎨',
    '.exe': '⚙️',
    '.bat': '🦇',
    '.ps1': '💠',
    '.sh': '🐚',
    '.zip': '📦',
    '.rar': '📦',
    '.7z': '📦',
    '.png': '🖼️',
    '.jpg': '🖼️',
    '.gif': '🖼️',
    '.mp3': '🎵',
    '.mp4': '🎬',
    '.pdf': '📕',
    '.doc': '📘',
    '.docx': '📘',
    '.xls': '📊',
    '.xlsx': '📊',
}

def get_icon(name, is_dir):
    if is_dir:
        return '📁'
    ext = os.path.splitext(name)[1].lower()
    return FILE_ICONS.get(ext, '📄')


class FileItem(ListItem):
    """A single file/directory item in the explorer"""
    
    def __init__(self, name: str, path: str, is_dir: bool):
        super().__init__()
        self.file_name = name
        self.file_path = path
        self.is_dir = is_dir
        self.icon = get_icon(name, is_dir)
    
    def compose(self) -> ComposeResult:
        style = "bold cyan" if self.is_dir else "white"
        yield Label(f"{self.icon} [{style}]{self.file_name}[/]", markup=True)


class ExplorerScreen(Screen):
    """Dual-pane file explorer with cyberpunk aesthetics"""
    
    CSS = """
    ExplorerScreen {
        background: #050505;
    }
    
    #explorer_container {
        height: 100%;
        width: 100%;
    }
    
    #file_list_container {
        width: 50%;
        height: 100%;
        border: solid #00aa55;
        background: #0a0f0a;
    }
    
    #file_list_header {
        height: 3;
        background: #001100;
        border-bottom: heavy #00aa55;
        padding: 0 1;
        color: #00ffaa;
        text-style: bold;
    }
    
    #file_list {
        height: 1fr;
        background: #0a0f0a;
        scrollbar-background: #0a0a0a;
        scrollbar-color: #004400;
    }
    
    #preview_container {
        width: 50%;
        height: 100%;
        border: solid #004488;
        background: #050a10;
    }
    
    #preview_header {
        height: 3;
        background: #001122;
        border-bottom: heavy #004488;
        padding: 0 1;
        color: #44aaff;
        text-style: bold;
    }
    
    #preview_content {
        height: 1fr;
        padding: 1;
        background: #050a10;
        color: #88aacc;
        overflow-y: auto;
    }
    
    #help_bar {
        dock: bottom;
        height: 1;
        background: #001100;
        color: #00ff88;
        text-align: center;
    }
    
    FileItem {
        padding: 0 1;
        height: 1;
    }
    
    FileItem:hover {
        background: #002200;
    }
    
    FileItem.-selected {
        background: #003300;
    }
    """
    
    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("q", "close", "Close"),
        Binding("enter", "select_item", "Open/Enter"),
        Binding("backspace", "go_up", "Parent Dir"),
    ]
    
    current_path = reactive("")
    selected_file = reactive("")
    
    def __init__(self, start_path: str = None):
        super().__init__()
        self.current_path = start_path or os.getcwd()
        self._on_cd_callback = None
    
    def set_cd_callback(self, callback):
        """Set callback to update shell cwd when navigating"""
        self._on_cd_callback = callback
    
    def compose(self) -> ComposeResult:
        with Horizontal(id="explorer_container"):
            with Vertical(id="file_list_container"):
                yield Static(id="file_list_header", markup=True)
                yield ListView(id="file_list")
            with Vertical(id="preview_container"):
                yield Static(id="preview_header", markup=True)
                yield Static(id="preview_content", markup=True)
        yield Static("[dim]↑↓[/] Navigate  [dim]Enter[/] Open  [dim]Backspace[/] Parent  [dim]Q/Esc[/] Close", id="help_bar", markup=True)
    
    def on_mount(self):
        self._refresh_file_list()
    
    def watch_current_path(self, new_path: str):
        """React to path changes"""
        if hasattr(self, '_is_mounted') and self._is_mounted:
            self._refresh_file_list()
    
    def _refresh_file_list(self):
        """Refresh the file listing"""
        header = self.query_one("#file_list_header", Static)
        
        # Shorten path for display
        display_path = self.current_path
        home = os.path.expanduser("~")
        if display_path.startswith(home):
            display_path = "~" + display_path[len(home):]
        
        header.update(f"📂 DIRECTORY: [white]{display_path}[/]")
        
        file_list = self.query_one("#file_list", ListView)
        file_list.clear()
        
        try:
            items = os.listdir(self.current_path)
            
            # Sort: directories first, then files, alphabetically
            dirs = sorted([i for i in items if os.path.isdir(os.path.join(self.current_path, i))], key=str.lower)
            files = sorted([i for i in items if not os.path.isdir(os.path.join(self.current_path, i))], key=str.lower)
            
            # Add parent directory option
            if self.current_path != os.path.dirname(self.current_path):  # Not at root
                file_list.append(FileItem("..", os.path.dirname(self.current_path), True))
            
            for d in dirs:
                file_list.append(FileItem(d, os.path.join(self.current_path, d), True))
            for f in files:
                file_list.append(FileItem(f, os.path.join(self.current_path, f), False))
                
        except PermissionError:
            self.query_one("#preview_content", Static).update("[red]⚠ ACCESS DENIED[/]")
        except Exception as e:
            self.query_one("#preview_content", Static).update(f"[red]Error: {e}[/]")
    
    def on_list_view_selected(self, event: ListView.Selected):
        """Handle item selection (Enter key)"""
        item = event.item
        if isinstance(item, FileItem):
            if item.is_dir:
                # Navigate into directory
                self.current_path = item.file_path
                self._refresh_file_list()
                if self._on_cd_callback:
                    self._on_cd_callback(self.current_path)
            else:
                # Open file with default application
                self._open_file(item.file_path)
    
    def on_list_view_highlighted(self, event: ListView.Highlighted):
        """Update preview when item is highlighted"""
        item = event.item
        if isinstance(item, FileItem):
            self._update_preview(item)
    
    def _update_preview(self, item: FileItem):
        """Update the preview pane"""
        header = self.query_one("#preview_header", Static)
        content = self.query_one("#preview_content", Static)
        
        if item.file_name == "..":
            header.update("📁 [white]Parent Directory[/]")
            content.update("[dim]Navigate to parent directory[/]")
            return
        
        header.update(f"{item.icon} [white]{item.file_name}[/]")
        
        if item.is_dir:
            # Count contents
            try:
                items = os.listdir(item.file_path)
                dirs = len([i for i in items if os.path.isdir(os.path.join(item.file_path, i))])
                files = len(items) - dirs
                content.update(f"[cyan]📁 Subdirectories:[/] {dirs}\n[cyan]📄 Files:[/] {files}")
            except:
                content.update("[dim]Cannot read directory[/]")
        else:
            # Try to preview text files
            try:
                size = os.path.getsize(item.file_path)
                if size > 100000:  # 100KB limit
                    content.update(f"[yellow]File too large to preview[/]\n[dim]Size: {size:,} bytes[/]")
                    return
                
                with open(item.file_path, 'r', encoding='utf-8', errors='replace') as f:
                    lines = f.readlines()[:25]  # First 25 lines
                    preview_text = ''.join(lines)
                    if len(lines) == 25:
                        preview_text += "\n[dim]... (truncated)[/]"
                    content.update(preview_text)
            except:
                content.update(f"[dim]Binary file or cannot preview[/]\n[dim]Size: {os.path.getsize(item.file_path):,} bytes[/]")
    
    def _open_file(self, path: str):
        """Open file with system default application"""
        try:
            if sys.platform == 'win32':
                os.startfile(path)
            elif sys.platform == 'darwin':
                subprocess.run(['open', path])
            else:
                subprocess.run(['xdg-open', path])
        except Exception:
            pass
    
    def action_close(self):
        """Close the explorer and return to terminal"""
        self.app.pop_screen()
    
    def action_go_up(self):
        """Navigate to parent directory"""
        parent = os.path.dirname(self.current_path)
        if parent != self.current_path:
            self.current_path = parent
            self._refresh_file_list()
            if self._on_cd_callback:
                self._on_cd_callback(self.current_path)
