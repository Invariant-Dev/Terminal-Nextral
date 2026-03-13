# 🚀 QUICKSTART - Nextral Terminal

## Fastest Way to Run (10 seconds)

### Windows Users - **JUST DO THIS:**

1. **Double-click `Nextral.bat`**
2. Wait for auto-install (first time only, ~30 seconds)
3. Enjoy! 🎉

**That's literally it.** The launcher:
- Checks for Python ✓
- Installs dependencies automatically ✓
- Detects your username ✓
- Launches Nextral ✓

---

## Want a Standalone .exe for Windows? (2 minutes)

1. **Double-click `build.bat`**
2. Wait 2-3 minutes for build
3. **Double-click `dist\Nextral.exe`**
4. Share it anywhere - no Python needed!

## Want a Linux Executable? (2 minutes)

1. **Ensure Docker Desktop is running**
2. **Double-click `build_linux_docker.bat`**
3. Wait for the build (it runs inside a Linux container)
4. Find your Linux binaries in the `dist` folder: `dist/Nextral` and `dist/Nextral-Setup`

---

## First Time Setup (if needed)

### If You Don't Have Python:

1. Go to https://python.org/downloads/
2. Click "Download Python"
3. Run installer
4. ✅ **CRITICAL**: Check "Add Python to PATH"
5. Click "Install Now"
6. Restart computer
7. Double-click `Nextral.bat`

### If Auto-Install Fails:

```bash
# Manual install (rare)
pip install rich textual psutil pyfiglet

# Then run
python launcher.py
```

---

## 🎮 Using Nextral

### After Boot Sequence:

The interface has **8 panels** and a **command input at the bottom**.

### Try These Commands:

Type in the **yellow-bordered box at bottom**, then press Enter:

```
status              # See system performance
processes           # Top CPU processes  
launch chrome       # Open Google Chrome
launch calc         # Open Calculator
network            # Network stats
memory             # RAM analysis
scan               # Security scan
help               # All commands
```

### Quick Reference:

**Launch Apps:**
- `launch chrome` / `firefox` / `edge`
- `launch notepad` / `calc` / `code`
- `launch cmd` / `powershell` / `explorer`
- `launch taskmgr` / `mspaint`

**System Queries:**
- `status` - Performance report
- `processes` - Top processes
- `network` - Bandwidth
- `disk` - Drive space
- `memory` - RAM details
- `uptime` - How long running

**Process Control:**
- `kill 1234` - Kill process with PID 1234

**Keyboard Shortcuts:**
- `Q` - Quit
- `D` - Dark mode
- `R` - Refresh
- `C` - Clear log

---

## 🔧 Troubleshooting

### Commands Not Working?
- Type in the **BOTTOM box** (yellow border)
- Press **Enter** after typing
- Commands are case-insensitive

### "Python not found"?
- Install Python from python.org
- **Check "Add to PATH"** during install
- Restart computer

### Dependencies Won't Install?
```bash
# Run this manually:
pip install rich textual psutil pyfiglet
```

### Markup Error?
**FIXED!** The latest version has all markup errors corrected.

---

## 🎨 Make It Look Amazing

**Windows Terminal (Recommended):**
1. Right-click title bar → Settings
2. Font: Cascadia Code or Fira Code
3. Color: Campbell or One Half Dark
4. Opacity: 80-85%
5. Fullscreen: Press F11

**Result:** Full cyberpunk immersion! 🔥

---

## 💡 Pro Tips

1. **Fullscreen** - Press F11 for maximum cool factor
2. **Quick Launch** - Add your favorite apps to launcher
3. **Process Monitor** - Use `processes` to find what's slowing you down
4. **Startup** - Put shortcut in `shell:startup` folder
5. **Network Check** - Monitor unexpected data usage

---

## 📦 What You Get

✓ Personalized boot sequence with your name  
✓ Real-time system monitoring  
✓ Interactive command system  
✓ App launcher  
✓ Process management  
✓ Security scanning  
✓ Network monitoring  
✓ JARVIS-style animations  
✓ **NO MARKUP ERRORS** - Fully stable!

---

## 🎯 Next Steps

1. **Explore Commands** - Type `help` to see all options
2. **Customize** - Edit nextral.py to add your apps
3. **Build .exe** - Share with friends
4. **Set as Default** - Make it your go-to terminal

---

**🎉 You're all set! Welcome to Nextral, agent.**

*For detailed documentation, see README.md*

**Remember: Type commands in the YELLOW box at the bottom!**

---

**⚡ NEXTRAL - Neural Extension Terminal & Response Array Layer ⚡**
