# vault_x.py - Vault-X: Encrypted Local Storage

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical, Horizontal, Container
from textual.widgets import Static, Input, Button, DirectoryTree, ProgressBar
from textual.binding import Binding
from textual.reactive import reactive
from textual.message import Message
import os
import hashlib
import base64
import asyncio
from pathlib import Path


def derive_key_bytes(password: str) -> bytes:
    """Derive a 32-byte key from password using SHA-256"""
    return hashlib.sha256(password.encode('utf-8')).digest()


def encrypt_file(file_path: str, password: str, progress_callback=None) -> tuple:
    """Encrypt a file and save as .enc"""
    chunk_size = 64 * 1024  # 64KB chunks
    try:
        key = derive_key_bytes(password)
        enc_path = file_path + ".enc"
        file_size = os.path.getsize(file_path)
        bytes_processed = 0

        with open(file_path, 'rb') as f_in, open(enc_path, 'wb') as f_out:
            while True:
                chunk = f_in.read(chunk_size)
                if not chunk:
                    break
                
                encrypted_chunk = bytearray()
                for i, b in enumerate(chunk):
                    key_index = (bytes_processed + i) % len(key)
                    encrypted_chunk.append(b ^ key[key_index])
                
                f_out.write(bytes(encrypted_chunk))
                bytes_processed += len(chunk)

                if progress_callback:
                    # Call the callback with progress percentage
                    progress_callback(bytes_processed / file_size)

        return True, enc_path
    except Exception as e:
        return False, str(e)


def decrypt_file(file_path: str, password: str, progress_callback=None) -> tuple:
    chunk_size = 64 * 1024  # 64KB chunks
    try:
        key = derive_key_bytes(password)
        dec_path = file_path[:-4] if file_path.endswith('.enc') else file_path + ".dec"
        file_size = os.path.getsize(file_path)
        bytes_processed = 0

        with open(file_path, 'rb') as f_in, open(dec_path, 'wb') as f_out:
            while True:
                chunk = f_in.read(chunk_size)
                if not chunk:
                    break
                
                decrypted_chunk = bytearray()
                for i, b in enumerate(chunk):
                    key_index = (bytes_processed + i) % len(key)
                    decrypted_chunk.append(b ^ key[key_index])
                
                f_out.write(bytes(decrypted_chunk))
                bytes_processed += len(chunk)

                if progress_callback:
                    progress_callback(bytes_processed / file_size)

        return True, dec_path
    except Exception as e:
        return False, str(e)


class FilePanel(Static):
    
    selected_file = reactive("")
    
    def watch_selected_file(self, path: str):
        self._render_info()
    
    def _render_info(self):
        if not self.selected_file or not os.path.isfile(self.selected_file):
            self.update("[dim]No file selected[/]")
            return
        
        try:
            stat = os.stat(self.selected_file)
            size = stat.st_size
            name = os.path.basename(self.selected_file)
            is_encrypted = name.endswith('.enc')
            
            size_str = f"{size:,} bytes"
            if size > 1024 * 1024:
                size_str = f"{size / (1024*1024):.2f} MB"
            elif size > 1024:
                size_str = f"{size / 1024:.2f} KB"
            
            status_icon = "🔒" if is_encrypted else "📄"
            status_text = "[green]ENCRYPTED[/]" if is_encrypted else "[yellow]PLAINTEXT[/]"
            
            content = f"""
[bold white]─── SELECTED FILE ───[/]

{status_icon} [bold]{name[:35]}[/]

  [cyan]◉[/] Size:    [white]{size_str}[/]
  [cyan]◉[/] Status:  {status_text}
  [cyan]◉[/] Path:    [dim]{self.selected_file[:40]}...[/]
"""
            self.update(content)
        except:
            self.update("[red]Error reading file[/]")


class VaultScreen(Screen):
    """Vault-X: Encrypted Local Storage"""
    
    CSS = """
    VaultScreen {
        background: #080510;
    }
    
    #header {
        dock: top;
        height: 3;
        background: #100815;
        border-bottom: heavy #aa4488;
        padding: 0 2;
        content-align: center middle;
    }
    
    #main_container {
        width: 100%;
        height: 1fr;
    }
    
    #left_panel {
        width: 1fr;
        height: 100%;
        padding: 1;
    }
    
    #file_tree {
        height: 1fr;
        background: #0a0810;
        border: round #553355;
    }
    
    #right_panel {
        width: 45;
        height: 100%;
        background: #0a0810;
        border-left: heavy #553355;
        padding: 1;
    }
    
    #file_info {
        height: 12;
        background: #0c0a12;
        border: round #443355;
        padding: 1;
    }
    
    #password_section {
        height: 4;
        margin-top: 1;
    }
    
    #password_input {
        width: 100%;
        background: #0a0810;
        border: solid #553355;
    }
    
    #button_section {
        height: auto;
        margin-top: 1;
    }
    
    #button_section Button {
        width: 100%;
        margin-bottom: 1;
    }
    
    #encrypt_btn {
        background: #224422;
    }
    
    #decrypt_btn {
        background: #442222;
    }
    
    #progress_section {
        height: 3;
        margin-top: 1;
    }
    
    #progress_bar {
        width: 100%;
    }
    
    #status {
        height: 2;
        margin-top: 1;
    }
    
    #stats {
        dock: bottom;
        height: 1;
        background: #100815;
        color: #aa4488;
        text-align: center;
    }
    """
    
    BINDINGS = [
        Binding("escape", "close", "Close", show=True),
        Binding("ctrl+e", "do_encrypt", "Encrypt", show=True),
        Binding("ctrl+d", "do_decrypt", "Decrypt", show=True),
    ]
    
    selected_file = reactive("")
    
    class ProgressUpdate(Message):
        """Message to update the progress bar from a worker."""
        def __init__(self, progress: float) -> None:
            self.progress = progress
            super().__init__()

    def compose(self) -> ComposeResult:
        yield Static(
            "[bold magenta]╔════════════════════════════════════════════════════════════════════════════════╗[/]\n"
            "[bold magenta]║[/]                          [bold white]VAULT-X: FILE ENCRYPTION[/]                          [bold magenta]║[/]\n"
            "[bold magenta]╚════════════════════════════════════════════════════════════════════════════════╝[/]",
            id="header", markup=True
        )
        
        with Horizontal(id="main_container"):
            with Vertical(id="left_panel"):
                yield DirectoryTree(os.getcwd(), id="file_tree")
            
            with Vertical(id="right_panel"):
                yield FilePanel(id="file_info")
                
                with Vertical(id="password_section"):
                    yield Static("[bold]🔑 Password:[/]", markup=True)
                    yield Input(id="password_input", placeholder="Enter encryption password", password=True)
                
                with Vertical(id="button_section"):
                    yield Button("🔐 ENCRYPT FILE", id="encrypt_btn", variant="success")
                    yield Button("🔓 DECRYPT FILE", id="decrypt_btn", variant="error")
                
                with Vertical(id="progress_section"):
                    yield ProgressBar(id="progress_bar", show_eta=False)
                
                yield Static(id="status", markup=True)
        
        yield Static(id="stats", markup=True)
    
    def on_mount(self):
        stats = self.query_one("#stats", Static)
        stats.update("[bold magenta]◈[/] Select file → Enter password → Encrypt/Decrypt  ESC=Exit")
    
    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected):
        self.selected_file = str(event.path)
        self.query_one("#file_info", FilePanel).selected_file = self.selected_file
    
    def on_progress_update(self, message: ProgressUpdate) -> None:
        """Handle progress update messages from the worker."""
        self.query_one("#progress_bar", ProgressBar).update(progress=message.progress * 100)

    def _update_status(self, text: str) -> None:
        """Helper to update status text."""
        self.query_one("#status", Static).update(text)

    def action_close(self):
        self.app.pop_screen()

    def do_encrypt_finished(self, result: tuple) -> None:
        """Callback for when encryption worker is done."""
        success, result_path = result
        self.query_one("#progress_bar", ProgressBar).update(progress=100)
        if success:
            self._update_status(f"[green]✓ Encrypted: {os.path.basename(result_path)}[/]")
            self.query_one("#file_tree", DirectoryTree).reload()
        else:
            self._update_status(f"[red]✗ Error: {result_path}[/]")

    def action_do_encrypt(self):
        if not self.selected_file:
            self._update_status("[red]✗ Select a file first![/]")
            return
        
        password = self.query_one("#password_input", Input).value
        if not password:
            self._update_status("[red]✗ Enter a password![/]")
            return
        
        self._update_status("[yellow]◈ Encrypting...[/]")
        self.query_one("#progress_bar", ProgressBar).update(progress=0)

        def progress_callback(progress_value: float) -> None:
            self.post_message(self.ProgressUpdate(progress_value))

        self.run_worker(
            lambda: encrypt_file(self.selected_file, password, progress_callback),
            self.do_encrypt_finished,
            exclusive=True
        )

    def do_decrypt_finished(self, result: tuple) -> None:
        """Callback for when decryption worker is done."""
        success, result_path = result
        self.query_one("#progress_bar", ProgressBar).update(progress=100)
        if success:
            self._update_status(f"[green]✓ Decrypted: {os.path.basename(result_path)}[/]")
            self.query_one("#file_tree", DirectoryTree).reload()
        else:
            self._update_status(f"[red]✗ Error: {result_path}[/]")

    def action_do_decrypt(self):
        if not self.selected_file:
            self._update_status("[red]✗ Select a file first![/]")
            return
        
        if not self.selected_file.endswith('.enc'):
            self._update_status("[yellow]⚠ Select a .enc file to decrypt[/]")
            return
        
        password = self.query_one("#password_input", Input).value
        if not password:
            self._update_status("[red]✗ Enter a password![/]")
            return
        
        self._update_status("[yellow]◈ Decrypting...[/]")
        self.query_one("#progress_bar", ProgressBar).update(progress=0)

        def progress_callback(progress_value: float) -> None:
            self.post_message(self.ProgressUpdate(progress_value))

        self.run_worker(
            lambda: decrypt_file(self.selected_file, password, progress_callback),
            self.do_decrypt_finished,
            exclusive=True
        )
    
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "encrypt_btn":
            self.action_do_encrypt()
        elif event.button.id == "decrypt_btn":
            self.action_do_decrypt()
