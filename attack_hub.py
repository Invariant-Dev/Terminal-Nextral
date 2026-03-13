"""
attack_hub.py - Strike Command Dashboard
Professional, clear interface for offensive security operations.
"""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical, Horizontal, Grid, Container, ScrollableContainer
from textual.widgets import Header, Footer, Static, Button, RichLog, Label, Input, ListView, ListItem
from textual.binding import Binding
from textual.reactive import reactive
import json
from pathlib import Path
from datetime import datetime

LOOT_FILE = Path(__file__).parent / "attack_loot.json"

ATTACK_TOOLS = [
    {"id": "nmap", "name": "Nmap Scanner", "icon": "[*]", "desc": "Network discovery & port scanning", "category": "RECON"},
    {"id": "nikto", "name": "Nikto Scanner", "icon": "[$]", "desc": "Web vulnerability assessment", "category": "RECON"},
    {"id": "osint", "name": "OSINT Tool", "icon": "[O]", "desc": "Open-source intelligence", "category": "RECON"},
    {"id": "xray", "name": "Vuln Scanner", "icon": "[X]", "desc": "Advanced vulnerability analysis", "category": "RECON"},
    
    {"id": "msf", "name": "Metasploit Bridge", "icon": "[M]", "desc": "MSF RPC interface & sessions", "category": "ELITE"},
    {"id": "venomous", "name": "Venomous Factory", "icon": "[V]", "desc": "Evasive payload generation", "category": "ELITE"},
    {"id": "burp", "name": "Proxy Intercept", "icon": "[B]", "desc": "HTTP/S Proxy & Repeater", "category": "ELITE"},
    
    {"id": "hydra", "name": "Hydra", "icon": "[H]", "desc": "Password brute-forcer", "category": "ATTACK"},
    {"id": "valkyrie", "name": "Valkyrie", "icon": "[V]", "desc": "Hash identifier & cracker", "category": "ATTACK"},
    {"id": "shell_lab", "name": "Shell Lab", "icon": "[S]", "desc": "Reverse shell & payload generator", "category": "ATTACK"},
    {"id": "stun", "name": "WhatsApp IP Tracer", "icon": "[U]", "desc": "Find WhatsApp server IPs", "category": "ATTACK"},
    
    {"id": "netcat", "name": "Netcat", "icon": "[N]", "desc": "TCP/UDP operations", "category": "UTILITIES"},
    {"id": "tcpdump", "name": "Tcpdump", "icon": "[T]", "desc": "Packet capture & sniffer", "category": "UTILITIES"},
    {"id": "exif", "name": "Exif Tool", "icon": "[E]", "desc": "Metadata forensic analyzer", "category": "UTILITIES"},
]


class AttackHub(Screen):
    """Strike Command - Professional Offensive Security Dashboard"""
    
    BINDINGS = [
        Binding("escape", "return_to_terminal", "Back to Terminal"),
        Binding("h", "show_help", "Help"),
    ]

    current_target = reactive("")
    stealth_level = reactive(0)
    
    CSS = """
AttackHub {
    background: #050508;
}

#hub_header {
    dock: top;
    height: 4;
    background: #0a0a12;
    border-bottom: heavy #ff0055;
}

#header_row1 {
    height: 1;
    content-align: left middle;
    padding: 0 2;
    background: #0a0a12;
}

#header_row2 {
    height: 1;
    content-align: left middle;
    padding: 0 2;
}

#header_row3 {
    height: 1;
    content-align: left middle;
    padding: 0 2;
}

.header-title {
    color: #ff0055;
    text-style: bold;
}

.header-target {
    color: #00e5ff;
}

.header-status {
    color: #8888aa;
}

#main_content {
    height: 1fr;
}

#tools_panel {
    width: 55%;
    border-right: heavy #1a1a2e;
    padding: 1;
}

#info_panel {
    width: 45%;
    padding: 1;
}

.section-header {
    color: #00e5ff;
    text-style: bold;
    margin-bottom: 1;
    padding: 0 1;
    background: #0a0a12;
    border-left: thick #00e5ff;
}

#target_box {
    height: auto;
    border: solid #1a1a2e;
    padding: 1;
    margin-bottom: 1;
    background: #0a0a12;
}

#target_input {
    margin-bottom: 1;
    background: #111122;
    border: solid #1a1a2e;
    color: #00e5ff;
    transition: border 0.3s;
}

#target_input:focus {
    border: solid #ff0055;
}

#loot_list {
    height: 150;
    background: #050508;
    border: solid #1a1a2e;
}

.loot-item {
    padding: 0 1;
    border-bottom: solid #1a1a2e;
    color: #00e5ff;
}

#mission_log {
    height: 1fr;
    background: #050508;
    border: solid #1a1a2e;
    color: #bbbbbb;
}

#help_panel {
    height: 1fr;
    background: #050508;
    border: solid #1a1a2e;
    padding: 1;
}

#help_text {
    color: #8888aa;
}

.tool-grid {
    layout: grid;
    grid-size: 2;
    grid-gutter: 1 1;
}

.tool-btn {
    width: 100%;
    height: 3;
    background: #1a1a2e;
    border: solid #1a1a2e;
    color: #bbbbbb;
    transition: background 0.3s, color 0.3s, border 0.3s;
}

.tool-btn:hover {
    background: #ff0055;
    border: solid #ff0055;
    color: #ffffff;
}

Button {
    background: #1a1a2e;
    border: solid #1a1a2e;
    color: #bbbbbb;
    transition: background 0.3s, color 0.3s, border 0.3s;
}

Button:hover {
    background: #00e5ff;
    border: solid #00e5ff;
    color: #000000;
}

Input {
    background: #111122;
    border: solid #1a1a2e;
    color: #00e5ff;
}

Input:focus {
    border: solid #ff0055;
    color: #ffffff;
}

RichLog {
    background: #050508;
    border: solid #1a1a2e;
}

ListView {
    background: #050508;
    border: solid #1a1a2e;
}

ListItem {
    background: #050508;
    color: #8888aa;
}

Header {
    background: #0a0a12;
    color: #00e5ff;
}

Footer {
    background: #0a0a12;
    color: #8888aa;
}
"""

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        with Container(id="hub_header"):
            with Horizontal(id="header_row1"):
                yield Static("[bold #ff4444]STRIKE COMMAND[/] | Offensive Security Dashboard", classes="header-title")
            with Horizontal(id="header_row2"):
                yield Static("[dim]TARGET:[/] ", classes="header-status")
                yield Static("--", id="header_target_display", classes="header-target")
                yield Static("  [dim]LOOT:[/] ", classes="header-status")
                yield Static("0 targets", id="header_loot_count", classes="header-status")
            with Horizontal(id="header_row3"):
                yield Static("[dim]Keys: [bold]Enter[/]=Launch Tool  [bold]H[/]=Help  [bold]Esc[/]=Return to Terminal", classes="header-status")
        
        with Horizontal(id="main_content"):
            with ScrollableContainer(id="tools_panel"):
                yield Label("[bold #cc4444]== RECONNAISSANCE ==[/]", classes="section-header")
                with Grid(classes="tool-grid"):
                    for tool in [t for t in ATTACK_TOOLS if t["category"] == "RECON"]:
                        yield Button(
                            f"{tool['icon']} {tool['name']}",
                            id=tool['id'],
                            classes="tool-btn"
                        )
                
                yield Label("[bold #cc4444]== ELITE OPERATIONS ==[/]", classes="section-header")
                with Grid(classes="tool-grid"):
                    for tool in [t for t in ATTACK_TOOLS if t["category"] == "ELITE"]:
                        yield Button(
                            f"{tool['icon']} {tool['name']}",
                            id=tool['id'],
                            classes="tool-btn"
                        )
                
                yield Label("[bold #cc4444]== ATTACK & EXPLOITATION ==[/]", classes="section-header")
                with Grid(classes="tool-grid"):
                    for tool in [t for t in ATTACK_TOOLS if t["category"] == "ATTACK"]:
                        yield Button(
                            f"{tool['icon']} {tool['name']}",
                            id=tool['id'],
                            classes="tool-btn"
                        )
                
                yield Label("[bold #cc4444]== UTILITIES ==[/]", classes="section-header")
                with Grid(classes="tool-grid"):
                    for tool in [t for t in ATTACK_TOOLS if t["category"] == "UTILITIES"]:
                        yield Button(
                            f"{tool['icon']} {tool['name']}",
                            id=tool['id'],
                            classes="tool-btn"
                        )
            
            with Vertical(id="info_panel"):
                yield Label("[bold #cc4444]TARGET SELECTION[/]", classes="section-header")
                with Container(id="target_box"):
                    yield Input(id="target_input", placeholder="Enter target IP or hostname...")
                    with Horizontal():
                        yield Button("SET TARGET", id="set_target_btn")
                        yield Button("CLEAR", id="clear_target_btn")
                
                yield Label("[bold #cc4444]LOOT DATABASE (Discovered Targets)[/]", classes="section-header")
                yield ListView(id="loot_list")
                
                yield Label("[bold #cc4444]MISSION LOG[/]", classes="section-header")
                yield RichLog(id="mission_log", markup=True)

        yield Footer()

    def on_mount(self):
        self._load_loot()
        self._update_display()
        log = self.query_one("#mission_log", RichLog)
        log.write("[bold #ff4444]== STRIKE COMMAND INITIALIZED ==[/]")
        log.write("")
        log.write("[dim]1. Set a target using the input field above[/]")
        log.write("[dim]2. Click any tool button to launch it[/]")
        log.write("[dim]3. Press [bold]H[/] for help at any time[/]")
        log.write("")
        log.write("[dim]Ready for operations.[/]")

    def _update_display(self):
        target = self.current_target or "--"
        self.query_one("#header_target_display", Static).update(f"[white]{target}[/]")
        
        loot_count = 0
        if LOOT_FILE.exists():
            try:
                with open(LOOT_FILE, 'r') as f:
                    data = json.load(f)
                    loot_count = len(data.get("targets", []))
            except:
                pass
        self.query_one("#header_loot_count", Static).update(f"[white]{loot_count} targets[/]")

    def _load_loot(self):
        loot_list = self.query_one("#loot_list", ListView)
        loot_list.clear()
        
        if LOOT_FILE.exists():
            try:
                with open(LOOT_FILE, 'r') as f:
                    data = json.load(f)
                    for target in data.get("targets", []):
                        ip = target.get("ip", "")
                        ports_list = list(target.get("ports", []))[:5]
                        ports = ", ".join(map(str, ports_list))
                        loot_list.append(ListItem(
                            Static(f"[bold #ff6666]::[/] [white]{ip}[/]  [dim]{ports}[/]", classes="loot-item")
                        ))
            except:
                pass

    def on_input_submitted(self, event: Input.Submitted):
        if event.input.id == "target_input":
            if event.input.value.strip():
                self.current_target = event.input.value.strip()
                self._update_display()
                log = self.query_one("#mission_log", RichLog)
                log.write(f"[bold #ff6644]>> TARGET SET:[/] {self.current_target}")
                event.input.value = ""

    def on_button_pressed(self, event: Button.Pressed):
        bid = event.button.id
        
        if bid == "set_target_btn":
            target_inp = self.query_one("#target_input", Input)
            if target_inp.value.strip():
                self.current_target = target_inp.value.strip()
                self._update_display()
                log = self.query_one("#mission_log", RichLog)
                log.write(f"[bold #ff6644]>> TARGET SET:[/] {self.current_target}")
                target_inp.value = ""
        
        elif bid == "clear_target_btn":
            self.current_target = ""
            self._update_display()
            log = self.query_one("#mission_log", RichLog)
            log.write("[dim]>> Target cleared[/]")
        
        else:
            tool_id = bid
            tool_info = next((t for t in ATTACK_TOOLS if t["id"] == tool_id), None)
            
            if tool_info:
                log = self.query_one("#mission_log", RichLog)
                log.write(f"[bold #ff6644]>> LAUNCHING:[/] {tool_info['name']} - {tool_info['desc']}")
                
                if hasattr(self.app, "dispatch_tool"):
                    self.app.dispatch_tool(tool_id, self.current_target)

    def action_return_to_terminal(self):
        for screen in self.app.screen_stack:
            if hasattr(screen, "switch_mode"):
                from nextral import Mode
                screen.switch_mode(Mode.GENERAL)
                break
        self.app.pop_screen()

    def action_show_help(self):
        log = self.query_one("#mission_log", RichLog)
        log.clear()
        log.write("[bold #ff4444]== STRIKE COMMAND HELP ==[/]")
        log.write("")
        log.write("[bold #cc4444]QUICK START:[/]")
        log.write("  1. Enter target IP/hostname in the input field")
        log.write("  2. Click [bold]SET TARGET[/] to save it")
        log.write("  3. Click any tool button to launch that tool")
        log.write("  4. The tool will use your selected target automatically")
        log.write("")
        log.write("[bold #cc4444]KEYBOARD SHORTCUTS:[/]")
        log.write("  [bold]Esc[/]   - Return to terminal")
        log.write("  [bold]H[/]     - Show this help")
        log.write("  [bold]Enter[/] - In target field, set the target")
        log.write("")
        log.write("[bold #cc4444]TOOL CATEGORIES:[/]")
        log.write("  [bold #cc4444]RECON:[/]     Nmap, Nikto, OSINT, Vuln Scanner")
        log.write("  [bold #cc4444]ATTACK:[/]    Hydra, Valkyrie, Shell Lab")
        log.write("  [bold #cc4444]UTILITIES:[/] Netcat, Tcpdump, Exif")
        log.write("")
        log.write("[dim]Discovered targets are saved to the Loot Database automatically.[/]")
