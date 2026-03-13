"""
Nextral Agent Screen — Full TUI for the AI Agent
Tabs: Chat, Email, WhatsApp, Files, Cyber, Tasks, Settings
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical, Horizontal, Container, ScrollableContainer
from textual.widgets import (
    Static, Input, Button, Header, Footer, TabbedContent, TabPane,
    Select, RichLog, ListView, ListItem, Label
)
from textual.binding import Binding
from agent_backend import AgentBackend
import asyncio


class AgentScreen(Screen):
    """Nextral AI Agent TUI — Chat, Email, Files, Tasks, Settings"""

    CSS = """
    AgentScreen {
        background: #080008;
    }

    /* ── GLOBAL ELEMENTS ─────────────────────────────────────── */
    TabbedContent {
        background: #080008;
    }

    TabPane {
        background: #080008;
        padding: 0;
    }

    ContentSwitcher {
        background: #080008;
    }

    /* ── NEXUS CORE HEADER ─────────────────────────────────── */
    #nexus_header {
        height: 3;
        background: #120012;
        border-bottom: solid #660066;
    }
    
    #nexus_title {
        text-align: center;
        color: #aa44ff;
        text-style: bold;
    }

    /* ── CHAT TAB ──────────────────────────────────────────── */
    #chat_log {
        height: 1fr;
        border: solid #440066;
        background: #050005;
        margin: 1 1 0 1;
        padding: 1;
        scrollbar-background: #050005;
        scrollbar-color: #440066;
        scrollbar-color-hover: #aa44ff;
    }

    #chat_input_row {
        height: auto;
        margin: 0 1 1 1;
        padding-top: 1;
    }

    #chat_input {
        width: 1fr;
        border: solid #440066;
        background: #050005;
        color: #cc88ff;
    }
    #chat_input:focus {
        border: solid #aa44ff;
    }

    .action-btn {
        min-width: 12;
        background: #330055;
        color: #cc88ff;
        border: none;
        margin-left: 1;
    }
    .action-btn:hover {
        background: #550088;
        color: white;
    }

    #exec_confirm_bar {
        display: none;
        height: auto;
        margin: 0 1;
        padding: 1;
        background: #1a001a;
        border: solid #660066;
    }

    #exec_confirm_bar.visible {
        display: block;
    }

    #email_confirm_bar {
        display: none;
        height: auto;
        margin: 0 1;
        padding: 1;
        background: #1a001a;
        border: solid #660066;
    }

    #email_confirm_bar.visible {
        display: block;
    }

    /* ── EMAIL TAB ─────────────────────────────────────────── */
    #email_log {
        height: 1fr;
        border: solid #440066;
        background: #050005;
        margin: 1 1 0 1;
        padding: 1;
        scrollbar-background: #050005;
        scrollbar-color: #440066;
    }

    #email_actions {
        height: auto;
        margin: 0 1 1 1;
        padding-top: 1;
    }

    .email-btn {
        min-width: 18;
        background: #330055;
        color: #cc88ff;
        border: none;
        margin-right: 1;
    }
    .email-btn:hover {
        background: #550088;
        color: white;
    }

    /* Compose Area */
    #compose_area {
        display: none;
        border: solid #440066;
        margin: 1;
        padding: 1;
        height: auto;
        background: #050005;
    }
    #compose_area.visible {
        display: block;
    }

    .compose-input {
        margin-bottom: 1;
        background: #050005;
        border: solid #330033;
        color: #cc88ff;
    }

    /* ── FILES TAB ─────────────────────────────────────────── */
    #file_log {
        height: 1fr;
        border: solid #004433;
        background: #050005;
        margin: 1 1 0 1;
        padding: 1;
        scrollbar-background: #050005;
        scrollbar-color: #004433;
    }

    #file_input_row {
        height: auto;
        margin: 0 1 1 1;
        padding-top: 1;
    }

    #file_path_input {
        width: 1fr;
        background: #050005;
        border: solid #004433;
        color: #44cc88;
    }

    .file-btn {
        min-width: 12;
        background: #003322;
        color: #44cc88;
        border: none;
        margin-left: 1;
    }
    .file-btn:hover {
        background: #005544;
        color: white;
    }

    /* ── TASKS TAB ─────────────────────────────────────────── */
    #task_log {
        height: 1fr;
        border: solid #443300;
        background: #050005;
        margin: 1 1 0 1;
        padding: 1;
        scrollbar-background: #050005;
        scrollbar-color: #443300;
    }

    #task_input_row {
        height: auto;
        margin: 0 1 1 1;
        padding-top: 1;
    }

    #new_task_input {
        width: 1fr;
        background: #050005;
        border: solid #443300;
        color: #ccaa44;
    }

    .task-btn {
        min-width: 12;
        background: #332200;
        color: #ccaa44;
        border: none;
        margin-left: 1;
    }
    .task-btn:hover {
        background: #554400;
        color: white;
    }

    /* ── SETTINGS TAB ──────────────────────────────────────── */
    .settings-section {
        border: solid #222022;
        margin: 1;
        padding: 1;
        height: auto;
        background: #050005;
    }

    .settings-title {
        color: #888888;
        text-style: bold;
        margin-bottom: 1;
    }

    .settings-label {
        color: #666666;
        margin-bottom: 0;
    }

    .settings-input {
        background: #050005;
        border: solid #222022;
        color: #aa88cc;
        margin-bottom: 1;
    }

    /* ── WHATSAPP TAB ──────────────────────────────────── */
    #wa_log {
        height: 1fr;
        border: solid #003322;
        background: #050005;
        margin: 1 1 0 1;
        padding: 1;
        scrollbar-background: #050005;
        scrollbar-color: #003322;
    }

    #wa_actions {
        height: auto;
        margin: 0 1 1 1;
        padding-top: 1;
    }

    .wa-btn {
        min-width: 14;
        background: #002211;
        color: #44cc88;
        border: none;
        margin-right: 1;
    }
    .wa-btn:hover {
        background: #004433;
        color: white;
    }

    #wa_send_area {
        display: none;
        border: solid #003322;
        margin: 1;
        padding: 1;
        height: auto;
        background: #050005;
    }
    #wa_send_area.visible {
        display: block;
    }

    .wa-input {
        margin-bottom: 1;
        background: #050005;
        border: solid #002211;
        color: #44cc88;
    }

    /* ── CYBER TAB ─────────────────────────────────────── */
    #cyber_log {
        height: 1fr;
        border: solid #440000;
        background: #050005;
        margin: 1 1 0 1;
        padding: 1;
        scrollbar-background: #050005;
        scrollbar-color: #440000;
        scrollbar-color-hover: #aa3333;
    }

    #cyber_actions {
        height: auto;
        margin: 0 1 1 1;
        padding-top: 1;
    }

    .cyber-btn {
        min-width: 14;
        background: #330000;
        color: #cc6666;
        border: none;
        margin-right: 1;
    }
    .cyber-btn:hover {
        background: #550000;
        color: white;
    }

    #cyber_input_area {
        display: none;
        border: solid #330000;
        margin: 1;
        padding: 1;
        height: auto;
        background: #050005;
    }
    #cyber_input_area.visible {
        display: block;
    }

    .cyber-input {
        margin-bottom: 1;
        background: #050005;
        border: solid #220000;
        color: #cc6666;
    }

    /* ── SCROLLABLE SETTINGS ─────────────────────────────── */
    #settings_scroll {
        height: 1fr;
    }
    
    /* ── TAB STYLING ─────────────────────────────────────── */
    Tab {
        background: #0a000a;
        color: #884488;
    }
    
    Tab:hover {
        background: #120012;
        color: #aa44ff;
    }
    
    Tab.active {
        background: #1a001a;
        color: #cc88ff;
    }
    """

    BINDINGS = [
        Binding("escape", "return_to_terminal", "Back to Terminal"),
    ]

    def __init__(self):
        super().__init__()
        self.backend = AgentBackend()
        self._wa_monitor_task = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with TabbedContent():
            # ═══════════════════════════════════════════
            # TAB 1: CHAT
            # ═══════════════════════════════════════════
            with TabPane("💬 Chat", id="tab_chat"):
                yield RichLog(id="chat_log", markup=True, wrap=True)

                # Exec confirmation bar (hidden by default)
                with Container(id="exec_confirm_bar"):
                    yield Static("", id="exec_cmd_preview")
                    with Horizontal():
                        yield Button("✓ EXECUTE", id="exec_yes", classes="action-btn")
                        yield Button("✗ CANCEL", id="exec_no", classes="action-btn")

                # Email confirmation bar (hidden by default)
                with Container(id="email_confirm_bar"):
                    yield Static("", id="email_preview")
                    with Horizontal():
                        yield Button("✓ SEND EMAIL", id="email_yes", classes="action-btn")
                        yield Button("✗ CANCEL", id="email_no", classes="action-btn")

                with Horizontal(id="chat_input_row"):
                    yield Input(id="chat_input", placeholder="Ask Nexus anything... (or /help)")
                    yield Button("SEND", id="send_btn", classes="action-btn")
                    yield Button("BRIEF", id="brief_btn", classes="action-btn")

            # ═══════════════════════════════════════════
            # TAB 2: EMAIL
            # ═══════════════════════════════════════════
            with TabPane("📧 Email", id="tab_email"):
                yield RichLog(id="email_log", markup=True, wrap=True)

                # Compose area (hidden by default)
                with Container(id="compose_area"):
                    yield Label("Compose Email", classes="settings-title")
                    yield Input(id="compose_to", placeholder="To address", classes="compose-input")
                    yield Input(id="compose_subject", placeholder="Subject", classes="compose-input")
                    yield Input(id="compose_body", placeholder="Body (one line)", classes="compose-input")
                    with Horizontal():
                        yield Button("SEND EMAIL", id="compose_send_btn", classes="email-btn")
                        yield Button("CANCEL", id="compose_cancel_btn", classes="email-btn")

                with Horizontal(id="email_actions"):
                    yield Button("📥 FETCH INBOX", id="fetch_btn", classes="email-btn")
                    yield Button("📝 COMPOSE", id="compose_btn", classes="email-btn")
                    yield Button("🤖 SUMMARIZE", id="summarize_btn", classes="email-btn")

            # ═══════════════════════════════════════════
            # TAB 3: FILES
            # ═══════════════════════════════════════════
            with TabPane("📁 Files", id="tab_files"):
                yield RichLog(id="file_log", markup=True, wrap=True)
                with Horizontal(id="file_input_row"):
                    yield Input(id="file_path_input", placeholder="Enter file path to analyze...")
                    yield Input(id="file_question_input", placeholder="Question (optional)...")
                    yield Button("ANALYZE", id="analyze_btn", classes="file-btn")

            # ═══════════════════════════════════════════
            # TAB 4: WHATSAPP
            # ═══════════════════════════════════════════
            with TabPane("💬 WhatsApp", id="tab_whatsapp"):
                yield RichLog(id="wa_log", markup=True, wrap=True)

                # Send area (hidden by default)
                with Container(id="wa_send_area"):
                    yield Label("Send WhatsApp Message", classes="settings-title")
                    yield Input(id="wa_chat_id", placeholder="Chat ID (from list above)", classes="wa-input")
                    yield Input(id="wa_msg_body", placeholder="Message body", classes="wa-input")
                    with Horizontal():
                        yield Button("SEND MSG", id="wa_send_msg_btn", classes="wa-btn")
                        yield Button("CANCEL", id="wa_send_cancel_btn", classes="wa-btn")

                with Horizontal(id="wa_actions"):
                    yield Button("🔌 START", id="wa_start_btn", classes="wa-btn")
                    yield Button("📱 QR CODE", id="wa_qr_btn", classes="wa-btn")
                    yield Button("💬 CHATS", id="wa_chats_btn", classes="wa-btn")
                    yield Button("✉️ SEND", id="wa_compose_btn", classes="wa-btn")
                    yield Button("🤖 SUMMARIZE", id="wa_summarize_btn", classes="wa-btn")
                    yield Button("⏹ STOP", id="wa_stop_btn", classes="wa-btn")

            # ═══════════════════════════════════════════
            # TAB 5: CYBER
            # ═══════════════════════════════════════════
            with TabPane("🛡 Cyber", id="tab_cyber"):
                yield RichLog(id="cyber_log", markup=True, wrap=True)

                # Input area (hidden by default, context-dependent)
                with Container(id="cyber_input_area"):
                    yield Label("", id="cyber_input_title", classes="settings-title")
                    yield Input(id="cyber_input_main", placeholder="Target / code...", classes="cyber-input")
                    yield Input(id="cyber_input_extra", placeholder="(optional extra)", classes="cyber-input")
                    with Horizontal():
                        yield Button("▶ RUN", id="cyber_run_btn", classes="cyber-btn")
                        yield Button("✗ CANCEL", id="cyber_cancel_btn", classes="cyber-btn")

                with Horizontal(id="cyber_actions"):
                    yield Button("🔍 OSINT", id="cyber_osint_btn", classes="cyber-btn")
                    yield Button("💧 LEAK", id="cyber_leak_btn", classes="cyber-btn")
                    yield Button("🛡 X-RAY", id="cyber_xray_btn", classes="cyber-btn")
                    yield Button("🔧 AUDIT", id="cyber_audit_btn", classes="cyber-btn")
                    yield Button("📦 SANDBOX", id="cyber_sandbox_btn", classes="cyber-btn")
                    yield Button("🔓 DEOBF", id="cyber_deobf_btn", classes="cyber-btn")

            # ═══════════════════════════════════════════
            # TAB 6: TASKS
            # ═══════════════════════════════════════════
            with TabPane("📋 Tasks", id="tab_tasks"):
                yield RichLog(id="task_log", markup=True, wrap=True)
                with Horizontal(id="task_input_row"):
                    yield Input(id="new_task_input", placeholder="Add a new task...")
                    yield Button("ADD", id="add_task_btn", classes="task-btn")
                    yield Button("REFRESH", id="refresh_tasks_btn", classes="task-btn")

        yield Footer()

    # ═══════════════════════════════════════════════════════════════════════
    # LIFECYCLE
    # ═══════════════════════════════════════════════════════════════════════

    def on_mount(self):
        log = self.query_one("#chat_log", RichLog)
        provider = self.backend.get_setting("provider", "Ollama")
        model = self.backend.get_setting(
            f"{provider.lower()}_model",
            self.backend.get_setting("ollama_model")
        )
        log.write("")
        log.write("[bold #aa44ff]┌────────────────────────────────────────────────────────────────────────┐[/]")
        log.write("[bold #aa44ff]│[/]  [bold white]NEXUS CORE — AI Automation Dashboard[/]                           [bold #aa44ff]│[/]")
        log.write("[bold #aa44ff]│[/]  [dim]Intelligent Command & Integration[/]                                   [bold #aa44ff]│[/]")
        log.write("[bold #aa44ff]└────────────────────────────────────────────────────────────────────────┘[/]")
        log.write(f"[bold purple]Provider:[/] {provider} [dim]|[/] [bold purple]Model:[/] {model}")
        log.write("[dim]Commands: /help, /exec <cmd>, /task <desc>[/]")
        log.write("[dim]Press Escape to return to terminal[/]\n")

        self._refresh_tasks()
        self.query_one("#chat_input").focus()
        
        # Start WhatsApp monitor if bridge is already running
        if self.backend._wa_process and self.backend._wa_process.returncode is None:
            if self._wa_monitor_task is None:
                self._wa_monitor_task = asyncio.create_task(self._wa_event_monitor())

    def action_return_to_terminal(self):
        for screen in self.app.screen_stack:
            if hasattr(screen, "switch_mode"):
                from nextral import Mode
                screen.switch_mode(Mode.GENERAL)
                break
        self.app.pop_screen()

    def on_unmount(self):
        """Clean up background tasks when screen is closed"""
        if self._wa_monitor_task:
            self._wa_monitor_task.cancel()
            self._wa_monitor_task = None

    # ═══════════════════════════════════════════════════════════════════════
    # EVENT HANDLERS
    # ═══════════════════════════════════════════════════════════════════════

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id

        # ── Chat ──
        if bid == "send_btn":
            await self._submit_chat()
        elif bid == "brief_btn":
            await self._daily_brief()

        # ── Exec Confirm ──
        elif bid == "exec_yes":
            await self._exec_confirmed()
        elif bid == "exec_no":
            self._exec_cancelled()

        # ── Email Confirm ──
        elif bid == "email_yes":
            await self._email_confirmed()
        elif bid == "email_no":
            self._email_cancelled()

        # ── Email ──
        elif bid == "fetch_btn":
            await self._fetch_inbox()
        elif bid == "compose_btn":
            self._toggle_compose(True)
        elif bid == "compose_cancel_btn":
            self._toggle_compose(False)
        elif bid == "compose_send_btn":
            await self._send_compose()
        elif bid == "summarize_btn":
            await self._summarize_inbox()

        # ── WhatsApp ──
        elif bid == "wa_start_btn":
            await self._wa_start()
        elif bid == "wa_qr_btn":
            await self._wa_show_qr()
        elif bid == "wa_chats_btn":
            await self._wa_list_chats()
        elif bid == "wa_compose_btn":
            self._wa_toggle_send(True)
        elif bid == "wa_send_cancel_btn":
            self._wa_toggle_send(False)
        elif bid == "wa_send_msg_btn":
            await self._wa_send_message()
        elif bid == "wa_summarize_btn":
            await self._wa_summarize()
        elif bid == "wa_stop_btn":
            await self._wa_stop()

        # ── Files ──
        elif bid == "analyze_btn":
            await self._analyze_file()

        # ── Cyber ──
        elif bid == "cyber_osint_btn":
            self._cyber_show_input("osint", "OSINT Recon", "Target domain or IP")
        elif bid == "cyber_leak_btn":
            self._cyber_show_input("leak", "Leak Check", "Email or domain to check")
        elif bid == "cyber_xray_btn":
            self._cyber_show_input("xray", "Vulnerability X-Ray", "Paste scan data or logs here", "Scan type (portscan/webscan/sniffer)")
        elif bid == "cyber_audit_btn":
            self._cyber_show_input("audit", "Config Audit", "Paste config file contents", "Config type (nginx/ssh/cloud)")
        elif bid == "cyber_sandbox_btn":
            self._cyber_show_input("sandbox", "Malware Sandbox", "Paste suspicious code here")
        elif bid == "cyber_deobf_btn":
            self._cyber_show_input("deobf", "De-Obfuscation", "Paste obfuscated code here")
        elif bid == "cyber_run_btn":
            await self._cyber_run()
        elif bid == "cyber_cancel_btn":
            self._cyber_hide_input()

        # ── Tasks ──
        elif bid == "add_task_btn":
            self._add_task()
        elif bid == "refresh_tasks_btn":
            self._refresh_tasks()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in various inputs"""
        # Chat Input
        if event.input.id == "chat_input":
            await self._submit_chat()
        elif event.input.id == "new_task_input":
            self._add_task()
        elif event.input.id == "file_path_input" or event.input.id == "file_question_input":
            await self._analyze_file()

    # ═══════════════════════════════════════════════════════════════════════
    # CHAT LOGIC
    # ═══════════════════════════════════════════════════════════════════════

    async def _submit_chat(self):
        inp = self.query_one("#chat_input", Input)
        log = self.query_one("#chat_log", RichLog)
        message = inp.value.strip()
        if not message:
            return

        inp.value = ""

        # Handle slash commands
        if message.startswith("/"):
            await self._handle_slash(message, log)
            return

        log.write(f"[bold green]YOU >[/] {message}")
        provider = self.backend.get_setting("provider", "Ollama")
        log.write(f"[dim italic]  ⟳ Thinking via {provider}...[/]")

        response = await self.backend.generate_response(message)
        
        # Format response for display (convert JSON commands to user-friendly messages)
        display_response = self._format_ai_response(response)
        log.write(f"[bold cyan]AI  >[/] {display_response}\n")

        # Check for pending exec command
        if self.backend.pending_command:
            self._show_exec_confirm(self.backend.pending_command)
        
        # Check for pending email
        if self.backend.pending_email:
            self._show_email_confirm(self.backend.pending_email)

    def _format_ai_response(self, response: str) -> str:
        """Convert JSON command/email format to user-friendly messages"""
        import json
        import re
        
        # Check if response contains a command JSON
        try:
            json_match = re.search(r'\{[^{}]*"action"\s*:\s*"exec"[^{}]*"cmd"\s*:\s*"([^"]+)"[^{}]*\}', response)
            if json_match:
                cmd = json_match.group(1)
                return f"[bold magenta]Nexus[/] requested to execute command: [cyan]${cmd}[/]"
        except (json.JSONDecodeError, AttributeError, IndexError):
            pass
        
        # Check if response contains an email JSON
        try:
            json_match = re.search(r'\{[^{}]*"action"\s*:\s*"email"[^{}]*\}', response)
            if json_match:
                return f"[bold magenta]Nexus[/] composed an email to send."
        except (json.JSONDecodeError, AttributeError, IndexError):
            pass
        
        # Return original response if no command/email format found
        return response

    async def _handle_slash(self, message: str, log: RichLog):
        parts = message.split(maxsplit=1)
        cmd = parts[0].lower()

        if cmd == "/help":
            log.write("[bold yellow]Available Commands:[/]")
            log.write("  [cyan]/help[/]           Show this help")
            log.write("  [cyan]/clear[/]          Clear chat history")
            log.write("  [cyan]/brief[/]          Daily briefing")
            log.write("  [cyan]/exec <cmd>[/]     Execute a shell command")
            log.write("  [cyan]/email[/]          Fetch latest emails")
            log.write("  [cyan]/analyze <file>[/] Analyze a file")
            log.write("  [cyan]/tasks[/]          List pending tasks")
            log.write("  [cyan]/provider[/]       Show current AI provider")
            log.write("  [cyan]/wa start[/]       Start WhatsApp bridge")
            log.write("  [cyan]/wa chats[/]       List WhatsApp chats")
            log.write("  [cyan]/wa stop[/]        Stop WhatsApp bridge")
            log.write("")
        elif cmd == "/clear":
            log.clear()
            self.backend.conversation_history.clear()
            log.write("[dim]Chat cleared.[/]\n")
        elif cmd == "/brief":
            await self._daily_brief()
        elif cmd == "/exec":
            if len(parts) > 1:
                self._show_exec_confirm(parts[1])
            else:
                log.write("[yellow]Usage: /exec <command>[/]")
        elif cmd == "/email":
            await self._fetch_inbox()
        elif cmd == "/analyze":
            if len(parts) > 1:
                self.query_one("#file_path_input", Input).value = parts[1]
                await self._analyze_file()
            else:
                log.write("[yellow]Usage: /analyze <filepath>[/]")
        elif cmd == "/tasks":
            self._refresh_tasks()
            log.write("[dim]Check the Tasks tab.[/]")
        elif cmd == "/provider":
            p = self.backend.get_setting("provider", "Ollama")
            m = self.backend.get_setting(f"{p.lower()}_model", "?")
            log.write(f"[cyan]Provider: {p} | Model: {m}[/]\n")
        elif cmd == "/wa":
            arg = parts[1].strip().lower() if len(parts) > 1 else ""
            if arg == "start":
                await self._wa_start()
            elif arg == "chats":
                await self._wa_list_chats()
            elif arg == "stop":
                await self._wa_stop()
            elif arg == "qr":
                await self._wa_show_qr()
            else:
                log.write("[yellow]Usage: /wa start|chats|stop|qr[/]")
        else:
            log.write(f"[yellow]Unknown command: {cmd}. Type /help[/]")

    async def _daily_brief(self):
        log = self.query_one("#chat_log", RichLog)
        log.write("[dim italic]  ⟳ Generating daily brief...[/]")
        brief = await self.backend.daily_brief()
        log.write(f"[bold cyan]{brief}[/]\n")

    # ═══════════════════════════════════════════════════════════════════════
    # TERMINAL CONTROL (EXEC)
    # ═══════════════════════════════════════════════════════════════════════

    def _show_exec_confirm(self, cmd: str):
        """Show beautifully styled confirmation bar for command execution"""
        bar = self.query_one("#exec_confirm_bar")
        preview = self.query_one("#exec_cmd_preview", Static)
        
        # Create a more visually appealing confirmation message
        confirm_text = (
            f"[bold cyan]┌─ COMMAND EXECUTION ─────────────────────────────[/]\n"
            f"[bold cyan]│[/] [yellow]{cmd}[/]\n"
            f"[bold cyan]└──────────────────────────────────────────────────[/]"
        )
        
        preview.update(confirm_text)
        bar.add_class("visible")
        self.backend.pending_command = cmd

    async def _exec_confirmed(self):
        cmd = self.backend.pending_command
        self.backend.pending_command = None
        bar = self.query_one("#exec_confirm_bar")
        bar.remove_class("visible")
        log = self.query_one("#chat_log", RichLog)

        if not cmd:
            return

        log.write(f"[bold yellow]EXEC >[/] {cmd}")
        log.write("[dim italic]  ⟳ Running...[/]")
        output = await self.backend.execute_command(cmd)
        log.write(f"[white]{output}[/]\n")

    def _exec_cancelled(self):
        self.backend.pending_command = None
        bar = self.query_one("#exec_confirm_bar")
        bar.remove_class("visible")
        log = self.query_one("#chat_log", RichLog)
        log.write("[dim]Command cancelled.[/]\n")

    # ═══════════════════════════════════════════════════════════════════════
    # EMAIL COMPOSITION (AI-Requested)
    # ═══════════════════════════════════════════════════════════════════════

    def _show_email_confirm(self, email_data: dict):
        """Show Gmail-like email preview for confirmation"""
        bar = self.query_one("#email_confirm_bar")
        preview = self.query_one("#email_preview", Static)
        
        to = email_data.get("to", "")
        subject = email_data.get("subject", "")
        body = email_data.get("body", "")
        
        # Create a Gmail-like email preview
        from_addr = self.backend.get_setting("smtp_user", "your@email.com")
        
        # Format the body to show preview (truncate long emails)
        body_preview = body[:200] + "..." if len(body) > 200 else body
        body_preview = body_preview.replace("\n", "\n  ")
        
        confirm_text = (
            f"[bold cyan]┌─ EMAIL COMPOSITION ──────────────────────────────[/]\n"
            f"[bold cyan]│[/]\n"
            f"[bold blue]╭─ FROM:[/] [white]{from_addr}[/]\n"
            f"[bold blue]├─ TO:[/]   [yellow]{to}[/]\n"
            f"[bold blue]├─ SUBJ:[/] [cyan]{subject}[/]\n"
            f"[bold blue]├─────────────────────────────────────────────────[/]\n"
            f"[dim]  {body_preview}[/]\n"
            f"[bold cyan]└──────────────────────────────────────────────────[/]"
        )
        
        preview.update(confirm_text)
        bar.add_class("visible")
        self.backend.pending_email = email_data

    async def _email_confirmed(self):
        """Send the composed email"""
        email_data = self.backend.pending_email
        self.backend.pending_email = None
        bar = self.query_one("#email_confirm_bar")
        bar.remove_class("visible")
        log = self.query_one("#chat_log", RichLog)

        if not email_data:
            return

        to = email_data.get("to", "")
        subject = email_data.get("subject", "")
        body = email_data.get("body", "")
        
        log.write(f"[bold cyan]EMAIL >[/] Sending to {to}")
        log.write("[dim italic]  ⟳ Sending email...[/]")
        
        result = await self.backend.send_email(to, subject, body)
        
        if "failed" in result.lower() or "error" in result.lower():
            log.write(f"[red]{result}[/]\n")
        else:
            log.write(f"[bold green]✓ {result}[/]\n")

    def _email_cancelled(self):
        """Cancel email composition"""
        self.backend.pending_email = None
        bar = self.query_one("#email_confirm_bar")
        bar.remove_class("visible")
        log = self.query_one("#chat_log", RichLog)
        log.write("[dim]Email cancelled.[/]\n")

    # ═══════════════════════════════════════════════════════════════════════
    # EMAIL
    # ═══════════════════════════════════════════════════════════════════════

    _cached_emails = []

    async def _fetch_inbox(self):
        log = self.query_one("#email_log", RichLog)
        log.write("[dim italic]  ⟳ Fetching inbox...[/]")

        emails = await self.backend.fetch_emails(15)

        if emails and emails[0].get("error"):
            log.write(f"[red]Error: {emails[0]['error']}[/]")
            return

        if not emails:
            log.write("[yellow]No unread emails.[/]\n")
            return

        self._cached_emails = emails
        log.write(f"[bold green]📧 {len(emails)} unread email(s):[/]\n")

        for i, em in enumerate(emails, 1):
            sender = em.get('from', '?')[:50]
            subj = em.get('subject', '(No Subject)')
            date = em.get('date', '')[:25]
            log.write(f"[bold cyan]  {i}. {subj}[/]")
            log.write(f"     [dim]From: {sender}[/]")
            log.write(f"     [dim]Date: {date}[/]")
            # Preview first 100 chars of body
            body_preview = em.get('body', '')[:100].replace('\n', ' ')
            if body_preview:
                log.write(f"     [dim italic]{body_preview}...[/]")
            log.write("")

    async def _summarize_inbox(self):
        log = self.query_one("#email_log", RichLog)

        if not self._cached_emails:
            log.write("[yellow]Fetch emails first with FETCH INBOX.[/]")
            return

        log.write("[dim italic]  ⟳ Summarizing with AI...[/]")
        summary = await self.backend.summarize_emails(self._cached_emails)
        log.write(f"[bold green]🤖 AI Summary:[/]\n{summary}\n")

    def _toggle_compose(self, show: bool):
        area = self.query_one("#compose_area")
        if show:
            area.add_class("visible")
        else:
            area.remove_class("visible")

    async def _send_compose(self):
        log = self.query_one("#email_log", RichLog)
        to = self.query_one("#compose_to", Input).value.strip()
        subject = self.query_one("#compose_subject", Input).value.strip()
        body = self.query_one("#compose_body", Input).value.strip()

        if not to or not subject:
            log.write("[yellow]To and Subject are required.[/]")
            return

        log.write(f"[dim italic]  ⟳ Sending to {to}...[/]")
        result = await self.backend.send_email(to, subject, body)
        log.write(f"[bold green]{result}[/]\n")

        # Clear fields and hide
        self.query_one("#compose_to", Input).value = ""
        self.query_one("#compose_subject", Input).value = ""
        self.query_one("#compose_body", Input).value = ""
        self._toggle_compose(False)

    # ═══════════════════════════════════════════════════════════════════════
    # FILE ANALYSIS
    # ═══════════════════════════════════════════════════════════════════════

    async def _analyze_file(self):
        log = self.query_one("#file_log", RichLog)
        path = self.query_one("#file_path_input", Input).value.strip()
        question = self.query_one("#file_question_input", Input).value.strip()

        if not path:
            log.write("[yellow]Enter a file path to analyze.[/]")
            return

        log.write(f"[dim italic]  ⟳ Analyzing {path}...[/]")
        result = await self.backend.analyze_file(path, question)
        log.write(f"[bold green]📄 Analysis:[/]\n{result}\n")

    # ═══════════════════════════════════════════════════════════════════════
    # TASKS
    # ═══════════════════════════════════════════════════════════════════════

    def _refresh_tasks(self):
        log = self.query_one("#task_log", RichLog)
        log.clear()
        tasks = self.backend.get_tasks(show_completed=False)

        if not tasks:
            log.write("[dim]No pending tasks. Add one below![/]\n")
            return

        log.write(f"[bold yellow]📋 {len(tasks)} Pending Task(s):[/]\n")
        for t in tasks:
            due = f" [dim](due: {t['due']})[/]" if t.get('due') else ""
            tid = t.get('id', '?')
            log.write(f"  [{tid}] {t['title']}{due}")
        log.write("")

    def _add_task(self):
        inp = self.query_one("#new_task_input", Input)
        title = inp.value.strip()
        if not title:
            return
        self.backend.add_task(title)
        inp.value = ""
        self._refresh_tasks()
        self.notify(f"✓ Task added: {title}", severity="information")

    # ═══════════════════════════════════════════════════════════════════════
    # WHATSAPP
    # ═══════════════════════════════════════════════════════════════════════

    _wa_last_chats = []
    _wa_monitor_task = None

    async def _wa_start(self):
        log = self.query_one("#wa_log", RichLog)
        
        if self._wa_monitor_task is None:
            self._wa_monitor_task = asyncio.create_task(self._wa_event_monitor())
            
        log.write("[dim italic]  ⟳ Starting WhatsApp bridge...[/]")
        result = await self.backend.whatsapp_start()
        log.write(f"[bold green]{result}[/]")
        log.write("")

    async def _wa_event_monitor(self):
        """Background task to drain WhatsApp events and update UI"""
        log = self.query_one("#wa_log", RichLog)
        try:
            while True:
                if self.backend._wa_event_queue:
                    events = await self.backend.whatsapp_drain_events()
                    for ev in events:
                        etype = ev.get("event")
                        if etype == "qr" and ev.get("qrText"):
                            log.write("[bold yellow]Scan this QR code with WhatsApp:[/]")
                            log.write(f"[white]{ev['qrText']}[/]")
                        elif etype == "ready":
                            info = ev.get("info", {})
                            log.write(f"[bold green]✓ Connected as {info.get('name', '?')} ({info.get('number', '?')})[/]")
                        elif etype == "authenticated":
                            log.write("[green]✓ Authenticated successfully![/]")
                        elif etype == "auth_failure":
                            log.write(f"[bold red]✗ Authentication Failure:[/] {ev.get('message', 'Unknown error')}")
                        elif etype == "loading":
                            log.write(f"[dim]Loading: {ev.get('percent', 0)}% - {ev.get('message', '')}[/]")
                        elif etype == "error":
                            log.write(f"[bold red]⚠ Bridge Error:[/] {ev.get('message', 'Unknown error')}")
                        elif etype == "debug":
                            # Only show debug logs if they look like errors or interesting info
                            msg = ev.get("message", "")
                            if "ERROR" in msg.upper() or "CRITICAL" in msg.upper():
                                log.write(f"[red]DEBUG-ERR: {msg}[/]")
                            else:
                                # Optional: log to a separate debug area or just stay silent
                                pass
                        elif etype == "disconnected":
                            log.write(f"[yellow]! WhatsApp Disconnected:[/] {ev.get('reason', 'Unknown reason')}")
                        elif etype == "message":
                            # Maybe notify the user in chat or just log here
                            log.write(f"[dim]Incoming msg from {ev.get('chatName', '?')}: {ev.get('body', '')[:50]}...[/]")
                
                await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            # log.write(f"[red]Monitor Error: {e}[/]")
            pass

    async def _wa_show_qr(self):
        log = self.query_one("#wa_log", RichLog)
        qr = await self.backend.whatsapp_get_qr()
        if qr and "No QR" not in qr:
            log.write("[bold yellow]Current QR Code:[/]")
            log.write(f"[white]{qr}[/]")
        else:
            log.write("[yellow]No QR code available at the moment. It might be authenticating or disconnected.[/]")
        log.write("")

    async def _wa_list_chats(self):
        log = self.query_one("#wa_log", RichLog)
        log.write("[dim italic]  ⟳ Fetching chats...[/]")
        result = await self.backend.whatsapp_get_chats(limit=20)

        if not result.get("ok"):
            log.write(f"[red]Error: {result.get('error', 'Unknown')}[/]")
            return

        chats = result.get("chats", [])
        if not chats:
            log.write("[yellow]No chats found.[/]")
            return

        self._wa_last_chats = chats
        log.write(f"[bold green]💬 {len(chats)} recent chat(s):[/]\n")

        for i, c in enumerate(chats, 1):
            name = c.get('name', 'Unknown')
            unread = c.get('unread', 0)
            last_msg = c.get('lastMsg', '')[:60]
            chat_id = c.get('id', '')
            group_tag = " [dim](group)[/]" if c.get('isGroup') else ""
            unread_tag = f" [bold red]({unread} unread)[/]" if unread > 0 else ""

            log.write(f"[bold cyan]  {i}. {name}{group_tag}{unread_tag}[/]")
            log.write(f"     [dim]ID: {chat_id}[/]")
            if last_msg:
                log.write(f"     [dim italic]{last_msg}[/]")
            log.write("")

    def _wa_toggle_send(self, show: bool):
        area = self.query_one("#wa_send_area")
        if show:
            area.add_class("visible")
        else:
            area.remove_class("visible")

    async def _wa_send_message(self):
        log = self.query_one("#wa_log", RichLog)
        chat_id = self.query_one("#wa_chat_id", Input).value.strip()
        body = self.query_one("#wa_msg_body", Input).value.strip()

        if not chat_id or not body:
            log.write("[yellow]Chat ID and message body are required.[/]")
            return

        log.write(f"[dim italic]  ⟳ Sending to {chat_id[:20]}...[/]")
        result = await self.backend.whatsapp_send_message(chat_id, body)

        if result.get("ok"):
            log.write(f"[bold green]✓ Message sent! ID: {result.get('messageId', '?')}[/]\n")
            self.query_one("#wa_msg_body", Input).value = ""
            self._wa_toggle_send(False)
        else:
            log.write(f"[red]Send failed: {result.get('error', 'Unknown')}[/]")

    async def _wa_summarize(self):
        log = self.query_one("#wa_log", RichLog)

        if not self._wa_last_chats:
            log.write("[yellow]Fetch chats first with the CHATS button.[/]")
            return

        # Summarize the first chat with unread messages, or the first chat
        target = None
        for c in self._wa_last_chats:
            if c.get('unread', 0) > 0:
                target = c
                break
        if not target:
            target = self._wa_last_chats[0]

        chat_id = target.get('id', '')
        name = target.get('name', 'Unknown')
        log.write(f"[dim italic]  ⟳ Summarizing chat with {name}...[/]")
        summary = await self.backend.whatsapp_summarize_chat(chat_id)
        log.write(f"[bold green]🤖 {name} — Summary:[/]\n{summary}\n")

    async def _wa_stop(self):
        log = self.query_one("#wa_log", RichLog)
        log.write("[dim italic]  ⟳ Stopping WhatsApp bridge...[/]")
        result = await self.backend.whatsapp_stop()
        log.write(f"[bold yellow]{result}[/]\n")

    # ═══════════════════════════════════════════════════════════════════════
    # CYBER COMMAND CENTER
    # ═══════════════════════════════════════════════════════════════════════

    _cyber_mode = None  # "osint", "leak", "xray", "audit", "sandbox", "deobf"

    def _cyber_show_input(self, mode: str, title: str, placeholder: str, extra_placeholder: str = ""):
        """Show the input area configured for a specific cyber tool"""
        self._cyber_mode = mode
        area = self.query_one("#cyber_input_area")
        area.add_class("visible")
        self.query_one("#cyber_input_title", Label).update(f"🛡 {title}")
        self.query_one("#cyber_input_main", Input).placeholder = placeholder
        self.query_one("#cyber_input_main", Input).value = ""
        extra = self.query_one("#cyber_input_extra", Input)
        if extra_placeholder:
            extra.placeholder = extra_placeholder
            extra.display = True
        else:
            extra.display = False
        extra.value = ""

    def _cyber_hide_input(self):
        self._cyber_mode = None
        self.query_one("#cyber_input_area").remove_class("visible")

    async def _cyber_run(self):
        """Dispatch the current cyber tool based on _cyber_mode"""
        log = self.query_one("#cyber_log", RichLog)
        main_val = self.query_one("#cyber_input_main", Input).value.strip()
        extra_val = self.query_one("#cyber_input_extra", Input).value.strip()

        if not main_val:
            log.write("[yellow]Please enter input before running.[/]")
            return

        self._cyber_hide_input()
        mode = self._cyber_mode or "osint"

        if mode == "osint":
            await self._cyber_osint(main_val, log)
        elif mode == "leak":
            await self._cyber_leak(main_val, log)
        elif mode == "xray":
            await self._cyber_xray(main_val, extra_val, log)
        elif mode == "audit":
            await self._cyber_audit(main_val, extra_val, log)
        elif mode == "sandbox":
            await self._cyber_sandbox(main_val, log)
        elif mode == "deobf":
            await self._cyber_deobf(main_val, log)

    async def _cyber_osint(self, target: str, log):
        log.write(f"[bold red]{'═' * 60}[/]")
        log.write(f"[bold red]  🔍 OSINT RECONNAISSANCE: {target}[/]")
        log.write(f"[bold red]{'═' * 60}[/]")
        log.write("[dim italic]  ⟳ Running DNS, port scan, headers, NSLookup...[/]\n")

        # Phase 1: Raw results
        results = await self.backend.osint_recon(target)

        # Display raw findings
        if results["dns"].get("ips"):
            log.write(f"[cyan]📡 DNS IPs:[/] {', '.join(results['dns']['ips'])}")
        if results["dns"].get("fqdn"):
            log.write(f"[cyan]📡 FQDN:[/] {results['dns']['fqdn']}")
        if results["dns"].get("reverse"):
            for r in results["dns"]["reverse"]:
                log.write(f"[cyan]📡 Reverse:[/] {r['ip']} → {r['hostname']}")

        if results["ports"]:
            svc = {21:"FTP",22:"SSH",23:"Telnet",25:"SMTP",53:"DNS",80:"HTTP",
                   110:"POP3",143:"IMAP",443:"HTTPS",445:"SMB",3306:"MySQL",
                   3389:"RDP",5432:"PostgreSQL",8080:"HTTP-ALT",8443:"HTTPS-ALT"}
            for p in results["ports"]:
                log.write(f"[green]  ◉ Port {p} OPEN[/] — {svc.get(p, 'Unknown')}")
        else:
            log.write("[dim]  No common ports responded.[/]")

        if results.get("headers"):
            for k in ["Server", "X-Powered-By", "Content-Security-Policy", "status_code"]:
                if k in results["headers"]:
                    log.write(f"[yellow]  Header {k}:[/] {results['headers'][k]}")

        if results.get("whois", {}).get("nslookup"):
            log.write(f"\n[dim]NSLookup:\n{results['whois']['nslookup']}[/]")

        # Phase 2: AI Analysis
        log.write("\n[dim italic]  ⟳ AI analyzing attack surface...[/]")
        ai_report = await self.backend.osint_recon_with_ai(target)
        log.write(f"\n[bold red]🤖 AI THREAT ASSESSMENT:[/]\n{ai_report}\n")

    async def _cyber_leak(self, query: str, log):
        log.write(f"[bold red]{'═' * 60}[/]")
        log.write(f"[bold red]  💧 LEAK CHECK: {query}[/]")
        log.write(f"[bold red]{'═' * 60}[/]")
        log.write("[dim italic]  ⟳ Consulting AI for breach intelligence...[/]\n")

        result = await self.backend.osint_leak_check(query)
        log.write(f"[bold yellow]🤖 Leak Intelligence:[/]\n{result}\n")

    async def _cyber_xray(self, data: str, scan_type: str, log):
        scan_type = scan_type or "general"
        log.write(f"[bold red]{'═' * 60}[/]")
        log.write(f"[bold red]  🛡 VULNERABILITY X-RAY ({scan_type.upper()})[/]")
        log.write(f"[bold red]{'═' * 60}[/]")
        log.write("[dim italic]  ⟳ AI analyzing scan results for CVEs and risks...[/]\n")

        result = await self.backend.xray_analyze_scan(scan_type, data)
        log.write(f"[bold red]🤖 X-Ray Analysis:[/]\n{result}\n")

    async def _cyber_audit(self, config: str, config_type: str, log):
        config_type = config_type or "unknown"
        log.write(f"[bold red]{'═' * 60}[/]")
        log.write(f"[bold red]  🔧 CONFIG SECURITY AUDIT ({config_type.upper()})[/]")
        log.write(f"[bold red]{'═' * 60}[/]")
        log.write("[dim italic]  ⟳ AI reviewing configuration for misconfigurations...[/]\n")

        result = await self.backend.xray_audit_config(config, config_type)
        log.write(f"[bold red]🤖 Audit Results:[/]\n{result}\n")

    async def _cyber_sandbox(self, code: str, log):
        log.write(f"[bold red]{'═' * 60}[/]")
        log.write(f"[bold red]  📦 MALWARE SANDBOX ANALYSIS[/]")
        log.write(f"[bold red]{'═' * 60}[/]")

        # Phase 1: Heuristic scan (instant)
        log.write("[dim italic]  ⟳ Running heuristic pattern scan...[/]\n")
        heuristics = self.backend.malware_heuristic_scan(code)

        # Display heuristic results
        threat = heuristics["threat_level"]
        color = {"CLEAN":"green","LOW":"yellow","MEDIUM":"#ff8800","HIGH":"red","CRITICAL":"bold red"}.get(threat, "white")
        log.write(f"[{color}]  ⚠ THREAT LEVEL: {threat} (Score: {heuristics['score']})[/]")

        if heuristics["categories_hit"]:
            log.write(f"[yellow]  Categories: {', '.join(heuristics['categories_hit'])}[/]\n")

        for f in heuristics["findings"][:15]:
            cat_color = {"credential_theft":"red","privilege_escalation":"red","network_c2":"red",
                         "evasion":"#ff8800","persistence":"#ff8800","registry_access":"yellow","file_ops":"yellow"}.get(f["category"], "white")
            log.write(f"[{cat_color}]  [{f['category'].upper()}] Line {f['line']}:[/] {f['context'][:80]}")

        # Phase 2: AI analysis
        log.write("\n[dim italic]  ⟳ AI performing deep behavior analysis...[/]")
        ai_result = await self.backend.malware_analyze(code)
        log.write(f"\n[bold red]🤖 AI Verdict:[/]\n{ai_result}\n")

    async def _cyber_deobf(self, code: str, log):
        log.write(f"[bold red]{'═' * 60}[/]")
        log.write(f"[bold red]  🔓 CODE DE-OBFUSCATION[/]")
        log.write(f"[bold red]{'═' * 60}[/]")
        log.write("[dim italic]  ⟳ AI reverse-engineering obfuscated code...[/]\n")

        result = await self.backend.malware_deobfuscate(code)
        log.write(f"[bold yellow]🤖 De-Obfuscation Result:[/]\n{result}\n")
