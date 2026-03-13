"""
tools_locator.py - Nextral External Tools Locator

Provides utilities for finding and executing external security tools
like nmap, netcat, nikto, hydra, tcpdump, openssl, etc.
"""

import os
import sys
import shutil
import subprocess
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
import json

CONFIG_FILE = Path(__file__).parent / "terminal_config.json"

DEFAULT_TOOLS = {
    "nmap": {
        "command": "nmap",
        "name": "Nmap",
        "description": "Network mapper - port scanning and network discovery",
        "category": "network_scanning",
        "install_linux": "sudo apt-get install nmap || sudo yum install nmap || sudo pacman -S nmap",
        "install_mac": "brew install nmap",
        "install_windows": "choco install nmap || Download from https://nmap.org/download.html",
        "common_paths": ["/usr/bin/nmap", "/usr/local/bin/nmap", "/opt/nmap/nmap"]
    },
    "netcat": {
        "command": "nc",
        "name": "Netcat",
        "description": "Network utility for reading/writing network connections",
        "category": "networking",
        "alias": "netcat",
        "install_linux": "sudo apt-get install netcat || sudo yum install nc || sudo pacman -S openbsd-netcat",
        "install_mac": "brew install netcat",
        "install_windows": "choco install netcat || Download from https://eternallybored.org/misc/netcat/",
        "common_paths": ["/usr/bin/nc", "/usr/local/bin/nc", "/bin/nc"]
    },
    "nikto": {
        "command": "nikto",
        "name": "Nikto",
        "description": "Web server scanner - detects dangerous files/CGIs and outdated software",
        "category": "web_scanning",
        "install_linux": "sudo apt-get install nikto || git clone https://github.com/sullo/nikto && cd nikto && perl nikto.pl -h",
        "install_mac": "brew install nikto",
        "install_windows": "perl -MCPAN -e \"install App::Nikto\" || Download from https://github.com/sullo/nikto",
        "common_paths": ["/usr/bin/nikto", "/usr/local/bin/nikto", "/usr/share/nikto"]
    },
    "hydra": {
        "command": "hydra",
        "name": "Hydra",
        "description": "Password attack tool - online password cracking",
        "category": "password_attacks",
        "install_linux": "sudo apt-get install hydra || sudo yum install hydra || sudo pacman -S hydra",
        "install_mac": "brew install hydra",
        "install_windows": "Download precompiled from https://github.com/vanhauser-thc/thc-hydra",
        "common_paths": ["/usr/bin/hydra", "/usr/local/bin/hydra"]
    },
    "tcpdump": {
        "command": "tcpdump",
        "name": "TCPDump",
        "description": "Packet analyzer - network traffic capture tool",
        "category": "packet_capture",
        "install_linux": "sudo apt-get install tcpdump || sudo yum install tcpdump || sudo pacman -S tcpdump",
        "install_mac": "brew install tcpdump",
        "install_windows": "choco install tcpdump || Use WinPcap/Npcap with tcpdump for Windows",
        "common_paths": ["/usr/bin/tcpdump", "/usr/local/bin/tcpdump", "/sbin/tcpdump"]
    },
    "openssl": {
        "command": "openssl",
        "name": "OpenSSL",
        "description": "SSL/TLS toolkit - certificate generation, encryption, testing",
        "category": "cryptography",
        "install_linux": "sudo apt-get install openssl || sudo yum install openssl || sudo pacman -S openssl",
        "install_mac": "brew install openssl@3",
        "install_windows": "choco install openssl || Download from https://slproweb.com/products/Win32OpenSSL.html",
        "common_paths": ["/usr/bin/openssl", "/usr/local/bin/openssl", "/usr/ssl/bin/openssl"]
    },
    "curl": {
        "command": "curl",
        "name": "cURL",
        "description": "Command-line URL transfer tool",
        "category": "network",
        "install_linux": "sudo apt-get install curl || sudo yum install curl || sudo pacman -S curl",
        "install_mac": "brew install curl",
        "install_windows": "choco install curl || Pre-installed on Windows 10+",
        "common_paths": ["/usr/bin/curl", "/usr/local/bin/curl", "/bin/curl"]
    },
    "wget": {
        "command": "wget",
        "name": "Wget",
        "description": "Non-interactive network downloader",
        "category": "network",
        "install_linux": "sudo apt-get install wget || sudo yum install wget || sudo pacman -S wget",
        "install_mac": "brew install wget",
        "install_windows": "choco install wget || Download from https://eternallybored.org/misc/wget/",
        "common_paths": ["/usr/bin/wget", "/usr/local/bin/wget", "/bin/wget"]
    },
    "ssh": {
        "command": "ssh",
        "name": "SSH",
        "description": "Secure Shell - encrypted remote access",
        "category": "remote_access",
        "install_linux": "sudo apt-get install openssh-client || sudo yum install openssh-clients || sudo pacman -S openssh",
        "install_mac": "Pre-installed",
        "install_windows": "choco install openssh || Pre-installed on Windows 10+",
        "common_paths": ["/usr/bin/ssh", "/usr/local/bin/ssh", "/bin/ssh", "/usr/bin/ssh.exe"]
    },
    "scp": {
        "command": "scp",
        "name": "SCP",
        "description": "Secure copy - file transfer over SSH",
        "category": "file_transfer",
        "install_linux": "sudo apt-get install openssh-client || sudo yum install openssh-clients",
        "install_mac": "Pre-installed",
        "install_windows": "choco install openssh",
        "common_paths": ["/usr/bin/scp", "/usr/local/bin/scp", "/bin/scp", "/usr/bin/scp.exe"]
    },
    "sqlmap": {
        "command": "sqlmap",
        "name": "SQLMap",
        "description": "Automatic SQL injection and database takeover tool",
        "category": "web_attacks",
        "install_linux": "git clone https://github.com/sqlmapproject/sqlmap.git && sudo ln -s sqlmap/sqlmap.py /usr/local/bin/sqlmap",
        "install_mac": "brew install sqlmap",
        "install_windows": "git clone https://github.com/sqlmapproject/sqlmap.git",
        "common_paths": ["/usr/bin/sqlmap", "/usr/local/bin/sqlmap", "/usr/share/sqlmap"]
    },
    "hashcat": {
        "command": "hashcat",
        "name": "Hashcat",
        "description": "Password recovery - fast hash cracking",
        "category": "password_attacks",
        "install_linux": "sudo apt-get install hashcat || sudo yum install hashcat || sudo pacman -S hashcat",
        "install_mac": "brew install hashcat",
        "install_windows": "Download from https://hashcat.net/hashcat/",
        "common_paths": ["/usr/bin/hashcat", "/usr/local/bin/hashcat"]
    },
    "socat": {
        "command": "socat",
        "name": "SoCat",
        "description": "Bidirectional data relay - netcat alternative with more features",
        "category": "networking",
        "install_linux": "sudo apt-get install socat || sudo yum install socat || sudo pacman -S socat",
        "install_mac": "brew install socat",
        "install_windows": "choco install socat",
        "common_paths": ["/usr/bin/socat", "/usr/local/bin/socat"]
    },
    "nim": {
        "command": "nim",
        "name": "Nim Compiler",
        "description": "Nim programming language compiler",
        "category": "development",
        "install_linux": "curl https://nim-lang.org/choosenim/init.sh -sSf | sh",
        "install_mac": "brew install nim",
        "install_windows": "choco install nim",
        "common_paths": ["/usr/bin/nim", "/usr/local/bin/nim"]
    },
    "rustc": {
        "command": "rustc",
        "name": "Rust Compiler",
        "description": "The Rust programming language compiler",
        "category": "development",
        "install_linux": "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh",
        "install_mac": "brew install rust",
        "install_windows": "Download from https://rustup.rs/",
        "common_paths": ["/usr/bin/rustc", "/usr/local/bin/rustc"]
    },
    "go": {
        "command": "go",
        "name": "Go Compiler",
        "description": "The Go programming language compiler",
        "category": "development",
        "install_linux": "sudo apt-get install golang || sudo yum install golang",
        "install_mac": "brew install go",
        "install_windows": "choco install golang",
        "common_paths": ["/usr/bin/go", "/usr/local/bin/go", "/usr/local/go/bin/go"]
    },
    "csc": {
        "command": "csc",
        "name": "C# Compiler",
        "description": "Microsoft C# Compiler",
        "category": "development",
        "install_linux": "sudo apt-get install mono-devel",
        "install_mac": "brew install mono",
        "install_windows": "Included with .NET Framework / Visual Studio",
        "common_paths": ["C:\\Windows\\Microsoft.NET\\Framework64\\v4.0.30319\\csc.exe", "C:\\Windows\\Microsoft.NET\\Framework\\v4.0.30319\\csc.exe", "/usr/bin/csc"]
    }
}


def load_config() -> Dict[str, Any]:
    """Load configuration from JSON file"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}


def save_config(config: Dict[str, Any]) -> None:
    """Save configuration to JSON file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
    except:
        pass


def get_tool_config() -> Dict[str, str]:
    """Get tool paths from config or use defaults"""
    config = load_config()
    tools_config = config.get("external_tools", {})
    
    result = {}
    for tool_key, tool_info in DEFAULT_TOOLS.items():
        command = tool_info.get("command")
        result[tool_key] = tools_config.get(tool_key, command)
    return result

# Log of tools recovered via automatic path injection
RECOVERED_TOOLS: List[str] = []

def find_tool(name: str) -> Optional[str]:
    """
    Find the path to an external tool.
    
    Args:
        name: Tool name (e.g., 'nmap', 'nc', 'hydra')
    
    Returns:
        Full path to tool if found, None otherwise
    """
    tool_key = name.lower()
    tool_info = DEFAULT_TOOLS.get(tool_key, {})
    
    config = load_config()
    tools_config = config.get("external_tools", {})
    
    configured_path = tools_config.get(tool_key)
    if configured_path:
        if os.path.isabs(configured_path):
            if os.path.exists(configured_path) and os.access(configured_path, os.X_OK):
                return configured_path
        else:
            found = shutil.which(configured_path)
            if found:
                return found
    
    command = tool_info.get("command", name)
    found = shutil.which(command)
    if found:
        return found
    
    for path in tool_info.get("common_paths", []):
        if os.path.exists(path) and os.access(path, os.X_OK):
            return path
    
    # ── Standard Windows discovery (Program Files, etc.) ──
    if sys.platform == "win32":
        standard_roots = [
            os.environ.get("ProgramFiles", "C:\\Program Files"),
            os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"),
            os.environ.get("ProgramData", "C:\\ProgramData"),
        ]
        
        search_patterns = {
            "nmap": ["Nmap\\nmap.exe"],
            "netcat": ["ncat\\ncat.exe", "netcat\\nc.exe"],
            "nikto": ["nikto\\nikto.pl"],
            "hydra": ["hydra\\hydra.exe"],
            "hashcat": ["hashcat\\hashcat.exe"],
        }
        
        patterns = search_patterns.get(tool_key, [])
        for root in standard_roots:
            for pattern in patterns:
                full_path = os.path.join(root, pattern)
                if os.path.exists(full_path):
                    # Temporarily inject into PATH for the current session
                    dir_path = os.path.dirname(full_path)
                    if dir_path not in os.environ["PATH"]:
                        os.environ["PATH"] += os.pathsep + dir_path
                        if name not in RECOVERED_TOOLS:
                            RECOVERED_TOOLS.append(name)
                    return full_path
    
    return None


def is_tool_installed(name: str) -> Tuple[bool, Optional[str]]:
    """
    Check if a tool is installed and return its path.
    
    Args:
        name: Tool name
    
    Returns:
        Tuple of (is_installed, path_or_none)
    """
    path = find_tool(name)
    return (path is not None, path)


def get_tool_info(name: str) -> Optional[Dict[str, Any]]:
    """Get information about a tool"""
    return DEFAULT_TOOLS.get(name.lower())


def get_install_command(name: str) -> Optional[str]:
    """Get platform-specific install command for a tool"""
    tool_info = DEFAULT_TOOLS.get(name.lower())
    if not tool_info:
        return None
    
    platform = sys.platform
    
    if platform == "linux" or platform.startswith("linux"):
        return tool_info.get("install_linux")
    elif platform == "darwin":
        return tool_info.get("install_mac")
    elif platform == "win32":
        return tool_info.get("install_windows")
    
    return None


def get_all_tools_by_category() -> Dict[str, List[Dict[str, str]]]:
    """Get all tools grouped by category"""
    categories = {}
    for tool_key, tool_info in DEFAULT_TOOLS.items():
        category = tool_info.get("category", "other")
        if category not in categories:
            categories[category] = []
        categories[category].append({
            "key": tool_key,
            "name": tool_info.get("name"),
            "description": tool_info.get("description"),
            "command": tool_info.get("command")
        })
    return categories


async def run_tool(
    name: str,
    args: List[str],
    timeout: int = 60,
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None
) -> Tuple[int, str, str]:
    """
    Run an external tool asynchronously.
    
    Args:
        name: Tool name
        args: Command-line arguments
        timeout: Timeout in seconds
        cwd: Working directory
        env: Environment variables
    
    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    tool_path = find_tool(name)
    if not tool_path:
        return (-1, "", f"Tool '{name}' not found. Please install it first.")
    
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    
    try:
        proc = await asyncio.create_subprocess_exec(
            tool_path,
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=full_env
        )
        
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout
            )
            stdout = stdout_bytes.decode('utf-8', errors='replace')
            stderr = stderr_bytes.decode('utf-8', errors='replace')
            return (proc.returncode, stdout, stderr)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return (-1, "", f"Command timed out after {timeout} seconds")
    
    except Exception as e:
        return (-1, "", f"Error running tool: {str(e)}")


def run_tool_sync(
    name: str,
    args: List[str],
    timeout: int = 60,
    cwd: Optional[str] = None
) -> Tuple[int, str, str]:
    """
    Run an external tool synchronously.
    
    Args:
        name: Tool name
        args: Command-line arguments
        timeout: Timeout in seconds
        cwd: Working directory
    
    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    tool_path = find_tool(name)
    if not tool_path:
        return (-1, "", f"Tool '{name}' not found. Please install it first.")
    
    try:
        result = subprocess.run(
            [tool_path] + args,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd
        )
        return (result.returncode, result.stdout, result.stderr)
    except subprocess.TimeoutExpired:
        return (-1, "", f"Command timed out after {timeout} seconds")
    except Exception as e:
        return (-1, "", f"Error running tool: {str(e)}")


def check_all_tools() -> Dict[str, Tuple[bool, Optional[str]]]:
    """Check which tools are installed"""
    results = {}
    for tool_key in DEFAULT_TOOLS.keys():
        results[tool_key] = is_tool_installed(tool_key)
    return results


def get_missing_tools() -> List[str]:
    """Get list of tools that are not installed"""
    missing = []
    for tool_key in DEFAULT_TOOLS.keys():
        installed, _ = is_tool_installed(tool_key)
        if not installed:
            missing.append(tool_key)
    return missing


if __name__ == "__main__":
    print("=== Nextral External Tools Check ===\n")
    
    results = check_all_tools()
    
    for tool_key, (installed, path) in results.items():
        tool_info = DEFAULT_TOOLS.get(tool_key, {})
        status = f"[green]✓ INSTALLED[/]: {path}" if installed else "[red]✗ NOT FOUND[/]"
        print(f"{tool_info.get('name', tool_key):12} - {status}")
    
    print("\n=== Missing Tools ===")
    missing = get_missing_tools()
    if missing:
        for tool_key in missing:
            tool_info = DEFAULT_TOOLS.get(tool_key, {})
            print(f"\n{tool_info.get('name', tool_key)}:")
            print(f"  Install: {get_install_command(tool_key)}")
    else:
        print("All tools are installed!")
