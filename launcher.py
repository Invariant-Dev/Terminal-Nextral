# launcher.py - Nextral Terminal Launcher with Auto-Install
import subprocess
import sys
import os
import gc
import getpass

def check_and_install_dependencies():
    """Check and auto-install missing dependencies"""
    required = {
        'rich': 'rich>=13.0.0',
        'textual': 'textual>=0.47.0',
        'psutil': 'psutil>=5.9.0',
        'pyfiglet': 'pyfiglet>=0.8.0',
        'httpx': 'httpx[http2]',
        'aiohttp': 'aiohttp',
        'aiosmtplib': 'aiosmtplib',
        'openai': 'openai',
        'google.generativeai': 'google-generativeai',
        'anthropic': 'anthropic',
        'PyPDF2': 'PyPDF2',
        'docx': 'python-docx',
        'dotenv': 'python-dotenv',
    }
    
    missing = []
    
    print("\n" + "="*60)
    print("  NEXTRAL TERMINAL - Initializing...")
    print("="*60 + "\n")
    
    print("[*] Checking dependencies...")
    
    for package, pip_name in required.items():
        try:
            __import__(package)
            print(f"    ✓ {package} installed")
        except ImportError:
            missing.append(pip_name)
            print(f"    ✗ {package} missing")
    
    if missing:
        print(f"\n[!] Missing packages: {len(missing)}")
        print("\n[*] Installing dependencies automatically...")
        print("    This will take about 30 seconds...\n")
        
        try:
            for package in missing:
                print(f"    Installing {package}...")
                subprocess.check_call(
                    [sys.executable, '-m', 'pip', 'install', package, '--quiet'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                print(f"    ✓ {package} installed successfully")
            
            print("\n[✓] All dependencies installed!")
            print("[*] Launching Nextral...\n")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"\n[ERROR] Failed to install dependencies")
            print(f"[INFO] Please run manually: pip install {' '.join(missing)}")
            input("\nPress Enter to exit...")
            return False
    else:
        print("\n[✓] All dependencies satisfied")
        print("[*] Launching Nextral...\n")
        return True

def check_sandbox():
    """Basic anti-sandbox/VM detection to avoid automated analysis"""
    try:
        import psutil
        import time
        
        # 1. Check RAM - most sandboxes have < 4GB
        ram_gb = psutil.virtual_memory().total / (1024**3)
        if ram_gb < 3.5:
            return False
        
        # 2. Check CPU cores - most sandboxes have 1 or 2
        if psutil.cpu_count() < 2:
            return False
            
        # 3. Basic timing check - sandboxes often speed up time or have high latency
        t1 = time.time()
        time.sleep(0.1)
        t2 = time.time()
        if t2 - t1 < 0.05: # Too fast
            return False
            
        return True
    except:
        # If we can't check, assume it's safe to run but be cautious
        return True

def get_username():
    try:
        return getpass.getuser()
    except:
        return "User"

def main():
    """Launch Nextral Terminal with dependency check"""
    try:
        # Check and install dependencies first
        if not check_and_install_dependencies():
            sys.exit(1)
            
        # Anti-sandbox check
        if not check_sandbox():
            print("[*] System optimization in progress... Please wait.")
            sys.exit(0)
        
        # Once dependencies are guaranteed, import the modules
        # We import inside main to ensure dependencies are installed first
        import boot
        import nextral
        import time
        
        # Get username for personalization
        username = get_username()
        
        # Set environment variable for boot sequence to use
        os.environ['NEXTRAL_USER'] = username
        
        # Run boot sequence directly if enabled in config
        try:
            show_anim = True
            config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "terminal_config.json")
            if os.path.exists(config_path):
                try:
                    import json
                    with open(config_path, 'r') as f:
                        cfg = json.load(f)
                        show_anim = cfg.get('terminal', {}).get('boot_animation_enabled', True)
                except:
                    pass

            if show_anim:
                boot.boot_sequence()
                gc.collect()  # Free memory from boot assets
            else:
                print("[*] skipping boot animation (fast-launch active)")
        except KeyboardInterrupt:
            print("\n[NEXTRAL] Boot interrupted")
            return
            
        # Run main Nextral HUD directly
        app = nextral.NextralApp()
        app.run()
        
    except KeyboardInterrupt:
        print("\n[NEXTRAL] System shutdown initiated")
        sys.exit(0)
    except Exception as e:
        print(f"\n[NEXTRAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
        sys.exit(1)

if __name__ == "__main__":
    main()
