"""
openssl_tool.py - Nextral OpenSSL Toolkit Module

A user-friendly interface for OpenSSL operations:
- Certificate generation
- SSL/TLS testing
- Key generation
- Hash generation
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical, Horizontal, Container
from textual.widgets import Header, Footer, Static, Button, Input, RichLog, Label, Select
from textual.binding import Binding
from textual.reactive import reactive
import asyncio
import sys

sys.path.insert(0, '.')
from tools_locator import is_tool_installed, run_tool


class OpenSSLTool(Screen):
    """OpenSSL Toolkit Interface"""
    
    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("r", "run_operation", "Run"),
        Binding("c", "clear_results", "Clear"),
    ]
    
    CSS = """
    OpenSSLTool {
        background: #0a0a12;
    }
    
    Header {
        background: #0a1a1a;
        color: #81c784;
    }
    
    #openssl_title {
        width: 100%;
        height: 3;
        content-align: center middle;
        background: #0d2a0d;
        color: #81c784;
        text-style: bold;
        border-bottom: solid #2e7d32;
    }
    
    #main_container {
        height: 1fr;
        border: solid #2e7d32;
        margin: 1;
    }
    
    #input_section {
        height: auto;
        border-bottom: solid #1b5e20;
        padding: 1 2;
        background: #050d05;
    }
    
    .input_label {
        color: #a5d6a7;
        margin-bottom: 0;
        text-style: bold;
    }
    
    .input_field {
        background: #0a150a;
        border: solid #2e7d32;
        color: #c8e6c9;
    }
    
    #operation_select {
        margin-bottom: 1;
    }
    
    #param_section {
        height: auto;
        border-bottom: solid #1b5e20;
        padding: 1 2;
        background: #050d05;
    }
    
    #results_section {
        height: 1fr;
        border: solid #2e7d32;
        background: #020502;
    }
    
    #results_log {
        height: 1fr;
        background: #050a05;
        border: solid #1b5e20;
        margin: 1;
        padding: 1;
    }
    
    #status_bar {
        dock: bottom;
        height: 2;
        background: #0a1a1a;
        color: #81c784;
        text-align: center;
    }
    
    #button_row {
        height: auto;
        padding: 1 2;
        background: #050d05;
        border-top: solid #1b5e20;
    }
    
    .action_btn {
        background: #2e7d32;
        color: #c8e6c9;
    }
    
    .action_btn:hover {
        background: #388e3c;
    }
    
    Footer {
        background: #0a1a1a;
        color: #81c784;
    }
    """
    
    OPERATIONS = [
        ("Generate Self-Signed Certificate", "gencert"),
        ("Generate RSA Key Pair", "genkey"),
        ("Generate CSR (Certificate Signing Request)", "gencsr"),
        ("Check SSL Certificate", "checkcert"),
        ("Hash a String/Hash File", "hash"),
        ("Generate Random Data", "rand"),
        ("Show Certificate Info", "showcert"),
        ("Convert Certificate Format", "convert"),
    ]
    
    def __init__(self):
        super().__init__()
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        yield Static("◈ OPENSSL TOOLKIT ◈", id="openssl_title")
        
        with Container(id="main_container"):
            with Container(id="input_section"):
                yield Label("SELECT OPERATION:", classes="input_label")
                yield Select(self.OPERATIONS, id="operation_select", value="gencert")
                
                yield Label("OUTPUT FILE / PATH:", classes="input_label")
                yield Input(
                    id="output_input",
                    placeholder="e.g., server.key, certificate.crt",
                    classes="input_field"
                )
            
            with Container(id="param_section"):
                yield Label("COMMON NAME (CN):", classes="input_label")
                yield Input(
                    id="cn_input",
                    placeholder="e.g., example.com, localhost",
                    classes="input_field"
                )
                
                yield Label("ADDITIONAL OPTIONS:", classes="input_label")
                yield Input(
                    id="options_input",
                    placeholder="-days 365 -nodes -sha256",
                    classes="input_field"
                )
                
                yield Label("INPUT FILE (for check/show):", classes="input_label")
                yield Input(
                    id="input_input",
                    placeholder="e.g., certificate.crt",
                    classes="input_field"
                )
            
            with Container(id="results_section"):
                yield RichLog(id="results_log", markup=True, wrap=True)
            
            with Horizontal(id="button_row"):
                yield Button("▶ RUN OPERATION", id="run_btn", variant="success")
                yield Button("↺ CLEAR", id="clear_btn", variant="default")
                yield Button("✕ CLOSE", id="close_btn", variant="default")
        
        yield Static(id="status_bar")
        yield Footer()
    
    def on_mount(self) -> None:
        self._update_status("[cyan]Select an operation and configure parameters, then press [bold]RUN[/]")
        
        log = self.query_one("#results_log", RichLog)
        log.write("[bold cyan]╔══════════════════════════════════════════════════════════════╗[/]")
        log.write("[bold cyan]║[/]                   [bold white]OPENSSL TOOLKIT[/]                          [bold cyan]║[/]")
        log.write("[bold cyan]╚══════════════════════════════════════════════════════════════╝[/]")
        log.write("")
        log.write("[dim]OpenSSL toolkit for certificate generation, SSL testing, and more.[/]")
        log.write("")
        
        installed, path = is_tool_installed("openssl")
        if not installed:
            log.write("[bold red]⚠ OPENSSL NOT FOUND![/]")
            log.write("[dim]Please install openssl or configure path in Settings.[/]")
        else:
            log.write(f"[green]✓ OpenSSL found: {path}[/]")
            log.write("")
    
    def _update_status(self, text: str) -> None:
        try:
            self.query_one("#status_bar", Static).update(text)
        except:
            pass
    
    def action_close(self) -> None:
        self.app.pop_screen()
    
    def action_run_operation(self) -> None:
        operation = self.query_one("#operation_select", Select).value
        if not operation:
            self._update_status("[red]Error: Please select an operation![/]")
            return
        
        installed, path = is_tool_installed("openssl")
        if not installed:
            log = self.query_one("#results_log", RichLog)
            log.write("[bold red]Error: OpenSSL is not installed or not found![/]")
            return
        
        log = self.query_one("#results_log", RichLog)
        log.write("")
        log.write(f"[bold green]>>> Running: {operation}[/]")
        log.write("")
        
        asyncio.create_task(self._run_operation(operation))
    
    async def _run_operation(self, operation: str) -> None:
        log = self.query_one("#results_log", RichLog)
        
        output = self.query_one("#output_input", Input).value.strip()
        cn = self.query_one("#cn_input", Input).value.strip()
        options = self.query_one("#options_input", Input).value.strip()
        input_file = self.query_one("#input_input", Input).value.strip()
        
        if operation == "gencert":
            if not output:
                output = "server.crt"
            key_file = output.replace(".crt", ".key")
            
            args = ["req", "-x509", "-newkey", "rsa:4096", "-keyout", key_file, "-out", output, "-days", "365", "-nodes"]
            if cn:
                args.extend(["-subj", f"/CN={cn}/C=US/ST=State/L=City/O=Organization"])
            if options:
                args.extend(options.split())
            
            returncode, stdout, stderr = await run_tool("openssl", args, timeout=60)
            
            if returncode == 0:
                log.write(f"[green]✓ Certificate generated successfully![/]")
                log.write(f"[dim]Certificate: {output}[/]")
                log.write(f"[dim]Private Key: {key_file}[/]")
                log.write("")
                log.write("[yellow]IMPORTANT: Keep your private key secure![/]")
            else:
                log.write(f"[red]Error: {stderr}[/]")
        
        elif operation == "genkey":
            if not output:
                output = "private.key"
            
            args = ["genrsa", "-out", output, "4096"]
            if options:
                args.extend(options.split())
            
            returncode, stdout, stderr = await run_tool("openssl", args, timeout=60)
            
            if returncode == 0:
                log.write(f"[green]✓ RSA key generated successfully![/]")
                log.write(f"[dim]Key file: {output}[/]")
                log.write("")
                log.write("[yellow]IMPORTANT: Keep your private key secure![/]")
            else:
                log.write(f"[red]Error: {stderr}[/]")
        
        elif operation == "gencsr":
            if not output:
                output = "request.csr"
            
            args = ["req", "-new", "-newkey", "rsa:4096", "-keyout", "private.key", "-out", output, "-nodes"]
            if cn:
                args.extend(["-subj", f"/CN={cn}/C=US/ST=State/L=City/O=Organization"])
            if options:
                args.extend(options.split())
            
            returncode, stdout, stderr = await run_tool("openssl", args, timeout=60)
            
            if returncode == 0:
                log.write(f"[green]✓ CSR generated successfully![/]")
                log.write(f"[dim]CSR file: {output}[/]")
                log.write(f"[dim]Private Key: private.key[/]")
            else:
                log.write(f"[red]Error: {stderr}[/]")
        
        elif operation == "checkcert":
            if not input_file:
                log.write("[red]Error: Please specify input certificate file![/]")
                return
            
            args = ["x509", "-in", input_file, "-text", "-noout"]
            
            returncode, stdout, stderr = await run_tool("openssl", args, timeout=30)
            
            if returncode == 0:
                log.write(f"[green]Certificate Info for {input_file}:[/]")
                log.write("")
                log.write(stdout)
            else:
                log.write(f"[red]Error: {stderr}[/]")
        
        elif operation == "hash":
            data = self.query_one("#options_input", Input).value.strip() or "test"
            
            args = ["dgst", "-sha256"]
            args.extend(data.split())
            
            returncode, stdout, stderr = await run_tool("openssl", args, timeout=30)
            
            if returncode == 0:
                log.write(f"[green]SHA256 Hash:[/]")
                log.write(stdout)
            else:
                log.write(f"[red]Error: {stderr}[/]")
        
        elif operation == "rand":
            if not output:
                output = "random.bin"
            
            bytes_count = self.query_one("#options_input", Input).value.strip() or "32"
            
            args = ["rand", "-out", output, "-base64", bytes_count]
            
            returncode, stdout, stderr = await run_tool("openssl", args, timeout=30)
            
            if returncode == 0:
                log.write(f"[green]✓ Random data generated![/]")
                log.write(f"[dim]File: {output}[/]")
                log.write(f"[dim]Bytes: {bytes_count}[/]")
            else:
                log.write(f"[red]Error: {stderr}[/]")
        
        elif operation == "showcert":
            if not input_file:
                log.write("[red]Error: Please specify input certificate file![/]")
                return
            
            args = ["x509", "-in", input_file, "-noout", "-subject", "-issuer", "-dates", "-serial"]
            
            returncode, stdout, stderr = await run_tool("openssl", args, timeout=30)
            
            if returncode == 0:
                log.write(f"[green]Certificate Summary for {input_file}:[/]")
                log.write("")
                log.write(stdout)
            else:
                log.write(f"[red]Error: {stderr}[/]")
        
        else:
            log.write(f"[yellow]Operation '{operation}' not yet implemented.[/]")
        
        self._update_status("[green]Operation complete.[/]")
    
    def action_clear_results(self) -> None:
        log = self.query_one("#results_log", RichLog)
        log.clear()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        
        if btn_id == "run_btn":
            self.action_run_operation()
        elif btn_id == "clear_btn":
            self.action_clear_results()
        elif btn_id == "close_btn":
            self.action_close()
