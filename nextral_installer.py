"""
Nextral Installer — Professional Cross-Platform Setup Wizard
Made by InvariantDev

A beautiful GUI installer that bundles Nextral.exe and installs it to a
user-chosen directory, with support for:
  • Add to PATH (Windows Registry / Linux shell profile)
  • Desktop shortcut (.lnk via VBScript on Windows / .desktop on Linux)
  • Custom application name
  • Icon embedding
  • Progress logging
"""

import os
import sys
import shutil
import platform
import json
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from pathlib import Path
import threading
import subprocess
import tempfile

# ══════════════════════════════════════════════════════════════════════════════
#  BRANDING — edit these to customise the installer
# ══════════════════════════════════════════════════════════════════════════════
APP_NAME        = "Nextral"
APP_VERSION     = "2.0"
APP_AUTHOR      = "InvariantDev"
EXE_NAME_WIN    = "Nextral.exe"
EXE_NAME_LINUX  = "Nextral"
ICON_FILENAME   = "icon.png"


def get_resource_path(relative_path: str) -> Path:
    """Get absolute path to bundled resource (supports PyInstaller _MEIPASS)."""
    if hasattr(sys, '_MEIPASS'):
        return Path(sys._MEIPASS) / relative_path
    return Path(__file__).parent / relative_path


class AnimatedButton(tk.Button):
    """A button with hover animation."""

    def __init__(self, master, normal_bg, hover_bg, **kwargs):
        super().__init__(master, bg=normal_bg, activebackground=hover_bg, **kwargs)
        self._normal = normal_bg
        self._hover = hover_bg
        self.bind("<Enter>", lambda e: self.config(bg=hover_bg))
        self.bind("<Leave>", lambda e: self.config(bg=normal_bg))


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN INSTALLER CLASS
# ══════════════════════════════════════════════════════════════════════════════

class NextralInstaller:
    """Professional GUI Installer for Nextral Terminal"""

    # ── Palette ──────────────────────────────────────────────────────────────
    BG          = "#0a0a12"
    BG_PANEL    = "#0f0f1a"
    BG_INPUT    = "#16162a"
    BG_LOG      = "#08080f"
    ACCENT      = "#00e5a0"
    ACCENT_DIM  = "#00b87a"
    ACCENT2     = "#00e5ff"
    FG          = "#e0e0e0"
    FG_DIM      = "#666680"
    BLUE        = "#4488ff"
    BORDER      = "#1e1e38"
    WARN        = "#ffaa00"
    ERR         = "#ff5555"

    def __init__(self):
        self.platform = platform.system().lower()
        self.install_dir = ""
        self.is_installing = False

        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} Installer")
        self.root.geometry("820x680")
        self.root.resizable(False, False)
        self.root.configure(bg=self.BG)

        # ── Try to set the window icon ──
        icon_path = get_resource_path(ICON_FILENAME)
        if icon_path.exists():
            try:
                img = tk.PhotoImage(file=str(icon_path))
                self.root.iconphoto(True, img)
                self._icon_img = img  # prevent GC
            except Exception:
                pass

        self._inject_styles()
        self._center_window()
        self._build_ui()
        self._write_initial_log()

    # ── Styles ───────────────────────────────────────────────────────────────
    def _inject_styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(
            "Custom.Horizontal.TProgressbar",
            troughcolor=self.BG_INPUT,
            background=self.ACCENT,
            bordercolor=self.BORDER,
            lightcolor=self.ACCENT,
            darkcolor=self.ACCENT_DIM,
        )

    def _center_window(self):
        self.root.update_idletasks()
        w, h = 820, 680
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    # ══════════════════════════════════════════════════════════════════════════
    #  UI CONSTRUCTION
    # ══════════════════════════════════════════════════════════════════════════
    def _build_ui(self):
        # ── Header ───────────────────────────────────────────────────────────
        header = tk.Frame(self.root, bg="#050508", height=90)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(
            header, text=f"◈ {APP_NAME.upper()}", font=("Consolas", 28, "bold"),
            fg=self.ACCENT, bg="#050508"
        ).pack(side=tk.LEFT, padx=30, pady=18)

        right_meta = tk.Frame(header, bg="#050508")
        right_meta.pack(side=tk.RIGHT, padx=30)
        tk.Label(
            right_meta, text=f"Setup v{APP_VERSION}", font=("Consolas", 11),
            fg=self.FG_DIM, bg="#050508"
        ).pack(anchor=tk.E)
        tk.Label(
            right_meta, text=f"by {APP_AUTHOR}", font=("Consolas", 9),
            fg=self.BLUE, bg="#050508"
        ).pack(anchor=tk.E)

        # ── Accent divider ───────────────────────────────────────────────────
        tk.Frame(self.root, bg=self.ACCENT, height=2).pack(fill=tk.X)

        # ── Body ─────────────────────────────────────────────────────────────
        body = tk.Frame(self.root, bg=self.BG)
        body.pack(fill=tk.BOTH, expand=True, padx=24, pady=16)

        # Platform row
        plat_frame = tk.Frame(body, bg=self.BG_PANEL, bd=0,
                              highlightbackground=self.BORDER, highlightthickness=1)
        plat_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(
            plat_frame,
            text=f"🖥  {platform.system()} {platform.release()}  •  {platform.machine()}  •  Python {platform.python_version()}",
            font=("Consolas", 9), fg=self.FG_DIM, bg=self.BG_PANEL, padx=10, pady=6
        ).pack(anchor=tk.W)

        # ── Installation Directory ───────────────────────────────────────────
        tk.Label(
            body, text="INSTALLATION DIRECTORY", font=("Consolas", 9, "bold"),
            fg=self.ACCENT, bg=self.BG
        ).pack(anchor=tk.W)

        dir_row = tk.Frame(body, bg=self.BG)
        dir_row.pack(fill=tk.X, pady=(4, 8))

        self.dir_var = tk.StringVar(value=self._default_dir())
        self.dir_entry = tk.Entry(
            dir_row, textvariable=self.dir_var, font=("Consolas", 10),
            fg=self.FG, bg=self.BG_INPUT, relief=tk.FLAT,
            insertbackground=self.ACCENT, highlightbackground=self.BORDER,
            highlightthickness=1, bd=0
        )
        self.dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6)

        AnimatedButton(
            dir_row, normal_bg=self.BG_INPUT, hover_bg="#1e2040",
            text="Browse", command=self._browse, font=("Consolas", 9),
            fg=self.FG, relief=tk.FLAT, padx=12, pady=6, cursor="hand2"
        ).pack(side=tk.LEFT, padx=(6, 0))

        # ── Application Name ────────────────────────────────────────────────
        name_row = tk.Frame(body, bg=self.BG)
        name_row.pack(fill=tk.X, pady=(0, 8))

        tk.Label(
            name_row, text="APPLICATION NAME:", font=("Consolas", 9, "bold"),
            fg=self.ACCENT2, bg=self.BG
        ).pack(side=tk.LEFT)

        self.name_var = tk.StringVar(value=APP_NAME)
        self.name_entry = tk.Entry(
            name_row, textvariable=self.name_var, font=("Consolas", 10),
            fg=self.FG, bg=self.BG_INPUT, relief=tk.FLAT,
            insertbackground=self.ACCENT2, highlightbackground=self.BORDER,
            highlightthickness=1, bd=0, width=25
        )
        self.name_entry.pack(side=tk.LEFT, padx=(10, 0), ipady=4)

        # ── Options Panel ────────────────────────────────────────────────────
        opt_frame = tk.LabelFrame(
            body, text="  INSTALLATION OPTIONS  ", font=("Consolas", 9, "bold"),
            fg=self.ACCENT, bg=self.BG_PANEL, bd=1, relief=tk.FLAT,
            highlightbackground=self.BORDER, highlightthickness=1,
            labelanchor="nw", padx=12, pady=8
        )
        opt_frame.pack(fill=tk.X, pady=(0, 8))

        # Row 1
        opt_row1 = tk.Frame(opt_frame, bg=self.BG_PANEL)
        opt_row1.pack(fill=tk.X, pady=(0, 4))

        self.opt_path = tk.BooleanVar(value=True)
        tk.Checkbutton(
            opt_row1, text=f"  Add {APP_NAME} to system PATH",
            variable=self.opt_path, font=("Consolas", 9),
            fg=self.FG, bg=self.BG_PANEL, activebackground=self.BG_PANEL,
            activeforeground=self.ACCENT, selectcolor=self.BG_INPUT,
            cursor="hand2"
        ).pack(side=tk.LEFT)

        self.opt_shortcut = tk.BooleanVar(value=True)
        tk.Checkbutton(
            opt_row1, text="  Create desktop shortcut",
            variable=self.opt_shortcut, font=("Consolas", 9),
            fg=self.FG, bg=self.BG_PANEL, activebackground=self.BG_PANEL,
            activeforeground=self.ACCENT, selectcolor=self.BG_INPUT,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=(24, 0))

        # Row 2
        opt_row2 = tk.Frame(opt_frame, bg=self.BG_PANEL)
        opt_row2.pack(fill=tk.X, pady=(0, 0))

        self.opt_launcher = tk.BooleanVar(value=True)
        tk.Checkbutton(
            opt_row2, text="  Create launcher script (bat/sh)",
            variable=self.opt_launcher, font=("Consolas", 9),
            fg=self.FG, bg=self.BG_PANEL, activebackground=self.BG_PANEL,
            activeforeground=self.ACCENT, selectcolor=self.BG_INPUT,
            cursor="hand2"
        ).pack(side=tk.LEFT)

        self.opt_config = tk.BooleanVar(value=True)
        tk.Checkbutton(
            opt_row2, text="  Write default configuration",
            variable=self.opt_config, font=("Consolas", 9),
            fg=self.FG, bg=self.BG_PANEL, activebackground=self.BG_PANEL,
            activeforeground=self.ACCENT, selectcolor=self.BG_INPUT,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=(24, 0))

        # ── Progress bar ─────────────────────────────────────────────────────
        self.progress = ttk.Progressbar(
            body, style="Custom.Horizontal.TProgressbar",
            mode="determinate", maximum=100, value=0
        )
        self.progress.pack(fill=tk.X, pady=(4, 0))

        self.progress_label = tk.Label(
            body, text="", font=("Consolas", 8), fg=self.FG_DIM, bg=self.BG
        )
        self.progress_label.pack(anchor=tk.W)

        # ── Log area ─────────────────────────────────────────────────────────
        tk.Label(
            body, text="INSTALLATION LOG", font=("Consolas", 9, "bold"),
            fg=self.ACCENT, bg=self.BG
        ).pack(anchor=tk.W, pady=(4, 2))

        log_frame = tk.Frame(
            body, bg=self.BG_LOG,
            highlightbackground=self.BORDER, highlightthickness=1
        )
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = scrolledtext.ScrolledText(
            log_frame, font=("Consolas", 9), fg=self.ACCENT, bg=self.BG_LOG,
            relief=tk.FLAT, state=tk.DISABLED, height=8,
            insertbackground=self.ACCENT
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Log tags
        self.log_text.tag_config("info",    foreground=self.FG)
        self.log_text.tag_config("success", foreground=self.ACCENT)
        self.log_text.tag_config("warning", foreground=self.WARN)
        self.log_text.tag_config("error",   foreground=self.ERR)
        self.log_text.tag_config("dim",     foreground=self.FG_DIM)
        self.log_text.tag_config("accent",  foreground=self.BLUE)
        self.log_text.tag_config("cyan",    foreground=self.ACCENT2)

        # ── Footer buttons ───────────────────────────────────────────────────
        footer = tk.Frame(self.root, bg=self.BG)
        footer.pack(fill=tk.X, padx=24, pady=(0, 18))

        self.install_btn = AnimatedButton(
            footer, normal_bg=self.ACCENT, hover_bg=self.ACCENT_DIM,
            text=f"▶  INSTALL {APP_NAME.upper()}",
            command=self._start_installation,
            font=("Consolas", 12, "bold"), fg="#000000", relief=tk.FLAT,
            padx=28, pady=12, cursor="hand2"
        )
        self.install_btn.pack(side=tk.LEFT)

        AnimatedButton(
            footer, normal_bg="#1e1e30", hover_bg="#2a2a40",
            text="✕  Close", command=self.root.destroy,
            font=("Consolas", 10), fg=self.FG_DIM,
            relief=tk.FLAT, padx=18, pady=12, cursor="hand2"
        ).pack(side=tk.RIGHT)

    # ══════════════════════════════════════════════════════════════════════════
    #  HELPERS
    # ══════════════════════════════════════════════════════════════════════════
    def _default_dir(self) -> str:
        if self.platform == "windows":
            return os.path.join(os.environ.get("LOCALAPPDATA", "C:\\"), APP_NAME)
        elif self.platform == "darwin":
            return f"/Applications/{APP_NAME}"
        return os.path.expanduser(f"~/{APP_NAME.lower()}")

    def _browse(self):
        d = filedialog.askdirectory(initialdir=self.dir_var.get())
        if d:
            self.dir_var.set(d)

    def _log(self, msg: str, tag: str = "info"):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, msg + "\n", tag)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update_idletasks()

    def _set_progress(self, value: int, label: str = ""):
        self.progress["value"] = value
        if label:
            self.progress_label.config(text=label, fg=self.FG_DIM)
        self.root.update_idletasks()

    # ══════════════════════════════════════════════════════════════════════════
    #  INITIAL LOG
    # ══════════════════════════════════════════════════════════════════════════
    def _write_initial_log(self):
        n = APP_NAME
        self._log("=" * 60, "accent")
        self._log(f"  Welcome to the {n} Terminal Installer", "accent")
        self._log("=" * 60, "accent")
        self._log("")
        self._log("What will be installed:", "info")

        exe_path = get_resource_path(EXE_NAME_WIN if self.platform == "windows" else EXE_NAME_LINUX)
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            self._log(f"  ✓  {exe_path.name} ({size_mb:.1f} MB)", "success")
        else:
            self._log(f"  ⚠  {EXE_NAME_WIN} (bundled — will be extracted)", "warning")

        self._log(f"  ✓  terminal_config.json (default config)", "success")
        self._log(f"  ✓  Launcher script (Nextral.bat / nextral.sh)", "success")
        self._log("")
        self._log("Configure the options above, then click INSTALL.", "dim")

    # ══════════════════════════════════════════════════════════════════════════
    #  INSTALLATION ENTRY POINT
    # ══════════════════════════════════════════════════════════════════════════
    def _start_installation(self):
        dest = self.dir_var.get().strip()
        if not dest:
            messagebox.showerror("Error", "Please select an installation directory.")
            return

        self.install_btn.config(
            state=tk.DISABLED, text="⏳  Installing...",
            bg=self.WARN, activebackground=self.WARN
        )
        self.is_installing = True
        threading.Thread(target=self._run_installation, daemon=True).start()

    # ══════════════════════════════════════════════════════════════════════════
    #  INSTALLATION LOGIC
    # ══════════════════════════════════════════════════════════════════════════
    def _run_installation(self):
        dest = Path(self.dir_var.get().strip())
        app_name = self.name_var.get().strip() or APP_NAME
        errors = []

        try:
            total_steps = 6
            step = 0

            # ── Step 1: Create directory ─────────────────────────────────────
            step += 1
            self._log("", "info")
            self._log("─" * 60, "dim")
            self._set_progress(int(step / total_steps * 100), "Creating directory…")
            self._log(f"[{step}/{total_steps}]  Creating install directory…", "info")
            dest.mkdir(parents=True, exist_ok=True)
            self._log(f"  ✓  {dest}", "success")

            # ── Step 2: Copy executable ──────────────────────────────────────
            step += 1
            exe_name = EXE_NAME_WIN if self.platform == "windows" else EXE_NAME_LINUX
            self._set_progress(int(step / total_steps * 100), f"Copying {exe_name}…")
            self._log(f"[{step}/{total_steps}]  Copying {app_name} executable…", "info")

            exe_src = get_resource_path(exe_name)
            if not exe_src.exists():
                # Fallback locations
                for alt in [Path(__file__).parent / "dist" / exe_name,
                            Path(__file__).parent / exe_name]:
                    if alt.exists():
                        exe_src = alt
                        break

            if exe_src.exists():
                shutil.copy2(exe_src, dest / exe_name)
                size_mb = (dest / exe_name).stat().st_size / (1024 * 1024)
                self._log(f"  ✓  {exe_name} ({size_mb:.1f} MB)", "success")
            else:
                self._log(f"  ⚠  {exe_name} not found — skipped.", "warning")
                self._log(f"     Place {exe_name} next to this installer.", "dim")
                errors.append(f"{exe_name} not found")

            # Copy icon
            icon_src = get_resource_path(ICON_FILENAME)
            if icon_src.exists():
                shutil.copy2(icon_src, dest / ICON_FILENAME)
                self._log(f"  ✓  {ICON_FILENAME} copied", "success")

            # ── Step 3: Write default config ─────────────────────────────────
            step += 1
            if self.opt_config.get():
                self._set_progress(int(step / total_steps * 100), "Writing configuration…")
                self._log(f"[{step}/{total_steps}]  Writing default configuration…", "info")

                config_src = get_resource_path("terminal_config.json")
                config_dst = dest / "terminal_config.json"

                if config_src.exists() and not config_dst.exists():
                    shutil.copy2(config_src, config_dst)
                    self._log("  ✓  terminal_config.json copied", "success")
                elif not config_dst.exists():
                    config = {
                        "user": {"username": "USER", "theme_color": "cyan", "auto_login": False},
                        "terminal": {"history_size": 1000, "max_output_lines": 2000, "crt_mode": False},
                        "shell": {"prompt_format": "{username}@Nextral {cwd} ~> "},
                        "external_tools": {
                            "nmap": "nmap", "netcat": "nc", "nikto": "nikto",
                            "hydra": "hydra", "tcpdump": "tcpdump", "openssl": "openssl",
                            "curl": "curl", "wget": "wget", "ssh": "ssh"
                        }
                    }
                    with open(config_dst, "w") as f:
                        json.dump(config, f, indent=4)
                    self._log("  ✓  terminal_config.json created", "success")
                else:
                    self._log("  ✓  terminal_config.json already exists — preserved", "dim")
            else:
                self._log(f"[{step}/{total_steps}]  Configuration — skipped (unchecked)", "dim")

            # ── Step 4: Create launcher ──────────────────────────────────────
            step += 1
            if self.opt_launcher.get():
                self._set_progress(int(step / total_steps * 100), "Creating launcher…")
                self._log(f"[{step}/{total_steps}]  Creating launcher script…", "info")

                if self.platform == "windows":
                    bat = dest / f"{app_name}.bat"
                    bat.write_text(
                        f'@echo off\r\n'
                        f'title {app_name} Terminal\r\n'
                        f'cd /d "{dest}"\r\n'
                        f'start "" "{exe_name}"\r\n',
                        encoding="utf-8"
                    )
                    self._log(f"  ✓  {app_name}.bat created", "success")
                else:
                    sh = dest / f"{app_name.lower()}.sh"
                    sh.write_text(
                        f'#!/bin/bash\n'
                        f'cd "{dest}"\n'
                        f'./{EXE_NAME_LINUX}\n'
                    )
                    os.chmod(sh, 0o755)
                    self._log(f"  ✓  {app_name.lower()}.sh created", "success")
            else:
                self._log(f"[{step}/{total_steps}]  Launcher script — skipped (unchecked)", "dim")

            # ── Step 5: Add to PATH ──────────────────────────────────────────
            step += 1
            if self.opt_path.get():
                self._set_progress(int(step / total_steps * 100), "Adding to PATH…")
                self._log(f"[{step}/{total_steps}]  Adding to system PATH…", "info")

                if self.platform == "windows":
                    self._add_to_path_windows(str(dest))
                else:
                    self._add_to_path_linux(str(dest))
            else:
                self._log(f"[{step}/{total_steps}]  Add to PATH — skipped (unchecked)", "dim")

            # ── Step 6: Create desktop shortcut ──────────────────────────────
            step += 1
            if self.opt_shortcut.get():
                self._set_progress(int(step / total_steps * 100), "Creating desktop shortcut…")
                self._log(f"[{step}/{total_steps}]  Creating desktop shortcut…", "info")

                if self.platform == "windows":
                    self._create_shortcut_windows(dest, app_name, exe_name)
                else:
                    self._create_shortcut_linux(dest, app_name)
            else:
                self._log(f"[{step}/{total_steps}]  Desktop shortcut — skipped (unchecked)", "dim")

            # ── Done ─────────────────────────────────────────────────────────
            self._set_progress(100, "Complete!")
            self._log("", "info")
            self._log("=" * 60, "success")
            if errors:
                self._log("  ⚠  INSTALLATION FINISHED WITH WARNINGS", "warning")
            else:
                self._log(f"  ✓  {app_name.upper()} INSTALLATION COMPLETE!", "success")
            self._log("=" * 60, "success")
            self._log(f"\n  Location: {dest}", "info")

            if self.opt_path.get():
                self._log(f"  PATH:     Open a NEW terminal and type '{app_name.lower()}'", "cyan")
            if self.opt_shortcut.get():
                self._log(f"  Shortcut: Check your Desktop", "cyan")

            if self.platform == "windows":
                self._log(f"  Launch:   double-click {app_name}.bat or {exe_name}", "accent")
            else:
                self._log(f"  Launch:   ./{app_name.lower()}.sh", "accent")
            self._log("\n  You can now close this installer.", "dim")

            self.root.after(0, self._on_complete, bool(errors))

        except Exception as exc:
            self._log(f"\n  ✗  Fatal error: {exc}", "error")
            import traceback
            self._log(traceback.format_exc(), "error")
            self.root.after(0, lambda: self.install_btn.config(
                state=tk.NORMAL, text=f"▶  INSTALL {APP_NAME.upper()}",
                bg=self.ACCENT, activebackground=self.ACCENT_DIM
            ))

    # ══════════════════════════════════════════════════════════════════════════
    #  ADD TO PATH
    # ══════════════════════════════════════════════════════════════════════════
    def _add_to_path_windows(self, install_dir: str):
        """Add install directory to user PATH via Windows Registry."""
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Environment",
                0, winreg.KEY_ALL_ACCESS
            )
            try:
                current_path, _ = winreg.QueryValueEx(key, "Path")
            except FileNotFoundError:
                current_path = ""

            # Check if already in PATH
            paths = [p.strip().rstrip("\\") for p in current_path.split(";") if p.strip()]
            norm_dir = install_dir.rstrip("\\")

            if norm_dir.lower() not in [p.lower() for p in paths]:
                new_path = current_path.rstrip(";") + ";" + install_dir
                winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
                self._log(f"  ✓  Added to user PATH (Registry)", "success")
                self._log(f"     {install_dir}", "dim")

                # Broadcast WM_SETTINGCHANGE so running Explorer picks it up
                try:
                    import ctypes
                    HWND_BROADCAST = 0xFFFF
                    WM_SETTINGCHANGE = 0x001A
                    SMTO_ABORTIFHUNG = 0x0002
                    result = ctypes.c_long()
                    ctypes.windll.user32.SendMessageTimeoutW(
                        HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment",
                        SMTO_ABORTIFHUNG, 5000, ctypes.byref(result)
                    )
                    self._log("  ✓  Environment refreshed (WM_SETTINGCHANGE broadcast)", "dim")
                except Exception:
                    self._log("  ⚠  Restart your terminal for PATH changes to take effect", "warning")
            else:
                self._log(f"  ✓  Already in PATH — no changes needed", "dim")

            winreg.CloseKey(key)

        except ImportError:
            self._log("  ⚠  winreg not available — cannot modify PATH", "warning")
        except PermissionError:
            self._log("  ⚠  Permission denied — run as Administrator for PATH modification", "warning")
        except Exception as e:
            self._log(f"  ⚠  Could not add to PATH: {e}", "warning")

    def _add_to_path_linux(self, install_dir: str):
        """Add install directory to PATH via shell profile files."""
        export_line = f'\n# Added by {APP_NAME} Installer\nexport PATH="$PATH:{install_dir}"\n'
        profiles_updated = []

        home = Path.home()
        for rc_file in [".bashrc", ".zshrc", ".profile"]:
            rc_path = home / rc_file
            if rc_path.exists():
                content = rc_path.read_text()
                if install_dir not in content:
                    with open(rc_path, "a") as f:
                        f.write(export_line)
                    profiles_updated.append(rc_file)

        # If no shell profile exists at all, create .bashrc
        if not profiles_updated:
            for rc_file in [".bashrc", ".profile"]:
                rc_path = home / rc_file
                if not rc_path.exists():
                    try:
                        with open(rc_path, "a") as f:
                            f.write(export_line)
                        profiles_updated.append(f"{rc_file} (created)")
                        break
                    except Exception:
                        continue

        if profiles_updated:
            self._log(f"  ✓  Added to PATH in: {', '.join(profiles_updated)}", "success")
            self._log(f"     Run 'source ~/{profiles_updated[0].split()[0]}' or open a new terminal", "dim")
        else:
            self._log("  ⚠  Could not find shell profile — add manually:", "warning")
            self._log(f'     export PATH="$PATH:{install_dir}"', "dim")

    # ══════════════════════════════════════════════════════════════════════════
    #  DESKTOP SHORTCUTS
    # ══════════════════════════════════════════════════════════════════════════
    def _create_shortcut_windows(self, dest: Path, app_name: str, exe_name: str):
        """Create a proper .lnk shortcut on Windows Desktop using VBScript."""
        try:
            desktop = Path(os.environ.get("USERPROFILE", "~")) / "Desktop"
            if not desktop.exists():
                desktop = Path.home() / "Desktop"

            lnk_path = desktop / f"{app_name}.lnk"
            target = str(dest / exe_name)
            icon_path = str(dest / ICON_FILENAME)
            working_dir = str(dest)

            # Build a small VBScript to create a proper .lnk
            vbs_content = (
                f'Set ws = CreateObject("WScript.Shell")\n'
                f'Set sc = ws.CreateShortcut("{lnk_path}")\n'
                f'sc.TargetPath = "{target}"\n'
                f'sc.WorkingDirectory = "{working_dir}"\n'
                f'sc.Description = "{app_name} Terminal"\n'
            )

            # Try to use .ico if available, fall back to exe icon
            ico_path = dest / "icon.ico"
            if ico_path.exists():
                vbs_content += f'sc.IconLocation = "{ico_path}"\n'
            elif (dest / exe_name).exists():
                vbs_content += f'sc.IconLocation = "{target}"\n'

            vbs_content += 'sc.Save\n'

            # Write & execute VBScript
            vbs_file = Path(tempfile.gettempdir()) / f"nextral_shortcut_{os.getpid()}.vbs"
            vbs_file.write_text(vbs_content, encoding="utf-8")

            result = subprocess.run(
                ["cscript", "//nologo", str(vbs_file)],
                capture_output=True, timeout=10
            )

            vbs_file.unlink(missing_ok=True)  # Cleanup

            if result.returncode == 0 and lnk_path.exists():
                self._log(f"  ✓  Desktop shortcut created: {lnk_path.name}", "success")
            else:
                # Fallback: create a .bat shortcut instead
                bat_path = desktop / f"{app_name}.bat"
                bat_path.write_text(
                    f'@echo off\r\ncd /d "{dest}"\r\nstart "" "{exe_name}"\r\n',
                    encoding="utf-8"
                )
                self._log(f"  ✓  Desktop shortcut created: {bat_path.name} (batch fallback)", "success")

        except Exception as e:
            # Last resort fallback
            try:
                desktop = Path(os.environ.get("USERPROFILE", "~")) / "Desktop"
                bat_path = desktop / f"{app_name}.bat"
                bat_path.write_text(
                    f'@echo off\r\ncd /d "{dest}"\r\nstart "" "{exe_name}"\r\n',
                    encoding="utf-8"
                )
                self._log(f"  ✓  Desktop shortcut created: {bat_path.name} (fallback)", "success")
            except Exception:
                self._log(f"  ⚠  Could not create desktop shortcut: {e}", "warning")

    def _create_shortcut_linux(self, dest: Path, app_name: str):
        """Create a .desktop file for Linux application menus and desktop."""
        try:
            desktop_entry = (
                f"[Desktop Entry]\n"
                f"Name={app_name}\n"
                f"Comment={app_name} Terminal — Advanced offensive security platform\n"
                f"Exec={dest / EXE_NAME_LINUX}\n"
                f"Icon={dest / ICON_FILENAME}\n"
                f"Terminal=true\n"
                f"Type=Application\n"
                f"Categories=System;TerminalEmulator;Security;\n"
                f"StartupNotify=true\n"
            )

            # 1. Install to ~/.local/share/applications/
            app_dir = Path.home() / ".local" / "share" / "applications"
            app_dir.mkdir(parents=True, exist_ok=True)
            desktop_file = app_dir / f"{app_name.lower()}.desktop"
            desktop_file.write_text(desktop_entry)
            os.chmod(desktop_file, 0o755)
            self._log(f"  ✓  Application menu entry: {desktop_file}", "success")

            # 2. Copy to ~/Desktop/ if it exists
            desktop_dir = Path.home() / "Desktop"
            if desktop_dir.exists():
                desk_shortcut = desktop_dir / f"{app_name.lower()}.desktop"
                desk_shortcut.write_text(desktop_entry)
                os.chmod(desk_shortcut, 0o755)
                self._log(f"  ✓  Desktop shortcut: {desk_shortcut.name}", "success")

                # Try to mark as trusted (GNOME)
                try:
                    subprocess.run(
                        ["gio", "set", str(desk_shortcut),
                         "metadata::trusted", "true"],
                        capture_output=True, timeout=5
                    )
                except Exception:
                    pass
            else:
                self._log("  ⚠  ~/Desktop not found — shortcut placed in app menu only", "dim")

        except Exception as e:
            self._log(f"  ⚠  Could not create .desktop entry: {e}", "warning")

    # ══════════════════════════════════════════════════════════════════════════
    #  COMPLETION
    # ══════════════════════════════════════════════════════════════════════════
    def _on_complete(self, had_warnings: bool):
        app_name = self.name_var.get().strip() or APP_NAME
        self.install_btn.config(
            text="✓  INSTALLED", bg=self.ACCENT_DIM,
            activebackground=self.ACCENT_DIM, state=tk.DISABLED
        )
        if had_warnings:
            messagebox.showwarning(
                "Installed with Warnings",
                f"{app_name} was installed but some files were missing.\n"
                "Check the log for details.\n\n"
                f"Tip: Place {EXE_NAME_WIN} next to this installer before running it."
            )
        else:
            dest = self.dir_var.get()
            msg = f"{app_name} has been installed to:\n{dest}\n\n"
            if self.opt_path.get():
                msg += "✓ Added to PATH (open a new terminal to use)\n"
            if self.opt_shortcut.get():
                msg += "✓ Desktop shortcut created\n"
            msg += f"\nRun {app_name} to launch."
            messagebox.showinfo("Installation Complete", msg)

    def run(self):
        self.root.mainloop()


def main():
    installer = NextralInstaller()
    installer.run()


if __name__ == "__main__":
    main()
