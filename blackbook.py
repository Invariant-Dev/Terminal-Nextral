# blackbook.py - The Blackbook: Command Snippet Manager
"""
A searchable vault for complex commands with:
- Add/Delete snippets
- Search filtering
- One-key paste to terminal
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical, Horizontal, Container
from textual.widgets import Static, ListView, ListItem, Input, Label, Button
from textual.binding import Binding
from textual.reactive import reactive
from textual import events
from rich.text import Text
from rich.panel import Panel
import json
import os
from pathlib import Path


SNIPPETS_FILE = Path(__file__).parent / "snippets.json"


def load_snippets() -> dict:
    """Load snippets from JSON file"""
    if SNIPPETS_FILE.exists():
        try:
            with open(SNIPPETS_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}


def save_snippets(snippets: dict):
    """Save snippets to JSON file"""
    try:
        with open(SNIPPETS_FILE, 'w') as f:
            json.dump(snippets, f, indent=2)
    except Exception as e:
        pass


class SnippetItem(ListItem):
    """A single snippet in the list"""
    
    def __init__(self, name: str, command: str):
        super().__init__()
        self.snippet_name = name
        self.snippet_command = command
    
    def compose(self) -> ComposeResult:
        yield Label(f"[bold cyan]◆[/] [white]{self.snippet_name}[/]", markup=True)
        yield Label(f"  [dim]{self.snippet_command[:50]}{'...' if len(self.snippet_command) > 50 else ''}[/]", markup=True)


class AddSnippetOverlay(Static):
    """Overlay for adding a new snippet"""
    
    def compose(self) -> ComposeResult:
        yield Static("""
[bold green]╔══════════════════════════════════════════════════╗[/]
[bold green]║[/]              [bold white]ADD NEW SNIPPET[/]                   [bold green]║[/]
[bold green]╚══════════════════════════════════════════════════╝[/]
""", markup=True)
        yield Label("[cyan]Name:[/]", markup=True)
        yield Input(id="snippet_name", placeholder="e.g., 'SSH Tunnel'")
        yield Label("[cyan]Command:[/]", markup=True)
        yield Input(id="snippet_command", placeholder="e.g., 'ssh -D 8080 user@host'")
        with Horizontal(id="add_buttons"):
            yield Button("Save", id="save_btn", variant="success")
            yield Button("Cancel", id="cancel_btn", variant="error")


class BlackbookScreen(Screen):
    """The Blackbook: Command Snippet Manager"""
    
    CSS = """
    BlackbookScreen {
        background: #050508;
    }
    
    #header {
        dock: top;
        height: 5;
        background: #050510;
        border-bottom: heavy #4444aa;
        padding: 0 2;
    }
    
    #snippet_list {
        height: 1fr;
        background: #050508;
        border: round #333366;
        scrollbar-background: #0a0a0a;
        scrollbar-color: #333366;
    }
    
    SnippetItem {
        padding: 1;
        height: auto;
    }
    
    SnippetItem:hover {
        background: #111122;
    }
    
    SnippetItem.-selected {
        background: #222244;
    }
    
    #search_bar {
        dock: top;
        height: 3;
        background: #0a0a10;
        border-bottom: solid #222244;
        padding: 0 1;
    }
    
    #search_input {
        width: 1fr;
        background: transparent;
        border: none;
        color: #8888ff;
    }
    
    #preview_panel {
        dock: bottom;
        height: 8;
        background: #0a0a15;
        border-top: heavy #4444aa;
        padding: 1;
    }
    
    #stats_bar {
        dock: bottom;
        height: 1;
        background: #0a0a10;
        color: #6666aa;
        text-align: center;
    }
    
    #add_overlay {
        layer: overlay;
        width: 100%;
        height: 100%;
        background: rgba(5, 5, 20, 0.9);
        align: center middle;
        display: none;
    }
    
    #add_overlay.visible {
        display: block;
    }
    
    AddSnippetOverlay {
        width: 60;
        height: auto;
        background: #0a0a15;
        border: double #4444aa;
        padding: 1 2;
    }
    
    #add_buttons {
        margin-top: 1;
        height: 3;
        width: 100%;
    }
    
    #add_buttons Button {
        width: 1fr;
        margin: 0 1;
    }
    """
    
    BINDINGS = [
        Binding("escape", "close_or_cancel", "Close/Cancel", show=True),
        Binding("enter", "use_snippet", "Use", show=True),
        Binding("a", "add_snippet", "Add", show=True),
        Binding("d", "delete_snippet", "Delete", show=True),
    ]
    
    search_text = reactive("")
    snippets = reactive({})
    adding = reactive(False)
    _selected_command = None  # Will be set when user selects a snippet
    _on_select_callback = None
    
    def set_select_callback(self, callback):
        """Set callback when snippet is selected"""
        self._on_select_callback = callback
    
    def compose(self) -> ComposeResult:
        yield Static(id="header", markup=True)
        with Horizontal(id="search_bar"):
            yield Static("[bold blue]◈ SEARCH:[/] ", markup=True)
            yield Input(id="search_input", placeholder="Type to search snippets...")
        yield ListView(id="snippet_list")
        yield Static(id="preview_panel", markup=True)
        yield Static(id="stats_bar", markup=True)
        
        # Add overlay
        with Container(id="add_overlay"):
            yield AddSnippetOverlay()
    
    def on_mount(self):
        # Header
        header = self.query_one("#header", Static)
        header.update("""
[bold blue]╔════════════════════════════════════════════════════════════════════════════════╗[/]
[bold blue]║[/]                          [bold white]THE BLACKBOOK: SNIPPET VAULT[/]                         [bold blue]║[/]
[bold blue]╚════════════════════════════════════════════════════════════════════════════════╝[/]
""")
        
        # Load snippets
        self.snippets = load_snippets()
        self._refresh_list()
    
    def _refresh_list(self):
        snippet_list = self.query_one("#snippet_list", ListView)
        snippet_list.clear()
        
        search = self.search_text.lower()
        filtered = {k: v for k, v in self.snippets.items() 
                    if search in k.lower() or search in v.lower()}
        
        for name, command in filtered.items():
            snippet_list.append(SnippetItem(name, command))
        
        # Update stats
        stats = self.query_one("#stats_bar", Static)
        stats.update(f"[bold blue]◈[/] SNIPPETS: {len(filtered)}/{len(self.snippets)} | [dim]A=Add D=Delete ENTER=Use ESC=Exit[/]")
        
        # Clear preview if empty
        if not filtered:
            preview = self.query_one("#preview_panel", Static)
            preview.update("[dim]No snippets found. Press [bold]A[/] to add one.[/]")
    
    def on_list_view_highlighted(self, event: ListView.Highlighted):
        """Update preview when snippet is highlighted"""
        item = event.item
        if isinstance(item, SnippetItem):
            preview = self.query_one("#preview_panel", Static)
            preview.update(f"""[bold cyan]◆ {item.snippet_name}[/]
[dim]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/]
[white]{item.snippet_command}[/]
[dim]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/]
[dim]Press ENTER to use this command[/]""")
    
    def on_input_changed(self, event: Input.Changed):
        if event.input.id == "search_input":
            self.search_text = event.value
            self._refresh_list()
    
    def action_close_or_cancel(self):
        if self.adding:
            self._hide_add_overlay()
        else:
            self.app.pop_screen()
    
    def action_use_snippet(self):
        if self.adding:
            return
        
        snippet_list = self.query_one("#snippet_list", ListView)
        if snippet_list.highlighted_child and isinstance(snippet_list.highlighted_child, SnippetItem):
            command = snippet_list.highlighted_child.snippet_command
            self._selected_command = command
            
            if self._on_select_callback:
                self._on_select_callback(command)
            
            self.app.pop_screen()
    
    def action_add_snippet(self):
        if self.adding:
            return
        self._show_add_overlay()
    
    def action_delete_snippet(self):
        if self.adding:
            return
        
        snippet_list = self.query_one("#snippet_list", ListView)
        if snippet_list.highlighted_child and isinstance(snippet_list.highlighted_child, SnippetItem):
            name = snippet_list.highlighted_child.snippet_name
            if name in self.snippets:
                del self.snippets[name]
                save_snippets(self.snippets)
                self._refresh_list()
    
    def _show_add_overlay(self):
        self.adding = True
        overlay = self.query_one("#add_overlay", Container)
        overlay.add_class("visible")
        self.query_one("#snippet_name", Input).focus()
    
    def _hide_add_overlay(self):
        self.adding = False
        overlay = self.query_one("#add_overlay", Container)
        overlay.remove_class("visible")
        # Clear inputs
        self.query_one("#snippet_name", Input).value = ""
        self.query_one("#snippet_command", Input).value = ""
    
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "save_btn":
            name = self.query_one("#snippet_name", Input).value.strip()
            command = self.query_one("#snippet_command", Input).value.strip()
            
            if name and command:
                self.snippets[name] = command
                save_snippets(self.snippets)
                self._hide_add_overlay()
                self._refresh_list()
        
        elif event.button.id == "cancel_btn":
            self._hide_add_overlay()
