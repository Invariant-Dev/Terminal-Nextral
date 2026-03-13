# nextral.py - Nextral Terminal v1.0 BETA [TRIAD SYSTEM]
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Static, Header, Footer, Input, RichLog
from textual.binding import Binding
from textual.screen import Screen
from textual import events
from textual.reactive import reactive
from textual import work

from datetime import datetime
import psutil
import platform
import sys
import os
import json
import asyncio
import socket
import subprocess
import signal
from pathlib import Path
from enum import Enum

# Import Elite modules
from geo_globe import GeoGlobe
from plugin_manager import PluginManager

import getpass
from pathlib import Path
import pyperclip


# ==============================================================================
# TRIAD SYSTEM - MODE CONSTANTS
# ==============================================================================

class Mode(Enum):
    GENERAL = "general"
    ATTACK = "attack"
    AGENT = "agent"

MODE_COLORS = {
    Mode.GENERAL: {"primary": "#00d4ff", "secondary": "#0066aa", "name": "GENERAL", "icon": "▣", "prompt": "➜"},
    Mode.ATTACK: {"primary": "#ff4444", "secondary": "#aa2222", "name": "STRIKE", "icon": "☠", "prompt": "⚡"},
    Mode.AGENT: {"primary": "#aa44ff", "secondary": "#6622aa", "name": "NEXUS", "icon": "◆", "prompt": "◈"},
}

MODE_GHOST_COMMANDS = {
    Mode.GENERAL: ["explore", "obelisk", "vault", "cipher", "settings", "ssh", "clear", "ls", "dir", "cd", "cat", "type"],
    Mode.ATTACK: ["nmap", "nikto", "hydra", "netcat", "tcpdump", "valkyrie", "osint", "xray", "shell-lab", "exif", "scan", "exploit", "stun", "whatsapp-ip", "whatsapp-tracer"],
    Mode.AGENT: ["agent", "ask", "nexus", "task", "email", "whatsapp", "analyze", "execute", "automate"],
}

# ==============================================================================
# CONFIGURATION
# ==============================================================================

CONFIG_FILE = Path(__file__).parent / "terminal_config.json"

def load_config():
    system_user = getpass.getuser().upper()
    default_cfg = {
        "user": {"username": system_user, "theme_color": "cyan"},
        "shell": {"prompt_format": "{username}@Nextral {cwd} ~> "},
        "terminal": {"history_size": 1000, "crt_mode": False}
    }
    
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                loaded = json.load(f)
                # Ensure the user section exists
                if "user" not in loaded:
                    loaded["user"] = default_cfg["user"]
                if "terminal" not in loaded:
                    loaded["terminal"] = default_cfg["terminal"]
                return loaded
        except:
            pass
    return default_cfg

def save_config(cfg):
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(cfg, f, indent=4)
    except:
        pass

CONFIG = load_config()

# ==============================================================================
# SHELL ENGINE (Embedded for simplicity and reliability)
# ==============================================================================

class ShellEngine:
    """Manages a real PowerShell subprocess"""
    
    def __init__(self):
        self.process = None
        self.cwd = os.path.expanduser("~")
        self.history = []
        self.history_index = 0
        self.history_limit = CONFIG.get("terminal", {}).get("history_size", 1000)
        self.delimiter = "<<NEXTRAL_CMD_END>>"
        
        self._output_callback = None
        self._done_callback = None
        self._reader_task = None
        self._is_busy = False

    async def start(self):
        """Start Shell process (PowerShell on Windows, Bash on Linux)"""
        import subprocess
        import sys
        
        is_windows = sys.platform == 'win32'
        shell_cmd = "powershell.exe" if is_windows else "/bin/bash"
        shell_args = ["-NoLogo", "-NoProfile", "-NoExit"] if is_windows else ["--login", "-i"]
        
        try:
            self.process = await asyncio.create_subprocess_exec(
                shell_cmd,
                *shell_args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if is_windows else 0
            )
            
            # Start background reader
            self._reader_task = asyncio.create_task(self._read_loop())
            
            if is_windows:
                # Set UTF-8 encoding for PowerShell
                await self._send_raw("[Console]::OutputEncoding = [System.Text.Encoding]::UTF8\n")
            else:
                # Prepare bash to be more quiet
                await self._send_raw("export PS1=''\n")
            
            await asyncio.sleep(0.3)
            return True
        except FileNotFoundError:
            return False
        except Exception as e:
            print(f"Shell start error: {e}")
            return False

    async def _send_raw(self, text):
        if self.process and self.process.stdin:
            self.process.stdin.write(text.encode('utf-8'))
            await self.process.stdin.drain()

    async def execute(self, cmd, on_output, on_done):
        """Execute a command"""
        if not self.process or self.process.returncode is not None:
            on_output("[red]Shell disconnected. Restarting...[/]\n")
            if not await self.start():
                on_output("[bold red]FATAL: Cannot start PowerShell.[/]\n")
                on_done()
                return
        
        self._output_callback = on_output
        self._done_callback = on_done
        self._is_busy = True
        
        # Security Check: Prevent killing the shell itself
        pid = str(self.process.pid) if self.process else ""
        cmd_lower = cmd.lower()
        kill_keywords = ["kill", "stop-process", "taskkill"]
        
        if pid and pid in cmd and any(k in cmd_lower for k in kill_keywords):
            on_output(f"\n[bold red]⚠ CRITICAL: TERMINATION PREVENTED[/]\n")
            on_output(f"[yellow]You are attempting to kill the active shell process (PID {pid}).[/]\n")
            on_output("[cyan]To safely close Nextral, please use the [bold]exit[/] or [bold]quit[/] command.[/]\n\n")
            self._is_busy = False
            on_done()
            return
        
        # Add to history
        if cmd.strip():
            self.history.append(cmd)
            if len(self.history) > self.history_limit:
                self.history = self.history[-self.history_limit:]
            self.history_index = len(self.history)
        
        # Send command with delimiter trailer
        import sys
        if sys.platform == 'win32':
            payload = f"{cmd}\n(Get-Location).Path | Write-Host -NoNewline; Write-Host '<<CWD_END>>'\nWrite-Host '{self.delimiter}'\n"
        else:
            # Linux Bash version
            payload = f"{cmd}\npwd | tr -d '\\n'; echo '<<CWD_END>>'\necho '{self.delimiter}'\n"
            
        await self._send_raw(payload)

    async def _read_loop(self):
        """Continuously read output — burst-mode for maximum throughput."""
        buffer = ""
        while True:
            try:
                if not self.process or not self.process.stdout:
                    await asyncio.sleep(0.1)
                    continue
                
                chunk = await self.process.stdout.read(4096)
                if not chunk:
                    if self.process.returncode is not None:
                        break  # Process ended
                    await asyncio.sleep(0.05)
                    continue
                
                text = chunk.decode('utf-8', errors='replace')
                buffer += text
                
                # Burst: drain all available data before processing
                while True:
                    try:
                        extra = self.process.stdout.read_nowait(8192) if hasattr(self.process.stdout, 'read_nowait') else b''
                    except Exception:
                        extra = b''
                    if not extra:
                        break
                    buffer += extra.decode('utf-8', errors='replace')
                
                # Process complete lines
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    await self._process_line(line)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                await asyncio.sleep(0.05)

    async def _process_line(self, line):
        """Process a single line of output"""
        line = line.rstrip('\r')
        
        # Check for CWD update first
        if "<<CWD_END>>" in line:
            path = line.replace("<<CWD_END>>", "").strip()
            if os.path.isdir(path):
                self.cwd = path
            if self.delimiter not in line:
                return # Hide the internal path update line
        
        # Check for delimiter
        if self.delimiter in line:
            self._is_busy = False
            if self._done_callback:
                self._done_callback()
            return
        
        # Skip prompt lines (they start with PS or look like common bash prompts)
        if line.strip().startswith("PS ") and ">" in line:
            return
        # Hide the shell echoing the delimiter command itself
        if f"echo '{self.delimiter}'" in line:
            return
        if f"Write-Host '{self.delimiter}'" in line:
            return
        
        # Normal output
        if self._output_callback and line.strip():
            self._output_callback(line)

    async def stop(self):
        """Standard shutdown for the shell process"""
        if self.process:
            try:
                if self.process.stdin:
                    self.process.stdin.close()
                self.process.terminate()
                await self.process.wait()
            except:
                pass
        if self._reader_task:
            self._reader_task.cancel()

    def interrupt(self):
        """Attempt to interrupt current command"""
        asyncio.create_task(self._restart())

    async def _restart(self):
        await self.stop()
        await asyncio.sleep(0.1)
        await self.start()
        if self._done_callback:
            self._done_callback()
        self._is_busy = False

    def history_up(self):
        if not self.history:
            return None
        if self.history_index > 0:
            self.history_index -= 1
        return self.history[self.history_index] if self.history else None

    def history_down(self):
        if not self.history:
            return ""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            return self.history[self.history_index]
        self.history_index = len(self.history)
        return ""

    def autocomplete(self, text):
        """Basic path autocomplete"""
        try:
            parts = text.split()
            if not parts:
                return None
            
            target = parts[-1]
            search_dir = self.cwd
            prefix = ""
            
            if os.path.sep in target or "/" in target:
                dirname = os.path.dirname(target)
                basename = os.path.basename(target)
                search_dir = os.path.join(self.cwd, dirname)
                prefix = dirname + os.path.sep
            else:
                basename = target
            
            if not os.path.isdir(search_dir):
                return None
            
            for item in os.listdir(search_dir):
                if item.lower().startswith(basename.lower()):
                    parts[-1] = prefix + item
                    return " ".join(parts)
        except:
            pass
        return None

    def get_ghost_suggestion(self, partial: str, mode: Mode = Mode.GENERAL) -> str:
        """Get ghost suggestion from history for the partial input, prioritized by mode"""
        if not partial:
            return ""
        
        partial_lower = partial.lower()
        partial_word = partial.split()[-1].lower() if partial.split() else partial_lower
        
        mode_commands = MODE_GHOST_COMMANDS.get(mode, [])
        
        # First priority: check mode-specific commands
        for cmd in reversed(self.history):
            if cmd.lower().startswith(partial_lower):
                # If command is in mode's priority list, score it higher
                cmd_first_word = cmd.split()[0].lower() if cmd.split() else ""
                if cmd_first_word in mode_commands and cmd.lower() != partial_lower:
                    return cmd[len(partial):]
        
        # Second: any history match
        for cmd in reversed(self.history):
            if cmd.lower().startswith(partial_lower) and cmd.lower() != partial_lower:
                return cmd[len(partial):]
        
        # Third: fallback to mode-specific known commands
        for known_cmd in mode_commands:
            if known_cmd.startswith(partial_word) and known_cmd != partial_word:
                if len(partial.split()) > 1:
                    return " " + known_cmd
                return known_cmd[len(partial_word):]
        
        return ""

# ==============================================================================
# WIDGETS
# ==============================================================================

# Braille sparkline helper ─────────────────────────────────
_BRAILLE = [" ", "▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]

def _sparkline(history: list, width: int = 20, color: str = "cyan") -> str:
    """Render a tiny sparkline from a list of 0–100 values."""
    if not history:
        return "[dim]" + " " * width + "[/dim]"
    # Take the last `width` samples
    data = list(history)[-width:]
    # Pad left with zeros if we don’t have enough yet
    data = [0] * (width - len(data)) + data
    peak = max(data) or 1
    chars = "".join(_BRAILLE[min(8, int(v / peak * 8))] for v in data)
    return f"[{color}]{chars}[/]"


class SystemPanel(Static):
    """System statistics panel with sparkline graphs."""

    _CPU_HIST: list = []
    _MEM_HIST: list = []
    _HIST_MAX = 24
    _tick_count = 0
    _cached_disk = None
    _timer_handle = None

    DEFAULT_CSS = """
    SystemPanel {
        border: solid rgba(0, 255, 255, 0.2);
        height: auto;
        padding: 0 1;
        margin-bottom: 1;
    }
    SystemPanel:hover {
        border: solid cyan;
    }
    """

    def on_mount(self):
        self.border_title = "[ CPU / MEM ]"
        self.display = False
        self._boot_time = psutil.boot_time()
        self._cpu_count_phys = psutil.cpu_count(logical=False) or 1
        self._cpu_count_log = psutil.cpu_count(logical=True) or 1

    def watch_display(self, visible: bool) -> None:
        """Start/stop the timer based on visibility to save CPU."""
        if visible and self._timer_handle is None:
            self._timer_handle = self.set_interval(1.0, self.refresh_stats)
        elif not visible and self._timer_handle is not None:
            self._timer_handle.stop()
            self._timer_handle = None

    def refresh_stats(self):
        if not self.display:
            return

        cpu            = psutil.cpu_percent(percpu=False)
        cpu_per_core   = psutil.cpu_percent(percpu=True)
        cpu_freq       = psutil.cpu_freq()
        mem            = psutil.virtual_memory()
        swap           = psutil.swap_memory()
        
        # Disk checks are slow, only run every 10 seconds
        if self._tick_count % 10 == 0 or self._cached_disk is None:
            self._cached_disk = psutil.disk_usage('/')
        self._tick_count += 1
        disk = self._cached_disk

        # Rolling history
        self._CPU_HIST.append(cpu)
        self._MEM_HIST.append(mem.percent)
        if len(self._CPU_HIST) > self._HIST_MAX: self._CPU_HIST.pop(0)
        if len(self._MEM_HIST) > self._HIST_MAX: self._MEM_HIST.pop(0)

        cpu_spark  = _sparkline(self._CPU_HIST, self._HIST_MAX, self._get_color(cpu))
        mem_spark  = _sparkline(self._MEM_HIST, self._HIST_MAX, self._get_color(mem.percent))

        cpu_color  = self._get_color(cpu)
        mem_color  = self._get_color(mem.percent)
        disk_color = self._get_color(disk.percent)
        swap_color = self._get_color(swap.percent)
        freq_str   = f"{cpu_freq.current / 1000:.2f}GHz" if cpu_freq else "n/a"
        freq_max   = f"{cpu_freq.max / 1000:.1f}" if cpu_freq else "?"

        mem_used_gb   = mem.used   / (1024**3)
        mem_total_gb  = mem.total  / (1024**3)
        mem_avail_gb  = mem.available / (1024**3)
        disk_used_gb  = disk.used  / (1024**3)
        disk_total_gb = disk.total / (1024**3)
        disk_free_gb  = disk.free  / (1024**3)
        swap_used_gb  = swap.used  / (1024**3)
        swap_total_gb = swap.total / (1024**3)

        # Per-core mini bar (show up to 8 cores)
        core_bars = ""
        for i, pct in enumerate(cpu_per_core[:8]):
            col = self._get_color(pct)
            bar = _BRAILLE[min(8, int(pct / 100 * 8))]
            core_bars += f"[{col}]{bar}[/]"
        if self._cpu_count_log > 8:
            core_bars += f"[dim]+{self._cpu_count_log-8}[/]"

        # Battery info
        bat_str = ""
        try:
            bat = psutil.sensors_battery()
            if bat:
                charging = "⚡" if bat.power_plugged else "🔋"
                bat_col = self._get_color(100 - bat.percent)
                bat_str = f"\n[bold cyan]BAT[/] [{bat_col}]{bat.percent:.0f}%[/] [dim]{charging}[/]"
        except Exception:
            pass

        self.update(
            f"[bold cyan]CPU[/] [{cpu_color}]{cpu:5.1f}%[/] [dim]{freq_str}/{freq_max}G {self._cpu_count_phys}C/{self._cpu_count_log}T[/]\n"
            f"[dim]cores [/]{core_bars}\n"
            f"{cpu_spark}\n"
            f"[bold cyan]MEM[/] [{mem_color}]{mem.percent:5.1f}%[/] [dim]{mem_used_gb:.1f}/{mem_total_gb:.1f}G  avail {mem_avail_gb:.1f}G[/]\n"
            f"{mem_spark}\n"
            f"[bold cyan]SWP[/] [{swap_color}]{swap.percent:4.1f}%[/] [dim]{swap_used_gb:.1f}/{swap_total_gb:.1f}G[/]\n"
            f"[bold cyan]DSK[/] [{disk_color}]{disk.percent:4.1f}%[/] "
            f"[dim]{disk_used_gb:.0f}/{disk_total_gb:.0f}G  free {disk_free_gb:.0f}G[/]"
            f"{bat_str}\n"
            f"[dim]⏱ {self._uptime()}[/]"
        )

    def _get_color(self, pct):
        if pct > 80: return "red"
        elif pct > 50: return "yellow"
        return "green"

    def _uptime(self):
        delta = datetime.now() - datetime.fromtimestamp(self._boot_time)
        h = delta.seconds // 3600
        m = (delta.seconds // 60) % 60
        return f"{delta.days}d {h}h {m}m"


class NetworkPanel(Static):
    """Network monitor panel with sparkline."""

    _UP_HIST: list  = []
    _DN_HIST: list  = []
    _HIST_MAX       = 24
    _tick_count     = 0
    _cached_conns   = (0, 0, 0)
    _cached_iface   = ("n/a", "n/a", "?")

    DEFAULT_CSS = """
    NetworkPanel {
        border: solid rgba(0, 255, 255, 0.2);
        height: auto;
        padding: 0 1;
        margin-bottom: 1;
    }
    NetworkPanel:hover {
        border: solid cyan;
    }
    """

    _timer_handle = None

    def on_mount(self):
        self.border_title = "[ NETWORK ]"
        io = psutil.net_io_counters()
        self.prev_sent    = io.bytes_sent
        self.prev_recv    = io.bytes_recv
        self.prev_pkts_s  = io.packets_sent
        self.prev_pkts_r  = io.packets_recv
        self.display = False

    def watch_display(self, visible: bool) -> None:
        """Start/stop the timer based on visibility."""
        if visible and self._timer_handle is None:
            self._timer_handle = self.set_interval(2.0, self.refresh_net)
        elif not visible and self._timer_handle is not None:
            self._timer_handle.stop()
            self._timer_handle = None

    def refresh_net(self):
        if not self.display:
            return

        net        = psutil.net_io_counters()
        up_rate    = (net.bytes_sent   - self.prev_sent)   / 2 / 1024
        down_rate  = (net.bytes_recv   - self.prev_recv)   / 2 / 1024
        pkts_up    = (net.packets_sent - self.prev_pkts_s) / 2
        pkts_dn    = (net.packets_recv - self.prev_pkts_r) / 2
        self.prev_sent   = net.bytes_sent
        self.prev_recv   = net.bytes_recv
        self.prev_pkts_s = net.packets_sent
        self.prev_pkts_r = net.packets_recv
        
        self._tick_count += 1

        # Rolling history (clamp to 9999 KB/s so graph is meaningful)
        self._UP_HIST.append(min(up_rate, 9999))
        self._DN_HIST.append(min(down_rate, 9999))
        if len(self._UP_HIST) > self._HIST_MAX: self._UP_HIST.pop(0)
        if len(self._DN_HIST) > self._HIST_MAX: self._DN_HIST.pop(0)

        up_spark   = _sparkline(self._UP_HIST,  self._HIST_MAX, "green")
        down_spark = _sparkline(self._DN_HIST,  self._HIST_MAX, "cyan")

        total_sent_mb = net.bytes_sent / (1024**2)
        total_recv_mb = net.bytes_recv / (1024**2)
        errin  = net.errin
        errout = net.errout
        dropin = net.dropin
        dropout = net.dropout

        try:
            if self._tick_count % 5 == 1: # Update every 10 seconds
                all_conns = psutil.net_connections()
                self._cached_conns = (
                    len([c for c in all_conns if c.status == 'ESTABLISHED']),
                    len([c for c in all_conns if c.status == 'LISTEN']),
                    len([c for c in all_conns if c.status == 'TIME_WAIT'])
                )
            est, listen, twait = self._cached_conns
        except Exception:
            est = listen = twait = 0

        try:
            if self._tick_count % 5 == 1:
                import socket as _socket
                loopback = ["loopback pseudo-interface 1", "lo", "loopback"]
                for iface, data in psutil.net_if_stats().items():
                    if data.isup and not any(lb in iface.lower() for lb in loopback):
                        a_iface = iface[:14]
                        i_speed = f"{data.speed}Mb" if data.speed else "?"
                        l_ip = "n/a"
                        for addr in psutil.net_if_addrs().get(iface, []):
                            if addr.family == _socket.AF_INET:
                                l_ip = addr.address
                                break
                        self._cached_iface = (a_iface, l_ip, i_speed)
                        break
            active_iface, local_ip, iface_speed = self._cached_iface
        except Exception:
            active_iface, local_ip, iface_speed = self._cached_iface

        up_clr   = "green" if up_rate   > 0 else "dim"
        down_clr = "cyan"  if down_rate > 0 else "dim"
        err_str  = f"[red]err {errin+errout}[/] " if (errin + errout) > 0 else ""
        drp_str  = f"[red]drp {dropin+dropout}[/]" if (dropin + dropout) > 0 else "[green]✓ clean[/]"

        self.update(
            f"[{up_clr}]▲[/] [bold]{up_rate:6.1f}[/] KB/s  [{down_clr}]▼[/] [bold]{down_rate:6.1f}[/] KB/s\n"
            f"[green]{up_spark}[/]\n"
            f"[cyan]{down_spark}[/]\n"
            f"[dim]↑ {total_sent_mb:.1f}MB  ↓ {total_recv_mb:.1f}MB  pkts ▲{pkts_up:.0f}/▼{pkts_dn:.0f}[/]\n"
            f"[bold cyan]EST[/] [white]{est}[/] [dim]LISTEN[/] [white]{listen}[/] [dim]TWAIT[/] [white]{twait}[/]\n"
            f"[dim]{active_iface} {local_ip} {iface_speed}[/]\n"
            f"{err_str}{drp_str}"
        )


class SecurityPanel(Static):
    """Security monitoring panel with system security info."""

    DEFAULT_CSS = """
    SecurityPanel {
        border: solid rgba(0, 255, 255, 0.2);
        height: auto;
        padding: 0 1;
        margin-bottom: 1;
    }
    SecurityPanel:hover {
        border: solid cyan;
    }
    """

    _timer_handle = None

    def on_mount(self):
        self.border_title = "[ SECURITY ]"
        self.display = False
        self._boot_time = psutil.boot_time()

    def watch_display(self, visible: bool) -> None:
        """Start/stop the timer based on visibility."""
        if visible and self._timer_handle is None:
            self._timer_handle = self.set_interval(3.0, self.refresh_sec)
        elif not visible and self._timer_handle is not None:
            self._timer_handle.stop()
            self._timer_handle = None

    def refresh_sec(self):
        """Refresh security information."""
        if not self.display:
            return
            
        try:
            # Get listening ports
            ports_listening = []
            ports_foreign   = set()
            try:
                conns = psutil.net_connections(kind='inet')
                for conn in conns:
                    if conn.status == 'LISTEN':
                        ports_listening.append(conn.laddr.port)
                    if conn.status == 'ESTABLISHED' and conn.raddr:
                        ports_foreign.add(conn.raddr.ip)
                ports_listening = sorted(set(ports_listening))
            except Exception:
                ports_listening = []

            # Get process count + suspicious (high CPU)
            proc_count  = 0
            sus_count   = 0
            try:
                for p in psutil.process_iter(['pid', 'cpu_percent']):
                    proc_count += 1
                    cpu_p = p.info.get('cpu_percent') or 0
                    if cpu_p and cpu_p > 50:
                        sus_count += 1
            except Exception:
                proc_count = len(psutil.pids())

            # System uptime
            uptime_secs  = datetime.now().timestamp() - self._boot_time
            uptime_hours = int(uptime_secs // 3600)
            uptime_mins  = int((uptime_secs % 3600) // 60)
            uptime_str   = f"{uptime_hours}h {uptime_mins}m" if uptime_hours > 0 else f"{uptime_mins}m"

            # Format ports display
            if ports_listening:
                ports_str = f"[yellow]{', '.join(map(str, ports_listening[:6]))}[/]"
                if len(ports_listening) > 6:
                    ports_str += f" [dim]+{len(ports_listening) - 6}[/]"
            else:
                ports_str = "[green]None[/]"

            sus_str     = f"[red]{sus_count} high-CPU[/]" if sus_count > 0 else "[green]none[/]"
            foreign_str = f"[yellow]{len(ports_foreign)}[/]" if ports_foreign else "[green]0[/]"
            health_icon = "[red]⚠ ALERT[/]" if sus_count > 0 else "[green]✓ OK[/]"

            self.update(
                f"[bold cyan]STATUS[/]   {health_icon}\n"
                f"[bold cyan]LISTEN[/]   {ports_str}\n"
                f"[bold cyan]REMOTE[/]   [dim]{len(ports_foreign)} unique IPs[/]\n"
                f"[bold cyan]PROCS[/]    [dim]{proc_count}[/]  [bold cyan]SUS[/] {sus_str}\n"
                f"[bold cyan]OPEN FD[/]  [dim]N/A (Opt)[/]\n"
                f"[bold cyan]UPTIME[/]   [dim]{uptime_str}[/]"
            )
        except Exception as e:
            self.update(f"[dim]Error reading security: {str(e)[:30]}[/]")


class GitPanel(Static):
    """Git repository status panel."""

    DEFAULT_CSS = """
    GitPanel {
        border: solid rgba(0, 255, 255, 0.2);
        height: auto;
        padding: 0 1;
        margin-bottom: 1;
    }
    GitPanel:hover {
        border: solid cyan;
    }
    """

    _timer_handle = None

    def on_mount(self):
        self.border_title = "[ GIT ]"
        self.display = False
        self._cwd = os.getcwd()

    def watch_display(self, visible: bool) -> None:
        """Start/stop the timer based on visibility."""
        if visible and self._timer_handle is None:
            self._timer_handle = self.set_interval(5.0, self.refresh_git)
        elif not visible and self._timer_handle is not None:
            self._timer_handle.stop()
            self._timer_handle = None

    def set_cwd(self, path):
        self._cwd = path
        self.refresh_git()

    def _run_git(self, *args):
        """Run a git command cross-platform."""
        flags = {"creationflags": subprocess.CREATE_NO_WINDOW} if sys.platform == 'win32' else {}
        return subprocess.run(
            ["git"] + list(args),
            cwd=self._cwd,
            capture_output=True,
            text=True,
            **flags
        )

    @work(exclusive=True, thread=True)
    def refresh_git(self):
        if not self.display:
            return

        try:
            result = self._run_git("rev-parse", "--is-inside-work-tree")
            if result.returncode != 0:
                self.display = False
                return
        except Exception:
            self.display = False
            return

        try:
            branch     = self._run_git("branch", "--show-current").stdout.strip() or "detached"
            status_out = self._run_git("status", "--porcelain").stdout.strip()
            lines      = status_out.split("\n") if status_out else []
            modified   = sum(1 for l in lines if l and l[0] in "M ")
            staged     = sum(1 for l in lines if l and l[0] in "MADRC")
            untracked  = sum(1 for l in lines if l and l.startswith("??"))
            deleted    = sum(1 for l in lines if l and l[0] == 'D')

            raw_commit  = self._run_git("log", "-1", "--format=%s|%an|%ar").stdout.strip()
            parts       = raw_commit.split("|") if raw_commit else ["", "", ""]
            commit_msg  = (parts[0][:22] + "…") if len(parts[0]) > 22 else parts[0]
            commit_auth = parts[1][:12] if len(parts) > 1 else ""
            commit_time = parts[2] if len(parts) > 2 else ""

            # Ahead/behind remote
            ahead_behind = self._run_git("rev-list", "--left-right", "--count",
                                         f"HEAD...@{{upstream}}").stdout.strip()
            if ahead_behind:
                ab_parts = ahead_behind.split()
                a_cnt = ab_parts[0] if len(ab_parts) > 0 else "?"
                b_cnt = ab_parts[1] if len(ab_parts) > 1 else "?"
                sync_str = f"[green]↑{a_cnt}[/] [cyan]↓{b_cnt}[/]"
            else:
                sync_str = "[dim]local[/]"

            # Stash count
            stash_out = self._run_git("stash", "list").stdout.strip()
            stash_cnt = len(stash_out.split("\n")) if stash_out else 0

            if untracked > 0 or modified > 0 or deleted > 0:
                health  = "[red]⚠[/]"
                b_color = "red" if untracked > 0 else "yellow"
            else:
                health  = "[green]✓[/]"
                b_color = "green" if not staged else "yellow"

            stash_str = f"  [dim]stash:{stash_cnt}[/]" if stash_cnt > 0 else ""

            self.update(
                f"{health} [{b_color}]⎇ {branch}[/]  {sync_str}{stash_str}\n"
                f"[yellow]+{staged}[/] staged [red]~{modified}[/] mod [dim]-{deleted}[/] del [dim]?{untracked}[/] new\n"
                f"[dim]{commit_msg or 'no commits'}[/]\n"
                f"[dim]{commit_auth}  {commit_time}[/]"
            )
        except Exception:
            self.update("[dim]No git repo or error[/]")




class GhostInput(Input):
    """Input with ghost suggestion overlay"""
    
    ghost_text = reactive("")
    current_mode = reactive(Mode.GENERAL)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._shell = None
    
    def set_shell(self, shell: ShellEngine):
        """Connect to shell engine for history access"""
        self._shell = shell
    
    def set_mode(self, mode: Mode):
        """Set current mode for context-aware suggestions"""
        self.current_mode = mode
        self._update_ghost()
    
    def watch_value(self, value: str) -> None:
        """Called automatically by Textual whenever self.value changes.
        
        This is the correct way to react to input changes without
        intercepting key events (which breaks the Input widget).
        """
        self._update_ghost()
    
    def _update_ghost(self):
        if self._shell and self.value:
            self.ghost_text = self._shell.get_ghost_suggestion(self.value, self.current_mode)
        else:
            self.ghost_text = ""
    
    def action_accept_ghost(self):
        """Accept the ghost suggestion (called on Right arrow at end)"""
        if self.ghost_text and self.cursor_position == len(self.value):
            self.value = self.value + self.ghost_text
            self.cursor_position = len(self.value)
            self.ghost_text = ""

    def action_paste_from_clipboard(self):
        """Standard Ctrl+V implementation"""
        try:
            text = pyperclip.paste()
            if text:
                text = text.replace("\r", "").replace("\n", " ")
                before = self.value[:self.cursor_position]
                after = self.value[self.cursor_position:]
                self.value = before + text + after
                self.cursor_position += len(text)
        except Exception:
            pass


# ==============================================================================
# MAIN TERMINAL SCREEN
# ==============================================================================

class TerminalScreen(Screen):
    """The main terminal interface"""
    
    BINDINGS = [
        Binding("up", "history_up", "History ↑", show=False),
        Binding("down", "history_down", "History ↓", show=False),
        Binding("tab", "autocomplete", "Autocomplete", show=False),
        Binding("ctrl+c", "interrupt", "ATTACKInterrupt", show=False),
        Binding("ctrl+l", "clear_screen", "Clear", show=False),
        Binding("right", "accept_ghost", "Accept Ghost", show=False),
        Binding("ctrl+b", "toggle_stealth", "Stealth Mode", show=False),
        Binding("ctrl+v", "paste_from_clipboard", "Paste", show=False),
    ]
    
    crt_mode = reactive(False)
    stealth_mode = reactive(False)
    active_pane = reactive("pane1")
    current_mode = reactive(Mode.GENERAL)
    
    def __init__(self):
        super().__init__()
        self.shell = ShellEngine()
        self._locked = False
        self.panes = {}
        self.crt_mode = CONFIG.get("terminal", {}).get("crt_mode", False)
        self._plugins = PluginManager()
        self._passthrough_mode = False
        self._passthrough_label = ""
        # Track widget activation order for 4-widget limit (oldest first)
        from collections import deque
        self._widget_order: deque = deque()  # stores panel IDs in activation order
    
    def switch_mode(self, new_mode: Mode):
        """Switch to a different Triad mode"""
        old_mode = self.current_mode
        self.current_mode = new_mode
        
        log = self.query_one("#output", RichLog)
        
        if new_mode not in MODE_COLORS:
            new_mode = Mode.GENERAL
        
        colors = MODE_COLORS[new_mode]
        
        log.write("")
        log.write(f"[bold {colors['primary']}]=== SWITCHED TO: {colors['name']} MODE ===[/]")
        
        if new_mode == Mode.GENERAL:
            log.write("Tools: File Explorer, Vault, Cipher, Settings")
        elif new_mode == Mode.ATTACK:
            log.write("Tools: Nmap, Nikto, Hydra, Netcat, WhatsApp Tracer")
        elif new_mode == Mode.AGENT:
            log.write("Tools: AI Chat, Email, WhatsApp Bridge")
        
        log.write("")
        
        self._apply_mode_css(new_mode)
        self._update_prompt()
        
        inp = self.query_one("#prompt", GhostInput)
        inp.set_mode(new_mode)
    
    def action_switch_mode_general(self):
        self.switch_mode(Mode.GENERAL)
    
    def action_switch_mode_attack(self):
        self.switch_mode(Mode.ATTACK)
        from attack_hub import AttackHub
        self.app.push_screen(AttackHub())
    
    def action_switch_mode_agent(self):
        self.switch_mode(Mode.AGENT)
        from agent_screen import AgentScreen
        self.app.push_screen(AgentScreen())

    def action_toggle_gui(self):
        if self.current_mode == Mode.ATTACK:
            from attack_hub import AttackHub
            self.app.push_screen(AttackHub())
        elif self.current_mode == Mode.AGENT:
            from agent_screen import AgentScreen
            self.app.push_screen(AgentScreen())
        else:
            self.query_one("#output", RichLog).write("[yellow]GUI Hub only available for ATTACK/AGENT modes. General mode is terminal-only.[/]")
    
    def _apply_mode_css(self, mode: Mode):
        """Apply mode-specific CSS classes to the screen"""
        self.remove_class("mode-general", "mode-attack", "mode-agent")
        
        if mode == Mode.GENERAL:
            self.add_class("mode-general")
        elif mode == Mode.ATTACK:
            self.add_class("mode-attack")
        elif mode == Mode.AGENT:
            self.add_class("mode-agent")

    async def on_unmount(self):
        await self.shell.stop()

    def compose(self) -> ComposeResult:
        # Full-height horizontal split: terminal on left, sidebar on right
        with Horizontal(id="app_body"):
            # ── LEFT: main terminal area ──────────────────────────────────
            with Vertical(id="main_layout"):
                with Horizontal(id="pane_container"):
                    yield RichLog(id="output", markup=True, wrap=True, highlight=True, max_lines=5000, classes="pane-active")
                    yield RichLog(id="output2", markup=True, wrap=True, highlight=True, max_lines=5000, classes="pane-hidden")
                yield Static(id="cwd_label", markup=True)
                with Horizontal(id="input_bar"):
                    yield Static(id="prompt_label", markup=True)
                    yield GhostInput(id="prompt", placeholder="Type a command...")

            # ── RIGHT: collapsible sidebar panels ─────────────────────────
            with Vertical(id="sidebar"):
                yield Static("[bold dim]── MONITORING ──[/]", id="sidebar_header")
                yield SystemPanel(id="sys_panel")
                yield NetworkPanel(id="net_panel")
                yield SecurityPanel(id="sec_panel")
                yield GitPanel(id="git_panel")
                yield GeoGlobe(id="geo_globe")

    async def on_mount(self):
        log = self.query_one("#output", RichLog)
        inp = self.query_one("#prompt", GhostInput)
        
        inp.set_shell(self.shell)
        
        # ── Welcome Banner ────────────────────────────────────────────────
        log.write("")
        log.write("[bold #00d4ff] ███╗   ██╗███████╗██╗  ██╗████████╗██████╗  █████╗ ██╗     [/]")
        log.write("[bold #00d4ff] ████╗  ██║██╔════╝╚██╗██╔╝╚══██╔══╝██╔══██╗██╔══██╗██║     [/]")
        log.write("[bold #00aaff] ██╔██╗ ██║█████╗   ╚███╔╝    ██║   ██████╔╝███████║██║     [/]")
        log.write("[bold #0088cc] ██║╚██╗██║██╔══╝   ██╔██╗    ██║   ██╔══██╗██╔══██║██║     [/]")
        log.write("[bold #006699] ██║ ╚████║███████╗██╔╝ ██╗   ██║   ██║  ██║██║  ██║███████╗[/]")
        log.write("[bold #004466] ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝[/]")
        log.write("")
        log.write("[dim]                    Advanced Terminal  [bold]v1.0[/bold]                    [/dim]")
        log.write("")
        log.write("[bold #00d4ff]┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄[/]")
        log.write("")
        log.write("[bold white]QUICK START[/bold white]")
        log.write("  [bold #00d4ff]mode[/] [dim]general[/dim]   — standard terminal (default)")
        log.write("  [bold #ff4444]mode[/] [dim]attack[/dim]    — security tools TUI (nmap, hydra, nikto)")
        log.write("  [bold #aa44ff]mode[/] [dim]agent[/dim]     — AI assistant TUI")
        log.write("  [bold white]explore[/bold white]          — interactive file browser")
        log.write("  [bold white]help[/bold white]             — full command reference")
        log.write("  [bold white]settings[/bold white]         — configure Nextral")
        log.write("")
        log.write("[bold #00d4ff]┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄[/]")
        log.write("")
        
        # Start shell
        log.write("[dim cyan]Initializing shell engine...[/]")
        success = await self.shell.start()
        
        if not success:
            log.write("[red]Error: Could not start shell[/]")
            return
        
        log.write("[bold green]✓ Shell ready[/]")
        log.write("")
        
        # Restore States
        self._restore_widget_states()
        
        self.stealth_mode = CONFIG.get("terminal", {}).get("stealth_mode", False)
        if self.stealth_mode:
            self.add_class("stealth-mode")

        if self.crt_mode:
            self.add_class("crt-mode")

        self._update_prompt()
        inp = self.query_one("#prompt", GhostInput)
        inp.set_mode(self.current_mode)
        inp.focus()
    def on_show(self):
        """Reload configuration and refresh UI when returning from settings."""
        self._restore_widget_states()
        self._update_prompt()

    def _restore_widget_states(self):
        """Sync widget visibility with the current CONFIG file."""
        global CONFIG
        CONFIG.clear()
        CONFIG.update(load_config())
        ui_cfg = CONFIG.get("ui", {})
        
        # Mapping of panel IDs to their refresh methods
        refresh_methods = {
            "#sys_panel": "refresh_stats",
            "#net_panel": "refresh_net",
            "#sec_panel": "refresh_sec",
            "#git_panel": "refresh_git",
        }

        # Update visibility for all widgets defined in _ALL_PANELS
        for pid, pcls, cfg_key in self._ALL_PANELS:
            try:
                p = self.query_one(pid, pcls)
                # Show sys and net panels by default if not in config
                new_state = ui_cfg.get(cfg_key, (pid in ("#sys_panel", "#net_panel")))
                p.display = new_state
                
                if new_state:
                    if pid not in self._widget_order:
                        self._widget_order.append(pid)
                    # Trigger refresh if visible
                    rf_name = refresh_methods.get(pid)
                    if rf_name and hasattr(p, rf_name):
                        getattr(p, rf_name)()
                else:
                    try:
                        self._widget_order.remove(pid)
                    except ValueError:
                        pass
            except Exception:
                pass
        
        # Enforce max widgets if config somehow has too many
        while len(self._widget_order) > self._MAX_WIDGETS:
            victim_id = self._widget_order.popleft()
            try:
                self.query_one(victim_id).display = False
            except: pass

        self._refresh_sidebar_visibility()

    def on_click(self, event: events.Click) -> None:
        """Any click on the terminal screen should focus the command input."""
        self.query_one("#prompt", GhostInput).focus()

    # ──────────────────────────────────────────────────────────────────────────
    # Widget management helpers
    # ──────────────────────────────────────────────────────────────────────────

    # All sidebar panels in registration order
    _ALL_PANELS = [
        ("#sys_panel",  SystemPanel,  "show_sys_panel"),
        ("#net_panel",  NetworkPanel, "show_net_panel"),
        ("#sec_panel",  SecurityPanel,"show_sec_panel"),
        ("#git_panel",  GitPanel,     "show_git_panel"),
        ("#geo_globe",  GeoGlobe,     "show_geo_globe"),
    ]
    _MAX_WIDGETS = 4

    def _active_widget_ids(self) -> list:
        """Return list of panel IDs that are currently displayed."""
        active = []
        for pid, pcls, _ in self._ALL_PANELS:
            try:
                if self.query_one(pid).display:
                    active.append(pid)
            except Exception:
                pass
        return active

    def _refresh_sidebar_visibility(self):
        """Show/hide sidebar based on whether any panel is visible."""
        try:
            sidebar = self.query_one("#sidebar")
            sidebar_header = self.query_one("#sidebar_header")
            visible = bool(self._active_widget_ids())
            sidebar.display = visible
            sidebar_header.display = visible
        except Exception:
            pass

    def _toggle_panel(self, panel_id: str, panel_cls, cfg_key: str, refresh_fn, log):
        """Toggle a panel. Enforce MAX_WIDGETS limit by evicting the oldest active panel."""
        try:
            panel = self.query_one(panel_id, panel_cls)
        except Exception:
            if log:
                log.write(f"[red]Panel {panel_id} not found[/]")
            return

        if panel.display:
            # Turning OFF
            panel.display = False
            try:
                self._widget_order.remove(panel_id)
            except ValueError:
                pass
            CONFIG.setdefault("ui", {})[cfg_key] = False
            save_config(CONFIG)
            self._refresh_sidebar_visibility()
            label = cfg_key.replace("show_", "").replace("_panel", "").replace("_globe", " globe").upper()
            if log:
                log.write(f"[dim]{label} widget hidden[/]")
        else:
            # Turning ON — enforce 4-widget limit
            active = self._active_widget_ids()
            if len(active) >= self._MAX_WIDGETS:
                # Evict the panel that was activated longest ago
                victim_id = None
                if self._widget_order:
                    victim_id = self._widget_order.popleft()
                else:
                    # fallback: evict first active
                    victim_id = active[0]
                for vid, vcls, vcfg in self._ALL_PANELS:
                    if vid == victim_id:
                        try:
                            vp = self.query_one(vid, vcls)
                            vp.display = False
                            CONFIG.setdefault("ui", {})[vcfg] = False
                            vlabel = vcfg.replace("show_", "").replace("_panel", "").replace("_globe", " globe").upper()
                            if log:
                                log.write(f"[yellow]⚠ Widget limit (4) reached — auto-hid {vlabel}[/]")
                        except Exception:
                            pass
                        break

            panel.display = True
            self._widget_order.append(panel_id)
            CONFIG.setdefault("ui", {})[cfg_key] = True
            save_config(CONFIG)
            if refresh_fn:
                try:
                    getattr(panel, refresh_fn)()
                except Exception:
                    pass
            self._refresh_sidebar_visibility()
            label = cfg_key.replace("show_", "").replace("_panel", "").replace("_globe", " globe").upper()
            if log:
                log.write(f"[dim]{label} widget enabled[/]")

    def _update_prompt(self):
        user = CONFIG.get("user", {}).get("username", "USER")
        cwd = self.shell.cwd or "."
        
        display_cwd = cwd
        home = os.path.expanduser("~")
        if not self.stealth_mode and display_cwd.startswith(home):
            display_cwd = "~" + display_cwd[len(home):]
        
        colors = MODE_COLORS.get(self.current_mode, MODE_COLORS[Mode.GENERAL])
        
        cwd_label = self.query_one("#cwd_label", Static)
        prompt_label = self.query_one("#prompt_label", Static)
        
        if self.stealth_mode:
            cwd_label.update("")
            prompt_label.update(f"{cwd}>")
        else:
            mode_indicator = f"[bold {colors['primary']}]{colors['icon']} {colors['name']}[/]"
            cwd_label.update(f"{mode_indicator} [white]{display_cwd}[/]")
            prompt_label.update(f"[bold {colors['primary']}]{colors['prompt']} {user}[/] [dim]~>[/]")
        
        try:
            git_panel = self.query_one("#git_panel", GitPanel)
            git_panel.set_cwd(self.shell.cwd)
        except:
            pass

    async def on_input_submitted(self, event: Input.Submitted):
        raw = event.value  # preserve exactly what the user typed
        cmd = raw.strip()
        event.input.value = ""

        # Clear ghost text
        if isinstance(event.input, GhostInput):
            event.input.ghost_text = ""

        if not raw:  # empty enter is fine in passthrough (sends bare \n)
            if not self._passthrough_mode:
                return

        active_id = "#output" if self.active_pane == "pane1" else "#output2"
        log = self.query_one(active_id, RichLog)
        user = CONFIG.get("user", {}).get("username", "USER")

        # ── PASSTHROUGH MODE ───────────────────────────────────────────────────
        # When a long-running process or SSH session is active, forward raw
        # text directly to the shell stdin; skip all command parsing.
        if self._passthrough_mode:
            if cmd.lower() in ("exit", "quit", "q"):
                # Safety hatch — let the user escape passthrough
                self.disable_passthrough()
                log.write("[bold yellow]⏎ Passthrough mode disabled.[/]")
                return
            # Echo raw input dimly so the user can see what was sent
            log.write(f"[dim]» {raw}[/]")
            await self.shell._send_raw(raw + "\n")
            return

        # ── NORMAL MODE ───────────────────────────────────────────────────────
        if not cmd:
            return

        # Echo command with professional UX
        log.write(f"\n[bold cyan]❯[/] [bold white]nextral[/]:[cyan]~[/][dim]$ {cmd}[/]")

        # If the shell is already busy, redirect as passthrough instead of
        # queuing a new command (prevents interleaved delimiter confusion).
        if self.shell._is_busy:
            log.write("[dim yellow]⚠ Shell busy — sending as raw stdin passthrough[/]")
            await self.shell._send_raw(raw + "\n")
            return

        # Check internal commands first
        if await self._handle_internal(cmd, log):
            return

        # Lock input and run shell command
        self._lock_input()

        def on_output(text):
            log.write(text)

        def on_done():
            self._unlock_input()

        await self.shell.execute(cmd, on_output, on_done)

    # ──────────────────────────────────────────────────────────────────────────
    # Passthrough mode helpers
    # ──────────────────────────────────────────────────────────────────────────

    def enable_passthrough(self, label: str = "PASSTHROUGH") -> None:
        """
        Enter passthrough mode.  All subsequent input is forwarded raw to
        the shell stdin (or whichever process is currently active).
        """
        self._passthrough_mode = True
        self._passthrough_label = label
        inp = self.query_one("#prompt", GhostInput)
        inp.placeholder = f"[{label}] Type commands — type 'exit' to leave passthrough"
        # Update the prompt label visually
        prompt_label = self.query_one("#prompt_label", Static)
        prompt_label.update(f"[bold yellow]PASSTHROUGH [{label}] ❯[/]")

    def disable_passthrough(self) -> None:
        """Exit passthrough mode and restore normal prompt."""
        self._passthrough_mode = False
        self._passthrough_label = ""
        inp = self.query_one("#prompt", GhostInput)
        inp.placeholder = ""
        self._update_prompt()

    # ──────────────────────────────────────────────────────────────────────────
    # Internal command dispatcher
    # ──────────────────────────────────────────────────────────────────────────

    async def _handle_internal(self, cmd, log):
        """Handle Nextral internal commands, then fall through to PluginManager."""
        parts = cmd.split()
        if not parts:
            return False
        cmd_name = parts[0].lower()

        if cmd_name in ("exit", "quit"):
            self.app.exit()
            return True

        if cmd_name in ("mode", "setmode"):
            if len(parts) < 2:
                log.write(f"[yellow]Current Mode:[/] {MODE_COLORS[self.current_mode]['name']}")
                log.write("[dim]Usage: mode <general|attack|agent>[/]")
                log.write("[dim]Shortcuts: Alt+1 (General), Alt+2 (Attack), Alt+3 (Agent)[/]")
                return True
            
            mode_arg = parts[1].lower()
            if mode_arg in ("general", "1", "hub", "g"):
                self.switch_mode(Mode.GENERAL)
            elif mode_arg in ("attack", "2", "strike", "a"):
                self.action_switch_mode_attack()
            elif mode_arg in ("agent", "3", "nexus", "ai", "n"):
                self.action_switch_mode_agent()
            else:
                log.write(f"[red]Unknown mode: {mode_arg}[/]")
                log.write("[dim]Valid modes: general, attack, agent[/]")
            return True
        
        if cmd_name == "attack":
            self.action_switch_mode_attack()
            return True
        
        if cmd_name == "agent":
            self.action_switch_mode_agent()
            return True
        
        if cmd_name == "hub":
            self.switch_mode(Mode.GENERAL)
            return True
        
        if cmd_name in ("attack-hub", "strike", "atk"):
            from attack_hub import AttackHub
            self.app.push_screen(AttackHub())
            return True

        if cmd_name in ("clear", "cls"):
            log.clear()
            return True

        if cmd_name == "passthrough":
            # Toggle passthrough mode manually
            if self._passthrough_mode:
                self.disable_passthrough()
                log.write("[bold yellow]⏎ Passthrough mode DISABLED.[/]")
            else:
                self.enable_passthrough("SHELL")
                log.write("[bold green]⚡ Passthrough mode ENABLED — raw stdin forwarding active.[/]")
                log.write("[dim]Type [bold]exit[/] to return to normal mode.[/]")
            return True

        if cmd_name == "copy":
            # Copy the current log lines to clipboard
            try:
                pyperclip.copy("Copy feature initialized. Currently logged content cannot be scraped easily from terminal. Use 'export' for full logs.")
                log.write("[green]>>> Last action: Notification copied to clipboard.[/]")
                log.write("[dim]Note: Real-time scraping of all log history is restricted due to TUI sandbox. Use system Shift+Select for terminal copy.[/]")
            except Exception:
                log.write("[red]ERROR: Clipboard access failed.[/]")
            return True

        if cmd_name == "setuser" and len(parts) > 1:
            new_user = parts[1].upper()
            CONFIG["user"]["username"] = new_user
            save_config(CONFIG)
            log.write(f"[green]Username globally updated to: {new_user}[/]")
            self._update_prompt()
            os.environ['NEXTRAL_USER'] = new_user
            return True
        
        # ── Widget toggle helpers ──────────────────────────────────────────────
        # Maps command names → (panel_id, panel_class, config_key, refresh_method)
        _PANEL_MAP = {
            "status":   ("#sys_panel",  SystemPanel,   "show_sys_panel",  "refresh_stats"),
            "sysinfo":  ("#sys_panel",  SystemPanel,   "show_sys_panel",  "refresh_stats"),
            "network":  ("#net_panel",  NetworkPanel,  "show_net_panel",  "refresh_net"),
            "netmon":   ("#net_panel",  NetworkPanel,  "show_net_panel",  "refresh_net"),
            "security": ("#sec_panel",  SecurityPanel, "show_sec_panel",  "refresh_sec"),
            "secmon":   ("#sec_panel",  SecurityPanel, "show_sec_panel",  "refresh_sec"),
            "git-visual": ("#git_panel", GitPanel,     "show_git_panel",  "refresh_git"),
            "gitmon":   ("#git_panel",  GitPanel,      "show_git_panel",  "refresh_git"),
            "globe":    ("#geo_globe",  GeoGlobe,      "show_geo_globe",  None),
            "earth":    ("#geo_globe",  GeoGlobe,      "show_geo_globe",  None),
            "geo":      ("#geo_globe",  GeoGlobe,      "show_geo_globe",  None),
        }

        if cmd_name in _PANEL_MAP:
            pid, pcls, cfg_key, refresh_fn = _PANEL_MAP[cmd_name]
            self._toggle_panel(pid, pcls, cfg_key, refresh_fn, log)
            return True

        # ── Show widget status ─────────────────────────────────────────────────
        if cmd_name == "widgets":
            active = self._active_widget_ids()
            log.write(f"[bold cyan]WIDGETS[/] [dim]({len(active)}/4 active)[/]")
            all_panels = [
                ("#sys_panel",  "CPU/MEM",    "status"),
                ("#net_panel",  "NETWORK",    "network"),
                ("#sec_panel",  "SECURITY",   "security"),
                ("#git_panel",  "GIT",        "gitmon"),
                ("#geo_globe",  "GEO-GLOBE",  "globe"),
            ]
            for pid, name, cmd in all_panels:
                try:
                    p = self.query_one(pid)
                    icon = "[green]●[/]" if p.display else "[dim]○[/]"
                    log.write(f"  {icon} [bold]{name}[/] [dim]— toggle: {cmd}[/]")
                except Exception:
                    pass
            log.write(f"[dim]Use 'toggle monitoring' or 'toggle dev' for group toggles.[/]")
            return True

        # ── Group toggles ──────────────────────────────────────────────────────
        if cmd_name == "toggle" and len(parts) >= 2:
            group = parts[1].lower()
            if group in ("monitoring", "mon", "system"):
                # Toggle CPU+MEM and NETWORK together
                for pid, pcls, cfg_k, rf in [
                    ("#sys_panel", SystemPanel, "show_sys_panel", "refresh_stats"),
                    ("#net_panel", NetworkPanel, "show_net_panel", "refresh_net"),
                ]:
                    self._toggle_panel(pid, pcls, cfg_k, rf, log)
                return True
            if group in ("security", "sec"):
                for pid, pcls, cfg_k, rf in [
                    ("#sec_panel", SecurityPanel, "show_sec_panel", "refresh_sec"),
                ]:
                    self._toggle_panel(pid, pcls, cfg_k, rf, log)
                return True
            if group in ("dev", "git"):
                for pid, pcls, cfg_k, rf in [
                    ("#git_panel", GitPanel, "show_git_panel", "refresh_git"),
                ]:
                    self._toggle_panel(pid, pcls, cfg_k, rf, log)
                return True
            if group in ("all",):
                active = self._active_widget_ids()
                if active:
                    # Turning ALL off
                    self._widget_order.clear()
                    for pid, pcls, cfg_k, rf in [
                        ("#sys_panel", SystemPanel, "show_sys_panel", "refresh_stats"),
                        ("#net_panel", NetworkPanel, "show_net_panel", "refresh_net"),
                        ("#sec_panel", SecurityPanel, "show_sec_panel", "refresh_sec"),
                        ("#git_panel", GitPanel, "show_git_panel", "refresh_git"),
                        ("#geo_globe", GeoGlobe, "show_geo_globe", None),
                    ]:
                        try:
                            p = self.query_one(pid, pcls)
                            p.display = False
                            CONFIG.setdefault("ui", {})[cfg_k] = False
                            if pid in self._widget_order:
                                self._widget_order.remove(pid)
                        except Exception:
                            pass
                    save_config(CONFIG)
                    self._refresh_sidebar_visibility()
                    log.write("[dim]All widgets hidden.[/]")
                else:
                    # Turning default widgets ON (up to max)
                    self._widget_order.clear()
                    count = 0
                    for pid, pcls, cfg_k, rf in [
                        ("#sys_panel", SystemPanel, "show_sys_panel", "refresh_stats"),
                        ("#net_panel", NetworkPanel, "show_net_panel", "refresh_net"),
                        ("#sec_panel", SecurityPanel, "show_sec_panel", "refresh_sec"),
                        ("#git_panel", GitPanel, "show_git_panel", "refresh_git"),
                    ]:
                        if count >= self._MAX_WIDGETS:
                            break
                        try:
                            p = self.query_one(pid, pcls)
                            p.display = True
                            CONFIG.setdefault("ui", {})[cfg_k] = True
                            self._widget_order.append(pid)
                            if rf and hasattr(p, rf):
                                getattr(p, rf)()
                            count += 1
                        except Exception:
                            pass
                    save_config(CONFIG)
                    self._refresh_sidebar_visibility()
                    log.write(f"[dim]Default widgets enabled ({count}).[/]")
                return True

        if cmd_name in ("globe", "earth", "geo"):
            self._toggle_panel("#geo_globe", GeoGlobe, "show_geo_globe", None, log)
            return True

        # =====================================================================
        # CRT SCANLINE MODE TOGGLE
        # =====================================================================
        if cmd_name in ("toggle-fx", "crt", "scanlines"):
            self.crt_mode = not self.crt_mode
            CONFIG.setdefault("terminal", {})["crt_mode"] = self.crt_mode
            save_config(CONFIG)
            
            if self.crt_mode:
                self.add_class("crt-mode")
                log.write("[bold green]▓▓▓ CRT MODE ACTIVATED ▓▓▓[/]")
                log.write("[dim]Scanlines and glow effects enabled.[/]")
            else:
                self.remove_class("crt-mode")
                log.write("[dim]CRT mode deactivated.[/]")
            return True

        # =====================================================================
        # PORT SCANNER with RADAR ANIMATION
        # =====================================================================
        if cmd_name == "portscan":
            if len(parts) < 2:
                log.write("[yellow]Usage: portscan <target> [port-range][/]")
                log.write("[dim]Example: portscan 127.0.0.1 20-80[/]")
                return True

            target = parts[1]
            port_range = parts[2] if len(parts) > 2 else "1-1024"
            await self._run_portscan(target, port_range, log)
            return True

        # =====================================================================
        # FILE EXPLORER  (needs special set_cd_callback wiring)
        # =====================================================================
        if cmd_name == "explore":
            from explorer_screen import ExplorerScreen
            explorer = ExplorerScreen(self.shell.cwd)

            def on_cd(new_path):
                self.shell.cwd = new_path
                self._update_prompt()

            explorer.set_cd_callback(on_cd)
            self.app.push_screen(explorer)
            return True

        # =====================================================================
        # BLACKBOOK  (needs special set_select_callback wiring)
        # =====================================================================
        if cmd_name in ("book", "blackbook", "snippets"):
            from blackbook import BlackbookScreen
            book = BlackbookScreen()

            def on_snippet_select(command):
                inp = self.query_one("#prompt", GhostInput)
                inp.value = command
                inp.cursor_position = len(command)

            book.set_select_callback(on_snippet_select)
            self.app.push_screen(book)
            return True

        # =====================================================================
        # HEX-RAY  (needs file-path resolution before push)
        # =====================================================================
        if cmd_name in ("hex", "hexray", "hex-ray"):
            if len(parts) < 2:
                log.write("[yellow]Usage: hex <file_path>[/]")
                log.write("[dim]Opens a binary hex view of the file.[/]")
                return True

            file_path = " ".join(parts[1:])
            if not os.path.isabs(file_path):
                file_path = os.path.join(self.shell.cwd, file_path)

            if not os.path.exists(file_path):
                log.write(f"[red]File not found: {file_path}[/]")
                return True

            from hex_ray import HexScreen
            self.app.push_screen(HexScreen(file_path))
            return True

        # =====================================================================
        # NETCAT  (needs mode inference from alias)
        # =====================================================================
        if cmd_name in ("nc", "netcat", "listen"):
            target = parts[1] if len(parts) > 1 else ""
            port = int(parts[2]) if len(parts) > 2 else 0
            mode = "listen" if cmd_name == "listen" else "connect"
            from netcat_screen import NetcatScreen
            self.app.push_screen(NetcatScreen(target, port, mode))
            return True

        # =====================================================================
        # SSH  (needs passthrough callback wiring)
        # =====================================================================
        if cmd_name in ("ssh", "sshclient"):
            host = parts[1] if len(parts) > 1 else ""
            from ssh_screen import SSHScreen
            ssh_screen = SSHScreen(host)

            # Wire up passthrough so TerminalScreen locks/unlocks stdin
            def _ssh_passthrough_cb(active: bool):
                if active:
                    self.enable_passthrough("SSH")
                else:
                    self.disable_passthrough()

            ssh_screen.set_passthrough_callback(_ssh_passthrough_cb)
            self.app.push_screen(ssh_screen)
            return True

        # =====================================================================
        # PLUGIN MANAGER — handle all remaining screen-launching commands
        # =====================================================================
        if self._plugins.dispatch(cmd, parts, self.app):
            return True

        if cmd_name == "ask":
            if len(parts) < 2:
                log.write("[yellow]Usage: ask <query>[/]")
                return True
                
            query = " ".join(parts[1:])
            log.write(f"[dim]Asking AI agent ({CONFIG.get('ai', {}).get('provider', 'Ollama')})...[/]")
            
            # Quick one-off query
            from agent_backend import AgentBackend
            backend = AgentBackend()
            response = await backend.generate_response(query)
            
            log.write(f"[bold cyan]AI:[/]\n{response}\n")
            return True

        # =====================================================================
        # THE SCAFFOLD (Multiplexing)
        # =====================================================================
        if cmd_name == "split":
            log1 = self.query_one("#output", RichLog)
            log2 = self.query_one("#output2", RichLog)
            
            if "pane-hidden" in log2.classes:
                # Enable Split
                log2.remove_class("pane-hidden")
                log1.add_class("pane-split")
                log2.add_class("pane-split")
                # Secondary starts as non-active
                log2.add_class("pane-inactive")
                log.write("[bold cyan]>>> MULTIPLEXING ENGAGED: Side-by-Side Mode[/]")
            else:
                # Disable Split
                log1.remove_class("pane-split")
                log2.remove_class("pane-split")
                log2.add_class("pane-hidden")
                # Force back to pane1
                self.active_pane = "pane1"
                log1.add_class("pane-active")
                log1.remove_class("pane-inactive")
                log1.write("[bold yellow]>>> MULTIPLEXING DISENGAGED: Single Mode[/]")
            return True

        if cmd_name in ("switch", "next"):
            log1 = self.query_one("#output", RichLog)
            log2 = self.query_one("#output2", RichLog)
            
            if "pane-hidden" in log2.classes:
                log.write("[red]ERROR: Single Mode active. Use 'split' to enable second pane.[/]")
                return True
                
            if self.active_pane == "pane1":
                self.active_pane = "pane2"
                log1.remove_class("pane-active")
                log1.add_class("pane-inactive")
                log2.remove_class("pane-inactive")
                log2.add_class("pane-active")
                log2.write("[cyan]>>> Focus: PANE 2[/]")
            else:
                self.active_pane = "pane1"
                log2.remove_class("pane-active")
                log2.add_class("pane-inactive")
                log1.remove_class("pane-inactive")
                log1.add_class("pane-active")
                log1.write("[cyan]>>> Focus: PANE 1[/]")
            return True

        if cmd_name == "audit":
            from rich.table import Table
            
            log.write("[bold yellow]>>> INITIATING SECURITY AUDIT...[/]")
            await asyncio.sleep(0.5)
            
            is_win = sys.platform == 'win32'
            try:
                if is_win:
                    is_admin = os.getlogin() == "Administrator" or subprocess.call("net session", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0
                else:
                    is_admin = os.getuid() == 0
            except:
                is_admin = False
            
            admin_status = "[bold green]ELEVATED[/]" if is_admin else "[bold yellow]STANDARD[/]"
            log.write(f"[cyan]Permission Level:[/cyan] {admin_status}")
            
            if is_win:
                log.write("[cyan]Scanning Firewall Profiles...[/cyan]")
                firewall_status = {}
                try:
                    proc = await asyncio.create_subprocess_shell("netsh advfirewall show allprofiles state", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
                    stdout, _ = await proc.communicate()
                    output = stdout.decode('utf-8', errors='ignore')
                    
                    current_profile = None
                    for line in output.splitlines():
                        if "Profile Settings" in line:
                            current_profile = line.split()[0]
                        if "State" in line and current_profile:
                            state = line.split()[1].strip()
                            firewall_status[current_profile] = state
                except:
                    pass
                
                fw_table = Table(box=None, show_header=False)
                for profile, state in firewall_status.items():
                    color = "green" if state.upper() == "ON" else "red"
                    fw_table.add_row(f"[dim]{profile}[/]", f"[{color}]{state.upper()}[/{color}]")
                log.write(fw_table)
            else:
                log.write("[cyan]Checking IP Tables / UFW...[/cyan]")
                try:
                    proc = await asyncio.create_subprocess_shell("ufw status", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
                    stdout, _ = await proc.communicate()
                    log.write(f"[dim]{stdout.decode().splitlines()[0] if stdout else 'UFW Status: Unknown'}[/]")
                except:
                    log.write("[dim]UFW not found or access denied.[/]")

            if is_win:
                log.write("[cyan]Checking Endpoint Protection...[/cyan]")
                av_found = []
                try:
                    proc = await asyncio.create_subprocess_shell("wmic /namespace:\\\\root\\SecurityCenter2 path AntivirusProduct get displayName", stdout=asyncio.subprocess.PIPE)
                    stdout, _ = await proc.communicate()
                    avs = [line.strip() for line in stdout.decode().splitlines() if line.strip() and "displayName" not in line]
                    av_found = avs
                except:
                    pass
                
                if av_found:
                    for av in av_found:
                        log.write(f"  [green]✓ {av} Detected[/]")
                else:
                    log.write("  [red]⚠ No registered Antivirus detected (or access denied)[/]")
            else:
                log.write("[cyan]Checking Security Modules...[/cyan]")
                # Simple check for common Linux security modules
                for mod in ["selinux", "apparmor"]:
                    try:
                        proc = await asyncio.create_subprocess_shell(f"aa-status --enabled || getenforce", stdout=asyncio.subprocess.PIPE)
                        stdout, _ = await proc.communicate()
                        if stdout: log.write(f"  [green]✓ {mod.upper()} Detected/Active[/]")
                    except:
                        pass

            log.write("[bold green]>>> AUDIT COMPLETE[/]\n")
            return True

        # =====================================================================
        # LAUNCHER (Platform Aware)
        # =====================================================================
        if cmd_name == "launch":
            if len(parts) < 2:
                log.write("[yellow]Usage: launch <app_name | file_path>[/]")
                return True
            
            target = parts[1]
            log.write(f"[dim]Attempting to launch: {target}...[/]")
            
            try:
                if sys.platform == 'win32':
                    # Windows specific shortcuts or generic start
                    apps = {
                        "chrome": "chrome",
                        "notepad": "notepad",
                        "calc": "calc",
                        "code": "code",
                        "explorer": "explorer"
                    }
                    cmd_to_run = apps.get(target.lower(), target)
                    os.startfile(cmd_to_run)
                else:
                    # Linux generic opener
                    subprocess.Popen(["xdg-open", target], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
                
                log.write(f"[green]✓ Process initiated for {target}[/]")
            except Exception as e:
                log.write(f"[red]Execution failed: {e}[/]")
            return True

        if cmd_name == "netscan":
            from rich.table import Table
            
            log.write("[bold yellow]>>> SCANNING ACTIVE CONNECTIONS...[/]")
            await asyncio.sleep(0.5)
            
            table = Table(title="ACTIVE LINKS", border_style="green", header_style="bold cyan")
            table.add_column("Proto", style="white")
            table.add_column("Local Address", style="cyan")
            table.add_column("Remote Address", style="magenta")
            table.add_column("Status", style="yellow")
            table.add_column("PID", style="dim")
            
            conns = psutil.net_connections(kind='inet')
            count = 0
            for c in conns:
                if c.status == 'ESTABLISHED':
                    count += 1
                    laddr = f"{c.laddr.ip}:{c.laddr.port}"
                    raddr = f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else "*"
                    table.add_row(
                        "TCP" if c.type == socket.SOCK_STREAM else "UDP", 
                        laddr, 
                        raddr, 
                        c.status, 
                        str(c.pid)
                    )
                    if count >= 15:
                        break
            
            log.write(table)
            if count == 0:
                log.write("[dim]No active external connections found.[/]")
            elif count >= 15:
                log.write("[dim italic]... output truncated for readability ...[/]")
            log.write("")
            return True
            
        if cmd_name == "help":
            from rich.table import Table
            from rich.panel import Panel
            
            # Header Panel
            log.write("")
            log.write(Panel.fit(
                "[bold cyan]N E X T R A L   C O M M A N D   I N D E X[/]\n[dim]v1.0 BETA — Advanced Operation Terminal[/]",
                border_style="cyan",
                padding=(1, 2)
            ))

            # 1. CORE MODES
            t1 = Table(show_header=True, header_style="bold magenta", box=None, expand=True)
            t1.add_column("CORE MODES", width=15)
            t1.add_column("Command", style="cyan", width=12)
            t1.add_column("Description", style="white")
            t1.add_row("GENERAL", "hub", "Default workspace for standard terminal operations.")
            t1.add_row("STRIKE", "attack", "Switch to Offensive TUI for network penetration tools.")
            t1.add_row("NEXUS", "agent", "Conversational AI agent mode for automated tasks.")
            log.write(t1)

            # 2. MONITORING & WIDGETS
            t2 = Table(show_header=True, header_style="bold green", box=None, expand=True)
            t2.add_column("UI & WIDGETS", width=15)
            t2.add_column("Command", style="cyan", width=12)
            t2.add_column("Effect", style="white")
            t2.add_row("STATUS", "widgets", "List all available dashboard widgets.")
            t2.add_row("MONITOR", "toggle mon", "Toggle System (CPU/MEM) and Network metrics.")
            t2.add_row("SECURE", "toggle sec", "Toggle system security & process monitoring.")
            t2.add_row("DEV", "toggle git", "Toggle Git repository tracking widgets.")
            t2.add_row("GLOBAL", "toggle all", "Immediately hide the sidebar and all active widgets.")
            t2.add_row("VISUAL", "crt", "Toggle retroactive scanline/phosphor CRT filter.")
            t2.add_row("PANIC", "stealth", "Toggle stealth mode (obscures UI with fake output).")
            log.write(t2)

            # 3. OPERATION TOOLS
            t3 = Table(show_header=True, header_style="bold red", box=None, expand=True)
            t3.add_column("OPERATIONS", width=15)
            t3.add_column("Command", style="cyan", width=12)
            t3.add_column("Tool Description", style="white")
            t3.add_row("RADAR", "portscan", "Radar-animated port scanner: [dim]portscan 127.0.0.1[/]")
            t3.add_row("NET-LINKS", "netscan", "Display active TCP/UDP established connections.")
            t3.add_row("ENCRYPT", "vault", "Manage encrypted secure file storage containers.")
            t3.add_row("PROTOCOL", "ssh", "Initiate secure shell connections to remote nodes.")
            t3.add_row("WEB-VULN", "nikto", "Web-server vulnerability scanner (Attack mode).")
            t3.add_row("MAP-NET", "nmap", "Network mapping & service discovery (Attack mode).")
            log.write(t3)

            # 4. SYSTEM & SHORTCUTS
            t4 = Table(show_header=True, header_style="bold yellow", box=None, expand=True)
            t4.add_column("SYSTEM", width=15)
            t4.add_column("Action", style="cyan", width=12)
            t4.add_column("Interaction", style="white")
            t4.add_row("FILE OPS", "ls / dir", "Standard directory listing.")
            t4.add_row("NAVIGATE", "cd <dir>", "Change current working directory.")
            t4.add_row("CLEAR", "clear / cls", "Wipe terminal scrollback history.")
            t4.add_row("SETTINGS", "settings", "Customize user profile and terminal behavior.")
            t4.add_row("EXIT", "exit / quit", "Safely terminate Nextral session.")
            t4.add_row("TAB", "[TAB]", "Trigger intelligent path & command autocomplete.")
            t4.add_row("ARROWS", "[↑ / ↓]", "Cycle through command history (standard shell).")
            t4.add_row("PASTE", "CTRL+V", "Paste text from system clipboard securely.")
            log.write(t4)

            log.write("\n[dim italic]Tip: You can run standard OS commands (pip, git, etc.) directly in GENERAL mode.[/]\n")
            return True
        
        return False

    async def _run_portscan(self, target: str, port_range: str, log):
        """Execute the animated port scanner"""
        from rich.table import Table
        
        # Parse port range
        try:
            if '-' in port_range:
                start, end = map(int, port_range.split('-'))
            else:
                start = end = int(port_range)
            ports = list(range(start, end + 1))
        except:
            log.write("[red]Invalid port range. Use format: 20-80 or 80[/]")
            return
        
        # Limit scan
        if len(ports) > 1000:
            log.write("[yellow]⚠ Limiting scan to first 1000 ports for performance.[/]")
            ports = ports[:1000]
        
        # Animated header
        log.write("")
        log.write("[bold red]█████████████████████████████████████████████████████████████[/]")
        log.write("[bold red]██[/]                                                         [bold red]██[/]")
        log.write("[bold red]██[/]         [bold white]◉ NEXTRAL RADAR PORT SCANNER ◉[/]               [bold red]██[/]")
        log.write("[bold red]██[/]                                                         [bold red]██[/]")
        log.write("[bold red]█████████████████████████████████████████████████████████████[/]")
        log.write("")
        log.write(f"[cyan]Target:[/] [white]{target}[/]")
        log.write(f"[cyan]Ports:[/]  [white]{start}-{end}[/] ({len(ports)} ports)")
        log.write("")
        
        # Radar sweep animation
        radar_frames = ["◜", "◠", "◝", "◞", "◡", "◟"]
        open_ports = []
        
        log.write("[yellow]>>> INITIATING SWEEP...[/]")
        await asyncio.sleep(0.3)
        
        # Scan with animation
        batch_size = 50
        for i in range(0, len(ports), batch_size):
            batch = ports[i:i+batch_size]
            
            # Radar animation frame
            frame = radar_frames[(i // batch_size) % len(radar_frames)]
            progress = int((i / len(ports)) * 30)
            bar = f"[green]{'█' * progress}[/][dim]{'░' * (30 - progress)}[/]"
            log.write(f"\r[cyan]{frame}[/] Scanning ports {batch[0]}-{batch[-1]}... {bar} {int((i/len(ports))*100)}%")
            
            # Parallel scan batch
            tasks = [self._check_port(target, p) for p in batch]
            results = await asyncio.gather(*tasks)
            
            for port, is_open in zip(batch, results):
                if is_open:
                    open_ports.append(port)
                    log.write(f"  [bold green]◉ PING! Port {port} OPEN[/]")
        
        log.write("")
        log.write("[bold green]>>> SCAN COMPLETE <<<[/]")
        log.write("")
        
        # Results table
        if open_ports:
            table = Table(title="[bold green]OPEN PORTS DETECTED[/]", border_style="green", header_style="bold cyan")
            table.add_column("Port", style="white", justify="right")
            table.add_column("Service", style="cyan")
            table.add_column("Status", style="green")
            
            # Common port names
            services = {
                20: "FTP-DATA", 21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP",
                53: "DNS", 80: "HTTP", 110: "POP3", 143: "IMAP", 443: "HTTPS",
                445: "SMB", 3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL",
                6379: "Redis", 8080: "HTTP-ALT", 27017: "MongoDB"
            }
            
            for port in open_ports:
                service = services.get(port, "Unknown")
                table.add_row(str(port), service, "● OPEN")
            
            log.write(table)
        else:
            log.write("[dim]No open ports found in the scanned range.[/]")
        
        log.write("")

    async def _check_port(self, host: str, port: int, timeout: float = 0.5) -> bool:
        """Check if a port is open"""
        try:
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=timeout
            )
            writer.close()
            await writer.wait_closed()
            return True
        except:
            return False
    
    def _lock_input(self):
        self._locked = True
        inp = self.query_one("#prompt", GhostInput)
        inp.disabled = True
        
    def _unlock_input(self):
        self._locked = False
        inp = self.query_one("#prompt", GhostInput)
        inp.disabled = False
        self._update_prompt()
        inp.focus()

    def action_history_up(self):
        if self._locked:
            return
        inp = self.query_one("#prompt", GhostInput)
        val = self.shell.history_up()
        if val is not None:
            inp.value = val
            inp.cursor_position = len(val)
            inp.ghost_text = ""

    def action_history_down(self):
        if self._locked:
            return
        inp = self.query_one("#prompt", GhostInput)
        val = self.shell.history_down()
        if val is not None:
            inp.value = val
            inp.cursor_position = len(val)
            inp.ghost_text = ""

    def action_toggle_stealth(self):
        """Toggle Stealth Mode (Panic Button)"""
        self.stealth_mode = not self.stealth_mode
        
        # Save state
        CONFIG.setdefault("terminal", {})["stealth_mode"] = self.stealth_mode
        save_config(CONFIG)
        
        log = self.query_one("#output", RichLog)
        
        if self.stealth_mode:
            self.add_class("stealth-mode")
            log.write("[bold white]⚠ STEALTH MODE ENGAGED - UI SUPPRESSED[/]")
            if sys.platform == 'win32':
                log.write("Microsoft Windows [Version 10.0.19045.5445]")
                log.write("(c) Microsoft Corporation. All rights reserved.")
            else:
                log.write("Linux engine v6.1.0-23-amd64 (debian-kernel@lists.debian.org)")
                log.write("(c) Free Software Foundation. All rights reserved.")
            log.write("")
        else:
            self.remove_class("stealth-mode")
            log.write("[bold cyan]>>> SYSTEM RESTORED - VISUALS ONLINE[/]")
        
        self._update_prompt()
            
    def action_autocomplete(self):
        if self._locked:
            return
        inp = self.query_one("#prompt", GhostInput)
        result = self.shell.autocomplete(inp.value)
        if result:
            inp.value = result
            inp.cursor_position = len(result)
            inp.ghost_text = ""

    def action_accept_ghost(self):
        """Accept ghost suggestion on Right arrow"""
        if self._locked:
            return
        inp = self.query_one("#prompt", GhostInput)
        if inp.ghost_text and inp.cursor_position == len(inp.value):
            inp.value = inp.value + inp.ghost_text
            inp.cursor_position = len(inp.value)
            inp.ghost_text = ""

    def action_paste_from_clipboard(self):
        """Handle Ctrl+V from screen level"""
        if not self._locked:
            inp = self.query_one("#prompt", GhostInput)
            inp.action_paste_from_clipboard()

    def _copy_to_clipboard(self, text: str, log: RichLog):
        """Copies the given text to the system clipboard."""
        try:
            pyperclip.copy(text)
            log.write(f"[green]Copied to clipboard:[/][dim] {text}[/]")
        except pyperclip.PyperclipException as e:
            log.write(f"[red]Error copying to clipboard: {e}[/]")
            log.write("[dim]Please ensure you have a clipboard utility installed (e.g., xclip or xsel on Linux).[/]")

    async def action_interrupt(self):
        log = self.query_one("#output", RichLog)
        log.write("[bold red]^C (INTERRUPT)[/]")
        self.shell.interrupt()

    def action_clear_screen(self):
        self.query_one("#output", RichLog).clear()
    
    def action_quit(self):
        self.app.exit()

# ==============================================================================
# MAIN APPLICATION
# ==============================================================================

class NextralApp(App):
    """Nextral Terminal Application"""
    
    CSS = """
    /* ================================================================ */
    /* Global Screen                                                    */
    /* ================================================================ */
    Screen {
        background: #07070f;
        layout: vertical;
    }

    /* Full-height horizontal layout body */
    #app_body {
        height: 1fr;
        width: 100%;
        layout: horizontal;
    }

    /* ================================================================ */
    /* Main Terminal Area                                               */
    /* ================================================================ */
    #main_layout {
        height: 100%;
        width: 1fr;
        layout: vertical;
        padding: 0 0 0 0;
    }

    #pane_container {
        height: 1fr;
        width: 100%;
    }

    #output, #output2 {
        scrollbar-background: #07070f;
        scrollbar-color: #1e3a5f;
        scrollbar-corner-color: #07070f;
        padding: 0 2;
    }

    #cwd_label {
        height: 1;
        width: 100%;
        padding: 0 2;
        color: #007ec2;
    }

    /* ================================================================ */
    /* Input Bar — Premium Typing Area                                   */
    /* ================================================================ */
    #input_bar {
        height: 3;
        width: 100%;
        padding: 0 0;
        margin-top: 0;
        background: #0b0d1a;
        border-top: solid #1a2a4a;
        transition: background 200ms;
    }

    #prompt_label {
        width: auto;
        height: 3;
        content-align: left middle;
        padding: 0 1 0 2;
    }

    #prompt {
        width: 1fr;
        height: 3;
        border: none;
        border-left: double #00d4ff;
        background: transparent;
        padding: 0 1;
        color: #e0f2fe;
        transition: border-left 200ms, background 200ms;
    }

    #prompt:focus {
        border-left: thick #00f0ff;
        background: #0d152a;
    }

    /* Ghost suggestion text */
    #prompt .input--suggestion {
        color: #4b5563;
        text-style: italic;
    }

    Input {
        border: none;
    }

    /* ================================================================ */
    /* Sidebar — Glassmorphism widget panels                            */
    /* ================================================================ */
    #sidebar {
        width: 36;
        height: 100%;
        layout: vertical;
        background: rgba(0,0,0,0) !important;
        padding: 0 0 0 0;
    }

    #sidebar_header {
        text-align: center;
        color: #2a3a5a;
        height: 1;
        padding: 0 1;
        margin-bottom: 0;
    }

    SystemPanel, NetworkPanel, SecurityPanel, GitPanel, GeoGlobe {
        background: rgba(0,0,0,0) !important;
    }

    SystemPanel {
        border-left: solid #00d4ff;
        padding: 0 1 0 1;
        height: auto;
        margin: 0;
        color: #c0d8f0;
    }

    NetworkPanel {
        border-left: solid #00ff88;
        padding: 0 1 0 1;
        height: auto;
        margin: 0;
        color: #c0f0d8;
    }

    SecurityPanel {
        border-left: solid #ffaa00;
        padding: 0 1 0 1;
        height: auto;
        margin: 0;
        color: #f0e0c0;
    }

    GitPanel {
        border-left: solid #aa44ff;
        padding: 0 1 0 1;
        height: auto;
        margin: 0;
        color: #d8c0f4;
    }

    GeoGlobe {
        border-left: solid #00aaff;
        padding: 0 1 0 1;
        height: auto;
        margin: 0;
        color: #c0d4f0;
    }

    /* Widget group label separators */
    .widget-group-label {
        color: #1a2a4a;
        height: 1;
        padding: 0 1;
        text-align: center;
    }

    /* ================================================================ */
    /* Pane visibility                                                  */
    /* ================================================================ */
    .pane-active  { opacity: 1.0; }
    .pane-inactive { opacity: 0.7; }
    .pane-split { width: 50%; border: solid #1a1a2e; }
    .pane-hidden { display: none; }

    /* ================================================================ */
    /* CRT Mode                                                        */
    /* ================================================================ */
    Screen.crt-mode { background: #020502; }
    Screen.crt-mode #output { text-style: bold; color: #00ff44; background: #010201; }
    Screen.crt-mode #cwd_label { text-style: bold; color: #00ff88; }
    Screen.crt-mode #prompt { color: #00ff66; text-style: bold; background: #020502; border-left: double #00ff44; }
    Screen.crt-mode #input_bar { background: #020502; border-top: solid #00ff44; }
    Screen.crt-mode SystemPanel,
    Screen.crt-mode NetworkPanel,
    Screen.crt-mode SecurityPanel,
    Screen.crt-mode GitPanel,
    Screen.crt-mode GeoGlobe { border-left: double #00ff44; background: rgba(0,0,0,0) !important; }

    /* ================================================================ */
    /* Stealth Mode                                                     */
    /* ================================================================ */
    Screen.stealth-mode { background: #000000; color: #cccccc; }
    Screen.stealth-mode #sidebar { display: none; }
    Screen.stealth-mode #output {
        background: #000000;
        color: #cccccc;
        text-style: none;
        scrollbar-background: #000000;
        scrollbar-color: #333333;
        border: none;
    }
    Screen.stealth-mode #cwd_label { display: none; }
    Screen.stealth-mode #input_bar { background: #000000; border-top: solid #333333; }
    Screen.stealth-mode #prompt_label { color: #cccccc; text-style: none; }
    Screen.stealth-mode #prompt { color: #cccccc; text-style: none; background: #000000; width: 1fr; border-left: solid #555555; }
    Screen.stealth-mode Header { display: none; }
    Screen.stealth-mode Footer { display: none; }

    /* ================================================================ */
    /* GENERAL MODE — Cyber Blue                                        */
    /* ================================================================ */
    Screen.mode-general { background: transparent; }
    Screen.mode-general #output { background: rgba(0,0,0,0); color: #c8d8e8; }
    Screen.mode-general #cwd_label { color: #00d4ff; }
    Screen.mode-general #input_bar { background: #0b0d1a; border-top: solid #0d2040; }
    Screen.mode-general #prompt { border-left: double #00d4ff; color: #00ffff; }
    Screen.mode-general #prompt:focus { border-left: double #00f8ff; background: #0d1525; }
    Screen.mode-general #prompt_label { color: #00d4ff; }
    Screen.mode-general Header { background: #0d1a2e; color: #00d4ff; }
    Screen.mode-general SystemPanel,
    Screen.mode-general NetworkPanel,
    Screen.mode-general SecurityPanel,
    Screen.mode-general GitPanel,
    Screen.mode-general GeoGlobe { background: rgba(0,0,0,0) !important; }

    /* ================================================================ */
    /* ATTACK MODE — Red                                                */
    /* ================================================================ */
    Screen.mode-attack { background: transparent; }
    Screen.mode-attack #output { background: rgba(0,0,0,0); color: #f0d0d0; }
    Screen.mode-attack #cwd_label { color: #ff5555; }
    Screen.mode-attack #input_bar { background: #150a0a; border-top: solid #400d0d; }
    Screen.mode-attack #prompt { border-left: double #ff4444; color: #ff6666; }
    Screen.mode-attack #prompt:focus { border-left: double #ff6666; background: #201010; }
    Screen.mode-attack #prompt_label { color: #ff4444; }
    Screen.mode-attack Header { background: #3a0d0d; color: #ff4444; }
    Screen.mode-attack SystemPanel,
    Screen.mode-attack NetworkPanel,
    Screen.mode-attack SecurityPanel,
    Screen.mode-attack GitPanel,
    Screen.mode-attack GeoGlobe { background: rgba(0,0,0,0) !important; }

    /* ================================================================ */
    /* AGENT MODE — Purple                                              */
    /* ================================================================ */
    Screen.mode-agent { background: transparent; }
    Screen.mode-agent #output { background: rgba(0,0,0,0); color: #e0d0f0; }
    Screen.mode-agent #cwd_label { color: #bb55ff; }
    Screen.mode-agent #input_bar { background: #110d1a; border-top: solid #281040; }
    Screen.mode-agent #prompt { border-left: double #aa44ff; color: #cc88ff; }
    Screen.mode-agent #prompt:focus { border-left: double #cc66ff; background: #160f20; }
    Screen.mode-agent #prompt_label { color: #aa44ff; }
    Screen.mode-agent Header { background: #1e0d3a; color: #aa44ff; }
    Screen.mode-agent SystemPanel,
    Screen.mode-agent NetworkPanel,
    Screen.mode-agent SecurityPanel,
    Screen.mode-agent GitPanel,
    Screen.mode-agent GeoGlobe { background: rgba(0,0,0,0) !important; }
    """
    
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
    ]
    
    def on_mount(self):
        self.title = "NEXTRAL"
        self.sub_title = "v1.0 BETA"
        self.push_screen(TerminalScreen())

    def dispatch_tool(self, tool_id: str, target: str = ""):
        """Helper for GUI screens to launch tools"""
        from textual.widgets import RichLog
        # Find the terminal screen to run command processing
        for screen in self.screen_stack:
            if hasattr(screen, "_handle_internal"):
                cmd = f"{tool_id} {target}".strip()
                # Run as if the user typed it
                self.run_worker(screen._handle_internal(cmd, screen.query_one("#output", RichLog)))
                break

    def execute_silent(self, cmd: str):
        """Execute a command directly to shell without UI echoes if possible"""
        for screen in self.screen_stack:
            if hasattr(screen, "shell"):
                def _null(t): pass
                def _done(): pass
                self.run_worker(screen.shell.execute(cmd, _null, _done))
                break

if __name__ == "__main__":
    # Ignore SIGINT to prevent CTRL+C from closing the application
    # Textual's Binding("ctrl+c", ...) will still be triggered.
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    NextralApp().run()
