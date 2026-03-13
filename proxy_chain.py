# proxy_chain.py - Proxy-Chain: Dynamic Network Route Map
# Real proxy testing with animated visualization

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical, Horizontal, Container
from textual.widgets import Static, Input, Footer
from textual.binding import Binding
from textual.reactive import reactive
import asyncio
import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".nextral"
AGENT_CONFIG = CONFIG_DIR / "agent_config.json"

# Default demo proxies (used when no proxies are configured)
DEFAULT_PROXIES = [
    {"host": "185.220.101.33", "port": 9050, "label": "Entry Guard"},
    {"host": "104.244.76.91", "port": 9050, "label": "Middle Relay"},
    {"host": "51.15.43.212", "port": 9050, "label": "Exit Node"},
]


def load_proxy_list() -> list:
    """Load proxy chain from agent config, or fall back to defaults"""
    try:
        if AGENT_CONFIG.exists():
            cfg = json.loads(AGENT_CONFIG.read_text())
            proxies_str = cfg.get("proxy_chain", "")
            if proxies_str:
                # Format: host:port,host:port,...
                result = []
                for i, entry in enumerate(proxies_str.split(",")):
                    entry = entry.strip()
                    if ":" in entry:
                        h, p = entry.rsplit(":", 1)
                        h = h.replace("socks5://", "").replace("http://", "")
                        labels = ["Entry Guard", "Middle Relay", "Exit Node", "Relay", "Relay"]
                        result.append({"host": h, "port": int(p), "label": labels[min(i, 4)]})
                if result:
                    return result
    except Exception:
        pass
    return DEFAULT_PROXIES


class NetworkMap(Static):
    """ASCII art network map with animated packet flow and real status"""

    packet_pos = reactive(0)
    is_animating = reactive(False)

    def __init__(self, proxy_list: list, test_results: list | None = None, **kw):
        super().__init__(**kw)
        self.proxy_list = proxy_list
        self.test_results = test_results or []

    def on_mount(self):
        self._render_map()
        self.set_interval(0.15, self._animate_packet)
        self.is_animating = True

    def update_results(self, results: list):
        self.test_results = results
        self._render_map()

    def _render_map(self):
        nodes = self.proxy_list
        results = self.test_results
        n_nodes = len(nodes)

        lines = []
        lines.append("[bold cyan]╔════════════════════════════════════════════════════════════════════════════════╗[/]")
        lines.append("[bold cyan]║[/]                     [bold white]SECURE PROXY-CHAIN ROUTE VISUALIZER[/]                     [bold cyan]║[/]")
        lines.append("[bold cyan]╚════════════════════════════════════════════════════════════════════════════════╝[/]")
        lines.append("")

        # ── Node diagram ──
        # Distribute nodes evenly across 80 chars
        total_width = 78
        if n_nodes > 0:
            node_positions = [5] + [5 + int((i + 1) * (total_width - 10) / (n_nodes)) for i in range(n_nodes)] + [total_width - 3]
        else:
            node_positions = [5, total_width - 3]

        connection_line = list(" " * 82)

        # Place node markers
        connection_line[node_positions[0]] = "◉"  # YOU
        for i in range(1, len(node_positions) - 1):
            if i - 1 < len(results) and results[i - 1].get("status") == "ONLINE":
                connection_line[node_positions[i]] = "◉"
            elif i - 1 < len(results):
                connection_line[node_positions[i]] = "◈"
            else:
                connection_line[node_positions[i]] = "◇"
        connection_line[node_positions[-1]] = "◎"  # TARGET

        # Draw connections
        for i in range(len(node_positions) - 1):
            start = node_positions[i] + 1
            end = node_positions[i + 1]
            for j in range(start, end):
                connection_line[j] = "─"

        # Animate packet
        total_path = sum(node_positions[i + 1] - node_positions[i] for i in range(len(node_positions) - 1))
        if self.is_animating and total_path > 0:
            packet_idx = self.packet_pos % total_path
            cumulative = 0
            for i in range(len(node_positions) - 1):
                segment_len = node_positions[i + 1] - node_positions[i]
                if packet_idx < cumulative + segment_len:
                    actual_pos = node_positions[i] + (packet_idx - cumulative)
                    if 0 < actual_pos < len(connection_line) - 1:
                        connection_line[actual_pos] = "●"
                    break
                cumulative += segment_len

        lines.append("[green]" + "".join(connection_line) + "[/]")

        # Labels row
        label_parts = ["[cyan]YOU[/]"]
        for i, node in enumerate(nodes):
            lbl = node.get("label", f"Hop {i+1}")
            if i < len(results):
                status = results[i].get("status", "?")
                if status == "ONLINE":
                    label_parts.append(f"[green]{lbl}[/]")
                elif status == "TIMEOUT":
                    label_parts.append(f"[yellow]{lbl}[/]")
                else:
                    label_parts.append(f"[red]{lbl}[/]")
            else:
                label_parts.append(f"[dim]{lbl}[/]")
        label_parts.append("[green]TARGET[/]")
        lines.append("")
        lines.append("  " + "    ".join(label_parts))

        # IP row
        ip_parts = ["[dim]Local[/]"]
        for node in nodes:
            ip_parts.append(f"[dim]{node['host']}[/]")
        ip_parts.append("[dim]Destination[/]")
        lines.append("  " + "   ".join(ip_parts))
        lines.append("")

        # ── Connection Status ──
        lines.append("[bold white]─── CONNECTION STATUS ───[/]")
        lines.append("")

        online_count = sum(1 for r in results if r.get("status") == "ONLINE")
        total = len(results)
        if total > 0 and online_count == total:
            lines.append(f"  [cyan]◉[/] Circuit Status:   [bold green]ESTABLISHED ({online_count}/{total} nodes)[/]")
        elif total > 0:
            lines.append(f"  [cyan]◉[/] Circuit Status:   [bold yellow]PARTIAL ({online_count}/{total} nodes online)[/]")
        else:
            lines.append(f"  [cyan]◉[/] Circuit Status:   [dim]NOT TESTED (press T to test)[/]")

        total_latency = sum(r.get("latency_ms", 0) or 0 for r in results)
        if total_latency > 0:
            lat_color = "green" if total_latency < 200 else "yellow" if total_latency < 500 else "red"
            lines.append(f"  [cyan]◉[/] Total Latency:    [{lat_color}]{total_latency:.0f}ms[/]")
        else:
            lines.append(f"  [cyan]◉[/] Total Latency:    [dim]── (untested)[/]")

        lines.append(f"  [cyan]◉[/] Proxy Chain:      [yellow]{n_nodes} hop(s)[/]")
        lines.append("")

        # Data flow bar
        flow_bar = "▓" * ((self.packet_pos % 20) + 1) + "░" * (20 - (self.packet_pos % 20))
        colors = ["green", "cyan", "blue", "cyan", "green"]
        lines.append(f"  [dim]Data Flow:[/] [{colors[self.packet_pos % 5]}]{flow_bar}[/]")

        self.update("\n".join(lines))

    def _animate_packet(self):
        if self.is_animating:
            self.packet_pos += 1
            self._render_map()


class NodeTable(Static):
    """Table showing real node details with test results"""

    def __init__(self, proxy_list: list, **kw):
        super().__init__(**kw)
        self.proxy_list = proxy_list
        self.test_results = []

    def on_mount(self):
        self._render_table()

    def update_results(self, results: list):
        self.test_results = results
        self._render_table()

    def _render_table(self):
        from rich.table import Table
        from rich import box

        table = Table(box=box.HORIZONTALS, border_style="dim blue", header_style="bold cyan", expand=True)
        table.add_column("#", style="cyan", width=3)
        table.add_column("LABEL", style="white", width=14)
        table.add_column("HOST:PORT", style="yellow", width=24)
        table.add_column("STATUS", width=12)
        table.add_column("LATENCY", justify="right", width=10)

        for i, node in enumerate(self.proxy_list):
            host_port = f"{node['host']}:{node['port']}"
            label = node.get("label", f"Hop {i+1}")

            if i < len(self.test_results):
                r = self.test_results[i]
                status = r.get("status", "?")
                latency = r.get("latency_ms")

                if status == "ONLINE":
                    status_str = "[bold green]● ONLINE[/]"
                elif status == "TIMEOUT":
                    status_str = "[yellow]◌ TIMEOUT[/]"
                elif status == "REFUSED":
                    status_str = "[red]✗ REFUSED[/]"
                else:
                    status_str = f"[red]{status[:12]}[/]"

                if latency is not None:
                    lat_color = "green" if latency < 100 else "yellow" if latency < 300 else "red"
                    lat_str = f"[{lat_color}]{latency:.0f}ms[/]"
                else:
                    lat_str = "[dim]──[/]"
            else:
                status_str = "[dim]UNTESTED[/]"
                lat_str = "[dim]──[/]"

            table.add_row(str(i + 1), label, host_port, status_str, lat_str)

        self.update(table)


class ProxyScreen(Screen):
    """Proxy-Chain: Dynamic Network Route Map with real testing"""

    CSS = """
    ProxyScreen {
        background: #050508;
    }

    #header {
        dock: top;
        height: 3;
        background: #0a0a10;
        border-bottom: heavy #44aa44;
        padding: 0 2;
        content-align: center middle;
    }

    #main_container {
        width: 100%;
        height: 1fr;
        padding: 1;
    }

    #network_map {
        height: 20;
        background: #080810;
        border: round #226622;
        padding: 1;
    }

    #node_table {
        height: 1fr;
        background: #080810;
        border: round #226622;
        padding: 1;
        margin-top: 1;
    }

    #proxy_input_row {
        dock: bottom;
        height: 3;
        padding: 0 1;
        background: #0a0a10;
    }

    #proxy_input {
        width: 1fr;
        background: #0a0a12;
        border: solid #226622;
        color: #44dd44;
    }

    #stats {
        dock: bottom;
        height: 1;
        background: #0a0a10;
        color: #44aa44;
        text-align: center;
    }
    """

    BINDINGS = [
        Binding("escape", "close", "Close", show=True),
        Binding("t", "test_chain", "Test Chain", show=True),
        Binding("space", "toggle_animation", "Pause/Resume", show=True),
    ]

    def __init__(self):
        super().__init__()
        self.proxy_list = load_proxy_list()

    def compose(self) -> ComposeResult:
        yield Static(
            "[bold green]╔════════════════════════════════════════════════════════════════════════╗[/]\n"
            "[bold green]║[/]                       [bold white]PROXY-CHAIN: NETWORK ROUTER[/]                       [bold green]║[/]\n"
            "[bold green]╚════════════════════════════════════════════════════════════════════════╝[/]",
            id="header", markup=True
        )

        with Vertical(id="main_container"):
            yield NetworkMap(self.proxy_list, id="network_map")
            yield NodeTable(self.proxy_list, id="node_table")

        with Horizontal(id="proxy_input_row"):
            yield Input(id="proxy_input", placeholder="Add proxies: host:port,host:port,...  (Enter to set)")

        yield Static(id="stats", markup=True)
        yield Footer()

    def on_mount(self):
        self.query_one("#stats", Static).update(
            "[bold green]◈[/] T=Test Chain  SPACE=Pause  ESC=Exit  [dim]Enter proxies below to configure[/]"
        )

    def action_close(self):
        self.app.pop_screen()

    def action_test_chain(self):
        asyncio.create_task(self._test_proxies())

    async def _test_proxies(self):
        stats = self.query_one("#stats", Static)
        net_map = self.query_one("#network_map", NetworkMap)
        node_tbl = self.query_one("#node_table", NodeTable)

        stats.update("[yellow]◈ Testing proxy chain connectivity...[/]")

        results = []
        for node in self.proxy_list:
            host, port = node["host"], node["port"]
            result = {"proxy": f"{host}:{port}", "host": host, "port": port, "status": "UNKNOWN", "latency_ms": None}

            start_time = asyncio.get_event_loop().time()
            try:
                _, writer = await asyncio.wait_for(
                    asyncio.open_connection(host, port), timeout=3.0
                )
                latency = (asyncio.get_event_loop().time() - start_time) * 1000
                writer.close()
                await writer.wait_closed()
                result["status"] = "ONLINE"
                result["latency_ms"] = round(latency, 1)
            except asyncio.TimeoutError:
                result["status"] = "TIMEOUT"
            except ConnectionRefusedError:
                result["status"] = "REFUSED"
            except Exception as e:
                result["status"] = f"ERR:{str(e)[:20]}"

            results.append(result)

        # Update visualizations
        net_map.update_results(results)
        node_tbl.update_results(results)

        online = sum(1 for r in results if r["status"] == "ONLINE")
        total = len(results)
        if online == total:
            stats.update(f"[bold green]✓ Chain tested: ALL {total} nodes ONLINE[/]")
        else:
            stats.update(f"[bold yellow]⚠ Chain tested: {online}/{total} nodes online[/]")

    async def on_input_submitted(self, event: Input.Submitted):
        if event.input.id == "proxy_input":
            raw = event.input.value.strip()
            if not raw:
                return

            # Parse comma-separated host:port entries
            new_proxies = []
            labels = ["Entry Guard", "Middle Relay", "Exit Node", "Relay 4", "Relay 5"]
            for i, entry in enumerate(raw.split(",")):
                entry = entry.strip()
                if ":" in entry:
                    h, p = entry.rsplit(":", 1)
                    h = h.replace("socks5://", "").replace("http://", "")
                    try:
                        new_proxies.append({"host": h, "port": int(p), "label": labels[min(i, 4)]})
                    except ValueError:
                        pass

            if new_proxies:
                self.proxy_list = new_proxies

                # Save to config
                try:
                    cfg = {}
                    if AGENT_CONFIG.exists():
                        cfg = json.loads(AGENT_CONFIG.read_text())
                    cfg["proxy_chain"] = raw
                    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
                    AGENT_CONFIG.write_text(json.dumps(cfg, indent=2))
                except Exception:
                    pass

                # Rebuild widgets
                net_map = self.query_one("#network_map", NetworkMap)
                node_tbl = self.query_one("#node_table", NodeTable)
                net_map.proxy_list = new_proxies
                net_map.test_results = []
                net_map._render_map()
                node_tbl.proxy_list = new_proxies
                node_tbl.test_results = []
                node_tbl._render_table()

                event.input.value = ""
                self.query_one("#stats", Static).update(
                    f"[green]✓ Proxy chain updated: {len(new_proxies)} node(s). Press T to test.[/]"
                )
            else:
                self.query_one("#stats", Static).update("[red]Invalid format. Use: host:port,host:port,...[/]")

    def action_toggle_animation(self):
        net_map = self.query_one("#network_map", NetworkMap)
        net_map.is_animating = not net_map.is_animating
        status = "resumed" if net_map.is_animating else "paused"
        self.query_one("#stats", Static).update(f"[cyan]◈ Animation {status}[/]")
