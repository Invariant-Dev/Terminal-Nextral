from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical, Horizontal
from textual.widgets import Header, Footer, Input, Button, RichLog, Static, DataTable
from textual.binding import Binding
import os
import sys
import subprocess
import asyncio
from pathlib import Path
import pyperclip

# Dependency Check & Auto-Install
DEPENDENCIES = {
    "PIL": "Pillow",
    "PyPDF2": "PyPDF2"
}

def check_dependencies():
    missing = []
    try:
        import PIL
    except ImportError:
        missing.append("Pillow")
    
    try:
        import PyPDF2
    except ImportError:
        missing.append("PyPDF2")
    
    return missing

class ExifRayScreen(Screen):
    """Exif-Ray Forensic Module: Metadata Extractor & Wiper"""

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Close"),
        Binding("a", "analyze_file", "Analyze"),
        Binding("w", "wipe_metadata", "Wipe Metadata"),
        Binding("c", "clear_log", "Clear"),
    ]

    CSS = """
    ExifRayScreen {
        background: #0f0f0f;
    }
    #exif_header {
        dock: top;
        height: auto;
        padding: 1;
        background: #1a1a1a;
        border-bottom: heavy #00ffcc;
    }
    #file_input {
        margin-bottom: 1;
        border: solid #00ffcc;
    }
    #exif_log {
        height: 1fr;
        background: #0f0f0f;
        border: round #333;
        padding: 1;
        scrollbar-color: #00ffcc;
    }
    .exif-btn {
        width: 20;
        background: #0088aa;
        color: white;
        margin-right: 1;
    }
    .exif-btn:hover {
        background: #00aabb;
    }
    #exif_table {
        margin-top: 1;
        height: 1fr;
        border: round #00ffcc;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="exif_header"):
            yield Static("[bold cyan]EXIF-RAY FORENSIC MODULE (Metadata Analyzer/Wiper)[/]")
            yield Input(placeholder="Enter file path (Image/PDF)...", id="file_input")
            
            with Horizontal():
                yield Button("ANALYZE", id="btn_analyze", classes="exif-btn", variant="primary")
                yield Button("WIPE METADATA", id="btn_wipe", classes="exif-btn", variant="error")
                
        yield RichLog(id="exif_log", markup=True)
        yield DataTable(id="exif_table", show_header=True, fixed_columns=1, zebra_stripes=True)
        yield Footer()

    def on_mount(self):
        missing = check_dependencies()
        if missing:
            self.log_message(f"[yellow]Missing dependencies: {', '.join(missing)}. Auto-installing...[/]")
            asyncio.create_task(self._install_deps(missing))
        
        table = self.query_one("#exif_table", DataTable)
        table.add_column("Key", width=30)
        table.add_column("Value")

    async def _install_deps(self, missing):
        log = self.query_one("#exif_log", RichLog)
        
        for pkg in missing:
            log.write(f"[cyan]Installing {pkg}...[/]")
            try:
                proc = await asyncio.create_subprocess_exec(
                    sys.executable, "-m", "pip", "install", pkg,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.communicate()
                if proc.returncode == 0:
                    log.write(f"[green]Successfully installed {pkg}.[/]")
                else:
                    log.write(f"[red]Failed to install {pkg}. Some features may not work.[/]")
            except Exception as e:
                log.write(f"[red]Error installing {pkg}: {e}[/]")
        
        log.write("[green]Dependencies checked. Ready.[/]")

    def log_message(self, message):
        self.query_one("#exif_log", RichLog).write(message)

    async def on_button_pressed(self, event: Button.Pressed):
        path = self.query_one("#file_input").value.strip()
        if not path:
            self.log_message("[red]Error: Please enter a file path.[/]")
            return
            
        if not os.path.exists(path):
            self.log_message(f"[red]Error: File not found: {path}[/]")
            return

        if event.button.id == "btn_analyze":
            self.analyze_file(path)
        elif event.button.id == "btn_wipe":
            self.wipe_metadata(path)

    def analyze_file(self, path):
        self.log_message(f"\n[bold yellow]Analyzing: {os.path.basename(path)}...[/]")
        table = self.query_one("#exif_table", DataTable)
        table.clear()
        
        ext = os.path.splitext(path)[1].lower()
        
        try:
            if ext in (".jpg", ".jpeg", ".png", ".tiff"):
                self._analyze_image(path)
            elif ext == ".pdf":
                self._analyze_pdf(path)
            else:
                self.log_message("[yellow]Unsupported file type for deep analysis. Basic stats only.[/]")
                stat = os.stat(path)
                table.add_row("Size", f"{stat.st_size} bytes")
                table.add_row("Created", str(stat.st_ctime))
                table.add_row("Modified", str(stat.st_mtime))
        except Exception as e:
            self.log_message(f"[red]Analysis Error: {e}[/]")

    def _analyze_image(self, path):
        from PIL import Image, ExifTags
        
        img = Image.open(path)
        exif_data = img._getexif()
        
        if not exif_data:
            self.log_message("[yellow]No EXIF data found in image.[/]")
            return

        table = self.query_one("#exif_table", DataTable)
        count = 0
        for tag_id, value in exif_data.items():
            tag = ExifTags.TAGS.get(tag_id, tag_id)
            # Truncate long binary data
            val_str = str(value)
            if len(val_str) > 100: val_str = val_str[:100] + "..."
            
            table.add_row(str(tag), val_str)
            count += 1
            
        self.log_message(f"[green]Found {count} metadata entries.[/]")

    def _analyze_pdf(self, path):
        import PyPDF2
        
        with open(path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            meta = reader.metadata
            
            if not meta:
                self.log_message("[yellow]No PDF metadata found.[/]")
                return

            table = self.query_one("#exif_table", DataTable)
            count = 0
            for key, value in meta.items():
                 # PDF keys look like '/Producer', strip slash
                key_clean = key.strip('/')
                table.add_row(key_clean, str(value))
                count += 1
                
            self.log_message(f"[green]Found {count} PDF metadata entries.[/]")

    def wipe_metadata(self, path):
        self.log_message(f"\n[bold red]WIPING METADATA: {os.path.basename(path)}...[/]")
        
        ext = os.path.splitext(path)[1].lower()
        new_path = f"{os.path.splitext(path)[0]}_clean{ext}"
        
        try:
            if ext in (".jpg", ".jpeg", ".png", ".tiff"):
                from PIL import Image
                img = Image.open(path)
                
                # Create a new image without data to strip everything including ICC profiles if possible
                data = list(img.getdata())
                clean_img = Image.new(img.mode, img.size)
                clean_img.putdata(data)
                
                clean_img.save(new_path)
                self.log_message(f"[bold green]✓ SUCCESS: Clean image saved to:[/]\n  {new_path}")
                try:
                    pyperclip.copy(os.path.abspath(new_path))
                except:
                    pass
                
            elif ext == ".pdf":
                import PyPDF2
                
                reader = PyPDF2.PdfReader(path)
                writer = PyPDF2.PdfWriter()
                
                for page in reader.pages:
                    writer.add_page(page)
                
                # Clear metadata
                writer.add_metadata({})
                
                with open(new_path, "wb") as f:
                    writer.write(f)
                    
                self.log_message(f"[bold green]✓ SUCCESS: Clean PDF saved to:[/]\n  {new_path}")
                try:
                    pyperclip.copy(os.path.abspath(new_path))
                except:
                    pass
            else:
                 self.log_message("[red]File type not supported for wiping.[/]")
                 
        except Exception as e:
            self.log_message(f"[red]Wipe Failed: {e}[/]")

