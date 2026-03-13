# obelisk.py - The Obelisk: Usage Heatmap Dashboard

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical, Horizontal, Container
from textual.widgets import Static, Footer
from textual.binding import Binding
from textual.reactive import reactive
from datetime import datetime, timedelta
import os
import json
from pathlib import Path
from collections import Counter
import random


HISTORY_FILE = Path(__file__).parent / ".nextral_history"


def load_history() -> list:
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, 'r') as f:
                return [line.strip() for line in f.readlines() if line.strip()]
        except:
            pass
    return []


def get_command_stats(history: list) -> dict:
    """Analyze command history"""
    if not history:
        # Generate sample data for demo
        sample_commands = ["ls", "cd", "git status", "python", "npm", "help", "clear", "cat", "grep", "code"]
        history = [random.choice(sample_commands) for _ in range(random.randint(50, 200))]
    
    counter = Counter()
    for cmd in history:
        # Extract base command
        base = cmd.split()[0] if cmd else ""
        if base:
            counter[base] += 1
    
    return dict(counter.most_common(10))


class HeatmapWidget(Static):
    """GitHub-style contribution heatmap"""
    
    def on_mount(self):
        self._render_heatmap()
    
    def _render_heatmap(self):
        # Generate 52 weeks x 7 days heatmap
        # Using random data for demo (would use real timestamps in production)
        
        lines = []
        lines.append("[bold white]─── COMMAND ACTIVITY HEATMAP (Last 52 Weeks) ───[/]")
        lines.append("")
        
        # Day labels
        day_labels = ["Mon", "   ", "Wed", "   ", "Fri", "   ", "Sun"]
        
        # Generate heatmap data (random for demo)
        heatmap_chars = ["░", "▒", "▓", "█"]
        heatmap_colors = ["dim", "green", "bold green", "bold white on green"]
        
        for day_idx, day_label in enumerate(day_labels):
            line = f"[dim]{day_label}[/] "
            for week in range(52):
                # Simulate activity level (0-3)
                # More recent weeks have higher activity
                base_activity = min(3, week // 15)
                activity = random.randint(0, base_activity + 1) if random.random() > 0.3 else 0
                activity = min(3, activity)
                
                char = heatmap_chars[activity]
                color = heatmap_colors[activity]
                line += f"[{color}]{char}[/]"
            
            lines.append(line)
        
        lines.append("")
        lines.append("[dim]Less[/] [dim]░[/][green]▒[/][bold green]▓[/][bold white on green]█[/] [dim]More[/]")
        
        self.update("\n".join(lines))


class TopCommandsWidget(Static):
    """Bar chart of most used commands"""
    
    def on_mount(self):
        self._render_chart()
    
    def _render_chart(self):
        history = load_history()
        stats = get_command_stats(history)
        
        if not stats:
            self.update("[dim]No command history available[/]")
            return
        
        lines = []
        lines.append("[bold white]─── TOP COMMANDS ───[/]")
        lines.append("")
        
        max_count = max(stats.values()) if stats else 1
        bar_width = 30
        
        for i, (cmd, count) in enumerate(stats.items()):
            # Calculate bar length
            bar_len = int((count / max_count) * bar_width)
            bar = "█" * bar_len + "░" * (bar_width - bar_len)
            
            # Color based on rank
            if i == 0:
                color = "bold yellow"
                rank = "🥇"
            elif i == 1:
                color = "white"
                rank = "🥈"
            elif i == 2:
                color = "dim"
                rank = "🥉"
            else:
                color = "cyan"
                rank = f" {i+1}."
            
            lines.append(f"{rank} [{color}]{cmd:<12}[/] [{color}]{bar}[/] [dim]{count:>4}[/]")
        
        self.update("\n".join(lines))


class SessionStatsWidget(Static):
    """Current session statistics"""
    
    def on_mount(self):
        self._render_stats()
    
    def _render_stats(self):
        history = load_history()
        
        # Calculate stats
        total_commands = len(history)
        unique_commands = len(set(cmd.split()[0] for cmd in history if cmd))
        
        # Session time (simulated)
        session_start = datetime.now() - timedelta(minutes=random.randint(10, 120))
        session_duration = datetime.now() - session_start
        
        lines = []
        lines.append("[bold white]─── SESSION STATISTICS ───[/]")
        lines.append("")
        lines.append(f"  [cyan]◉[/] Total Commands:     [bold white]{total_commands}[/]")
        lines.append(f"  [cyan]◉[/] Unique Commands:    [bold white]{unique_commands}[/]")
        lines.append(f"  [cyan]◉[/] Session Duration:   [yellow]{str(session_duration).split('.')[0]}[/]")
        lines.append(f"  [cyan]◉[/] Commands/Minute:    [green]{total_commands / max(1, session_duration.seconds // 60):.1f}[/]")
        lines.append("")
        
        # Fun productivity meter
        productivity = min(100, (total_commands * 2) + random.randint(10, 30))
        prod_bar = "█" * (productivity // 5) + "░" * (20 - productivity // 5)
        prod_color = "green" if productivity > 70 else "yellow" if productivity > 40 else "red"
        
        lines.append(f"  [bold]Productivity:[/] [{prod_color}]{prod_bar}[/] [{prod_color}]{productivity}%[/]")
        
        self.update("\n".join(lines))


class ObeliskScreen(Screen):
    """The Obelisk: Usage Heatmap Dashboard"""
    
    CSS = """
    ObeliskScreen {
        background: #080808;
    }
    
    #header {
        dock: top;
        height: 3;
        background: #101010;
        border-bottom: heavy #888844;
        padding: 0 2;
        content-align: center middle;
    }
    
    #main_container {
        width: 100%;
        height: 1fr;
        padding: 1;
    }
    
    #heatmap {
        height: 12;
        background: #0a0a0a;
        border: round #444422;
        padding: 1;
    }
    
    #bottom_row {
        height: 1fr;
        margin-top: 1;
    }
    
    #top_commands {
        width: 1fr;
        height: 100%;
        background: #0a0a0a;
        border: round #444422;
        padding: 1;
        margin-right: 1;
    }
    
    #session_stats {
        width: 40;
        height: 100%;
        background: #0a0a0a;
        border: round #444422;
        padding: 1;
    }
    
    #stats {
        dock: bottom;
        height: 1;
        background: #101010;
        color: #888844;
        text-align: center;
    }
    """
    
    BINDINGS = [
        Binding("escape", "close", "Close", show=True),
        Binding("r", "refresh", "Refresh", show=True),
    ]
    
    def compose(self) -> ComposeResult:
        yield Static(
            "[bold yellow]╔════════════════════════════════════════════════════════════════════════════════╗[/]\n"
            "[bold yellow]║[/]                       [bold white]THE OBELISK: ACTIVITY DASHBOARD[/]                      [bold yellow]║[/]\n"
            "[bold yellow]╚════════════════════════════════════════════════════════════════════════════════╝[/]",
            id="header", markup=True
        )
        
        with Vertical(id="main_container"):
            yield HeatmapWidget(id="heatmap")
            
            with Horizontal(id="bottom_row"):
                yield TopCommandsWidget(id="top_commands")
                yield SessionStatsWidget(id="session_stats")
        
        yield Static(id="stats", markup=True)
    
    def on_mount(self):
        stats = self.query_one("#stats", Static)
        stats.update("[bold yellow]◈[/] R=Refresh Data  ESC=Exit")
    
    def action_close(self):
        self.app.pop_screen()
    
    def action_refresh(self):
        self.query_one("#heatmap", HeatmapWidget)._render_heatmap()
        self.query_one("#top_commands", TopCommandsWidget)._render_chart()
        self.query_one("#session_stats", SessionStatsWidget)._render_stats()
        self.query_one("#stats", Static).update("[green]✓ Data refreshed![/]")
