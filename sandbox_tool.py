"""
Malware Sandbox — Advanced Standalone Code Analysis
"""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical, Horizontal
from textual.widgets import Header, Footer, Input, Button, RichLog, Static
from textual.binding import Binding
import re
import math
import collections
import string

class SandboxTool(Screen):
    """Standalone Malware Analysis Environment"""
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Close"),
        Binding("ctrl+s", "analyze_code", "Static Analysis"),
    ]

    CSS = """
    SandboxTool {
        background: #0f0f12;
    }
    #sandbox_header {
        dock: top;
        height: auto;
        padding: 1;
        background: #18181b;
        border-bottom: heavy #ca8a04;
    }
    #sandbox_input {
        margin-bottom: 1;
        border: solid #ca8a04;
    }
    #sandbox_log {
        height: 1fr;
        background: #0f0f12;
        border: round #18181b;
        padding: 1;
        scrollbar-color: #ca8a04;
    }
    .sandbox-btn {
        width: 20;
        background: #ca8a04;
        color: white;
        margin-right: 1;
    }
    .sandbox-btn:hover {
        background: #eab308;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="sandbox_header"):
            yield Static("[bold yellow]PASTE CODE / FILE PATH[/]")
            yield Input(placeholder="powershell -enc ... OR /path/to/suspicious.py", id="sandbox_input")
            with Horizontal():
                yield Button("STATIC ANALYSIS", id="btn_static", classes="sandbox-btn")
                yield Button("STRING DUMP", id="btn_strings", classes="sandbox-btn")
                yield Button("ENTROPY CHECK", id="btn_entropy", classes="sandbox-btn")
        yield RichLog(id="sandbox_log", markup=True)
        yield Footer()

    async def on_button_pressed(self, event: Button.Pressed):
        code = self.query_one("#sandbox_input").value.strip()
        if not code:
            return
        
        # Check if file path
        import os
        if os.path.exists(code) and os.path.isfile(code):
            try:
                with open(code, 'r', errors='ignore') as f:
                    code = f.read()
            except:
                pass
        
        if event.button.id == "btn_static":
            self.static_analysis(code)
        elif event.button.id == "btn_strings":
            self.string_dump(code)
        elif event.button.id == "btn_entropy":
            self.entropy_check(code)

    def static_analysis(self, code: str):
        log = self.query_one("#sandbox_log", RichLog)
        
        log.write("\n[bold yellow]Starting Static Heuristics...[/]")
        
        indicators = {
            "Suspicious C2": [r"socket", r"connect", r"http\.client", r"urlread", r"downloadstring"],
            "Persistence": [r"startup", r"registry", r"schtasks", r"cron"],
            "Obfuscation": [r"base64", r"eval", r"exec", r"encode", r"xor"],
            "System Mods": [r"chmod", r"reg add", r"kill", r"rm -rf"]
        }
        
        score = 0
        hits = 0
        
        for name, patterns in indicators.items():
            for pat in patterns:
                if re.search(pat, code, re.IGNORECASE):
                    hits += 1
                    score += 10
                    log.write(f"  [red]⚠ {name}:[/] {pat}")
        
        if hits == 0:
            log.write("  [green]No static IOCs detected.[/]")
        else:
            log.write(f"  [bold red]Threat Score: {score}/100[/]")

    def string_dump(self, code: str):
        log = self.query_one("#sandbox_log", RichLog)
        log.write("\n[bold yellow]Extracting Interesting Strings...[/]")
        
        # Extract ASCII strings > 4 chars
        found = []
        chars = string.ascii_letters + string.digits + "/.:_-"
        curr = ""
        for c in code:
            if c in chars:
                curr += c
            else:
                if len(curr) > 4:
                    found.append(curr)
                curr = ""
        
        # Filter noise
        interesting = [s for s in found if ("http" in s or "/" in s or "." in s) and len(s) > 6]
        
        for s in interesting[:20]:
            log.write(f"  [cyan]{s}[/]")
        
        if not interesting:
            log.write("  [dim]No URLs or paths found.[/]")

    def entropy_check(self, code: str):
        log = self.query_one("#sandbox_log", RichLog)
        
        # Shannon entropy calculation
        if not code: return 0
        entropy = 0
        for x in range(256):
            p_x = float(code.count(chr(x))) / len(code)
            if p_x > 0:
                entropy += - p_x * math.log(p_x, 2)
        
        log.write(f"\n[bold yellow]Shannon Entropy: {entropy:.4f}[/]")
        
        if entropy > 7.5:
            log.write("  [red]HIGH (Packed/Encrypted/Compressed)[/]")
        elif entropy > 5.0:
            log.write("  [yellow]MEDIUM (Possible text/code mix)[/]")
        else:
            log.write("  [green]LOW (Likely plain text/source code)[/]")
