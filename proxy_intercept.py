"""
Nextral Proxy Intercept — proxy_intercept.py
HTTP/S proxy interceptor using mitmdump in the background.
It mimics Burp Suite's Interceptor functionality.
Requires mitmproxy: pip install mitmproxy
"""
import os
import sys
import tempfile
import threading
import subprocess
import asyncio
import json
import time
from pathlib import Path
from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical, Horizontal, Container
from textual.widgets import Header, Footer, Static, Button, RichLog, Label, Input, ListView, ListItem, TextArea
from textual.binding import Binding
from textual.reactive import reactive

try:
    import mitmproxy
    MITM_AVAILABLE = True
except ImportError:
    MITM_AVAILABLE = False

# We'll communicate with the mitmdump process via a JSON line log file
PROXY_LOG_FILE = Path(tempfile.gettempdir()) / "nextral_proxy_log.json"

# Mitmproxy Addon script to write flows to a file
MITM_ADDON_SCRIPT = """
import json
from mitmproxy import http

class NextralLogger:
    def __init__(self, logfile):
        self.logfile = logfile
        # Clear log on start
        with open(self.logfile, 'w') as f:
            f.write("")

    def response(self, flow: http.HTTPFlow):
        data = {
            "id": flow.id,
            "method": flow.request.method,
            "url": flow.request.url,
            "status": flow.response.status_code,
            "req_headers": dict(flow.request.headers),
            "res_headers": dict(flow.response.headers),
            "req_content": flow.request.content.decode('utf-8', 'ignore') if flow.request.content else "",
            "res_content": flow.response.content.decode('utf-8', 'ignore') if flow.response.content else "",
        }
        with open(self.logfile, 'a') as f:
            f.write(json.dumps(data) + "\\n")

addons = [NextralLogger('%s')]
"""

class ProxyInterceptScreen(Screen):
    """Proxy Intercept Interface"""

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Close"),
        Binding("c", "clear_history", "Clear History"),
    ]

    CSS = """
    ProxyInterceptScreen {
        background: #050508;
    }
    
    #proxy_header {
        dock: top;
        height: 5;
        background: #0a0a12;
        border-bottom: heavy #00e5ff;
        padding: 0 1;
    }
    
    .proxy-title {
        color: #00e5ff;
        text-style: bold;
        font-size: 140%;
    }
    
    .proxy-subtitle {
        color: #8888aa;
    }
    
    #control_panel {
        layout: horizontal;
        height: 3;
        margin-top: 1;
        align: left middle;
    }
    
    .proxy-input {
        background: #0a0a12;
        border: solid #1a1a2e;
        color: #00e5ff;
        width: 15;
        transition: border 0.3s;
    }
    
    .proxy-input:focus {
        border: solid #00e5ff;
    }
    
    .proxy-btn {
        background: #1a1a2e;
        border: solid #1a1a2e;
        color: #bbbbbb;
        min-width: 15;
        transition: background 0.3s, color 0.3s, border 0.3s;
    }
    
    .proxy-btn:hover {
        background: #00e5ff;
        color: #000000;
        border: solid #00e5ff;
    }
    
    #main_split {
        height: 1fr;
        layout: horizontal;
    }
    
    #history_panel {
        width: 30%;
        border-right: heavy #1a1a2e;
        padding: 1;
    }
    
    #details_panel {
        width: 70%;
        padding: 1;
        layout: vertical;
    }
    
    .section-label {
        color: #00e5ff;
        text-style: bold;
        background: #0a0a12;
        padding: 0 1;
        margin-bottom: 1;
        border-left: thick #00e5ff;
    }
    
    #flow_list {
        height: 1fr;
        border: solid #1a1a2e;
        background: #050508;
    }
    
    .flow-item {
        color: #88bbff;
        padding: 0 1;
    }
    
    .flow-item-err {
        color: #ff0055;
        padding: 0 1;
    }
    
    TextArea {
        height: 1fr;
        border: solid #1a1a2e;
        background: #050508;
        color: #00e5ff;
        transition: border 0.3s;
    }
    
    TextArea:focus {
        border: solid #00e5ff;
    }
    
    #details_split {
        height: 1fr;
        layout: horizontal;
    }
    
    .half-pane {
        width: 1fr;
        padding: 0 1;
    }
    """

    proxy_running = reactive(False)
    flows = reactive([])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.proxy_process = None
        self.log_thread = None
        self.stop_logging = threading.Event()
        self.flow_data = {}
        
        # Write the addon script
        self.addon_path = Path(tempfile.gettempdir()) / "nextral_proxy_addon.py"
        script_content = MITM_ADDON_SCRIPT % str(PROXY_LOG_FILE).replace('\\', '\\\\')
        with open(self.addon_path, "w") as f:
            f.write(script_content)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        with Container(id="proxy_header"):
            yield Static("🌐 BURP-TERMINAL (PROXY INTERCEPT) 🌐", classes="proxy-title")
            yield Static("Intercept and edit HTTP/HTTPS requests on the fly.", classes="proxy-subtitle")
            
            with Horizontal(id="control_panel"):
                yield Label("Port:", style="margin-top: 1; margin-right: 1;")
                yield Input(value="8080", id="proxy_port", classes="proxy-input")
                yield Button("START PROXY", id="btn_toggle_proxy", classes="proxy-btn")
                yield Button("REPEATER", id="btn_repeater", classes="proxy-btn")

        if not MITM_AVAILABLE:
            with Vertical(classes="msf-missing-pkg", style="padding: 2; align: center middle; height: 1fr;"):
                yield Static("[bold red]mitmproxy is not installed.[/]")
                yield Static("Please run: [bold cyan]pip install mitmproxy[/]")
            yield Footer()
            return

        with Horizontal(id="main_split"):
            with Vertical(id="history_panel"):
                yield Label("HTTP HISTORY", classes="section-label")
                yield ListView(id="flow_list")
                
            with Vertical(id="details_panel"):
                yield Label("REQUEST / RESPONSE VIEWER", classes="section-label")
                with Horizontal(id="details_split"):
                    with Vertical(classes="half-pane"):
                        yield Label("Request", classes="section-label")
                        yield TextArea(id="req_view", read_only=False, language="http")
                    with Vertical(classes="half-pane"):
                        yield Label("Response", classes="section-label")
                        yield TextArea(id="res_view", read_only=True, language="json")

        yield Footer()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_toggle_proxy":
            if self.proxy_running:
                self.stop_proxy()
            else:
                await self.start_proxy()
        elif event.button.id == "btn_repeater":
            self.send_repeater_request()

    async def start_proxy(self) -> None:
        port = self.query_one("#proxy_port", Input).value
        
        # mitmdump command
        cmd = ["mitmdump", "-p", port, "-s", str(self.addon_path)]
        
        try:
            self.proxy_process = await asyncio.create_subprocess_exec(
                *cmd, 
                stdout=asyncio.subprocess.DEVNULL, 
                stderr=asyncio.subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            self.proxy_running = True
            
            btn = self.query_one("#btn_toggle_proxy", Button)
            btn.label = "STOP PROXY"
            btn.variant = "error"
            self.query_one("#proxy_port", Input).disabled = True
            
            # Start loop to read log file
            self.stop_logging.clear()
            self.log_thread = threading.Thread(target=self._tail_log_file, daemon=True)
            self.log_thread.start()
            
            self.app.notify(f"Proxy started on port {port}", severity="information")
        except Exception as e:
            self.app.notify(f"Failed to start proxy: {e}", severity="error")

    def stop_proxy(self) -> None:
        if self.proxy_process:
            self.proxy_process.terminate()
            self.proxy_process = None
            
        self.stop_logging.set()
        self.proxy_running = False
        
        btn = self.query_one("#btn_toggle_proxy", Button)
        btn.label = "START PROXY"
        btn.variant = "default"
        self.query_one("#proxy_port", Input).disabled = False

        self.app.notify("Proxy stopped", severity="information")

    def _tail_log_file(self) -> None:
        # Create empty if not exists
        open(PROXY_LOG_FILE, 'a').close()
        
        last_size = os.path.getsize(PROXY_LOG_FILE)
        
        with open(PROXY_LOG_FILE, 'r') as f:
            # Go to end of file
            f.seek(0, 2)
            while not self.stop_logging.is_set():
                curr_size = os.path.getsize(PROXY_LOG_FILE)
                if curr_size <= last_size:
                    time.sleep(0.5)
                    continue
                
                # Burst read
                lines = f.readlines()
                if not lines:
                    time.sleep(0.5)
                    continue
                
                last_size = f.tell()
                for line in lines:
                    try:
                        data = json.loads(line)
                        self.app.call_from_thread(self._add_flow, data)
                    except Exception:
                        pass

    def _add_flow(self, data: dict) -> None:
        flow_id = data["id"]
        self.flow_data[flow_id] = data
        
        # Memory capping
        if len(self.flow_data) > 500:
            oldest_id = next(iter(self.flow_data))
            del self.flow_data[oldest_id]
            # Remove from list view. 
            lst = self.query_one("#flow_list", ListView)
            if len(lst.children) > 500:
                lst.children[-1].remove()
        
        status = data["status"]
        method = data["method"]
        url = data["url"]
        
        # Shorten URL
        if len(url) > 50:
            url = url[:47] + "..."
            
        style_class = "flow-item"
        if status >= 400:
            style_class = "flow-item-err"
            
        display_text = f"[{status}] {method} {url}"
        
        lst = self.query_one("#flow_list", ListView)
        item = ListItem(Static(display_text, classes=style_class), name=flow_id)
        # Insert at top
        lst.insert(0, item)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        flow_id = event.item.name
        if not flow_id or flow_id not in self.flow_data:
            return
            
        data = self.flow_data[flow_id]
        
        # Format Request
        req_text = f"{data['method']} {data['url']} HTTP/1.1\n"
        for k, v in data['req_headers'].items():
            req_text += f"{k}: {v}\n"
        req_text += "\n" + data['req_content']
        
        self.query_one("#req_view", TextArea).text = req_text
        
        # Format Response
        res_text = f"HTTP/1.1 {data['status']}\n"
        for k, v in data['res_headers'].items():
            res_text += f"{k}: {v}\n"
        res_text += "\n" + data['res_content']
        
        self.query_one("#res_view", TextArea).text = res_text

    def send_repeater_request(self) -> None:
        """Send the modified request directly using Python requests."""
        raw_req = self.query_one("#req_view", TextArea).text
        if not raw_req: return
        
        try:
            import requests
            lines = raw_req.split('\n')
            if not lines: return
            
            req_line = lines[0].split(' ')
            if len(req_line) < 2: return
            
            method = req_line[0]
            url = req_line[1]
            
            headers = {}
            body = ""
            in_body = False
            
            for line in lines[1:]:
                if in_body:
                    body += line + "\n"
                elif line.strip() == "":
                    in_body = True
                else:
                    k, v = line.split(":", 1)
                    headers[k.strip()] = v.strip()
                    
            # Add proxy if running so we see it in our own log, or bypass
            proxies = {}
            if self.proxy_running:
                port = self.query_one("#proxy_port", Input).value
                proxies = {
                    "http": f"http://127.0.0.1:{port}",
                    "https": f"http://127.0.0.1:{port}",
                }
                
            res = requests.request(method, url, headers=headers, data=body, proxies=proxies, verify=False)
            
            res_text = f"HTTP/1.1 {res.status_code}\n"
            for k, v in res.headers.items():
                res_text += f"{k}: {v}\n"
            res_text += "\n" + res.text
            
            self.query_one("#res_view", TextArea).text = res_text
            self.app.notify("Repeater request sent!", severity="information")
            
        except ImportError:
            self.app.notify("Missing 'requests' module", severity="error")
        except Exception as e:
            self.query_one("#res_view", TextArea).text = f"Error sending request:\n{e}"
            self.app.notify("Repeater failed", severity="error")

    def action_clear_history(self) -> None:
        self.flow_data = {}
        self.query_one("#flow_list", ListView).clear()
        self.query_one("#req_view", TextArea).text = ""
        self.query_one("#res_view", TextArea).text = ""

    def on_unmount(self) -> None:
        self.stop_proxy()

