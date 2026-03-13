# geo_globe.py - Geo-Earth: Rotating ASCII Globe with IP Geolocation
"""
A spinning ASCII globe that shows your location based on IP.
"""

from textual.widgets import Static
from textual.reactive import reactive
import asyncio
import math

# ASCII globe frames - 8 frame rotation
# Each frame is a different rotation angle of the Earth
GLOBE_FRAMES = [
    # Frame 0 - Americas centered
    """
      .--.
    .'    '.
   /  .--.  \\
  |  /    \\  |
  | |  ●   | |
  |  \\    /  |
   \\  '--'  /
    '.    .'
      '--'
""",
    # Frame 1
    """
      .--.
    .'    '.
   /   .--.\\
  |   /    |\\
  |  |  ●  ||
  |   \\   / |
   \\  '--' /
    '.    .'
      '--'
""",
    # Frame 2 - Atlantic
    """
      .--.
    .'    '.
   /    .--\\
  |    /   |\\
  |   | ●  ||
  |    \\   /|
   \\   '--'/
    '.    .'
      '--'
""",
    # Frame 3
    """
      .--.
    .'    '.
   /     .-\\
  |    .-  |\\
  |   | ●   |
  |    '-  /|
   \\    '-'/
    '.    .'
      '--'
""",
    # Frame 4 - Europe/Africa
    """
      .--.
    .'    '.
   /--     /
  |\\   .  | |
  || ●  | | |
  |/   '  | |
   \\--   /
    '.    .'
      '--'
""",
    # Frame 5
    """
      .--.
    .'    '.
   /--.    /
  |\\   .  | |
  ||  ● | | |
  |/   '| | |
   \\--' /
    '.    .'
      '--'
""",
    # Frame 6 - Asia
    """
      .--.
    .'    '.
   /.--.   /
  ||    . ||
  || ●   |||
  ||    ' ||
   \\.--' /
    '.    .'
      '--'
""",
    # Frame 7 - Pacific
    """
      .--.
    .'    '.
   / .--.  \\
  ||/    \\ |
  ||  ●   ||
  ||\\    / |
   \\ '--'  /
    '.    .'
      '--'
""",
]

# Simplified globe with location marker
GLOBE_TEMPLATE = """
    [cyan]╭─────────────╮[/]
    [cyan]│[/] [dim].--.[/]       [cyan]│[/]
    [cyan]│[/][dim].'    '.[/]    [cyan]│[/]
    [cyan]│[/][dim]/  .--.  \\[/]   [cyan]│[/]
    [cyan]│[/][dim]| /    \\ |[/]   [cyan]│[/]
    [cyan]│[/][dim]||  {marker}   ||[/]   [cyan]│[/]
    [cyan]│[/][dim]| \\    / |[/]   [cyan]│[/]
    [cyan]│[/][dim]\\  '--'  /[/]   [cyan]│[/]
    [cyan]│[/] [dim]'.  .'[/]     [cyan]│[/]
    [cyan]│[/]  [dim]'--'[/]      [cyan]│[/]
    [cyan]╰─────────────╯[/]
"""

# More detailed spinning frames
SPIN_FRAMES = [
    # Frame 0
    """    [cyan]╭─────────────╮[/]
    [cyan]│[/]    [dim].--.[/]    [cyan]│[/]
    [cyan]│[/]  [dim].'    '.[/]  [cyan]│[/]
    [cyan]│[/] [dim]/  .--.  \\[/] [cyan]│[/]
    [cyan]│[/][dim]|  /    \\  |[/][cyan]│[/]
    [cyan]│[/][dim]| | {m}  | |[/][cyan]│[/]
    [cyan]│[/][dim]|  \\    /  |[/][cyan]│[/]
    [cyan]│[/] [dim]\\  '--'  /[/] [cyan]│[/]
    [cyan]│[/]  [dim]'.    .'[/]  [cyan]│[/]
    [cyan]│[/]    [dim]'--'[/]    [cyan]│[/]
    [cyan]╰─────────────╯[/]""",
    # Frame 1
    """    [cyan]╭─────────────╮[/]
    [cyan]│[/]    [dim].--.[/]    [cyan]│[/]
    [cyan]│[/]  [dim].'    '.[/]  [cyan]│[/]
    [cyan]│[/] [dim]/   .--\\[/]  [cyan]│[/]
    [cyan]│[/][dim]|   /   |\\[/] [cyan]│[/]
    [cyan]│[/][dim]|  | {m} ||[/] [cyan]│[/]
    [cyan]│[/][dim]|   \\  / |[/] [cyan]│[/]
    [cyan]│[/] [dim]\\  '--'/[/]  [cyan]│[/]
    [cyan]│[/]  [dim]'.    .'[/]  [cyan]│[/]
    [cyan]│[/]    [dim]'--'[/]    [cyan]│[/]
    [cyan]╰─────────────╯[/]""",
    # Frame 2
    """    [cyan]╭─────────────╮[/]
    [cyan]│[/]    [dim].--.[/]    [cyan]│[/]
    [cyan]│[/]  [dim].'    '.[/]  [cyan]│[/]
    [cyan]│[/] [dim]/    .-\\[/]  [cyan]│[/]
    [cyan]│[/][dim]|    / |\\[/]  [cyan]│[/]
    [cyan]│[/][dim]|   |{m}||[/]  [cyan]│[/]
    [cyan]│[/][dim]|    \\ /|[/]  [cyan]│[/]
    [cyan]│[/] [dim]\\   '-'/[/]  [cyan]│[/]
    [cyan]│[/]  [dim]'.    .'[/]  [cyan]│[/]
    [cyan]│[/]    [dim]'--'[/]    [cyan]│[/]
    [cyan]╰─────────────╯[/]""",
    # Frame 3
    """    [cyan]╭─────────────╮[/]
    [cyan]│[/]    [dim].--.[/]    [cyan]│[/]
    [cyan]│[/]  [dim].'    '.[/]  [cyan]│[/]
    [cyan]│[/] [dim]/     -\\[/]  [cyan]│[/]
    [cyan]│[/][dim]|     /|\\[/]  [cyan]│[/]
    [cyan]│[/][dim]|    |{m}|[/]  [cyan]│[/]
    [cyan]│[/][dim]|     \\/|[/]  [cyan]│[/]
    [cyan]│[/] [dim]\\    -'/[/]  [cyan]│[/]
    [cyan]│[/]  [dim]'.    .'[/]  [cyan]│[/]
    [cyan]│[/]    [dim]'--'[/]    [cyan]│[/]
    [cyan]╰─────────────╯[/]""",
    # Frame 4
    """    [cyan]╭─────────────╮[/]
    [cyan]│[/]    [dim].--.[/]    [cyan]│[/]
    [cyan]│[/]  [dim].'    '.[/]  [cyan]│[/]
    [cyan]│[/]  [dim]\\-.    /[/] [cyan]│[/]
    [cyan]│[/] [dim]|\\  . | |[/] [cyan]│[/]
    [cyan]│[/] [dim]|| {m}| | |[/][cyan]│[/]
    [cyan]│[/] [dim]|/  ' | |[/] [cyan]│[/]
    [cyan]│[/]  [dim]/-.   \\[/]  [cyan]│[/]
    [cyan]│[/]  [dim]'.    .'[/]  [cyan]│[/]
    [cyan]│[/]    [dim]'--'[/]    [cyan]│[/]
    [cyan]╰─────────────╯[/]""",
    # Frame 5
    """    [cyan]╭─────────────╮[/]
    [cyan]│[/]    [dim].--.[/]    [cyan]│[/]
    [cyan]│[/]  [dim].'    '.[/]  [cyan]│[/]
    [cyan]│[/]  [dim]\\--.   /[/] [cyan]│[/]
    [cyan]│[/] [dim]|\\   . ||[/] [cyan]│[/]
    [cyan]│[/] [dim]|| {m} |||[/] [cyan]│[/]
    [cyan]│[/] [dim]|/   ' ||[/] [cyan]│[/]
    [cyan]│[/]  [dim]/--.  \\[/]  [cyan]│[/]
    [cyan]│[/]  [dim]'.    .'[/]  [cyan]│[/]
    [cyan]│[/]    [dim]'--'[/]    [cyan]│[/]
    [cyan]╰─────────────╯[/]""",
    # Frame 6
    """    [cyan]╭─────────────╮[/]
    [cyan]│[/]    [dim].--.[/]    [cyan]│[/]
    [cyan]│[/]  [dim].'    '.[/]  [cyan]│[/]
    [cyan]│[/]  [dim]\\.--   /[/] [cyan]│[/]
    [cyan]│[/] [dim]||    .||[/] [cyan]│[/]
    [cyan]│[/] [dim]|| {m} |||[/] [cyan]│[/]
    [cyan]│[/] [dim]||    '||[/] [cyan]│[/]
    [cyan]│[/]  [dim]/.--' \\[/]  [cyan]│[/]
    [cyan]│[/]  [dim]'.    .'[/]  [cyan]│[/]
    [cyan]│[/]    [dim]'--'[/]    [cyan]│[/]
    [cyan]╰─────────────╯[/]""",
    # Frame 7
    """    [cyan]╭─────────────╮[/]
    [cyan]│[/]    [dim].--.[/]    [cyan]│[/]
    [cyan]│[/]  [dim].'    '.[/]  [cyan]│[/]
    [cyan]│[/] [dim]/ .--.  \\[/] [cyan]│[/]
    [cyan]│[/][dim]||/    \\ |[/] [cyan]│[/]
    [cyan]│[/][dim]||  {m}  ||[/] [cyan]│[/]
    [cyan]│[/][dim]||\\    / |[/] [cyan]│[/]
    [cyan]│[/] [dim]\\ '--' /[/]  [cyan]│[/]
    [cyan]│[/]  [dim]'.    .'[/]  [cyan]│[/]
    [cyan]│[/]    [dim]'--'[/]    [cyan]│[/]
    [cyan]╰─────────────╯[/]""",
]



class GeoGlobe(Static):
    """A rotating ASCII globe widget with IP geolocation"""
    
    frame = reactive(0)
    public_ip = reactive("Scanning...")
    location = reactive("Triangulating...")
    lat = reactive(0.0)
    lon = reactive(0.0)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._fetched = False
        self._scan_dots = 0
    
    def on_mount(self):
        # Start rotation
        self.set_interval(0.2, self._rotate)
        # Fetch IP info
        self.call_later(self._fetch_geo)
    
    def _rotate(self):
        self.frame = (self.frame + 1) % len(SPIN_FRAMES)
        self._scan_dots = (self._scan_dots + 1) % 4
        self._render_globe()
    
    async def _fetch_geo(self):
        """Fetch geolocation from IP"""
        if self._fetched:
            return
        
        import urllib.request
        import json
        
        try:
            # Use ip-api.com (free, no key required)
            with urllib.request.urlopen("http://ip-api.com/json/", timeout=5) as response:
                data = json.loads(response.read().decode())
                self.public_ip = data.get("query", "Unknown")
                self.location = f"{data.get('city', '?')}, {data.get('country_code', '?')}"
                self.lat = data.get("lat", 0)
                self.lon = data.get("lon", 0)
                self._fetched = True
        except Exception as e:
            self.public_ip = "Offline"
            self.location = "Unknown"
    
    def _render_globe(self):
        import random
        marker = "[bold red]●[/]"
        globe = SPIN_FRAMES[self.frame].format(m=marker)
        
        # Noise for "tech" feel
        noise_lat = self.lat + (random.uniform(-0.001, 0.001) if self._fetched else 0)
        noise_lon = self.lon + (random.uniform(-0.001, 0.001) if self._fetched else 0)
        dots = "." * self._scan_dots
        
        # Signal strength bar
        rssi = random.randint(3, 10)
        signal = f"[green]{'|' * rssi}[/][dim]{'|' * (10-rssi)}[/]"
        
        grid_top = "[dim]┌───────────────────────────────┐[/]"
        grid_mid = "[dim]├───────────────────────────────┤[/]"
        grid_bot = "[dim]└───────────────────────────────┘[/]"
        
        if not self._fetched:
            status = f"[yellow blinking]SCANNING{dots:<3}[/]"
        else:
            status = "[bold green]LOCKED  [/]"

        info = f"""{grid_top}
 [bold cyan]LOCATION SYSTEMS[/]         {status}
{grid_mid}
{globe}
{grid_mid}
 [dim]IP ADDR :[/] [white]{self.public_ip:<15}[/]
 [dim]GEO LOC :[/] [white]{self.location:<15}[/]
 [dim]COORDS  :[/] [cyan]{noise_lat:7.4f}, {noise_lon:7.4f}[/]
 [dim]SIGNAL  :[/] {signal}
{grid_bot}"""
        self.update(info)
    
    def watch_public_ip(self, value):
        self._render_globe()
    
    def watch_location(self, value):
        self._render_globe()
