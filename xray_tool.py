"""
Vulnerability X-Ray Tool — Advanced Standalone Scanner
"""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical, Horizontal
from textual.widgets import Header, Footer, Input, Button, RichLog, Static, ProgressBar
from textual.binding import Binding
import re
import json

class XRayTool(Screen):
    """Standalone Vulnerability Assessment Tool"""
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Close"),
        Binding("ctrl+a", "analyze", "Analyze Input"),
        Binding("ctrl+l", "clear_log", "Clear"),
    ]

    CSS = """
    XRayTool {
        background: #0f172a;
    }
    #xray_header {
        dock: top;
        height: auto;
        padding: 1;
        background: #1e293b;
        border-bottom: heavy #ef4444;
    }
    #xray_input {
        margin-bottom: 1;
        border: solid #ef4444;
    }
    #xray_log {
        height: 1fr;
        background: #0f172a;
        border: round #1e293b;
        padding: 1;
        scrollbar-color: #ef4444;
    }
    .xray-btn {
        width: 20;
        background: #ef4444;
        color: white;
        margin-right: 1;
    }
    .xray-btn:hover {
        background: #f87171;
    }
    """

    # Local CVE Database (Simplified for demo, would be loaded from JSON)
    CVE_DB = {
        "ssh": {"OpenSSH 7.2": "CVE-2016-6210", "OpenSSH 8.1": "CVE-2020-14145"},
        "nginx": {"1.14": "CVE-2018-16843", "1.16": "CVE-2019-9511"},
        "apache": {"2.4.49": "CVE-2021-41773", "2.4.50": "CVE-2021-42013"},
        "tomcat": {"9.0.0": "CVE-2020-9484"},
        "wordpress": {"5.8": "CVE-2021-41484"},
        "drupal": {"8.5": "CVE-2018-7600 (Drupalgeddon2)"},
        "php": {"7.4.3": "CVE-2020-7066"}
    }

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="xray_header"):
            yield Static("[bold red]VULNERABILITY SCAN DATA (Paste logs/headers/text)[/]")
            yield Input(placeholder="Server: Apache/2.4.49 ...", id="xray_input")
            with Horizontal():
                yield Button("CVE LOOKUP", id="btn_cve", classes="xray-btn")
                yield Button("CONFIG AUDIT", id="btn_audit", classes="xray-btn")
                yield Button("SECRET SCAN", id="btn_secrets", classes="xray-btn")
        yield RichLog(id="xray_log", markup=True)
        yield ProgressBar(id="progress", show_eta=False)
        yield Footer()

    async def on_button_pressed(self, event: Button.Pressed):
        data = self.query_one("#xray_input").value.strip()
        if not data:
            return
        
        if event.button.id == "btn_cve":
            self.analyze_cve(data)
        elif event.button.id == "btn_audit":
            self.audit_config(data)
        elif event.button.id == "btn_secrets":
            self.scan_secrets(data)

    def analyze_cve(self, data: str):
        log = self.query_one("#xray_log", RichLog)
        progress = self.query_one("#progress", ProgressBar)
        
        log.write(f"\n[bold red]Started CVE Analysis on Input Data...[/]")
        progress.update(total=10, progress=0)

        hits = 0
        
        # Simple keyword matching against DB
        for service, versions in self.CVE_DB.items():
            if service in data.lower():
                log.write(f"  [yellow]Detected Service:[/] {service.upper()}")
                for ver, cve in versions.items():
                    if ver in data:
                        log.write(f"    [bold red]CRITICAL MATCH:[/] {ver} -> {cve}")
                        hits += 1
                    else:
                        # Version guessing
                        pass
        
        if hits == 0:
            log.write("  [green]No known CVEs found in local database for this input.[/]")
        else:
            log.write(f"  [bold red]Found {hits} high-severity vulnerabilities![/]")
        
        progress.update(progress=10)

    def audit_config(self, data: str):
        """Mock audit for common misconfigurations"""
        log = self.query_one("#xray_log", RichLog)
        log.write("\n[bold red]Starting Configuration Audit...[/]")
        
        issues = []
        if "root" in data and "permit" in data.lower():
            issues.append("PermitRootLogin enabled (SSH)")
        if "server_tokens" in data and "on" in data.lower():
            issues.append("Nginx Server Tokens exposed")
        if "debug" in data.lower() and "true" in data.lower():
            issues.append("Debug Mode enabled in production")
        if "indexes" in data.lower() and "on" in data.lower():
            issues.append("Directory Indexing enabled (Apache/Nginx)")
            
        for issue in issues:
            log.write(f"  [red]⚠ MISCONFIG:[/] {issue}")
            
        if not issues:
            log.write("  [green]No obvious misconfigurations detected.[/]")

    def scan_secrets(self, data: str):
        """Regex scan for keys/passwords"""
        log = self.query_one("#xray_log", RichLog)
        
        patterns = {
            "AWS Key": r"AKIA[0-9A-Z]{16}",
            "Private Key": r"-----BEGIN PRIVATE KEY-----",
            "Generic API": r"(api_key|access_token)[\s=:]+([a-zA-Z0-9_\-]+)",
            "Password": r"(password|passwd|pwd)[\s=:]+([^\s]+)"
        }
        
        log.write("\n[bold red]Scanning for Leaked Secrets...[/]")
        found = False
        import re
        for name, pat in patterns.items():
            matches = re.findall(pat, data, re.IGNORECASE)
            for m in matches:
                found = True
                val = m if isinstance(m, str) else m[1]
                log.write(f"  [red]⚠ LEAKED {name.upper()}:[/] {val[:4]}...***")
        
        if not found:
            log.write("  [green]No secrets found.[/]")
