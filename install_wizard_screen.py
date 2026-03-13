"""
install_wizard_screen.py — Nextral Integrated Install Wizard

A built-in wizard to install/configure Nextral and external tools.
Hybrid platform support with Linux focus.
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical, Horizontal, Container, ScrollableContainer
from textual.widgets import (
    Header, Footer, Static, Button, Input, RichLog, Label,
    ProgressBar, Checkbox
)
from textual.binding import Binding
from textual.reactive import reactive
from textual import work
import subprocess
import sys
import os
import shutil
import platform
import json
from pathlib import Path


class InstallWizardScreen(Screen):
    """Professional Installation Wizard for Nextral — Linux-Focused, Cross-Platform"""

    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("r", "start_install", "Run Install"),
    ]

    CSS = """
    InstallWizardScreen {
        background: #080810;
    }

    /* ── Header bar ── */
    #wizard_header {
        width: 100%;
        height: 5;
        background: #0a1a2e;
        border-bottom: heavy #00e5ff;
        padding: 1 2;
    }
    .wiz-title {
        color: #00e5ff;
        text-style: bold;
    }
    .wiz-subtitle {
        color: #555577;
    }

    /* ── Main layout ── */
    #wiz_main {
        height: 1fr;
        layout: grid;
        grid-size: 2 1;
        grid-columns: 1fr 2fr;
    }

    /* ── Steps panel (left) ── */
    #steps_panel {
        border: solid #1565c0;
        padding: 1;
        background: #050d18;
    }
    .steps-title {
        color: #00e5ff;
        text-style: bold;
        margin-bottom: 1;
    }

    .step_button {
        width: 100%;
        height: 3;
        margin: 0 0 1 0;
        background: #0d2847;
        color: #90caf9;
    }
    .step_button:hover {
        background: #1565c0;
    }
    .step_button.active {
        background: #1976d2;
        color: white;
    }

    /* ── Action buttons ── */
    .action_btn {
        width: 100%;
        height: 3;
        margin: 1 0 0 0;
    }

    /* ── Right panel ── */
    #right_panel {
        border: solid #0d47a1;
        padding: 1;
        background: #030810;
    }

    #log_area {
        height: 1fr;
        background: #020508;
        border: solid #0d47a1;
    }

    /* ── Options box ── */
    #options_box {
        border: solid #1565c0;
        margin: 1 0;
        padding: 1;
        background: #0a1525;
        height: auto;
    }
    .opt-title {
        color: #00e5ff;
        text-style: bold;
        margin-bottom: 1;
    }

    Checkbox {
        margin-bottom: 0;
        color: #aaaacc;
    }
    Checkbox.-on {
        color: #00e5ff;
    }

    /* ── Config section ── */
    #config_section {
        border: solid #1565c0;
        margin: 1 0 0 0;
        padding: 1;
        background: #0a1525;
        height: auto;
    }
    .config-title {
        color: #00e5ff;
        text-style: bold;
        margin-bottom: 1;
    }
    .input_label {
        color: #aaaacc;
    }

    Input {
        margin-bottom: 1;
    }

    /* ── Status bar ── */
    #status_bar {
        dock: bottom;
        height: 1;
        background: #0a1a2e;
        color: #555577;
        padding: 0 2;
    }

    Footer {
        background: #0a1a2e;
        color: #64b5f6;
    }
    """

    current_step = reactive(1)
    installing = reactive(False)

    STEPS = [
        ("1", "Platform Check", "Detect OS & architecture"),
        ("2", "Dependencies", "Install Python packages"),
        ("3", "Security Tools", "Find/install ext. tools"),
        ("4", "Configuration", "Personalize Nextral"),
    ]

    def __init__(self):
        super().__init__()
        self.detected_platform = ""
        self.python_cmd = sys.executable

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Container(id="wizard_header"):
            yield Static("◈  NEXTRAL INSTALLATION WIZARD  ◈", classes="wiz-title")
            yield Static("Professional setup & dependency manager — Linux-focused, cross-platform", classes="wiz-subtitle")

        with Container(id="wiz_main"):
            # ── Left: Steps ──
            with Container(id="steps_panel"):
                yield Label("INSTALLATION STEPS", classes="steps-title")

                for step_num, step_title, step_desc in self.STEPS:
                    yield Button(
                        f"[bold]{step_num}[/] {step_title}\n[dim]{step_desc}[/]",
                        id=f"step_{step_num}",
                        classes="step_button"
                    )

                yield Button(
                    "▶ START INSTALLATION",
                    id="start_btn", variant="success", classes="action_btn"
                )
                yield Button(
                    "↺ CHECK STATUS",
                    id="check_btn", variant="default", classes="action_btn"
                )

            # ── Right: Log + Options ──
            with ScrollableContainer(id="right_panel"):
                yield Label("INSTALLATION LOG", classes="steps-title")
                yield RichLog(id="log_area", markup=True, wrap=True, max_lines=3000)

                # ── Options (PATH, Desktop, etc.) ──
                with Container(id="options_box"):
                    yield Label("⚙️  INSTALLATION OPTIONS", classes="opt-title")
                    yield Checkbox("Add Nextral to system PATH", id="opt_path", value=True)
                    yield Checkbox("Create desktop shortcut / .desktop entry", id="opt_shortcut", value=True)
                    yield Checkbox("Install missing Python packages", id="opt_deps", value=True)

                # ── Quick Config ──
                with Container(id="config_section"):
                    yield Label("🎨  QUICK CONFIGURATION", classes="config-title")
                    yield Label("Username:", classes="input_label")
                    yield Input(id="config_username", placeholder="Your name", value="USER")
                    yield Label("Theme Color:", classes="input_label")
                    yield Input(id="config_theme", placeholder="cyan", value="cyan")

        yield Static("Ready. Configure options and click START INSTALLATION.", id="status_bar")
        yield Footer()

    def on_mount(self) -> None:
        self._update_status("[cyan]Welcome to Nextral Installation Wizard![/]")
        self._log("[bold cyan]╔════════════════════════════════════════════════════════════════╗[/]")
        self._log("[bold cyan]║[/]         [bold white]NEXTRAL TERMINAL — INSTALLATION WIZARD[/]              [bold cyan]║[/]")
        self._log("[bold cyan]╚════════════════════════════════════════════════════════════════╝[/]")
        self._log("")
        self._log("[yellow]This wizard will install Nextral and configure your environment.[/]")
        self._log("[yellow]It supports Linux, macOS, and Windows.[/]")
        self._log("")
        self._log("[cyan]Click [bold]START INSTALLATION[/] or select a step from the left.[/]")
        self._detect_platform()

    def _log(self, message: str) -> None:
        try:
            self.query_one("#log_area", RichLog).write(message)
        except Exception:
            pass

    def _update_status(self, message: str) -> None:
        try:
            self.query_one("#status_bar", Static).update(message)
        except Exception:
            pass

    # ══════════════════════════════════════════════════════════════════════════
    #  PLATFORM DETECTION
    # ══════════════════════════════════════════════════════════════════════════
    def _detect_platform(self) -> None:
        system = platform.system().lower()
        self.detected_platform = system

        self._log("")
        self._log("[bold]Platform Detection:[/]")

        if system == "linux":
            self._log("[green]✓ Linux detected[/]")
            try:
                distro = platform.freedesktop_os_release().get('NAME', 'Unknown')
            except Exception:
                distro = "Unknown"
            self._log(f"  Distribution: {distro}")
            self._log(f"  Kernel: {platform.release()}")
            self._log(f"  Machine: {platform.machine()}")

            # Detect package manager
            pkg_mgrs = [
                ("apt", "apt-get"),
                ("dnf", "dnf"),
                ("yum", "yum"),
                ("pacman", "pacman"),
                ("zypper", "zypper"),
                ("apk", "apk"),
            ]
            found_pm = None
            for name, cmd in pkg_mgrs:
                if shutil.which(cmd):
                    found_pm = name
                    break
            if found_pm:
                self._log(f"  [green]✓[/] Package manager: {found_pm}")
            else:
                self._log(f"  [yellow]⚠[/] No known package manager detected")

        elif system == "windows":
            self._log("[green]✓ Windows detected[/]")
            self._log(f"  Version: {platform.version()}")
            self._log(f"  Machine: {platform.machine()}")
        elif system == "darwin":
            self._log("[green]✓ macOS detected[/]")
            self._log(f"  Version: {platform.mac_ver()[0]}")
        else:
            self._log(f"[yellow]⚠ Unknown platform: {system}[/]")

        self._log(f"  Python: {sys.version.split()[0]}")
        self._log("")

    # ══════════════════════════════════════════════════════════════════════════
    #  INSTALLATION
    # ══════════════════════════════════════════════════════════════════════════
    def action_start_install(self) -> None:
        if self.installing:
            return
        self.installing = True
        self._update_status("[yellow]Installation in progress...[/]")
        self._run_installation()

    @work(thread=True)
    def _run_installation(self):
        """Run the full installation process."""
        self._log("")
        self._log("[bold yellow]═══════════════════════════════════════════════════════════════[/]")
        self._log("[bold yellow]  STARTING INSTALLATION...[/]")
        self._log("[bold yellow]═══════════════════════════════════════════════════════════════[/]")
        self._log("")

        # ── Step 1: Platform ─────────────────────────────────────────────────
        self._log("[bold cyan]STEP 1: Platform Verification[/]")
        self._log(f"  Detected: {self.detected_platform}")
        self._log("[green]✓ Platform verified[/]")
        self._log("")

        # ── Step 2: Dependencies ─────────────────────────────────────────────
        install_deps = True
        try:
            install_deps = self.query_one("#opt_deps", Checkbox).value
        except Exception:
            pass

        self._log("[bold cyan]STEP 2: Python Dependencies[/]")
        if install_deps:
            deps = [
                "textual", "rich", "psutil", "pyperclip",
                "pillow", "jinja2", "aiohttp", "httpx", "pyfiglet"
            ]
            for dep in deps:
                self._log(f"  Installing {dep}...")
                try:
                    result = subprocess.run(
                        [sys.executable, "-m", "pip", "install", dep, "--quiet"],
                        capture_output=True, timeout=120
                    )
                    if result.returncode == 0:
                        self._log(f"    [green]✓ {dep}[/]")
                    else:
                        self._log(f"    [yellow]⚠ {dep} (may already be installed)[/]")
                except Exception:
                    self._log(f"    [red]✗ {dep} FAILED[/]")
            self._log("[green]✓ Dependencies installed[/]")
        else:
            self._log("  [dim]Skipped (unchecked)[/]")
        self._log("")

        # ── Step 3: External Tools ───────────────────────────────────────────
        self._log("[bold cyan]STEP 3: External Security Tools[/]")
        self._log("  Checking installed tools...")

        tools = [
            ("nmap", "Network Mapper"),
            ("nc", "Netcat"),
            ("tcpdump", "Packet Analyzer"),
            ("openssl", "OpenSSL"),
            ("curl", "cURL"),
            ("wget", "Wget"),
            ("ssh", "SSH Client"),
            ("hydra", "Hydra"),
            ("nikto", "Nikto"),
        ]

        missing = []
        for tool_cmd, tool_name in tools:
            path = shutil.which(tool_cmd)
            if path:
                self._log(f"  [green]✓[/] {tool_name}: {path}")
            else:
                self._log(f"  [red]✗[/] {tool_name}: Not found")
                missing.append(tool_cmd)

        self._log("")
        if missing:
            self._log("[yellow]To install missing tools:[/]")
            if self.detected_platform == "linux":
                # Detect package manager and show the right command
                if shutil.which("apt-get"):
                    self._log(f"    sudo apt-get install {' '.join(missing)}")
                elif shutil.which("dnf"):
                    self._log(f"    sudo dnf install {' '.join(missing)}")
                elif shutil.which("pacman"):
                    self._log(f"    sudo pacman -S {' '.join(missing)}")
                elif shutil.which("yum"):
                    self._log(f"    sudo yum install {' '.join(missing)}")
                else:
                    self._log(f"    Use your package manager to install: {', '.join(missing)}")
            elif self.detected_platform == "windows":
                self._log(f"    choco install {' '.join(missing)}")
            elif self.detected_platform == "darwin":
                self._log(f"    brew install {' '.join(missing)}")
        else:
            self._log("[green]✓ All tools detected![/]")
        self._log("")

        # ── Step 4: Configuration ────────────────────────────────────────────
        self._log("[bold cyan]STEP 4: Configuration[/]")

        try:
            username = self.query_one("#config_username", Input).value
            theme = self.query_one("#config_theme", Input).value

            config_path = Path("terminal_config.json")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
            else:
                config = {}

            config.setdefault("user", {})
            config["user"]["username"] = username
            config["user"]["theme_color"] = theme

            config.setdefault("external_tools", {})
            for tool_cmd, _ in tools:
                path = shutil.which(tool_cmd)
                if path:
                    config["external_tools"][tool_cmd] = path

            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)

            self._log(f"  [green]✓[/] Username: {username}")
            self._log(f"  [green]✓[/] Theme: {theme}")
            self._log(f"  [green]✓[/] Tool paths auto-detected and saved")
            self._log(f"  [green]✓[/] Configuration saved to {config_path}")
        except Exception as e:
            self._log(f"  [red]✗[/] Configuration error: {e}")

        self._log("")

        # ── PATH integration ─────────────────────────────────────────────────
        add_path = False
        try:
            add_path = self.query_one("#opt_path", Checkbox).value
        except Exception:
            pass

        if add_path:
            self._log("[bold cyan]STEP 5: PATH Integration[/]")
            install_dir = str(Path.cwd())

            if self.detected_platform == "linux" or self.detected_platform == "darwin":
                export_line = f'\n# Added by Nextral Installer\nexport PATH="$PATH:{install_dir}"\n'
                profiles_updated = []
                home = Path.home()

                for rc_file in [".bashrc", ".zshrc", ".profile"]:
                    rc_path = home / rc_file
                    if rc_path.exists():
                        content = rc_path.read_text()
                        if install_dir not in content:
                            try:
                                with open(rc_path, "a") as f:
                                    f.write(export_line)
                                profiles_updated.append(rc_file)
                            except Exception:
                                pass

                if profiles_updated:
                    self._log(f"  [green]✓[/] Added to PATH in: {', '.join(profiles_updated)}")
                    self._log(f"  [dim]  Run 'source ~/{profiles_updated[0]}' or open a new terminal[/]")
                else:
                    self._log("  [dim]Already in PATH or no shell profile found[/]")

            elif self.detected_platform == "windows":
                try:
                    import winreg
                    key = winreg.OpenKey(
                        winreg.HKEY_CURRENT_USER, r"Environment",
                        0, winreg.KEY_ALL_ACCESS
                    )
                    try:
                        current_path, _ = winreg.QueryValueEx(key, "Path")
                    except FileNotFoundError:
                        current_path = ""

                    paths = [p.strip().rstrip("\\") for p in current_path.split(";") if p.strip()]
                    if install_dir.rstrip("\\").lower() not in [p.lower() for p in paths]:
                        new_path = current_path.rstrip(";") + ";" + install_dir
                        winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
                        self._log(f"  [green]✓[/] Added to user PATH (Registry)")
                    else:
                        self._log(f"  [dim]Already in PATH[/]")
                    winreg.CloseKey(key)
                except Exception as e:
                    self._log(f"  [yellow]⚠[/] Could not add to PATH: {e}")

            self._log("")

        # ── Desktop shortcut ─────────────────────────────────────────────────
        add_shortcut = False
        try:
            add_shortcut = self.query_one("#opt_shortcut", Checkbox).value
        except Exception:
            pass

        if add_shortcut:
            self._log("[bold cyan]STEP 6: Desktop Shortcut[/]")
            cwd = Path.cwd()
            icon_path = cwd / "icon.png"

            if self.detected_platform == "linux" or self.detected_platform == "darwin":
                exe_path = cwd / "Nextral"
                if not exe_path.exists():
                    exe_path = cwd / "dist" / "Nextral"

                desktop_entry = (
                    f"[Desktop Entry]\n"
                    f"Name=Nextral\n"
                    f"Comment=Nextral Terminal — Advanced offensive security platform\n"
                    f"Exec={exe_path}\n"
                    f"Icon={icon_path}\n"
                    f"Terminal=true\n"
                    f"Type=Application\n"
                    f"Categories=System;TerminalEmulator;Security;\n"
                    f"StartupNotify=true\n"
                )

                # Application menu
                app_dir = Path.home() / ".local" / "share" / "applications"
                app_dir.mkdir(parents=True, exist_ok=True)
                desktop_file = app_dir / "nextral.desktop"
                try:
                    desktop_file.write_text(desktop_entry)
                    os.chmod(desktop_file, 0o755)
                    self._log(f"  [green]✓[/] App menu entry: {desktop_file}")
                except Exception as e:
                    self._log(f"  [yellow]⚠[/] App menu entry failed: {e}")

                # Desktop
                desktop_dir = Path.home() / "Desktop"
                if desktop_dir.exists():
                    desk_file = desktop_dir / "nextral.desktop"
                    try:
                        desk_file.write_text(desktop_entry)
                        os.chmod(desk_file, 0o755)
                        # GNOME trust
                        try:
                            subprocess.run(
                                ["gio", "set", str(desk_file), "metadata::trusted", "true"],
                                capture_output=True, timeout=5
                            )
                        except Exception:
                            pass
                        self._log(f"  [green]✓[/] Desktop shortcut: {desk_file.name}")
                    except Exception as e:
                        self._log(f"  [yellow]⚠[/] Desktop shortcut failed: {e}")

            elif self.detected_platform == "windows":
                exe_path = cwd / "Nextral.exe"
                if not exe_path.exists():
                    exe_path = cwd / "dist" / "Nextral.exe"

                try:
                    import tempfile
                    desktop = Path(os.environ.get("USERPROFILE", "~")) / "Desktop"
                    lnk_path = desktop / "Nextral.lnk"
                    vbs = (
                        f'Set ws = CreateObject("WScript.Shell")\n'
                        f'Set sc = ws.CreateShortcut("{lnk_path}")\n'
                        f'sc.TargetPath = "{exe_path}"\n'
                        f'sc.WorkingDirectory = "{cwd}"\n'
                        f'sc.Description = "Nextral Terminal"\n'
                        f'sc.Save\n'
                    )
                    vbs_file = Path(tempfile.gettempdir()) / f"nextral_sc_{os.getpid()}.vbs"
                    vbs_file.write_text(vbs, encoding="utf-8")
                    subprocess.run(["cscript", "//nologo", str(vbs_file)], capture_output=True, timeout=10)
                    vbs_file.unlink(missing_ok=True)
                    self._log(f"  [green]✓[/] Desktop shortcut: {lnk_path.name}")
                except Exception as e:
                    self._log(f"  [yellow]⚠[/] Desktop shortcut failed: {e}")

            self._log("")

        # ── Done ─────────────────────────────────────────────────────────────
        self._log("[bold green]═══════════════════════════════════════════════════════════════[/]")
        self._log("[bold green]  ✓  INSTALLATION COMPLETE![/]")
        self._log("[bold green]═══════════════════════════════════════════════════════════════[/]")
        self._log("")
        self._log("[bold cyan]Next steps:[/]")
        if self.detected_platform == "linux" or self.detected_platform == "darwin":
            self._log("  1. Run [yellow]python3 nextral.py[/] to start Nextral")
            self._log("  2. Or run [yellow]./dist/Nextral[/] if you built the executable")
            if add_path:
                self._log("  3. Open a [bold]new terminal[/] and type [yellow]Nextral[/]")
        else:
            self._log("  1. Run [yellow]python nextral.py[/] to start Nextral")
            self._log("  2. Or run [yellow]dist\\Nextral.exe[/] if you built the executable")
        self._log("")

        self.installing = False
        self._update_status("[green]✓ Installation complete![/]")

    def action_close(self) -> None:
        self.app.pop_screen()

    # ══════════════════════════════════════════════════════════════════════════
    #  BUTTON HANDLERS
    # ══════════════════════════════════════════════════════════════════════════
    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id

        if btn_id == "start_btn":
            self.action_start_install()

        elif btn_id == "check_btn":
            self._log("")
            self._log("[bold cyan]═══════════════════════════════════════════════════════════════[/]")
            self._log("[bold cyan]  SYSTEM STATUS CHECK[/]")
            self._log("[bold cyan]═══════════════════════════════════════════════════════════════[/]")
            self._log("")

            self._log(f"[bold]Python:[/] {sys.version.split()[0]}")
            self._log(f"[bold]Platform:[/] {platform.system()} {platform.release()} ({platform.machine()})")
            self._log("")

            # Python deps
            self._log("[bold]Python Packages:[/]")
            deps_check = ["textual", "rich", "psutil", "pyperclip", "pillow", "pyfiglet"]
            for dep in deps_check:
                try:
                    mod = __import__(dep)
                    ver = getattr(mod, '__version__', '?')
                    self._log(f"  [green]✓[/] {dep} ({ver})")
                except ImportError:
                    self._log(f"  [red]✗[/] {dep}")

            self._log("")
            self._log("[bold]External Tools:[/]")
            tools = ["nmap", "nc", "tcpdump", "openssl", "curl", "wget", "ssh", "hydra", "nikto"]
            for tool in tools:
                path = shutil.which(tool)
                if path:
                    self._log(f"  [green]✓[/] {tool}: {path}")
                else:
                    self._log(f"  [red]✗[/] {tool}: Not found")

            # PATH check
            self._log("")
            self._log("[bold]PATH Check:[/]")
            cwd = str(Path.cwd())
            if cwd in os.environ.get("PATH", ""):
                self._log(f"  [green]✓[/] Current directory is in PATH")
            else:
                self._log(f"  [yellow]⚠[/] Current directory is NOT in PATH")

            self._log("")

        elif btn_id and btn_id.startswith("step_"):
            step_num = btn_id.split("_")[1]
            self.current_step = int(step_num)

            if step_num == "1":
                self._detect_platform()
            elif step_num == "2":
                self._log("[cyan]Dependencies will be installed during full installation.[/]")
            elif step_num == "3":
                self._log("[cyan]External tools check will run during installation.[/]")
            elif step_num == "4":
                self._log("[cyan]Configuration can be customized in the panel on the right.[/]")
