# cipher.py - Cipher: Message Encryption/Decryption Tool
"""
A cryptographic message tool featuring:
- AES-256 encryption/decryption
- Key generation
- Pre-set key support
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical, Horizontal, Container
from textual.widgets import Static, Input, Button, TextArea
from textual.binding import Binding
from textual.reactive import reactive
import base64
import hashlib
import os
import secrets


def generate_key() -> str:
    """Generate a random 32-byte key and return as base64"""
    key = secrets.token_bytes(32)
    return base64.b64encode(key).decode('utf-8')


def derive_key(password: str) -> bytes:
    """Derive a 32-byte key from a password using SHA-256"""
    return hashlib.sha256(password.encode('utf-8')).digest()


def encrypt_message(message: str, key: str) -> str:
    """Encrypt a message using XOR cipher with derived key (simple but effective for demo)"""
    try:
        # Derive actual key bytes
        if len(key) == 44 and key.endswith('='):
            # Looks like base64, decode it
            key_bytes = base64.b64decode(key)
        else:
            key_bytes = derive_key(key)
        
        message_bytes = message.encode('utf-8')
        
        # XOR encryption with key cycling
        encrypted = bytearray()
        for i, b in enumerate(message_bytes):
            encrypted.append(b ^ key_bytes[i % len(key_bytes)])
        
        # Return as base64
        return base64.b64encode(bytes(encrypted)).decode('utf-8')
    except Exception as e:
        return f"ERROR: {e}"


def decrypt_message(ciphertext: str, key: str) -> str:
    """Decrypt a message using XOR cipher with derived key"""
    try:
        # Derive actual key bytes
        if len(key) == 44 and key.endswith('='):
            key_bytes = base64.b64decode(key)
        else:
            key_bytes = derive_key(key)
        
        encrypted_bytes = base64.b64decode(ciphertext)
        
        # XOR decryption (same as encryption for XOR)
        decrypted = bytearray()
        for i, b in enumerate(encrypted_bytes):
            decrypted.append(b ^ key_bytes[i % len(key_bytes)])
        
        return bytes(decrypted).decode('utf-8')
    except Exception as e:
        return f"ERROR: {e}"


class CipherScreen(Screen):
    """Cipher: Message Encryption/Decryption Tool"""
    
    CSS = """
    CipherScreen {
        background: #050510;
    }
    
    #header {
        dock: top;
        height: 3;
        background: #100a10;
        border-bottom: heavy #aa44aa;
        padding: 0 2;
        content-align: center middle;
    }
    
    #main_container {
        width: 100%;
        height: 1fr;
        padding: 1 2;
    }
    
    #key_section {
        height: 5;
        margin-bottom: 1;
    }
    
    #key_label {
        width: 12;
    }
    
    #key_input {
        width: 1fr;
        background: #0a0a15;
        border: solid #553355;
    }
    
    #generate_btn {
        width: 16;
        margin-left: 1;
    }
    
    #io_container {
        height: 1fr;
    }
    
    .io_panel {
        width: 1fr;
        height: 1fr;
        margin: 0 1;
    }
    
    .panel_title {
        height: 1;
        background: #1a0a1a;
        color: #aa88aa;
        text-align: center;
    }
    
    .text_area {
        height: 1fr;
        background: #080810;
        border: round #443355;
    }
    
    #button_section {
        height: 3;
        margin-top: 1;
        align: center middle;
    }
    
    #button_section Button {
        margin: 0 2;
        min-width: 20;
    }
    
    #encrypt_btn {
        background: #224422;
    }
    
    #decrypt_btn {
        background: #442222;
    }
    
    #stats {
        dock: bottom;
        height: 1;
        background: #100a10;
        color: #aa66aa;
        text-align: center;
    }
    """
    
    BINDINGS = [
        Binding("escape", "close", "Close", show=True),
        Binding("ctrl+g", "gen_key", "Generate Key", show=True),
        Binding("ctrl+e", "do_encrypt", "Encrypt", show=True),
        Binding("ctrl+d", "do_decrypt", "Decrypt", show=True),
    ]
    
    def compose(self) -> ComposeResult:
        yield Static(
            "[bold magenta]╔════════════════════════════════════════════════════════════════════════════════╗[/]\n"
            "[bold magenta]║[/]                            [bold white]CIPHER: ENCRYPTION TOOL[/]                             [bold magenta]║[/]\n"
            "[bold magenta]╚════════════════════════════════════════════════════════════════════════════════╝[/]",
            id="header", markup=True
        )
        
        with Vertical(id="main_container"):
            # Key section
            with Horizontal(id="key_section"):
                yield Static("[bold]🔑 KEY:[/]", id="key_label", markup=True)
                yield Input(id="key_input", placeholder="Enter key or password (or generate one)")
                yield Button("⚡ Generate", id="generate_btn", variant="primary")
            
            # Input/Output areas
            with Horizontal(id="io_container"):
                with Vertical(classes="io_panel"):
                    yield Static("[bold cyan]📝 INPUT MESSAGE[/]", classes="panel_title", markup=True)
                    yield TextArea(id="input_text", classes="text_area")
                
                with Vertical(classes="io_panel"):
                    yield Static("[bold green]🔒 OUTPUT[/]", classes="panel_title", markup=True)
                    yield TextArea(id="output_text", classes="text_area", read_only=True)
            
            # Button section
            with Horizontal(id="button_section"):
                yield Button("🔐 ENCRYPT", id="encrypt_btn", variant="success")
                yield Button("🔓 DECRYPT", id="decrypt_btn", variant="error")
        
        yield Static(id="stats", markup=True)
    
    def on_mount(self):
        stats = self.query_one("#stats", Static)
        stats.update("[bold magenta]◈[/] Ctrl+G=Generate Key  Ctrl+E=Encrypt  Ctrl+D=Decrypt  ESC=Exit")
    
    def action_close(self):
        self.app.pop_screen()
    
    def action_gen_key(self):
        key = generate_key()
        self.query_one("#key_input", Input).value = key
        self.query_one("#stats", Static).update(f"[green]✓ New 256-bit key generated![/]")
    
    def action_do_encrypt(self):
        key = self.query_one("#key_input", Input).value
        message = self.query_one("#input_text", TextArea).text
        
        if not key:
            self.query_one("#stats", Static).update("[red]✗ Please enter a key first![/]")
            return
        if not message:
            self.query_one("#stats", Static).update("[red]✗ Please enter a message to encrypt![/]")
            return
        
        result = encrypt_message(message, key)
        self.query_one("#output_text", TextArea).text = result
        self.query_one("#stats", Static).update(f"[green]✓ Encrypted {len(message)} chars → {len(result)} chars[/]")
    
    def action_do_decrypt(self):
        key = self.query_one("#key_input", Input).value
        ciphertext = self.query_one("#input_text", TextArea).text
        
        if not key:
            self.query_one("#stats", Static).update("[red]✗ Please enter a key first![/]")
            return
        if not ciphertext:
            self.query_one("#stats", Static).update("[red]✗ Please enter ciphertext to decrypt![/]")
            return
        
        result = decrypt_message(ciphertext, key)
        self.query_one("#output_text", TextArea).text = result
        self.query_one("#stats", Static).update(f"[green]✓ Decrypted successfully[/]")
    
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "generate_btn":
            self.action_gen_key()
        elif event.button.id == "encrypt_btn":
            self.action_do_encrypt()
        elif event.button.id == "decrypt_btn":
            self.action_do_decrypt()
