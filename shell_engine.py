import asyncio
import os
import signal
import subprocess
import sys
import json
from datetime import datetime

class ShellEngine:
    def __init__(self, loop=None):
        self.loop = loop or asyncio.get_event_loop()
        self.process = None
        self.cwd = os.getcwd()
        self.history = []
        self.history_index = 0
        self.is_running = False
        self.delimiter = "NEXTRAL_EOF"
        self.username = "USER"
        
        # Callbacks for current command
        self._current_output_cb = None
        self._current_done_cb = None
        self._reader_task = None
        
        self.history_limit = 1000
        
    async def start(self):
        """Start the PowerShell/Bash subprocess"""
        env = os.environ.copy()
        is_windows = sys.platform == 'win32'
        shell_cmd = "powershell.exe" if is_windows else "/bin/bash"
        shell_args = ["-NoLogo", "-NoExit"] if is_windows else ["--login", "-i"]
        
        try:
            # We use -NoExit or --login to keep shell alive
            self.process = await asyncio.create_subprocess_exec(
                shell_cmd, 
                *shell_args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                creationflags=subprocess.CREATE_NO_WINDOW if is_windows else 0
            )
            self.is_running = True
            
            # Start persistent reader
            self._reader_task = asyncio.create_task(self._background_reader())
            
            # Initialize
            if is_windows:
                await self.run_hidden_command('[Console]::OutputEncoding = [System.Text.Encoding]::UTF8')
            else:
                await self.run_hidden_command("export PS1=''")
            return True
        except Exception as e:
            print(f"Failed to start shell: {e}")
            return False

    async def stop(self):
        """Clean shutdown"""
        if self.process:
            try:
                self.process.kill()
            except:
                pass
        if self._reader_task:
            self._reader_task.cancel()

    async def run_hidden_command(self, cmd):
        """Run internal setup command"""
        if not self.process: return
        try:
            input_str = f"{cmd}\n"
            self.process.stdin.write(input_str.encode('utf-8'))
            await self.process.stdin.drain()
        except:
            pass

    async def run_command(self, cmd, output_callback, done_callback):
        """Run user command"""
        if not self.process or self.process.returncode is not None:
            output_callback("[red]Shell died. Restarting...[/]\n")
            if not await self.start():
                output_callback("[bold red]FATAL: Restart failed.[/]\n")
                done_callback()
                return

        # Register callbacks
        self._current_output_cb = output_callback
        self._current_done_cb = done_callback

        # Security Check: Prevent killing the shell itself
        pid = str(self.process.pid) if self.process else ""
        cmd_lower = cmd.lower()
        kill_keywords = ["kill", "stop-process", "taskkill"]
        
        if pid and pid in cmd and any(k in cmd_lower for k in kill_keywords):
            output_callback(f"\n[bold red]⚠ CRITICAL: TERMINATION PREVENTED[/]\n")
            output_callback(f"[yellow]You are attempting to kill the active shell process (PID {pid}).[/]\n")
            output_callback("[cyan]To safely close Nextral, please use the [bold white]exit[/] or [bold white]quit[/] command.[/]\n\n")
            if done_callback: done_callback()
            return

        # Add to history
        if cmd.strip():
            self.history.append(cmd)
            self.history = self.history[-self.history_limit:]
            self.history_index = len(self.history)

        # Send command with delimiter trailer
        # We output CWD *before* the delimiter so that the UI can update the prompt with the new CWD immediately on completion
        if sys.platform == 'win32':
            payload = f"{cmd}\n(Get-Location).Path | Write-Host -NoNewline; Write-Host '<<CWD_END>>'\nWrite-Host '{self.delimiter}'\n"
        else:
            payload = f"{cmd}\npwd | tr -d '\\n'; echo '<<CWD_END>>'\necho '{self.delimiter}'\n"
        
        try:
            self.process.stdin.write(payload.encode('utf-8'))
            await self.process.stdin.drain()
        except Exception as e:
            output_callback(f"[red]Write error: {e}[/]\n")
            if done_callback: done_callback()

    async def _background_reader(self):
        """Persistent reader loop"""
        if not self.process: return
        
        while True:
            try:
                line = await self.process.stdout.readline()
                if not line:
                    break # EOF
                
                decoded = line.decode('utf-8', errors='replace')
                
                # Check for CWD update
                if "<<CWD_END>>" in decoded:
                    path = decoded.replace("<<CWD_END>>", "").strip()
                    # Keep path only if it's a valid directory to avoid garbage
                    if path and os.path.isdir(path):
                        self.cwd = path
                    # We do NOT return or continue here, because the delimiter might follow on next line (or same line?)
                    # Actually, we should hide this line from output_cb
                    continue

                # Check for delimiter
                if self.delimiter in decoded:
                    if self._current_done_cb:
                        self._current_done_cb()
                        self._current_done_cb = None
                        self._current_output_cb = None
                    continue 
                
                # Normal Output
                if self._current_output_cb:
                    self._current_output_cb(decoded)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log error?
                print(f"Reader error: {e}")
                await asyncio.sleep(0.1)

    def send_interrupt(self):
        """Try to interrupt"""
        # On Windows, best we can do for invisible shell is restart if stuck,
        # or rely on powershell's own behavior if we render it? 
        # But we are invisible.
        # Sending Break event might work if in a job.
        # For now, simplistic approach:
        asyncio.create_task(self.restart())

    async def restart(self):
        await self.stop()
        await self.start()

    def get_history_previous(self, current):
        if not self.history: return None
        if self.history_index > 0:
            self.history_index -= 1
            return self.history[self.history_index]
        return self.history[0] if self.history else None

    def get_history_next(self, current):
        if not self.history: return None
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            return self.history[self.history_index]
        self.history_index = len(self.history)
        return ""

    def autocomplete(self, partial):
        # Basic file completion
        try:
            search = partial.strip()
            if not search: return None
            
            # Directory to look in
            dirname = os.path.dirname(search)
            basename = os.path.basename(search)
            
            search_dir = os.path.join(self.cwd, dirname) if dirname else self.cwd
            
            if not os.path.exists(search_dir): return None
            
            for item in os.listdir(search_dir):
                if item.lower().startswith(basename.lower()):
                    # Return full relative path
                    if dirname:
                        return os.path.join(dirname, item)
                    return item
        except:
            pass
        return None
