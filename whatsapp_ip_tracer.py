"""
WhatsApp IP Tracer - Simple Terminal Version

A simple CLI tool to capture STUN traffic and identify WhatsApp server IPs.
"""

import subprocess
import sys
import re
import time
import signal
import os

FILTER = 'stun && frame.len == 86 && stun.type.method == 0x0001'

def find_tshark():
    """Find tshark executable."""
    import shutil
    path = shutil.which('tshark')
    if path:
        return path
    
    locations = [
        r"C:\Program Files\Wireshark\tshark.exe",
        r"C:\Program Files (x86)\Wireshark\tshark.exe",
    ]
    
    for loc in locations:
        if os.path.exists(loc):
            return loc
    
    return 'tshark'

def check_tshark():
    """Check if tshark is available."""
    tshark_path = find_tshark()
    try:
        result = subprocess.run(
            [tshark_path, '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except:
        return False

def list_interfaces():
    """List available network interfaces."""
    tshark_path = find_tshark()
    try:
        result = subprocess.run(
            [tshark_path, '-D'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            interfaces = []
            for line in result.stdout.splitlines():
                line = line.strip()
                if line and line[0].isdigit():
                    parts = line.split('. ', 1)
                    if len(parts) > 1:
                        iface = parts[1].strip()
                        if iface:
                            interfaces.append((iface, iface))
            return interfaces
    except:
        pass
    
    return [("eth0", "eth0"), ("Wi-Fi", "Wi-Fi"), ("Ethernet", "Ethernet")]

class Stoppable:
    def __init__(self):
        self.stopped = False

def run_capture(interface):
    """Run the capture."""
    tshark_path = find_tshark()
    
    cmd = [
        tshark_path,
        '-i', interface,
        '-Y', FILTER,
        '-T', 'fields',
        '-e', 'frame.time_epoch',
        '-e', 'ip.src',
        '-e', 'ip.dst',
        '-e', 'frame.interface_name',
        '-E', 'separator=|',
    ]
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    seen_ips = set()
    packet_count = 0
    stop_flag = Stoppable()
    
    print("\n" + "="*60)
    print("WHATSAPP IP TRACER - CAPTURING")
    print("="*60)
    print("\n[!] Make a WhatsApp call to the target now!")
    print("[!] Watch for IPs appearing below...\n")
    print("-"*60)
    
    while not stop_flag.stopped:
        line = process.stdout.readline()
        if not line:
            break
        if line.strip():
            parts = line.strip().split('|')
            if len(parts) >= 4:
                packet_count += 1
                dst_ip = parts[2]
                iface = parts[3]
                
                seen_ips.add(dst_ip)
                
                try:
                    ts = float(parts[0])
                    import datetime
                    timestamp = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
                except:
                    timestamp = time.strftime('%H:%M:%S')
                
                print(f"\n[!] POTENTIAL IP OBTAINED: {dst_ip} AT {timestamp}")
                print(f"    -> Interface: {iface}")
                print(f"    -> Packets: {packet_count} | Unique IPs: {len(seen_ips)}")
    
    process.terminate()
    print("\n" + "="*60)
    print("CAPTURE STOPPED")
    print(f"Total packets: {packet_count}")
    print(f"Unique IPs found: {len(seen_ips)}")
    print("="*60)

def main():
    print("\n" + "="*60)
    print("        WHATSAPP IP TRACER")
    print("="*60)
    print()
    
    if not check_tshark():
        print("[ERROR] tshark not found!")
        print("Please install Wireshark (includes tshark)")
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    print("[OK] tshark found\n")
    
    print("Available Network Interfaces:")
    interfaces = list_interfaces()
    for i, (name, desc) in enumerate(interfaces, 1):
        print(f"  {i}. {name}")
    print()
    
    # Try to auto-detect Wi-Fi or first available
    interface = interfaces[0][0]
    for name, desc in interfaces:
        if 'Wi-Fi' in desc or 'wifi' in desc.lower():
            interface = name
            print(f"[+] Auto-selected Wi-Fi interface: {interface}")
            break
    else:
        print(f"[+] Using first interface: {interface}")
    
    print(f"\n[+] Using interface: {interface}")
    print("[!] Press Ctrl+C to stop\n")
    print("Ready to capture... Make a WhatsApp call now!")
    print("-"*60)
    
    def signal_handler(sig, frame):
        print("\n\n[!] Stopping capture...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        run_capture(interface)
    except KeyboardInterrupt:
        print("\n\n[!] Capture stopped by user")
    except Exception as e:
        print(f"\n[!] Error: {e}")

if __name__ == "__main__":
    main()
