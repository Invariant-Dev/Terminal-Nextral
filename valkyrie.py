from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical, Horizontal
from textual.widgets import Header, Footer, Input, Button, RichLog, Static, RadioButton, RadioSet, ProgressBar
from textual.binding import Binding
import hashlib
import asyncio
import itertools
import string
import os
import pyperclip

class ValkyrieScreen(Screen):
    """Valkyrie Hash Cracker & Identifier"""

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Close"),
        Binding("c", "crack_hash", "Crack"),
        Binding("i", "identify_hash", "Identify"),
        Binding("l", "clear_log", "Clear Log"),
    ]

    CSS = """
    ValkyrieScreen {
        background: #0d1117;
    }
    #valkyrie_header {
        dock: top;
        height: auto;
        padding: 1;
        background: #161b22;
        border-bottom: heavy #8b949e;
    }
    #hash_input {
        margin-bottom: 1;
        border: solid #58a6ff;
    }
    #wordlist_input {
        margin-bottom: 1;
        border: solid #238636;
    }
    #valkyrie_log {
        height: 1fr;
        background: #0d1117;
        border: round #30363d;
        padding: 1;
        scrollbar-color: #58a6ff;
    }
    .valkyrie-btn {
        width: 20;
        background: #238636;
        color: white;
        margin-right: 1;
    }
    .valkyrie-btn:hover {
        background: #2ea043;
    }
    #mode_select {
        height: auto;
        margin-bottom: 1;
        background: #161b22;
        padding: 1;
        border: round #30363d;
    }
    """

    COMMON_PASSWORDS = [
        "123456", "password", "12345678", "qwerty", "123456789", "12345", "111111", 
        "1234567", "dragon", "admin", "welcome", "login", "master", "000000", "123123"
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="valkyrie_header"):
            yield Static("[bold cyan]VALKYRIE HASH CRACKER (MD5 / SHA1 / SHA256)[/]")
            yield Input(placeholder="Enter Target Hash...", id="hash_input")
            
            with Horizontal(id="mode_select"):
                with RadioSet(id="crack_mode"):
                    yield RadioButton("Dictionary (Built-in)", value=True, id="mode_builtin")
                    yield RadioButton("Dictionary (File)", id="mode_file")
                    yield RadioButton("Brute Force (Numeric 4-6)", id="mode_brute")
            
            yield Input(placeholder="Wordlist Path (Optional for built-in/brute force)", id="wordlist_input", disabled=True)
            
            with Horizontal():
                yield Button("IDENTIFY", id="btn_identify", classes="valkyrie-btn", variant="primary")
                yield Button("CRACK", id="btn_crack", classes="valkyrie-btn", variant="error")
                
        yield RichLog(id="valkyrie_log", markup=True)
        yield ProgressBar(id="progress", show_eta=True, total=100)
        yield Footer()

    def on_mount(self):
        self.query_one("#wordlist_input").display = False # Start hidden

    def on_radio_set_changed(self, event: RadioSet.Changed):
        w_input = self.query_one("#wordlist_input")
        if event.pressed.id == "mode_file":
            w_input.disabled = False
            w_input.display = True
            w_input.focus()
        else:
            w_input.disabled = True
            w_input.display = False

    async def on_button_pressed(self, event: Button.Pressed):
        target_hash = self.query_one("#hash_input").value.strip()
        
        if not target_hash:
            self.log_message("[red]Error: Please enter a hash string.[/]")
            return

        if event.button.id == "btn_identify":
            self.identify_hash(target_hash)
        elif event.button.id == "btn_crack":
            self.action_crack_hash()

    def log_message(self, message):
        log = self.query_one("#valkyrie_log", RichLog)
        log.write(message)

    def identify_hash(self, hash_str: str):
        length = len(hash_str)
        self.log_message(f"\n[bold yellow]Analyzing Hash: {hash_str[:8]}... ({length} chars)[/]")
        
        candidates = []
        if length == 32:
            candidates.append("MD5")
            candidates.append("NTLM")
        elif length == 40:
            candidates.append("SHA-1")
            candidates.append("RIPEMD-160")
        elif length == 64:
            candidates.append("SHA-256")
        elif length == 96:
            candidates.append("SHA-384")
        elif length == 128:
            candidates.append("SHA-512")
            
        if candidates:
            self.log_message(f"[green]Likely Algorithms: {', '.join(candidates)}[/]")
            return candidates
        else:
            self.log_message("[red]Unknown Hash Format (Check length). Only hex digests supported.[/]")
            return []

    def action_crack_hash(self):
        target_hash = self.query_one("#hash_input").value.strip()
        if not target_hash:
            return
            
        asyncio.create_task(self._run_crack(target_hash))

    async def _run_crack(self, target_hash):
        log = self.query_one("#valkyrie_log", RichLog)
        progress = self.query_one("#progress", ProgressBar)
        
        candidates = self.identify_hash(target_hash)
        if not candidates:
            return

        algo_map = {
            "MD5": hashlib.md5,
            "SHA-1": hashlib.sha1,
            "SHA-256": hashlib.sha256
        }
        
        # Determine likely algorithm object
        hash_func = None
        algo_name = "Unknown"
        
        # Simple heuristic: prioritize MD5 -> SHA1 -> SHA256
        if "MD5" in candidates:
            hash_func = hashlib.md5
            algo_name = "MD5"
        elif "SHA-1" in candidates:
            hash_func = hashlib.sha1
            algo_name = "SHA-1"
        elif "SHA-256" in candidates:
            hash_func = hashlib.sha256
            algo_name = "SHA-256"
        else:
            log.write("[yellow]Warning: defaulting to MD5 check logic, might fail.[/]")
            hash_func = hashlib.md5
            algo_name = "MD5 (Assumed)"

        mode = self.query_one("#crack_mode").pressed_button.id
        log.write(f"[bold cyan]Starting Attack using {algo_name}... Mode: {mode}[/]")
        
        found = False
        password = None
        
        if mode == "mode_builtin":
            total = len(self.COMMON_PASSWORDS)
            progress.update(total=total, progress=0)
            
            for i, word in enumerate(self.COMMON_PASSWORDS):
                if i % 5 == 0: await asyncio.sleep(0.01) # UI responsiveness
                
                h = hash_func(word.encode()).hexdigest()
                if h == target_hash.lower():
                    found = True
                    password = word
                    break
                progress.advance(1)
                
        elif mode == "mode_file":
            path = self.query_one("#wordlist_input").value.strip()
            if not os.path.exists(path):
                log.write(f"[red]Error: Wordlist file not found: {path}[/]")
                return
            
            # Count lines for progress bar (optional, might be slow for huge files)
            # Just do an estimate or indeterminate
            progress.update(total=None) 
            
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    count = 0
                    for line in f:
                        count += 1
                        if count % 1000 == 0: 
                            await asyncio.sleep(0.001)
                            log.write(f"[dim]Checked {count} words...[/]")
                        
                        word = line.strip()
                        if not word: continue
                        
                        h = hash_func(word.encode()).hexdigest()
                        if h == target_hash.lower():
                            found = True
                            password = word
                            break
            except Exception as e:
                log.write(f"[red]File Error: {e}[/]")

        elif mode == "mode_brute":
            # Numeric brute force 4-8 digits
            log.write("[yellow]Starting Numeric Brute Force (4-8 digits)...[/]")
            chars = string.digits
            
            # Estimate total steps? It's huge. Just update non-deterministically
            progress.update(total=None)
            
            count = 0
            for length in range(4, 9): # 4 to 8
                log.write(f"[cyan]Checking length {length}...[/]")
                for p in itertools.product(chars, repeat=length):
                    word = "".join(p)
                    count += 1
                    
                    if count % 5000 == 0: 
                        await asyncio.sleep(0.001)
                    
                    h = hash_func(word.encode()).hexdigest()
                    if h == target_hash.lower():
                        found = True
                        password = word
                        break
                if found: break
                
        if found:
            log.write("\n[bold green]★ PASSWORD CRACKED SUCCESSFULLY! ★[/]")
            log.write(f"[bold white]Hash:[/] {target_hash}")
            log.write(f"[bold white]Password:[/] [bold green on black]{password}[/]")
            log.write(f"[dim]Algorithm: {algo_name}[/]")
            try:
                pyperclip.copy(password)
                log.write("[green]✓ Password auto-copied to clipboard.[/]")
            except:
                pass
            progress.update(progress=100)
        else:
            log.write("\n[red]Cracking Failed. Password not found in wordlist/range.[/]")
            progress.update(progress=0)
