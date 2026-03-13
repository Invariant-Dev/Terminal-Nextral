"""
plugin_manager.py — Nextral Plugin Dispatch Engine

Loads plugin definitions from plugins/plugins.json and provides a
dispatch() method that the TerminalScreen can call to route commands
to the correct module/action.

Plugin JSON schema:
{
  "plugins": [
    {
      "id":      "nmap",              // unique plugin id
      "aliases": ["nmap", "nmap-scan"], // command triggers
      "module":  "nmap_screen",       // Python module to import
      "class":   "NmapScreen",        // Textual Screen class
      "args":    ["target"],          // which CLI args to pass (by position)
      "help":    "Network mapper",    // one-liner for help
      "category":"HACKING"            // help category grouping
    }
  ]
}

The PluginManager is intentionally lightweight — it does NOT handle
internal built-ins (clear, exit, status panels, etc.) which are still
managed by TerminalScreen._handle_internal_builtins().  The refactored
_handle_internal() calls builtins first, then falls through to here.
"""

from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from textual.widgets import RichLog
    from textual.app import App

PLUGINS_FILE = Path(__file__).parent / "plugins" / "plugins.json"


class PluginManager:
    """Data-driven plugin dispatcher for Nextral terminal commands."""

    def __init__(self) -> None:
        self._plugins: list[dict] = []
        self._alias_map: dict[str, dict] = {}
        self._load()

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Load plugin definitions from plugins/plugins.json."""
        if not PLUGINS_FILE.exists():
            PLUGINS_FILE.parent.mkdir(parents=True, exist_ok=True)
            self._write_defaults()

        try:
            with open(PLUGINS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._plugins = data.get("plugins", [])
        except Exception as e:
            print(f"[PluginManager] Failed to load plugins.json: {e}")
            self._plugins = []

        # Build alias → plugin map
        self._alias_map = {}
        for plugin in self._plugins:
            for alias in plugin.get("aliases", []):
                self._alias_map[alias.lower()] = plugin

    def reload(self) -> None:
        """Hot-reload plugins from disk."""
        self._plugins = []
        self._alias_map = {}
        self._load()

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------

    def get_plugin(self, cmd_name: str) -> Optional[dict]:
        """Return plugin definition for a command alias, or None."""
        return self._alias_map.get(cmd_name.lower())

    def dispatch(self, cmd: str, parts: list[str], app: "App") -> bool:
        """
        Try to dispatch the command to a registered plugin.

        Returns True if a plugin was matched and pushed (so
        TerminalScreen knows to stop processing).
        Returns False if no plugin matched.
        """
        if not parts:
            return False

        cmd_name = parts[0].lower()
        plugin = self._alias_map.get(cmd_name)
        if not plugin:
            return False

        try:
            module = importlib.import_module(plugin["module"])
            cls = getattr(module, plugin["class"])

            # Build constructor arguments from positional CLI parts
            constructor_args = []
            for arg_key in plugin.get("args", []):
                # arg_key tells us which positional slot → index from parts
                slot = plugin["args"].index(arg_key) + 1  # 1-indexed (skip cmd itself)
                constructor_args.append(parts[slot] if len(parts) > slot else "")

            screen_instance = cls(*constructor_args)
            app.push_screen(screen_instance)
            return True

        except Exception as ex:
            # Fallback: write error to the active log if possible
            print(f"[PluginManager] Error loading plugin '{plugin.get('id')}': {ex}")
            return False

    # ------------------------------------------------------------------
    # Help generation
    # ------------------------------------------------------------------

    def help_text(self) -> str:
        """Build a Rich-markup help block from plugin definitions."""
        categories: dict[str, list[str]] = {}
        for plugin in self._plugins:
            cat = plugin.get("category", "PLUGINS")
            aliases = "/".join(f"[green]{a}[/]" for a in plugin.get("aliases", []))
            desc = plugin.get("help", "")
            line = f"  {aliases:<40} {desc}"
            categories.setdefault(cat, []).append(line)

        lines = []
        for cat, entries in categories.items():
            lines.append(f"\n[bold magenta]━━━ {cat} ━━━[/]")
            lines.extend(entries)
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Default plugin registry
    # ------------------------------------------------------------------

    def _write_defaults(self) -> None:
        """Write the default plugins.json to disk."""
        defaults = {
            "plugins": [
                # ── Security / Hacking ──────────────────────────────────
                {
                    "id": "nmap",
                    "aliases": ["nmap", "nmap-scan"],
                    "module": "nmap_screen",
                    "class": "NmapScreen",
                    "args": ["target"],
                    "help": "Network mapper & port scanner",
                    "category": "HACKING & FORENSICS"
                },
                {
                    "id": "nikto",
                    "aliases": ["nikto", "niktoscan", "webscan", "dirbust"],
                    "module": "nikto_screen",
                    "class": "NiktoScreen",
                    "args": ["target"],
                    "help": "Web vulnerability scanner",
                    "category": "HACKING & FORENSICS"
                },
                {
                    "id": "hydra",
                    "aliases": ["hydra", "brute"],
                    "module": "hydra_screen",
                    "class": "HydraScreen",
                    "args": ["target", "service"],
                    "help": "Online password / brute-force cracker",
                    "category": "HACKING & FORENSICS"
                },
                {
                    "id": "netcat",
                    "aliases": ["nc", "netcat", "listen"],
                    "module": "netcat_screen",
                    "class": "NetcatScreen",
                    "args": ["target", "port"],
                    "help": "TCP/UDP connect or listen tool",
                    "category": "HACKING & FORENSICS"
                },
                {
                    "id": "tcpdump",
                    "aliases": ["tcpdump", "packetcap", "sniff", "netcap"],
                    "module": "tcpdump_screen",
                    "class": "TcpdumpScreen",
                    "args": ["interface"],
                    "help": "Professional packet capture / sniffer",
                    "category": "HACKING & FORENSICS"
                },
                {
                    "id": "stun",
                    "aliases": ["stun", "whatsapp-ip", "whatsapp-tracer"],
                    "module": "whatsapp_ip_tracer_screen",
                    "class": "WhatsAppIPTracerScreen",
                    "args": [],
                    "help": "WhatsApp IP Tracer - Find WhatsApp server IPs",
                    "category": "HACKING & FORENSICS"
                },
                {
                    "id": "openssl",
                    "aliases": ["openssl", "ssltool", "cert"],
                    "module": "openssl_tool",
                    "class": "OpenSSLTool",
                    "args": [],
                    "help": "Certificate & crypto toolkit",
                    "category": "HACKING & FORENSICS"
                },
                {
                    "id": "valkyrie",
                    "aliases": ["valkyrie", "hashcrack", "crack"],
                    "module": "valkyrie",
                    "class": "ValkyrieScreen",
                    "args": [],
                    "help": "Hash identifier & cracker",
                    "category": "HACKING & FORENSICS"
                },
                {
                    "id": "exif",
                    "aliases": ["exif", "metadata", "exif-ray"],
                    "module": "exif_ray",
                    "class": "ExifRayScreen",
                    "args": [],
                    "help": "Metadata forensic analyzer",
                    "category": "HACKING & FORENSICS"
                },
                # ── SSH ─────────────────────────────────────────────────
                {
                    "id": "ssh",
                    "aliases": ["ssh", "sshclient"],
                    "module": "ssh_screen",
                    "class": "SSHScreen",
                    "args": ["host"],
                    "help": "Interactive SSH client with connection manager",
                    "category": "REMOTE ACCESS"
                },
                # ── Cybersec ─────────────────────────────────────────────
                {
                    "id": "osint",
                    "aliases": ["osint", "recon"],
                    "module": "osint_tool",
                    "class": "OSINTTool",
                    "args": [],
                    "help": "Open-source intelligence tool",
                    "category": "CYBERSEC TOOLS"
                },
                {
                    "id": "xray",
                    "aliases": ["xray", "vulnscan"],
                    "module": "xray_tool",
                    "class": "XRayTool",
                    "args": [],
                    "help": "Advanced vulnerability scanner",
                    "category": "CYBERSEC TOOLS"
                },
                {
                    "id": "sandbox",
                    "aliases": ["sandbox", "malanalyze"],
                    "module": "sandbox_tool",
                    "class": "SandboxTool",
                    "args": [],
                    "help": "Malware analysis sandbox",
                    "category": "CYBERSEC TOOLS"
                },
                # ── Elite Modules ────────────────────────────────────────
                {
                    "id": "sentinel",
                    "aliases": ["sentinel"],
                    "module": "sentinel",
                    "class": "SentinelScreen",
                    "args": [],
                    "help": "Visual process manager (Task Manager)",
                    "category": "ELITE MODULES"
                },
                {
                    "id": "blackbook",
                    "aliases": ["book", "blackbook", "snippets"],
                    "module": "blackbook",
                    "class": "BlackbookScreen",
                    "args": [],
                    "help": "Command snippet vault",
                    "category": "ELITE MODULES"
                },
                {
                    "id": "breach",
                    "aliases": ["breach", "breachwatch", "watch"],
                    "module": "breach_watch",
                    "class": "BreachWatchScreen",
                    "args": [],
                    "help": "Real-time security event monitor",
                    "category": "ELITE MODULES"
                },
                {
                    "id": "vault",
                    "aliases": ["vault", "vaultx", "vault-x"],
                    "module": "vault_x",
                    "class": "VaultScreen",
                    "args": [],
                    "help": "Secure file encryption vault",
                    "category": "ELITE MODULES"
                },
                # ── Core Utilities ───────────────────────────────────────
                {
                    "id": "cipher",
                    "aliases": ["cipher", "encrypt", "decrypt"],
                    "module": "cipher",
                    "class": "CipherScreen",
                    "args": [],
                    "help": "Message encryption tool",
                    "category": "CORE UTILITIES"
                },
                {
                    "id": "proxychain",
                    "aliases": ["proxy", "proxychain", "route"],
                    "module": "proxy_chain",
                    "class": "ProxyScreen",
                    "args": [],
                    "help": "Network route visualization",
                    "category": "CORE UTILITIES"
                },
                {
                    "id": "obelisk",
                    "aliases": ["obelisk", "stats", "activity"],
                    "module": "obelisk",
                    "class": "ObeliskScreen",
                    "args": [],
                    "help": "Activity heatmap & dashboard",
                    "category": "CORE UTILITIES"
                },
                {
                    "id": "agent",
                    "aliases": ["agent"],
                    "module": "agent_screen",
                    "class": "AgentScreen",
                    "args": [],
                    "help": "Integrated AI Agent HUD",
                    "category": "CORE UTILITIES"
                },
                {
                    "id": "settings",
                    "aliases": ["settings"],
                    "module": "settings_screen",
                    "class": "SettingsScreen",
                    "args": [],
                    "help": "Configure Nextral preferences",
                    "category": "CORE UTILITIES"
                },
                {
                    "id": "install",
                    "aliases": ["install", "installwizard", "setup", "wizard"],
                    "module": "install_wizard_screen",
                    "class": "InstallWizardScreen",
                    "args": [],
                    "help": "Dependency installer wizard",
                    "category": "CORE UTILITIES"
                }
            ]
        }

        try:
            with open(PLUGINS_FILE, "w", encoding="utf-8") as f:
                json.dump(defaults, f, indent=2)
        except Exception as e:
            print(f"[PluginManager] Could not write default plugins.json: {e}")
