"""
OSINT Recon Suite — Advanced Standalone Intelligence Tool
"""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical, Horizontal
from textual.widgets import Header, Footer, Input, Button, RichLog, Static, ProgressBar
from textual.binding import Binding
import asyncio
import socket
import ssl
import json
import re
from urllib.request import urlopen, Request

# Optional: requests, dnspython for cleaner code, but using stdlib where possible for portability
try:
    import dns.resolver
    DNS_AVAIL = True
except ImportError:
    DNS_AVAIL = False

class OSINTTool(Screen):
    """Advanced OSINT Reconnaissance Tool"""
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Close"),
        Binding("ctrl+r", "run_recon", "Run Recon"),
    ]

    CSS = """
    OSINTTool {
        background: #0f172a;
    }
    #osint_header {
        dock: top;
        height: auto;
        padding: 1;
        background: #1e293b;
        border-bottom: heavy #3b82f6;
    }
    #osint_input {
        margin-bottom: 1;
        border: solid #3b82f6;
    }
    #osint_log {
        height: 1fr;
        background: #0f172a;
        border: round #1e293b;
        padding: 1;
        scrollbar-color: #3b82f6;
    }
    .recon-btn {
        width: 20;
        background: #3b82f6;
        color: white;
        margin-right: 1;
    }
    .recon-btn:hover {
        background: #60a5fa;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="osint_header"):
            yield Static("[bold blue]TARGET DOMAIN / IP[/]")
            yield Input(placeholder="example.com", id="osint_input")
            with Horizontal():
                yield Button("RUN FULL RECON", id="btn_run", classes="recon-btn")
                yield Button("WHOIS ONLY", id="btn_whois", classes="recon-btn")
                yield Button("DNS ONLY", id="btn_dns", classes="recon-btn")
        yield RichLog(id="osint_log", markup=True)
        yield ProgressBar(id="progress", show_eta=False)
        yield Footer()

    async def on_button_pressed(self, event: Button.Pressed):
        target = self.query_one("#osint_input").value.strip()
        if not target:
            return
        
        if event.button.id == "btn_run":
            await self.run_recon(target, full=True)
        elif event.button.id == "btn_whois":
            await self.run_recon(target, mode="whois")
        elif event.button.id == "btn_dns":
            await self.run_recon(target, mode="dns")

    async def run_recon(self, target: str, full=False, mode=None):
        log = self.query_one("#osint_log", RichLog)
        prog = self.query_one("#progress", ProgressBar)
        
        log.clear()
        prog.update(total=100, progress=0)
        
        log.write(f"[bold blue]Starting OSINT Recon on: {target}[/]")
        log.write(f"[dim]{'-'*50}[/]")

        # 1. DNS Resolution
        if full or mode == "dns":
            prog.update(progress=20)
            log.write("\n[bold cyan]1. DNS Enumeration[/]")
            try:
                # Basic A record
                ip = socket.gethostbyname(target)
                log.write(f"  [green]A Record (IP):[/] {ip}")
                
                # Reverse DNS
                try:
                    rev = socket.gethostbyaddr(ip)
                    log.write(f"  [green]Reverse DNS:[/] {rev[0]}")
                except:
                    pass

                # Expanded DNS if dnspython available
                if DNS_AVAIL:
                    try:
                        for rtype in ['MX', 'NS', 'TXT', 'SOA']:
                            answers = dns.resolver.resolve(target, rtype)
                            for rdata in answers:
                                log.write(f"  [green]{rtype}:[/] {rdata.to_text()}")
                    except:
                        pass
                else:
                    log.write("  [dim](Install 'dnspython' for full record enumeration)[/]")

            except Exception as e:
                log.write(f"  [red]DNS Error: {e}[/]")

        # 2. Port Scan (Fast)
        if full:
            prog.update(progress=40)
            log.write("\n[bold cyan]2. Service Discovery (Top Ports)[/]")
            common_ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 3306, 3389, 5432, 8080, 8443]
            open_ports = []
            
            async def scan_port(port):
                try:
                    connector = asyncio.open_connection(target, port)
                    _, writer = await asyncio.wait_for(connector, timeout=0.5)
                    writer.close()
                    await writer.wait_closed()
                    return port
                except:
                    return None

            results = await asyncio.gather(*[scan_port(p) for p in common_ports])
            for p in results:
                if p:
                    log.write(f"  [green]OPEN:[/] {p}")
                    open_ports.append(p)
            
            if not open_ports:
                log.write("  [dim]No common ports found open.[/]")
        
        # 3. HTTP Headers & Security headers
        if full:
            prog.update(progress=60)
            log.write("\n[bold cyan]3. Web Technology Analysis[/]")
            try:
                # Try HTTPS then HTTP
                url = f"https://{target}"
                req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                try:
                    resp = urlopen(req, timeout=3)
                except:
                    url = f"http://{target}"
                    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    resp = urlopen(req, timeout=3)
                
                headers = dict(resp.headers)
                log.write(f"  [yellow]Server:[/] {headers.get('Server', 'Unknown')}")
                log.write(f"  [yellow]X-Powered-By:[/] {headers.get('X-Powered-By', 'Not exposed')}")
                
                # Check for security headers
                sec_headers = {
                    'Strict-Transport-Security': 'HSTS',
                    'Content-Security-Policy': 'CSP', 
                    'X-Frame-Options': 'X-Frame',
                    'X-XSS-Protection': 'XSS-Prot'
                }
                
                log.write("  [white]Security Configuration:[/]")
                for h, name in sec_headers.items():
                    if h in headers:
                        log.write(f"    [green]✓ {name} present[/]")
                    else:
                        log.write(f"    [red]✗ {name} missing[/]")
                        
            except Exception as e:
                log.write(f"  [red]Web Probe Failed: {e}[/]")

        # 4. WHOIS (via RDAP or simple socket)
        if full or mode == "whois":
            prog.update(progress=80)
            log.write("\n[bold cyan]4. WHOIS / Registration[/]")
            try:
                # Simple WHOIS fallback
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(2)
                s.connect(("whois.iana.org", 43))
                s.send(f"{target}\r\n".encode())
                
                response = b""
                while True:
                    data = s.recv(4096)
                    if not data: break
                    response += data
                s.close()
                
                # Parse key info
                text = response.decode(errors='ignore')
                for line in text.split('\n'):
                    if ':' in line:
                        k, v = line.split(':', 1)
                        if k.strip().lower() in ['registrar', 'creation date', 'expiry date', 'registrant organization']:
                            log.write(f"  [white]{k.strip()}:[/] {v.strip()}")
            except Exception as e:
                log.write(f"  [red]WHOIS lookup failed: {e}[/]")

        prog.update(progress=100)
        log.write("\n[bold green]Scan Complete.[/]")

