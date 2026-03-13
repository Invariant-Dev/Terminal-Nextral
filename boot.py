# boot.py - Nextral Terminal Boot Sequence
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.text import Text
from rich.panel import Panel
from rich.align import Align
from rich.table import Table
from rich.style import Style
import time
import random
import sys
import os
import getpass

console = Console()

def get_username():
    """Get username from config, env, or system"""
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "terminal_config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                import json
                cfg = json.load(f)
                return cfg.get('user', {}).get('username', 'USER')
        except:
            pass

    username = os.environ.get('NEXTRAL_USER')
    if not username:
        try:
            import getpass
            username = getpass.getuser().upper()
        except:
            username = "USER"
    return username.upper()

def glitch_text(text, duration=0.3):
    """Create a glitch effect with modern colors"""
    chars = "█▓▒░!@#$%^&*()_+-=[]{}|;:,.<>?~`"
    original = text
    for _ in range(int(duration * 10)):
        glitched = ''.join(random.choice(chars) if random.random() < 0.3 else c for c in original)
        console.print(f"\r[bold cyan]{glitched}[/bold cyan]", end="", style="cyan")
        time.sleep(0.03)
    console.print(f"\r[bold gradient(90;cyan,blue)]{original}[/]", style="gradient(90;cyan,blue)")

def matrix_rain(lines=5):
    """Matrix-style digital rain effect with modern aesthetic"""
    chars = "01"
    colors = ["#00ff41", "#00ff66", "#00ff88", "#39ff14", "#00ff41"]
    width = min(console.width, 100)
    
    for _ in range(lines):
        line = ''.join(random.choice(chars) for _ in range(width))
        color = random.choice(colors)
        console.print(f"[bold]{color}[/bold]{line}[/]")
        time.sleep(0.05)

def scan_animation():
    """Scanning animation effect with modern styling"""
    console.print("\n[bold cyan]► INITIATING DEEP SYSTEM SCAN[/bold cyan]\n")
    
    scan_items = [
        ("Kernel modules", "✓ OK", "green"),
        ("Device drivers", "✓ SECURE", "green"),
        ("Network interfaces", "✓ VERIFIED", "green"),
        ("Memory sectors", "✓ CLEAN", "green"),
        ("CPU cores", "✓ OPTIMAL", "green"),
        ("Storage volumes", "✓ MOUNTED", "green"),
        ("Security tokens", "✓ VALID", "green"),
        ("Encryption keys", "✓ ACTIVE", "green"),
    ]
    
    for item, status, color in scan_items:
        for i in range(3):
            dots = "●" * (i + 1) + "○" * (2 - i)
            console.print(f"\r  [dim cyan]Scanning {item}[/dim cyan] [cyan]{dots}[/cyan]", end="")
            time.sleep(0.08)
        console.print(f"\r  [dim]Scanning {item}...[/] [{color}]{status}[/{color}]")
        time.sleep(0.1)

def pulse_effect(text, color="cyan", pulses=3):
    """Pulsing text effect with modern gradient"""
    if not sys.stdout.isatty():
        console.print(f"[{color}]{text}[/]")
        return

    for i in range(pulses):
        for intensity in ["dim", "", "bold", "bright", "bold", "", "dim"]:
            style = f"{intensity} {color}".strip()
            console.print(f"\r[{style}]{text}[/]", end="")
            time.sleep(0.06)
    console.print()

def ascii_logo():
    """Display Nextral ASCII art with enhanced styling"""
    logo = """
[bold gradient(180;cyan,#00aaff,blue)][cyan]
 ███╗   ██╗███████╗██╗  ██╗████████╗██████╗  █████╗ ██╗     
 ████╗  ██║██╔════╝╚██╗██╔╝╚══██╔══╝██╔══██╗██╔══██╗██║     
 ██╔██╗ ██║█████╗   ╚███╔╝    ██║   ██████╔╝███████║██║     
 ██║╚██╗██║██╔══╝   ██╔██╗    ██║   ██╔══██╗██╔══██║██║     
 ██║ ╚████║███████╗██╔╝ ██╗   ██║   ██║  ██║██║  ██║███████╗
 ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝
[/gradient(180;cyan,#00aaff,blue)][bold cyan]━━━[/bold cyan] [bold white]NEXTRAL[/bold white] [bold cyan]━━━[/bold cyan]"""
    return logo

def typing_effect(text, style="cyan", delay=0.03):
    """Simulate typing effect with cursor"""
    for char in text:
        console.print(f"[{style}]{char}[/]", end="")
        time.sleep(delay)
    console.print()

def personalized_greeting(username):
    """Show personalized greeting with modern styling"""
    greetings = [
        f"Welcome back, [bold cyan]{username}[/]",
        f"Access granted, [bold cyan]{username}[/]",
        f"Hello, [bold cyan]{username}[/]",
        f"System ready for [bold cyan]{username}[/]",
        f"Good to see you, [bold cyan]{username}[/]",
    ]
    
    greeting = random.choice(greetings)
    
    console.print()
    console.print(Panel.fit(
        f"[bold gradient(90;green,cyan)]{greeting}[/]\n"
        f"[cyan]User Level: [bold white]ADMIN[/]  [cyan]Clearance: [bold green]UNRESTRICTED[/]",
        border_style="cyan",
        title="[bold white]▣ AUTHENTICATION ▣[/]",
        padding=(1, 2),
        style="on #0a0a15"
    ))
    time.sleep(1.5)

def boot_sequence():
    """Main boot sequence with enhanced effects"""
    console.clear()
    console.screen()
    
    # Matrix rain intro with modern colors
    colors = ["#00ff41", "#00ff66", "#39ff14", "#00ff88"]
    for c in colors:
        console.print(f"[bold]{c}[/bold]█" * min(console.width, 100), end="")
    console.print()
    matrix_rain(3)
    time.sleep(0.3)
    
    # Initial glitch with modern styling
    console.print("\n")
    glitch_text("▓▓▓ NEXTRAL TERMINAL ▓▓▓", 0.5)
    console.print()
    
    # Logo with pulse - centered and styled
    console.print(Align.center(ascii_logo()), justify="center")
    console.print()
    pulse_effect("▓▓▓ NEXTRAL TERMINAL ▓▓▓", "cyan", 2)
    console.print(Align.center("[dim]Neural Extension Terminal & Response Array Layer[/]"))
    console.print(Align.center("[italic dim]crafted with precision[/]\n"))
    time.sleep(1)
    
    # Get username for personalization
    username = get_username()
    
    # Typing effect for initialization
    typing_effect(">>> Establishing secure connection...", "yellow", 0.02)
    time.sleep(0.4)
    typing_effect(f">>> Detecting user profile: [cyan]{username}[/cyan]", "white", 0.02)
    time.sleep(0.5)
    
    # Security check with animation
    console.print(Panel.fit(
        "[bold yellow]⚠ SECURITY PROTOCOL INITIATED ⚠[/]",
        border_style="yellow",
        padding=(0, 1),
        style="on #1a1a00"
    ))
    time.sleep(0.8)
    
    # Biometric verification with more detail
    with Progress(
        SpinnerColumn("dots", style="cyan"),
        TextColumn("[progress.description]{task.description}", style="cyan"),
        BarColumn(bar_width=40, style="cyan", complete_style="green"),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%", style="green"),
        console=console,
    ) as progress:
        
        stages = [
            ("Scanning for permission level in system", "cyan"),
        ]
        
        for stage, color in stages:
            task = progress.add_task(f"[{color}]{stage}...[/]", total=100)
            for _ in range(100):
                progress.update(task, advance=1)
                time.sleep(random.uniform(0.008, 0.015))
            time.sleep(0.2)
    
    console.print("[bold green]✓[/] [green]Identity verified[/]")
    console.print("[bold green]✓[/] [green]Access granted[/]")
    time.sleep(0.5)
    
    # Personalized greeting
    personalized_greeting(username)
    
    # Scanning animation
    scan_animation()
    console.print()
    
    # System initialization with enhanced effects
    tasks = [
    ("Loading environment variables", "cyan", "▶"),
    ("Checking configuration files", "yellow", "▶"),
    ("Initializing logging system", "blue", "▶"),
    ("Connecting to database", "magenta", "▶"),
    ("Validating API keys", "red", "▶"),
    ("Establishing network connection", "blue", "▶"),
    ("Loading core modules", "cyan", "▶"),
    ("Initializing cache", "white", "▶"),
    ("Starting background services", "green", "▶"),
    ("Performing startup checks", "yellow", "▶"),
    (f"Loading user profile: {username}", "green", "▶"),
    ("System ready", "green", "▶"),
    ]
    
    console.print("[bold white on #1a1a2e]▓▓▓ SYSTEM INITIALIZATION SEQUENCE ▓▓▓[/]\n")
    
    with Progress(
        TextColumn("{task.fields[icon]} "),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=40, style="cyan", complete_style="green"),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        
        for task_name, color, icon in tasks:
            task = progress.add_task(f"[{color}]{task_name}[/]", total=100, icon=icon)
            for _ in range(100):
                progress.update(task, advance=1)
                time.sleep(random.uniform(0.003, 0.01))
            time.sleep(0.12)
    
    console.print()
    
    # System status table with modern styling
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_row("[bold cyan]Neural Network:[/]", "[bold green]● ONLINE[/]")
    table.add_row("[bold cyan]Security Status:[/]", "[bold green]● ACTIVE[/]")
    table.add_row("[bold cyan]Defense Protocol:[/]", "[bold green]● ENGAGED[/]")
    table.add_row("[bold cyan]Threat Level:[/]", "[bold green]● MINIMAL[/]")
    table.add_row("[bold cyan]Command Interface:[/]", "[bold green]● READY[/]")
    table.add_row(f"[bold cyan]Current User:[/]", f"[bold cyan]{username}[/]")
    
    console.print(Panel(
        Align.center(table),
        title="[bold green]⚡ ALL SYSTEMS OPERATIONAL ⚡[/]",
        border_style="cyan",
        padding=(1, 2),
        style="on #0a0a15"
    ))
    
    time.sleep(1.5)
    
    # Loading message
    console.print("\n[bold white]Launching command interface...[/]")
    
    # Animated countdown with modern style
    for i in range(3, 0, -1):
        console.print(f"[bold gradient(90;cyan,blue){i}[/]", end="")
        time.sleep(0.3)
        console.print("[dim].[/]", end="")
        time.sleep(0.3)
    
    console.print("\n")
    
    # Final ready message
    pulse_effect(f"▓▓▓ NEXTRAL READY FOR {username.upper()} ▓▓▓", "green", 2)
    console.print()
    time.sleep(0.5)

if __name__ == "__main__":
    try:
        boot_sequence()
    except KeyboardInterrupt:
        console.print("\n[red]Boot sequence interrupted[/]")
        sys.exit(0)
