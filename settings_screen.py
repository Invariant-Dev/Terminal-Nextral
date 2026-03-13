"""
Nextral Settings Screen — Unified configuration editor
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical, Horizontal, Container, ScrollableContainer
from textual.widgets import (
    Static, Input, Button, Header, Footer, 
    Label, Select, Switch, Checkbox
)
from textual.binding import Binding
import json
from pathlib import Path
import getpass
import os

CONFIG_FILE = Path(__file__).parent / "terminal_config.json"


class SettingsScreen(Screen):
    """Comprehensive settings editor for Nextral"""

    CSS = """
    SettingsScreen {
        background: #030712;
    }

    Header {
        background: #001100;
        color: #00ff00;
    }

    Footer {
        background: #001100;
    }

    #settings_title {
        width: 100%;
        background: #0a0f0a;
        border: solid #004400;
        padding: 1;
        color: #00ffaa;
        text-style: bold;
        margin-bottom: 1;
    }

    #settings_scroll {
        height: 1fr;
        border: solid #0e7490;
        background: #0a0a12;
        padding: 1;
    }

    .settings-section {
        border: solid #374151;
        margin: 0 0 2 0;
        padding: 1;
        height: auto;
        background: #0a0a12;
    }

    .settings-title {
        color: #9ca3af;
        text-style: bold;
        margin-bottom: 1;
    }

    .settings-label {
        color: #6b7280;
        margin: 1 0 0 0;
    }

    .settings-input {
        background: #111827;
        border: solid #1f2937;
        margin-bottom: 1;
        width: 100%;
    }

    .settings-input:focus {
        border: solid #0e7490;
        background: #1a2a3a;
    }

    #button_bar {
        height: auto;
        dock: bottom;
        background: #0a0a12;
        border-top: solid #003322;
        padding: 1;
    }

    .settings-btn {
        margin-right: 1;
        width: 1fr;
    }

    #save_btn {
        background: #065f46;
        color: #34d399;
        text-style: bold;
    }

    #save_btn:hover {
        background: #34d399;
        color: #030712;
    }

    #cancel_btn {
        background: #7f1d1d;
        color: #fca5a5;
    }

    #cancel_btn:hover {
        background: #dc2626;
        color: white;
    }

    #reset_btn {
        background: #78350f;
        color: #fbbf24;
    }

    #reset_btn:hover {
        background: #f59e0b;
        color: #030712;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel_settings", "Back", priority=True),
    ]

    # Email provider SMTP hosts mapping
    EMAIL_PROVIDERS = {
        "gmail": {"smtp_host": "smtp.gmail.com", "smtp_port": 587},
        "outlook": {"smtp_host": "smtp-mail.outlook.com", "smtp_port": 587},
        "yahoo": {"smtp_host": "smtp.mail.yahoo.com", "smtp_port": 587},
        "custom": {"smtp_host": "", "smtp_port": 587}
    }

    def __init__(self):
        super().__init__()
        self.config = self._load_config()
        self.original_config = json.loads(json.dumps(self.config))

    def _load_config(self):
        """Load configuration from JSON file"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        return self._default_config()

    def _default_config(self):
        """Default configuration"""
        system_user = getpass.getuser().upper()
        return {
            "user": {
                "username": system_user,
                "theme_color": "cyan",
                "auto_login": True
            },
            "terminal": {
                "history_size": 1000,
                "max_output_lines": 2000,
                "cursor_style": "block",
                "blinking_cursor": True,
                "typing_effect_speed": 0.0,
                "crt_mode": False,
                "boot_animation_enabled": True
            },
            "shell": {
                "prompt_format": "{username}@Nextral {cwd} ~> "
            },
            "widgets": {
                "default_visible": False,
                "animations_enabled": True
            },
            "ai": {
                "provider": "Ollama",
                "ollama_model": "qwen3:4b",
                "openai_key": "",
                "openai_model": "gpt-3.5-turbo",
                "gemini_key": "",
                "gemini_model": "gemini-pro",
                "anthropic_key": "",
                "anthropic_model": "claude-3-opus-20240229",
                "imap_host": "imap.gmail.com",
                "imap_user": "",
                "imap_password": "",
                "smtp_host": "smtp.gmail.com",
                "smtp_port": 587,
                "smtp_user": "",
                "smtp_password": "",
                "ollama_url_primary": "http://localhost:11434",
                "ollama_url_secondary": "http://192.168.0.5:11434",
                "shodan_api_key": ""
            },
            "external_tools": {
                "nmap": "nmap",
                "netcat": "nc",
                "nikto": "nikto",
                "hydra": "hydra",
                "tcpdump": "tcpdump",
                "openssl": "openssl",
                "curl": "curl",
                "wget": "wget",
                "ssh": "ssh",
                "sqlmap": "sqlmap",
                "hashcat": "hashcat"
            }
        }

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        yield Static("⚙️ NEXTRAL CONFIGURATION", id="settings_title")

        with ScrollableContainer(id="settings_scroll"):
            # USER SETTINGS
            with Vertical(classes="settings-section"):
                yield Label("👤 USER SETTINGS", classes="settings-title")
                yield Label("Username:", classes="settings-label")
                yield Input(id="user_username", placeholder="Username", classes="settings-input")
                yield Label("Theme Color:", classes="settings-label")
                yield Select(
                    [("Cyan", "cyan"), ("Green", "green"), ("Blue", "blue"), ("Red", "red"), ("Magenta", "magenta"), ("Yellow", "yellow"), ("White", "white")],
                    id="user_theme_color"
                )
                yield Label("Auto Login:", classes="settings-label")
                yield Switch(id="user_auto_login")

            # TERMINAL SETTINGS
            with Vertical(classes="settings-section"):
                yield Label("💻 TERMINAL SETTINGS", classes="settings-title")
                yield Label("History Size:", classes="settings-label")
                yield Input(id="terminal_history_size", placeholder="1000", classes="settings-input", type="integer")
                yield Label("Max Output Lines:", classes="settings-label")
                yield Input(id="terminal_max_output_lines", placeholder="2000", classes="settings-input", type="integer")
                yield Label("Cursor Style:", classes="settings-label")
                yield Select(
                    [("Block", "block"), ("Underline", "underline"), ("Bar", "bar")],
                    id="terminal_cursor_style"
                )
                yield Label("Blinking Cursor:", classes="settings-label")
                yield Switch(id="terminal_blinking_cursor")
                yield Label("Typing Effect Speed (0 for instant):", classes="settings-label")
                yield Input(id="terminal_typing_effect_speed", placeholder="0.0", classes="settings-input", type="number")
                yield Label("CRT Mode:", classes="settings-label")
                yield Switch(id="terminal_crt_mode")
                yield Label("Boot Animation:", classes="settings-label")
                yield Switch(id="terminal_boot_animation")

            # SHELL SETTINGS
            with Vertical(classes="settings-section"):
                yield Label("🐚 SHELL SETTINGS", classes="settings-title")
                yield Label("Prompt Format:", classes="settings-label")
                yield Input(id="shell_prompt_format", placeholder="{username}@Nextral {cwd} ~> ", classes="settings-input")

            # WIDGET SETTINGS
            with Vertical(classes="settings-section"):
                yield Label("🎨 WIDGET SETTINGS", classes="settings-title")
                yield Label("Default Visible:", classes="settings-label")
                yield Switch(id="widgets_default_visible")
                yield Label("Animations Enabled:", classes="settings-label")
                yield Switch(id="widgets_animations_enabled")
                yield Label("Show System Panel:", classes="settings-label")
                yield Switch(id="ui_show_sys_panel")
                yield Label("Show Network Panel:", classes="settings-label")
                yield Switch(id="ui_show_net_panel")
                yield Label("Show Security Panel:", classes="settings-label")
                yield Switch(id="ui_show_sec_panel")
                yield Label("Show Git Panel:", classes="settings-label")
                yield Switch(id="ui_show_git_panel")
                yield Label("Sidebar Transparency (0-100%):", classes="settings-label")
                yield Input(id="ui_sidebar_transparency", placeholder="0", classes="settings-input", type="integer")

            # AI SETTINGS
            with Vertical(classes="settings-section"):
                yield Label("🤖 AI PROVIDER SETTINGS", classes="settings-title")
                yield Label("Provider:", classes="settings-label")
                yield Input(id="ai_provider", placeholder="Ollama", classes="settings-input")
                yield Label("Ollama Model:", classes="settings-label")
                yield Input(id="ai_ollama_model", placeholder="qwen3:4b", classes="settings-input")
                yield Label("Ollama URL Primary:", classes="settings-label")
                yield Input(id="ai_ollama_url_primary", placeholder="http://localhost:11434", classes="settings-input")
                yield Label("Ollama URL Secondary:", classes="settings-label")
                yield Input(id="ai_ollama_url_secondary", placeholder="http://192.168.0.5:11434", classes="settings-input")

            # OPENAI SETTINGS
            with Vertical(classes="settings-section"):
                yield Label("🔑 OPENAI SETTINGS", classes="settings-title")
                yield Label("API Key:", classes="settings-label")
                yield Input(id="ai_openai_key", placeholder="sk-...", password=True, classes="settings-input")
                yield Label("Model:", classes="settings-label")
                yield Input(id="ai_openai_model", placeholder="gpt-3.5-turbo", classes="settings-input")

            # GEMINI SETTINGS
            with Vertical(classes="settings-section"):
                yield Label("✨ GEMINI SETTINGS", classes="settings-title")
                yield Label("API Key:", classes="settings-label")
                yield Input(id="ai_gemini_key", placeholder="AIza...", password=True, classes="settings-input")
                yield Label("Model:", classes="settings-label")
                yield Input(id="ai_gemini_model", placeholder="gemini-pro", classes="settings-input")

            # ANTHROPIC SETTINGS
            with Vertical(classes="settings-section"):
                yield Label("🧠 ANTHROPIC SETTINGS", classes="settings-title")
                yield Label("API Key:", classes="settings-label")
                yield Input(id="ai_anthropic_key", placeholder="sk-ant-...", password=True, classes="settings-input")
                yield Label("Model:", classes="settings-label")
                yield Input(id="ai_anthropic_model", placeholder="claude-3-opus-20240229", classes="settings-input")

            # EMAIL IMAP SETTINGS
            with Vertical(classes="settings-section"):
                yield Label("📧 EMAIL - IMAP (Receiving)", classes="settings-title")
                yield Label("Host:", classes="settings-label")
                yield Input(id="ai_imap_host", placeholder="imap.gmail.com", classes="settings-input")
                yield Label("Email:", classes="settings-label")
                yield Input(id="ai_imap_user", placeholder="your-email@gmail.com", classes="settings-input")
                yield Label("Password:", classes="settings-label")
                yield Input(id="ai_imap_password", placeholder="app-password", password=True, classes="settings-input")

            # EMAIL SMTP SETTINGS
            with Vertical(classes="settings-section"):
                yield Label("📬 EMAIL - SMTP (Sending)", classes="settings-title")
                yield Label("Email Provider:", classes="settings-label")
                yield Select(
                    [
                        ("Gmail", "gmail"),
                        ("Outlook/Office 365", "outlook"),
                        ("Yahoo", "yahoo"),
                        ("Custom", "custom")
                    ],
                    value="gmail",
                    id="email_provider_select"
                )
                yield Label("Host:", classes="settings-label")
                yield Input(id="ai_smtp_host", placeholder="smtp.gmail.com", classes="settings-input")
                yield Label("Port:", classes="settings-label")
                yield Input(id="ai_smtp_port", placeholder="587", classes="settings-input")
                yield Label("Email:", classes="settings-label")
                yield Input(id="ai_smtp_user", placeholder="your-email@gmail.com", classes="settings-input")
                yield Label("Password:", classes="settings-label")
                yield Input(id="ai_smtp_password", placeholder="app-password", password=True, classes="settings-input")

            # SECURITY SETTINGS
            with Vertical(classes="settings-section"):
                yield Label("🔐 SECURITY APIS", classes="settings-title")
                yield Label("Shodan API Key:", classes="settings-label")
                yield Input(id="ai_shodan_api_key", placeholder="YOUR_SHODAN_KEY", password=True, classes="settings-input")

            # EXTERNAL TOOLS SETTINGS
            with Vertical(classes="settings-section"):
                yield Label("🔧 EXTERNAL TOOLS PATHS", classes="settings-title")
                yield Label("Nmap Path:", classes="settings-label")
                yield Input(id="tool_nmap", placeholder="nmap (or /usr/bin/nmap)", classes="settings-input")
                yield Label("Netcat Path:", classes="settings-label")
                yield Input(id="tool_netcat", placeholder="nc (or /usr/bin/nc)", classes="settings-input")
                yield Label("Nikto Path:", classes="settings-label")
                yield Input(id="tool_nikto", placeholder="nikto (or /usr/bin/nikto)", classes="settings-input")
                yield Label("Hydra Path:", classes="settings-label")
                yield Input(id="tool_hydra", placeholder="hydra (or /usr/bin/hydra)", classes="settings-input")
                yield Label("TCPDump Path:", classes="settings-label")
                yield Input(id="tool_tcpdump", placeholder="tcpdump (or /usr/bin/tcpdump)", classes="settings-input")
                yield Label("OpenSSL Path:", classes="settings-label")
                yield Input(id="tool_openssl", placeholder="openssl (or /usr/bin/openssl)", classes="settings-input")
                yield Label("cURL Path:", classes="settings-label")
                yield Input(id="tool_curl", placeholder="curl", classes="settings-input")
                yield Label("Wget Path:", classes="settings-label")
                yield Input(id="tool_wget", placeholder="wget", classes="settings-input")
                yield Label("SSH Path:", classes="settings-label")
                yield Input(id="tool_ssh", placeholder="ssh", classes="settings-input")
                yield Label("SQLMap Path:", classes="settings-label")
                yield Input(id="tool_sqlmap", placeholder="sqlmap", classes="settings-input")
                yield Label("Hashcat Path:", classes="settings-label")
                yield Input(id="tool_hashcat", placeholder="hashcat", classes="settings-input")
                yield Button("🔍 DETECT TOOLS", id="detect_tools_btn", variant="primary")

        with Horizontal(id="button_bar"):
            yield Button("💾 SAVE", id="save_btn", classes="settings-btn")
            yield Button("↺ RESET", id="reset_btn", classes="settings-btn")
            yield Button("✕ CANCEL", id="cancel_btn", classes="settings-btn")

        yield Footer()

    def on_mount(self):
        """Populate settings from config"""
        self._populate_fields()
        self.query_one("#user_username").focus()

    def _detect_email_provider(self, smtp_host: str) -> str:
        """Detect which email provider is configured"""
        smtp_host_lower = smtp_host.lower()
        for provider, config in self.EMAIL_PROVIDERS.items():
            if config["smtp_host"].lower() == smtp_host_lower:
                return provider
        return "custom"

    def _populate_fields(self):
        """Load all config values into input fields"""
        cfg = self.config
        
        try:
            # User
            self.query_one("#user_username").value = str(cfg.get("user", {}).get("username", ""))
            self.query_one("#user_theme_color").value = str(cfg.get("user", {}).get("theme_color", "cyan"))
            self.query_one("#user_auto_login").value = cfg.get("user", {}).get("auto_login", True)
            
            # Terminal
            self.query_one("#terminal_history_size").value = str(cfg.get("terminal", {}).get("history_size", 1000))
            self.query_one("#terminal_max_output_lines").value = str(cfg.get("terminal", {}).get("max_output_lines", 2000))
            self.query_one("#terminal_cursor_style").value = str(cfg.get("terminal", {}).get("cursor_style", "block"))
            self.query_one("#terminal_blinking_cursor").value = cfg.get("terminal", {}).get("blinking_cursor", True)
            self.query_one("#terminal_typing_effect_speed").value = str(cfg.get("terminal", {}).get("typing_effect_speed", 0.0))
            self.query_one("#terminal_crt_mode").value = cfg.get("terminal", {}).get("crt_mode", False)
            self.query_one("#terminal_boot_animation").value = cfg.get("terminal", {}).get("boot_animation_enabled", True)
            
            # Shell
            self.query_one("#shell_prompt_format").value = str(cfg.get("shell", {}).get("prompt_format", "{username}@Nextral {cwd} ~> "))
            
            # Widgets
            self.query_one("#widgets_default_visible").value = cfg.get("widgets", {}).get("default_visible", False)
            self.query_one("#widgets_animations_enabled").value = cfg.get("widgets", {}).get("animations_enabled", True)
            
            # UI (Widget Visibility)
            self.query_one("#ui_show_sys_panel").value = cfg.get("ui", {}).get("show_sys_panel", True)
            self.query_one("#ui_show_net_panel").value = cfg.get("ui", {}).get("show_net_panel", True)
            self.query_one("#ui_show_sec_panel").value = cfg.get("ui", {}).get("show_sec_panel", False)
            self.query_one("#ui_show_git_panel").value = cfg.get("ui", {}).get("show_git_panel", False)
            self.query_one("#ui_sidebar_transparency").value = str(cfg.get("ui", {}).get("sidebar_transparency", 0))
            
            # AI
            self.query_one("#ai_provider").value = str(cfg.get("ai", {}).get("provider", "Ollama"))
            self.query_one("#ai_ollama_model").value = str(cfg.get("ai", {}).get("ollama_model", "qwen3:4b"))
            self.query_one("#ai_ollama_url_primary").value = str(cfg.get("ai", {}).get("ollama_url_primary", "http://localhost:11434"))
            self.query_one("#ai_ollama_url_secondary").value = str(cfg.get("ai", {}).get("ollama_url_secondary", ""))
            self.query_one("#ai_openai_key").value = str(cfg.get("ai", {}).get("openai_key", ""))
            self.query_one("#ai_openai_model").value = str(cfg.get("ai", {}).get("openai_model", "gpt-3.5-turbo"))
            self.query_one("#ai_gemini_key").value = str(cfg.get("ai", {}).get("gemini_key", ""))
            self.query_one("#ai_gemini_model").value = str(cfg.get("ai", {}).get("gemini_model", "gemini-pro"))
            self.query_one("#ai_anthropic_key").value = str(cfg.get("ai", {}).get("anthropic_key", ""))
            self.query_one("#ai_anthropic_model").value = str(cfg.get("ai", {}).get("anthropic_model", "claude-3-opus-20240229"))
            
            # Email
            self.query_one("#ai_imap_host").value = str(cfg.get("ai", {}).get("imap_host", "imap.gmail.com"))
            self.query_one("#ai_imap_user").value = str(cfg.get("ai", {}).get("imap_user", ""))
            self.query_one("#ai_imap_password").value = str(cfg.get("ai", {}).get("imap_password", ""))
            
            smtp_host = str(cfg.get("ai", {}).get("smtp_host", "smtp.gmail.com"))
            provider = self._detect_email_provider(smtp_host)
            self.query_one("#email_provider_select").value = provider
            
            self.query_one("#ai_smtp_host").value = smtp_host
            self.query_one("#ai_smtp_port").value = str(cfg.get("ai", {}).get("smtp_port", 587))
            self.query_one("#ai_smtp_user").value = str(cfg.get("ai", {}).get("smtp_user", ""))
            self.query_one("#ai_smtp_password").value = str(cfg.get("ai", {}).get("smtp_password", ""))
            
            # Security
            self.query_one("#ai_shodan_api_key").value = str(cfg.get("ai", {}).get("shodan_api_key", ""))
            
            # External Tools
            tools = cfg.get("external_tools", {})
            self.query_one("#tool_nmap").value = str(tools.get("nmap", "nmap"))
            self.query_one("#tool_netcat").value = str(tools.get("netcat", "nc"))
            self.query_one("#tool_nikto").value = str(tools.get("nikto", "nikto"))
            self.query_one("#tool_hydra").value = str(tools.get("hydra", "hydra"))
            self.query_one("#tool_tcpdump").value = str(tools.get("tcpdump", "tcpdump"))
            self.query_one("#tool_openssl").value = str(tools.get("openssl", "openssl"))
            self.query_one("#tool_curl").value = str(tools.get("curl", "curl"))
            self.query_one("#tool_wget").value = str(tools.get("wget", "wget"))
            self.query_one("#tool_ssh").value = str(tools.get("ssh", "ssh"))
            self.query_one("#tool_sqlmap").value = str(tools.get("sqlmap", "sqlmap"))
            self.query_one("#tool_hashcat").value = str(tools.get("hashcat", "hashcat"))
        except Exception as e:
            self.notify(f"Error loading settings: {e}", severity="error")

    def _save_config(self):
        """Save configuration to file"""
        try:
            cfg = self.config
            
            # User
            cfg["user"]["username"] = self.query_one("#user_username").value
            cfg["user"]["theme_color"] = self.query_one("#user_theme_color").value
            cfg["user"]["auto_login"] = self.query_one("#user_auto_login").value
            
            # Terminal
            cfg["terminal"]["history_size"] = int(self.query_one("#terminal_history_size").value or 1000)
            cfg["terminal"]["max_output_lines"] = int(self.query_one("#terminal_max_output_lines").value or 2000)
            cfg["terminal"]["cursor_style"] = self.query_one("#terminal_cursor_style").value
            cfg["terminal"]["blinking_cursor"] = self.query_one("#terminal_blinking_cursor").value
            cfg["terminal"]["typing_effect_speed"] = float(self.query_one("#terminal_typing_effect_speed").value or 0.0)
            cfg["terminal"]["crt_mode"] = self.query_one("#terminal_crt_mode").value
            cfg["terminal"]["boot_animation_enabled"] = self.query_one("#terminal_boot_animation").value
            
            # Shell
            cfg["shell"]["prompt_format"] = self.query_one("#shell_prompt_format").value
            
            # Widgets
            cfg["widgets"]["default_visible"] = self.query_one("#widgets_default_visible").value
            cfg["widgets"]["animations_enabled"] = self.query_one("#widgets_animations_enabled").value
            
            # UI
            cfg.setdefault("ui", {})
            cfg["ui"]["show_sys_panel"] = self.query_one("#ui_show_sys_panel").value
            cfg["ui"]["show_net_panel"] = self.query_one("#ui_show_net_panel").value
            cfg["ui"]["show_sec_panel"] = self.query_one("#ui_show_sec_panel").value
            cfg["ui"]["show_git_panel"] = self.query_one("#ui_show_git_panel").value
            cfg["ui"]["sidebar_transparency"] = int(self.query_one("#ui_sidebar_transparency").value or 0)
            
            # AI
            cfg["ai"]["provider"] = self.query_one("#ai_provider").value
            cfg["ai"]["ollama_model"] = self.query_one("#ai_ollama_model").value
            cfg["ai"]["ollama_url_primary"] = self.query_one("#ai_ollama_url_primary").value
            cfg["ai"]["ollama_url_secondary"] = self.query_one("#ai_ollama_url_secondary").value
            cfg["ai"]["openai_key"] = self.query_one("#ai_openai_key").value
            cfg["ai"]["openai_model"] = self.query_one("#ai_openai_model").value
            cfg["ai"]["gemini_key"] = self.query_one("#ai_gemini_key").value
            cfg["ai"]["gemini_model"] = self.query_one("#ai_gemini_model").value
            cfg["ai"]["anthropic_key"] = self.query_one("#ai_anthropic_key").value
            cfg["ai"]["anthropic_model"] = self.query_one("#ai_anthropic_model").value
            
            # Email
            cfg["ai"]["imap_host"] = self.query_one("#ai_imap_host").value
            cfg["ai"]["imap_user"] = self.query_one("#ai_imap_user").value
            cfg["ai"]["imap_password"] = self.query_one("#ai_imap_password").value
            cfg["ai"]["smtp_host"] = self.query_one("#ai_smtp_host").value
            cfg["ai"]["smtp_port"] = int(self.query_one("#ai_smtp_port").value or 587)
            cfg["ai"]["smtp_user"] = self.query_one("#ai_smtp_user").value
            cfg["ai"]["smtp_password"] = self.query_one("#ai_smtp_password").value
            
            # Security
            cfg["ai"]["shodan_api_key"] = self.query_one("#ai_shodan_api_key").value
            
            # External Tools
            cfg.setdefault("external_tools", {})
            cfg["external_tools"]["nmap"] = self.query_one("#tool_nmap").value
            cfg["external_tools"]["netcat"] = self.query_one("#tool_netcat").value
            cfg["external_tools"]["nikto"] = self.query_one("#tool_nikto").value
            cfg["external_tools"]["hydra"] = self.query_one("#tool_hydra").value
            cfg["external_tools"]["tcpdump"] = self.query_one("#tool_tcpdump").value
            cfg["external_tools"]["openssl"] = self.query_one("#tool_openssl").value
            cfg["external_tools"]["curl"] = self.query_one("#tool_curl").value
            cfg["external_tools"]["wget"] = self.query_one("#tool_wget").value
            cfg["external_tools"]["ssh"] = self.query_one("#tool_ssh").value
            cfg["external_tools"]["sqlmap"] = self.query_one("#tool_sqlmap").value
            cfg["external_tools"]["hashcat"] = self.query_one("#tool_hashcat").value
            
            with open(CONFIG_FILE, 'w') as f:
                json.dump(cfg, f, indent=4)
            
            self.notify("✓ Settings saved successfully!", severity="information")
        except Exception as e:
            self.notify(f"Error saving settings: {e}", severity="error")

    def action_cancel_settings(self):
        """Close settings without saving"""
        self.app.pop_screen()

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle email provider selection change"""
        if event.select.id == "email_provider_select":
            provider = event.select.value
            if provider in self.EMAIL_PROVIDERS:
                config = self.EMAIL_PROVIDERS[provider]
                self.query_one("#ai_smtp_host").value = config["smtp_host"]
                self.query_one("#ai_smtp_port").value = str(config["smtp_port"])

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        
        if bid == "save_btn":
            self._save_config()
            self.app.pop_screen()
        elif bid == "cancel_btn":
            self.app.pop_screen()
        elif bid == "reset_btn":
            self.config = self._default_config()
            self._populate_fields()
            self.notify("⚠ Settings reset to defaults (not saved yet)", severity="warning")
        elif bid == "detect_tools_btn":
            await self._detect_tools()
    
    async def _detect_tools(self):
        """Auto-detect installed external tools"""
        import shutil
        
        tools_to_check = [
            ("tool_nmap", "nmap"),
            ("tool_netcat", "nc"),
            ("tool_nikto", "nikto"),
            ("tool_hydra", "hydra"),
            ("tool_tcpdump", "tcpdump"),
            ("tool_openssl", "openssl"),
            ("tool_curl", "curl"),
            ("tool_wget", "wget"),
            ("tool_ssh", "ssh"),
            ("tool_sqlmap", "sqlmap"),
            ("tool_hashcat", "hashcat"),
        ]
        
        found = 0
        for widget_id, tool_cmd in tools_to_check:
            path = shutil.which(tool_cmd)
            if path:
                self.query_one(f"#{widget_id}").value = path
                found += 1
        
        self.notify(f"Detected {found} external tools!", severity="information")
