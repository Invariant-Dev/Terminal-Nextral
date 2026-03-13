# 🖥️ Nextral Terminal

> **N**eural **Ex**tension **T**erminal & **R**esponse **A**rray **L**ayer

A cinematic, personalized cyberpunk terminal with auto-install, interactive commands, and JARVIS-style animations

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)
![License](https://img.shields.io/badge/License-GPLv3-blue.svg)

## 🎯 What is Nextral?

Nextral is a futuristic terminal interface that transforms your command line into a cinematic experience. Think Tony Stark's JARVIS meets a cyberpunk hacker terminal.

### ✨ Key Features:

- **AUTO-INSTALL** - Automatically installs all dependencies
- **PERSONALIZED** - Greets you by name and customizes the interface
- **NEVER CRASHES** - Robust error handling and dependency management
- **GORGEOUS ANIMATIONS** - Matrix rain, glitch effects, pulsing indicators, scanlines
- **JARVIS-STYLE** - Animated scanners, rotating indicators, dynamic status
- **FULLY INTERACTIVE** - Query system stats, launch apps, manage processes
- **PRODUCTION-READY** - Fixed all markup errors, stable and reliable

## 🚀 Quick Start

### Option 1: One-Click Launch (Recommended!)

1. **Just double-click `Nextral.bat`**
2. First run auto-installs everything (~30 seconds)
3. Watch the cinematic boot sequence
4. Enjoy your personalized Nextral terminal!

**That's it!** The launcher automatically:
- Checks for Python ✓
- Installs missing packages ✓
- Detects your username ✓
- Launches the full system ✓

### Option 2: Manual Python Run

```bash
# Run the launcher (it will auto-install dependencies)
python launcher.py

# OR install manually first
pip install rich textual psutil pyfiglet
python launcher.py
```

### Option 3: Build Standalone .exe

```bash
# Easy way - double-click build.bat

# Manual way
pip install pyinstaller
pyinstaller nextral.spec

# Your .exe is in dist/Nextral.exe
```

## 🎮 How to Use

### Boot Sequence (Automatic)
When you launch Nextral, you'll see:
1. **Matrix Rain** - Digital waterfall effect
2. **Glitch Animation** - Cyberpunk aesthetic
3. **Logo Display** - ASCII art with pulsing effects
4. **Security Checks** - Multi-stage biometric verification
5. **Personalized Greeting** - "Welcome back, [Your Name]"
6. **System Scan** - Kernel, drivers, network validation
7. **Initialization** - 12 animated progress bars
8. **Ready Message** - System armed and operational

### Main HUD Interface
The interface shows 8 live panels:

1. **System Core** - CPU/RAM/Disk with animated bars
2. **Network Probe** - Upload/download speeds with arrows
3. **Defense Matrix** - Threat detection with radar scanner
4. **Process Monitor** - Top processes with CPU bars
5. **System Info** - Your personalized system details
6. **App Launcher** - Quick launch guide
7. **Command Interface** - Available commands
8. **Output Log** - Command results (personalized)

### Using Commands

Type in the **bottom input field** (yellow border):

```
USERNAME@NEXTRAL:~$ status
```

**Example Commands:**
```
status          → Full system performance report
processes       → Top 5 CPU-consuming processes  
network         → Network bandwidth statistics
disk            → Disk usage across all drives
memory          → Detailed RAM analysis
uptime          → System uptime information
scan            → Security threat scan
launch chrome   → Open Google Chrome
launch calc     → Open Calculator
kill 1234       → Terminate process with PID 1234
clear           → Clear output log
help            → Show all commands
```

### Keyboard Shortcuts
- `Q` - Quit application
- `D` - Toggle dark mode  
- `R` - Refresh all panels
- `C` - Clear output log
- `Ctrl+C` - Emergency exit

## 🎨 Personalization

Nextral automatically personalizes for you:

- **Boot Sequence** - "Welcome back, [Your Name]"
- **HUD Title** - Shows your username
- **Command Prompt** - `[YOUR NAME]@NEXTRAL:~$`
- **Status Bar** - Displays your user info
- **System Info Panel** - Shows your name and system

It detects your Windows username automatically!

## 📁 Project Structure

```
nextral_terminal/
│
├── launcher.py          # Smart launcher with auto-install
├── boot.py             # Cinematic boot with personalization
├── nextral.py          # Interactive HUD with full features
├── requirements.txt    # Python dependencies
├── nextral.spec        # PyInstaller config
├── Nextral.bat         # One-click launcher
├── build.bat           # Build .exe script
└── README.md          # This file
```

## 🌟 Animations & Effects

### Boot Sequence
- Matrix rain intro
- Glitch text effects
- Typing animations
- Progress bars with icons
- Pulsing text
- Personalized greetings
- Multi-stage verification

### Main HUD
- Rotating spinners (◐◓◑◒◢◣◤◥●◉○)
- Animated bars (█▓░)
- Pulsing indicators
- Dynamic arrows (▲▲▲▼▼▼)
- Color-coded warnings
- Radar-style scanners
- Speed indicators

## 📊 Available Commands

### System Queries
| Command | Description |
|---------|-------------|
| `status` | Full performance report |
| `processes` | Top CPU processes |
| `network` | Network statistics |
| `disk` | Disk usage all drives |
| `memory` | RAM analysis |
| `uptime` | System uptime |
| `scan` | Security scan |

### Application Control
| Command | Description |
|---------|-------------|
| `launch chrome` | Open Chrome |
| `launch firefox` | Open Firefox |
| `launch edge` | Open Edge |
| `launch notepad` | Open Notepad |
| `launch calc` | Open Calculator |
| `launch code` | Open VS Code |
| `launch cmd` | Open Command Prompt |
| `launch powershell` | Open PowerShell |
| `launch explorer` | Open File Explorer |
| `launch taskmgr` | Open Task Manager |
| `kill <pid>` | Terminate process |

### System
| Command | Description |
|---------|-------------|
| `help` | Show all commands |
| `clear` | Clear output log |

## 🔧 Troubleshooting

### "Python is not installed"
1. Download from https://python.org/downloads/
2. **CRITICAL**: Check "Add Python to PATH"
3. Restart computer
4. Run Nextral.bat again

### "ModuleNotFoundError"
**This shouldn't happen!** The launcher auto-installs.

But if it does:
```bash
pip install rich textual psutil pyfiglet
```

### Dependencies won't install
```bash
# Try with --user flag
pip install --user rich textual psutil pyfiglet
```

### Commands not working
- Type in the **BOTTOM input field** (yellow border)
- Press Enter after typing
- Commands are case-insensitive

### .exe build fails
- Update PyInstaller: `pip install --upgrade pyinstaller`
- Run build.bat as administrator
- Check antivirus isn't blocking

### .exe won't run
- Windows Defender may flag it (false positive)
- Add to exclusions
- Or run from the source with Python

## 💡 Customization

### Change Update Speeds
Edit `nextral.py`:
```python
self.set_interval(0.5, self.update_stats)  # Change 0.5 to your preference
```

### Add Custom Apps
Edit the `cmd_launch` method:
```python
apps = {
    'chrome': 'chrome',
    'myapp': 'path/to/myapp.exe',  # Add yours
}
```

### Modify Colors
Edit CSS in `nextral.py`:
```python
Static {
    border: solid cyan;  # Change to: red, green, magenta, etc.
}
```

### Add Custom Commands
Add to the `NEXTRAL` class:
```python
def cmd_mycommand(self, log):
    log.write("Your custom output!")
```

## 🎨 Terminal Styling

For the best experience:

**Windows Terminal Settings:**
1. Right-click title bar → Settings
2. **Font**: Cascadia Code, Fira Code, or JetBrains Mono
3. **Color Scheme**: Campbell, One Half Dark, or Tango Dark
4. **Background**: Black (#000000)
5. **Opacity**: 80-85%
6. **Cursor**: Filled box or vintage

## 🚀 Advanced Usage

### Auto-Launch on Startup
1. Press `Win+R`
2. Type: `shell:startup`
3. Create shortcut to `Nextral.bat`
4. Nextral runs on Windows login!

### Windows Terminal Profile
1. Open Windows Terminal settings
2. Add new profile
3. Command line: `python C:\path\to\launcher.py`
4. Set as default profile

## 📊 System Requirements

- **OS**: Windows 10/11
- **Python**: 3.8 or higher
- **RAM**: 50MB for app
- **Storage**: 100MB for dependencies
- **Terminal**: Windows Terminal (recommended)

## 🏆 Tips & Tricks

1. **Fullscreen** - Press F11 in Windows Terminal
2. **Dark Mode** - Press `D` to toggle
3. **Monitor Processes** - Use `processes` to find memory hogs
4. **Quick Launch** - Set up for apps you use frequently
5. **Network Monitoring** - Watch for unexpected bandwidth spikes
6. **Process Management** - Use `kill` for unresponsive apps

## 🙏 Credits

Built with amazing tools:
- [Rich](https://github.com/Textualize/rich) - Terminal formatting
- [Textual](https://github.com/Textualize/textual) - TUI framework
- [psutil](https://github.com/giampaolo/psutil) - System monitoring
- [PyFiglet](https://github.com/pwaller/pyfiglet) - ASCII art

## 📝 License

GNU General Public License v3.0 - Free to use, modify, and distribute

---

**⚡ NEXTRAL - Neural Extension Terminal & Response Array Layer ⚡**

*System armed and monitoring. Advanced neural interface online.*

**Made with ❤️ for cyberpunk enthusiasts and terminal power users**

*"The future of terminal interfaces is here."*
