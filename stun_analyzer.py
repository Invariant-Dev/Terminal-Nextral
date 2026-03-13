"""
WhatsApp STUN Analyzer - Core Module

A passive STUN traffic analysis tool for protocol research and diagnostics.

WHAT IS STUN?
-------------
STUN (Session Traversal Utilities for NAT) is a protocol defined in RFC 5389.
It allows a client to discover its public IP address and the type of NAT gateway
it sits behind. This is essential for peer-to-peer real-time communication.

STUN Binding Requests (0x0001):
-------------------------------
The STUN protocol uses different message types identified by a method code
and a class code combined in the message header:

- Method 0x0001 (Binding): Used to discover the client's external mapping
- Class bits (0x0100 = Request, 0x0110 = Indication)

Therefore, a STUN Binding Request has stun.type.method == 0x0001.

WHY frame.len == 86?
--------------------
A typical STUN Binding Request packet is:
- Ethernet header: 14 bytes
- IP header (IPv4): 20 bytes  
- UDP header: 8 bytes
- STUN header: 20 bytes (magic cookie + transaction ID)
- STUN attributes: ~24 bytes (typically MAPPED-ADDRESS or XOR-MAPPED-ADDRESS)

Total: ~86 bytes

This is a HEURISTIC, not a guarantee. Actual packet sizes vary based on:
- IPv6 (40 byte IP header)
- VLAN tags
- Additional STUN attributes
- Network MTU settings

This tool does NOT:
- Hack WhatsApp or any messaging application
- Intercept or decrypt message contents
- Identify or trace individual users
- Access any account or personal data

It only observes STUN signaling patterns on the local network interface
for educational and diagnostic purposes.
"""

import subprocess
import sys
import re
import json
import argparse
import threading
import time
from datetime import datetime
from typing import Optional, Set, Dict, Any, List
from dataclasses import dataclass, asdict


@dataclass
class StunPacket:
    """Represents a parsed STUN Binding Request packet."""
    timestamp: str
    src_ip: str
    dst_ip: str
    interface: str


class CaptureRunner:
    """
    Spawns tshark and reads stdout line by line.
    
    Applies the exact display filter:
    stun && frame.len == 86 && stun.type.method == 0x0001
    """
    
    FILTER = 'stun && frame.len == 86 && stun.type.method == 0x0001'
    
    def __init__(self, interface: Optional[str] = None, pcap_file: Optional[str] = None):
        self.interface: Optional[str] = interface
        self.pcap_file: Optional[str] = pcap_file
        self.process: Optional[subprocess.Popen] = None
        self._stop_event = threading.Event()
    
    def _build_command(self) -> List[str]:
        """Build tshark command with appropriate arguments."""
        cmd = ['tshark']
        
        if self.pcap_file:
            cmd.extend(['-r', self.pcap_file])
        elif self.interface:
            cmd.extend(['-i', self.interface])
        else:
            raise ValueError("Either interface or pcap_file must be specified")
        
        cmd.extend([
            '-Y', self.FILTER,
            '-T', 'fields',
            '-e', 'frame.time_epoch',
            '-e', 'ip.src',
            '-e', 'ip.dst',
            '-e', 'frame.interface_name',
            '-E', 'separator=|',
        ])
        
        return cmd
    
    def start(self, callback) -> None:
        """Start capture and call callback for each packet line."""
        cmd = self._build_command()
        
        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
        except FileNotFoundError:
            raise RuntimeError("tshark not found. Please install Wireshark/tshark.")
        except PermissionError:
            raise RuntimeError(
                "Permission denied. Capture may require elevated privileges.\n"
                "On Linux: run with sudo or add user to 'pcap' group.\n"
                "On Windows: run as Administrator."
            )
        
        while not self._stop_event.is_set():
            if not self.process or not self.process.stdout:
                break
            line = self.process.stdout.readline()
            if not line:
                break
            if line.strip():
                callback(line.strip())
    
    def stop(self) -> None:
        """Stop the capture process."""
        self._stop_event.set()
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=2)
            except:
                try:
                    self.process.kill()
                except:
                    pass


class Parser:
    """
    Extracts fields from tshark output line.
    
    Expected format: timestamp|src_ip|dst_ip|interface
    """
    
    LINE_PATTERN = re.compile(r'^([^|]+)\|([^|]+)\|([^|]+)\|(.+)$')
    
    def parse(self, line: str) -> Optional[StunPacket]:
        """Parse a tshark output line into a StunPacket."""
        match = self.LINE_PATTERN.match(line)
        if not match:
            return None
        
        try:
            timestamp_epoch = float(match.group(1))
            timestamp = datetime.fromtimestamp(timestamp_epoch).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        except (ValueError, OSError):
            timestamp = match.group(1)
        
        return StunPacket(
            timestamp=timestamp,
            src_ip=match.group(2),
            dst_ip=match.group(3),
            interface=match.group(4)
        )


class OutputRenderer:
    """
    Renders parsed packets to terminal or JSON format.
    """
    
    def __init__(self, use_json: bool = False):
        self.use_json = use_json
    
    def render(self, packet: StunPacket, stats: Dict[str, int]) -> None:
        """Render a single packet."""
        if self.use_json:
            self._render_json(packet, stats)
        else:
            self._render_terminal(packet, stats)
    
    def _render_terminal(self, packet: StunPacket, stats: Dict[str, int]) -> None:
        """Render packet in terminal-friendly format."""
        print(f"[{packet.timestamp}] {packet.src_ip} -> {packet.dst_ip} | iface: {packet.interface}")
        print(f"    Packets: {stats['total']} | Unique Peers: {stats['unique']}")
    
    def _render_json(self, packet: StunPacket, stats: Dict[str, int]) -> None:
        """Render packet as JSON."""
        output = {
            "timestamp": packet.timestamp,
            "source_ip": packet.src_ip,
            "destination_ip": packet.dst_ip,
            "interface": packet.interface,
            "stats": {
                "total_packets": stats['total'],
                "unique_peers": stats['unique']
            }
        }
        print(json.dumps(output))
    
    def render_stats(self, stats: Dict[str, int]) -> None:
        """Render final statistics."""
        if self.use_json:
            print(json.dumps({"final_stats": stats}))
        else:
            print(f"\n=== Capture Complete ===")
            print(f"Total STUN Binding Requests: {stats['total']}")
            print(f"Unique Source IPs: {stats['unique']}")


class StunAnalyzer:
    """
    Main analyzer orchestrating capture, parsing, and output.
    """
    
    def __init__(self, interface: Optional[str] = None, pcap_file: Optional[str] = None, json_output: bool = False):
        self.interface: Optional[str] = interface
        self.pcap_file: Optional[str] = pcap_file
        self.json_output = json_output
        
        self.runner = CaptureRunner(interface, pcap_file)
        self.parser = Parser()
        self.renderer = OutputRenderer(json_output)
        
        self.seen_ips: Set[str] = set()
        self.stats = {"total": 0, "unique": 0}
        self.running = False
    
    def _handle_packet(self, line: str) -> None:
        """Process a single packet line."""
        packet = self.parser.parse(line)
        if packet:
            self.stats["total"] += 1
            self.seen_ips.add(packet.src_ip)
            self.stats["unique"] = len(self.seen_ips)
            self.renderer.render(packet, self.stats.copy())
    
    def run(self) -> None:
        """Run the analyzer (blocking)."""
        self.running = True
        
        if not self.json_output:
            print("=" * 60)
            print("WhatsApp STUN Analyzer")
            print("=" * 60)
            print("Capturing STUN Binding Requests...")
            print(f"Filter: {CaptureRunner.FILTER}")
            print("-" * 60)
        
        try:
            self.runner.start(self._handle_packet)
        except RuntimeError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        finally:
            self.running = False
            self.renderer.render_stats(self.stats)
    
    def run_async(self) -> None:
        """Run the analyzer in a separate thread."""
        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()
    
    def stop(self) -> None:
        """Stop the analyzer."""
        self.runner.stop()


def check_tshark() -> tuple[bool, str]:
    """Check if tshark is available."""
    try:
        result = subprocess.run(
            ['tshark', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return True, "tshark is available"
        return False, "tshark returned non-zero"
    except FileNotFoundError:
        return False, "tshark not found"
    except subprocess.TimeoutExpired:
        return False, "tshark check timed out"
    except Exception as e:
        return False, str(e)


def list_interfaces() -> List[str]:
    """List available network interfaces."""
    try:
        result = subprocess.run(
            ['tshark', '-D'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            interfaces = []
            for line in result.stdout.splitlines():
                match = re.match(r'^\d+\.\s+([^\s]+)', line)
                if match:
                    interfaces.append(match.group(1))
            return interfaces
        return []
    except:
        return []


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="WhatsApp IP Finder - STUN Traffic Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --iface eth0
  %(prog)s --iface "Wi-Fi" --json
  %(prog)s --pcap capture.pcap
  
Note: Capturing packets may require elevated privileges.
        """
    )
    
    parser.add_argument(
        '--iface',
        metavar='NAME',
        help='Network interface to capture on (required for live capture)'
    )
    
    parser.add_argument(
        '--pcap',
        metavar='FILE',
        help='Read from pcap file instead of live interface'
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output in JSON format'
    )
    
    parser.add_argument(
        '--list-ifaces',
        action='store_true',
        help='List available network interfaces'
    )
    
    args = parser.parse_args()
    
    if args.list_ifaces:
        print("Available network interfaces:")
        for iface in list_interfaces():
            print(f"  - {iface}")
        sys.exit(0)
    
    if not args.iface and not args.pcap:
        print("Error: Either --iface or --pcap must be specified", file=sys.stderr)
        print("Use --list-ifaces to see available interfaces", file=sys.stderr)
        sys.exit(1)
    
    available, msg = check_tshark()
    if not available:
        print(f"Error: {msg}", file=sys.stderr)
        print("Please install Wireshark/tshark to use this tool.", file=sys.stderr)
        sys.exit(1)
    
    if args.iface and not args.pcap:
        interfaces = list_interfaces()
        if interfaces and args.iface not in interfaces:
            print(f"Warning: Interface '{args.iface}' not in tshark's list", file=sys.stderr)
            print(f"Available: {', '.join(interfaces)}", file=sys.stderr)
    
    analyzer = StunAnalyzer(
        interface=args.iface,
        pcap_file=args.pcap,
        json_output=args.json
    )
    
    try:
        analyzer.run()
    except KeyboardInterrupt:
        print("\nInterrupted.")
        analyzer.stop()


if __name__ == '__main__':
    main()
