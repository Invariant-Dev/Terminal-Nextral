# 🖥️ Nextral Terminal
> **N**eural **Ex**tension **T**erminal & **R**esponse **A**rray **L**ayer

A cinematic, cross-platform cyberpunk terminal equipped with advanced offensive security tools, an evasive payload generator, and JARVIS-style animations.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)
![License](https://img.shields.io/badge/License-GPLv3-blue.svg)

---

## ⚠️ LEGAL & EDUCATIONAL WAIVER

**READ CAREFULLY BEFORE DOWNLOADING OR USING NEXTRAL TERMINAL:**

Nextral Terminal contains advanced offensive security tools, including a Payload Factory capable of generating evasive malware elements, integrated C2 listeners, and network exploitation utilities. 

**THIS SOFTWARE IS STRICTLY FOR EDUCATIONAL PURPOSES, AUTHORIZED PENETRATION TESTING, AND CYBERSECURITY RESEARCH ONLY.**

By using this software, you explicitly agree to the following:
1. You will not use Nextral Terminal or any generated payloads against systems, networks, or devices without explicit, written, and authorized consent from the owner.
2. The creator(s) and contributor(s) of this project take **ZERO responsibility** for any misuse, damage, data loss, or unlawful activities caused by this tool.
3. You are solely responsible for ensuring that your use of this software complies with all local, state, national, and international laws.
4. "Hacking" without permission is a federal crime. If you misuse this tool, you are on your own.

---

## 🎯 What is Nextral?

Nextral is a futuristic terminal interface that transforms your command line into a cinematic experience while acting as a powerful hub for cybersecurity operations. Think Tony Stark's JARVIS meets a highly capable hacker terminal.

### ✨ Key Features:
- **VENOMOUS PAYLOAD FACTORY V4** - Modular C2 framework with polymorphic encoding, EDR evasion, API unhooking, direct syscalls (HellsGate), and multi-language stagers (Nim, Rust, Go, C#, Python, PS1).
- **INTEGRATED C2 LISTENER** - Built-in asynchronous Command & Control listener for handling reverse shells and encrypted beacon traffic (DNS & ICMP).
- **CROSS-PLATFORM** - Fully supported on Windows and Modern Linux distributions.
- **OFFENSIVE TOOLKIT** - Includes Metasploit integration, proxy interception, OSINT tools, network sniffers, and automated breach watching.
- **CINEMATIC UI** - "Cyberpunk Noir" aesthetic with Matrix rain, glitch transitions, pulsing indicators, rotating scanners, and a premium glassmorphism HUD.
- **AUTO-INSTALL** - Self-bootstrapping installer that handles all Python dependencies and platform-specific configurations automatically.

---

## 🚀 Full Setup Guide

Nextral Terminal is designed to be as frictionless as possible out of the box. Choose the method that matches your operating system.

### Option 1: Quick Install (Windows)

1. Ensure **Python 3.8+** is installed and added to your system `PATH`.
2. Double-click the `Nextral.bat` file in the root directory.
3. The launcher will automatically verify your Python installation, install required libraries (`textual`, `rich`, `psutil`, etc.), and launch the terminal.
4. Watch the cinematic boot sequence and enjoy.

### Option 2: Quick Install (Linux / macOS)

1. Open your terminal and navigate to the Nextral directory.
2. Grant execution permissions to the setup script:
   ```bash
   chmod +x Nextral.sh
   chmod +x build_linux.sh
   ```
3. Run the shell script:
   ```bash
   ./Nextral.sh
   ```
4. It will create a virtual environment, install the requirements, and drop you straight into the cyber HUD.

### Option 3: Manual Environment Setup (All Platforms)

If you prefer to manage the environment yourself:

```bash
# 1. Create a virtual environment
python3 -m venv .venv

# 2. Activate it
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# 3. Install requirements
pip install -r requirements.txt

# 4. Launch Nextral
python nextral.py
```

### Option 4: Build Standalone Executable

If you want to compile Nextral into a portable executable that doesn't require a Python installation on the target machine:

**Windows:**
Double-click `build.bat` or run:
```bash
pip install pyinstaller
pyinstaller nextral.spec
# Finds exe in dist/Nextral.exe
```

**Linux:**
Run the provided compiler script:
```bash
./build_linux.sh
# Finds binary in dist/Nextral
```

---

## 🛡️ Offensive Toolkit Overview

Nextral is not just a pretty face; it includes a full suite of interactive security apps available from the main dashboard.

### ☣️ Venomous Payload Factory
The crown jewel of Nextral's offensive suite. Generate weaponized, highly-evasive payloads directly from the terminal.
- **Languages:** Python, Golang, C#, Nim, Rust, PowerShell, DuckyScript, One-Liners.
- **Stagers:** Standard TCP, DNS Tunneling, ICMP Beacons.
- **Evasion:** XOR Encryption, Junk Code Injection, Sandbox Detection avoidance.
- **C2:** Features an integrated `🎧 LISTEN` tab to catch your incoming reverse shells directly within the app.

### 🌐 Proxy Intercept & MSF Bridge
- **MSF Bridge:** An adaptive interface linking directly to your Metasploit RPC server for launching automated exploits and tracking sessions.
- **Proxy Interceptor:** Zero-latency burst-fire interception of web traffic, acting as a lightweight localized Burp Suite.

### 🔍 Recon & Analysis
- **OSINT Hub:** Gather intelligence on targets.
- **Network Probe:** Live packet capturing and bandwidth monitoring.
- **System Scan:** Automated threat and vulnerability scanning.

---

## 📊 Standard HUD Commands

Type commands into the **bottom input field** (yellow/cyan border):

```
USERNAME@NEXTRAL:~$ status
```

| Command | Description |
|---------|-------------|
| `status` | Full performance report (CPU, RAM, Disk) |
| `network` | Network bandwidth statistics |
| `processes` | Top CPU-consuming processes |
| `attackhub` | Open the Offensive Security Dashboard |
| `payloads` | Open Venomous Payload Factory |
| `listen` | Start a quick netcat-style listener |
| `clear` | Clear output log |
| `help` | Show all HUD commands |

---

## 🎨 Terminal Styling Recommendations

Nextral handles its own UI (via Textual), but your terminal emulator controls font rendering. For the ultimate cyberpunk experience:

1. **Terminal:** Use Windows Terminal, GNOME Terminal, or Alacritty.
2. **Font:** Install and set your terminal font to **Cascadia Code**, **Fira Code**, or **JetBrains Mono** to ensure perfect icon rendering. 
3. **Background:** Pure Black (`#000000`).
4. **Opacity:** 85-90% for a true glassmorphism feel over your desktop background.

---

## 📁 Project Structure

```
nextral_terminal/
│
├── launcher.py              # Smart launcher with auto-installs
├── nextral.py               # Main Hub and Terminal HUD
├── attack_hub.py            # Offensive Capabilities Dashboard
├── payload_factory.py       # Venomous Payload Generator UI
├── msf_bridge.py            # Metasploit RPC Bridge
├── generators/              # Modular Payload generation code
│   ├── base.py
│   ├── nim_gen.py
│   ├── c2_listener.py       # Built-in async C2 server
│   └── ...
├── Nextral.bat / .sh        # Multi-platform bootstrap scripts
└── README.md
```

---

## 📝 License

**GNU General Public License v3.0** - Free to use, modify, and distribute.

---

**⚡ NEXTRAL - Neural Extension Terminal & Response Array Layer ⚡**

*System armed and monitoring. Advanced neural interface online.*

**Made with ❤️ for ethical hackers, red teamers, and cyberpunk enthusiasts.**
