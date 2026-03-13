"""
Nextral AI Agent Backend — Multi-Provider + Skills Engine
Supports: Ollama (default/free), OpenAI, Gemini, Anthropic
Skills:   Email (IMAP/SMTP), File Analysis, Terminal Control, Tasks, Calendar
"""

import os
import sys
import json
import re
import asyncio
import subprocess
import imaplib
import email as email_lib
from email.message import EmailMessage
from email import policy
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

try:
    import aiohttp
except ImportError:
    aiohttp = None

try:
    import aiosmtplib
except ImportError:
    aiosmtplib = None

try:
    import openai
except ImportError:
    openai = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    import anthropic
except ImportError:
    anthropic = None

try:
    import PyPDF2
    PDF_OK = True
except ImportError:
    PDF_OK = False

try:
    from docx import Document as DocxDocument
    DOCX_OK = True
except ImportError:
    DOCX_OK = False

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

EXECUTOR = ThreadPoolExecutor(max_workers=4)
BASE_DIR = Path(__file__).parent
TASKS_FILE = BASE_DIR / "tasks.json"
CALENDAR_FILE = BASE_DIR / "calendar.json"
HISTORY_FILE = BASE_DIR / "agent_history.json"

# ============================================================================
# JSON HELPERS
# ============================================================================

def _load_json(filepath: Path) -> list:
    if not filepath.exists():
        return []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def _save_json(filepath: Path, data: list):
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except:
        pass

# ============================================================================
# AGENT BACKEND
# ============================================================================

class AgentBackend:
    """Full-featured AI Agent backend with skills"""

    PROVIDERS = ["Ollama", "OpenAI", "Gemini", "Anthropic"]

    SYSTEM_PROMPT = (
        "You are Nexus, the AI assistant embedded inside Nextral Terminal — "
        "a cybersecurity-themed hacker terminal. You are helpful, concise, and "
        "knowledgeable about programming, security, networking, and system administration. "
        "When the user asks you to run a command, respond ONLY with a JSON block like: "
        '{"action":"exec","cmd":"<command>"} — the terminal will handle execution. '
        "When the user asks you to compose and send an email, respond ONLY with a JSON block like: "
        '{"action":"email","to":"email@example.com","subject":"Subject Here","body":"Email message body"} — the terminal will show a confirmation. '
        "For everything else, answer in plain text."
    )

    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = str(BASE_DIR / "terminal_config.json")
        self.config_path = config_path
        self.config = {}
        self.load_config()
        self.conversation_history: List[Dict[str, str]] = []
        self.pending_command: Optional[str] = None  # For terminal control
        self.pending_email: Optional[Dict[str, str]] = None  # For email composition

    # ── CONFIG ──────────────────────────────────────────────────────────────

    def load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
            except:
                self.config = {}
        else:
            self.config = {}

        # Ensure AI section exists with defaults
        defaults = {
            "provider": "Ollama",
            "ollama_model": os.getenv("OLLAMA_MODEL", "gemma2:2b"),
            "openai_key": "",
            "openai_model": "gpt-3.5-turbo",
            "gemini_key": "",
            "gemini_model": "gemini-pro",
            "anthropic_key": "",
            "anthropic_model": "claude-3-haiku-20240307",
            "imap_host": os.getenv("IMAP_HOST", "imap.gmail.com"),
            "imap_user": os.getenv("IMAP_USER", ""),
            "imap_password": os.getenv("IMAP_PASSWORD", ""),
            "smtp_host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
            "smtp_port": int(os.getenv("SMTP_PORT", "587")),
            "smtp_user": os.getenv("SMTP_USER", ""),
            "smtp_password": os.getenv("SMTP_PASSWORD", ""),
        }

        if "ai" not in self.config:
            self.config["ai"] = defaults
            self.save_config()
        else:
            # Fill missing keys with defaults
            for k, v in defaults.items():
                if k not in self.config["ai"]:
                    self.config["ai"][k] = v
            self.save_config()

    def save_config(self):
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
        except:
            pass

    def get_setting(self, key: str, default: Any = "") -> Any:
        return self.config.get("ai", {}).get(key, default)

    def set_setting(self, key: str, value: Any):
        if "ai" not in self.config:
            self.config["ai"] = {}
        self.config["ai"][key] = value
        self.save_config()

    # ── AI GENERATION ───────────────────────────────────────────────────────

    async def generate_response(self, prompt: str) -> str:
        """Generate AI response using the configured provider"""
        provider = self.get_setting("provider", "Ollama")

        self.conversation_history.append({"role": "user", "content": prompt})

        try:
            if provider == "Ollama":
                response = await self._generate_ollama(prompt)
            elif provider == "OpenAI":
                response = await self._generate_openai(prompt)
            elif provider == "Gemini":
                response = await self._generate_gemini(prompt)
            elif provider == "Anthropic":
                response = await self._generate_anthropic(prompt)
            else:
                response = f"Unknown provider: {provider}"

            self.conversation_history.append({"role": "assistant", "content": response})

            # Check if AI wants to execute a command
            self.pending_command = self._extract_command(response)
            
            # Check if AI wants to send an email
            self.pending_email = self._extract_email(response)

            return response
        except Exception as e:
            error_msg = f"Error ({provider}): {str(e)}"
            self.conversation_history.append({"role": "assistant", "content": error_msg})
            return error_msg

    def _extract_command(self, response: str) -> Optional[str]:
        """Extract an exec command from AI response if present"""
        try:
            match = re.search(r'\{[^}]*"action"\s*:\s*"exec"[^}]*\}', response)
            if match:
                data = json.loads(match.group())
                if data.get("action") == "exec" and data.get("cmd"):
                    return data["cmd"]
        except:
            pass
        return None

    def _extract_email(self, response: str) -> Optional[Dict[str, str]]:
        """Extract an email composition from AI response if present"""
        try:
            match = re.search(r'\{[^}]*"action"\s*:\s*"email"[^}]*\}', response)
            if match:
                data = json.loads(match.group())
                if (data.get("action") == "email" and 
                    data.get("to") and 
                    data.get("subject") and 
                    data.get("body")):
                    return {
                        "to": data["to"],
                        "subject": data["subject"],
                        "body": data["body"]
                    }
        except:
            pass
        return None

    async def _generate_ollama(self, prompt: str) -> str:
        if not aiohttp:
            return "aiohttp not installed. Run: pip install aiohttp"

        model = self.get_setting("ollama_model", "gemma2:2b")
        
        # Get URLs from settings
        primary = self.get_setting("ollama_url_primary", "http://localhost:11434").rstrip("/")
        secondary = self.get_setting("ollama_url_secondary", "").rstrip("/")
        
        urls_to_try = []
        if primary: urls_to_try.append(primary)
        if secondary: urls_to_try.append(secondary)
        
        # Always fallback to default localhost if not already in list
        default_local = "http://localhost:11434"
        if default_local not in urls_to_try:
            urls_to_try.append(default_local)

        # Build messages payload
        messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
        for msg in self.conversation_history[-10:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        payload = {"model": model, "messages": messages, "stream": False}

        errors = []
        
        print(f"\n[Ollama] AI Request to models: {urls_to_try}")

        async with aiohttp.ClientSession() as session:
            for base_url in urls_to_try:
                base_url = base_url.rstrip("/")
                # Adjust endpoint based on user input or default to chat
                target_url = f"{base_url}/api/chat"
                
                print(f"[Ollama] Trying connection to: {target_url} ...")
                
                try:
                    async with session.post(target_url, json=payload, timeout=aiohttp.ClientTimeout(total=600)) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            
                            # Parse response - support multiple formats
                            content = None
                            
                            # 1. /api/chat format
                            if "message" in data and "content" in data["message"]:
                                content = data["message"]["content"]
                            
                            # 2. /api/generate format
                            elif "response" in data:
                                content = data["response"]
                                
                            # 3. Fallback extraction
                            if not content:
                                # Try to dump just the message part if it exists
                                content = data.get("message", data)
                                if isinstance(content, dict):
                                    content = content.get("content", str(content))
                                    
                            print(f"[Ollama] Success from {base_url}")
                            return str(content)
                        else:
                            text = await resp.text()
                            err_msg = f"{base_url}: HTTP {resp.status} - {text[:1000]}"
                            print(f"[Ollama] Fail: {err_msg}")
                            errors.append(err_msg)
                except Exception as e:
                    err_msg = f"{base_url}: Connection Failed - {repr(e)}"
                    print(f"[Ollama] Error: {err_msg}")
                    errors.append(err_msg)
                    # Continue to next URL

        return f"Ollama failed on all instances.\nErrors:\n" + "\n".join(errors)

    async def _generate_openai(self, prompt: str) -> str:
        if not openai:
            return "OpenAI SDK not installed. Run: pip install openai"
        api_key = self.get_setting("openai_key")
        if not api_key:
            return "OpenAI API Key not configured. Go to Settings tab."

        client = openai.AsyncOpenAI(api_key=api_key)
        model = self.get_setting("openai_model", "gpt-3.5-turbo")
        messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
        for msg in self.conversation_history[-10:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        try:
            resp = await client.chat.completions.create(model=model, messages=messages)
            return resp.choices[0].message.content
        except Exception as e:
            return f"OpenAI Error: {e}"

    async def _generate_gemini(self, prompt: str) -> str:
        if not genai:
            return "Google AI SDK not installed. Run: pip install google-generativeai"
        api_key = self.get_setting("gemini_key")
        if not api_key:
            return "Gemini API Key not configured. Go to Settings tab."
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(self.get_setting("gemini_model", "gemini-pro"))
        try:
            resp = await model.generate_content_async(prompt)
            return resp.text
        except Exception as e:
            return f"Gemini Error: {e}"

    async def _generate_anthropic(self, prompt: str) -> str:
        if not anthropic:
            return "Anthropic SDK not installed. Run: pip install anthropic"
        api_key = self.get_setting("anthropic_key")
        if not api_key:
            return "Anthropic API Key not configured. Go to Settings tab."
        client = anthropic.AsyncAnthropic(api_key=api_key)
        model = self.get_setting("anthropic_model", "claude-3-haiku-20240307")
        try:
            msg = await client.messages.create(
                model=model, max_tokens=2048,
                system=self.SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return msg.content[0].text
        except Exception as e:
            return f"Anthropic Error: {e}"

    # ── SKILL: EMAIL ────────────────────────────────────────────────────────

    def _get_imap_conn(self):
        host = self.get_setting("imap_host", "imap.gmail.com")
        user = self.get_setting("imap_user")
        pw = self.get_setting("imap_password")
        if not user or not pw:
            raise RuntimeError("Email credentials not configured. Go to Agent > Settings.")
        M = imaplib.IMAP4_SSL(host)
        M.login(user, pw)
        return M

    def fetch_emails_sync(self, limit: int = 15) -> List[Dict]:
        """Blocking IMAP fetch — runs in executor"""
        emails = []
        try:
            M = self._get_imap_conn()
            M.select('INBOX')
            typ, data = M.search(None, 'UNSEEN')
            if typ != 'OK' or not data[0]:
                M.close(); M.logout()
                return []

            msg_ids = data[0].split()
            msg_ids = msg_ids[-limit:]  # latest N

            for num in msg_ids:
                try:
                    typ2, data2 = M.fetch(num, '(RFC822)')
                    if typ2 != 'OK':
                        continue
                    for part in data2:
                        if isinstance(part, tuple):
                            msg = email_lib.message_from_bytes(part[1], policy=policy.default)
                            body = ""
                            if msg.is_multipart():
                                for p in msg.walk():
                                    if p.get_content_type() == 'text/plain':
                                        try:
                                            body = p.get_content(); break
                                        except: continue
                                if not body:
                                    for p in msg.walk():
                                        if p.get_content_type() == 'text/html':
                                            try:
                                                body = re.sub(r'<[^>]+>', '', p.get_content()); break
                                            except: continue
                            else:
                                try: body = msg.get_content()
                                except: body = str(msg.get_payload())

                            body = re.sub(r'\n{3,}', '\n\n', body.strip())
                            emails.append({
                                'id': num.decode() if isinstance(num, bytes) else str(num),
                                'from': msg.get('From', ''),
                                'subject': msg.get('Subject', '(No Subject)'),
                                'body': body,
                                'date': msg.get('Date', ''),
                            })
                            break
                except:
                    continue

            M.close(); M.logout()
        except Exception as e:
            return [{"error": str(e)}]
        return emails

    async def fetch_emails(self, limit: int = 15) -> List[Dict]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(EXECUTOR, self.fetch_emails_sync, limit)

    async def send_email(self, to: str, subject: str, body: str) -> str:
        if not aiosmtplib:
            return "aiosmtplib not installed. Run: pip install aiosmtplib"

        host = self.get_setting("smtp_host", "smtp.gmail.com")
        port = self.get_setting("smtp_port", 587)
        user = self.get_setting("smtp_user")
        pw = self.get_setting("smtp_password")

        if not user or not pw:
            return "SMTP credentials not configured. Go to Agent > Settings."

        msg = EmailMessage()
        msg['From'] = user
        msg['To'] = to
        msg['Subject'] = subject
        msg.set_content(body)

        try:
            await aiosmtplib.send(msg, hostname=host, port=port, start_tls=True,
                                  username=user, password=pw, timeout=30)
            # Log to history
            hist = _load_json(HISTORY_FILE)
            hist.append({'type': 'email_sent', 'to': to, 'subject': subject,
                         'ts': datetime.now().isoformat()})
            _save_json(HISTORY_FILE, hist)
            return f"Email sent to {to}"
        except Exception as e:
            return f"Send failed: {e}"

    async def summarize_emails(self, emails: List[Dict]) -> str:
        if not emails:
            return "No emails to summarize."
        texts = []
        for i, em in enumerate(emails[:10], 1):
            texts.append(f"Email {i}:\nFrom: {em.get('from','?')}\n"
                         f"Subject: {em.get('subject','?')}\n"
                         f"Body: {em.get('body','')[:300]}\n")
        prompt = ("Summarize these emails concisely. Provide:\n"
                  "1. Overall summary (2-3 sentences)\n"
                  "2. Key action items (bullets)\n\n"
                  f"EMAILS:\n{'---'.join(texts)}\n\nSUMMARY:")
        return await self.generate_response(prompt)

    # ── SKILL: FILE ANALYSIS ────────────────────────────────────────────────

    def read_file_smart(self, filepath: str) -> str:
        """Read file contents with format-aware handling"""
        p = Path(filepath)
        if not p.exists():
            return f"File not found: {filepath}"
        ext = p.suffix.lower()
        try:
            if ext == '.pdf':
                if not PDF_OK:
                    return "PyPDF2 not installed. Run: pip install PyPDF2"
                text = []
                with open(filepath, 'rb') as f:
                    pdf = PyPDF2.PdfReader(f)
                    for page in pdf.pages:
                        text.append(page.extract_text() or "")
                return "\n\n".join(text)
            elif ext in ('.docx', '.doc'):
                if not DOCX_OK:
                    return "python-docx not installed. Run: pip install python-docx"
                doc = DocxDocument(filepath)
                return "\n\n".join([p.text for p in doc.paragraphs if p.text.strip()])
            else:
                with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                    return f.read()
        except Exception as e:
            return f"Error reading file: {e}"

    async def analyze_file(self, filepath: str, question: str = "") -> str:
        content = self.read_file_smart(filepath)
        if content.startswith("Error") or content.startswith("File not found"):
            return content

        prompt = (f"Analyze this file:\n\nFILE: {Path(filepath).name}\n"
                  f"CONTENT:\n{content[:4000]}\n\n")
        if question:
            prompt += f"QUESTION: {question}\n\n"
        prompt += "ANALYSIS:"
        return await self.generate_response(prompt)

    # ── SKILL: TERMINAL CONTROL ─────────────────────────────────────────────

    async def execute_command(self, cmd: str, cwd: str = None) -> str:
        """Execute a shell command and return output"""
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                EXECUTOR,
                lambda: subprocess.run(
                    cmd, shell=True, capture_output=True, text=True,
                    timeout=30, cwd=cwd or str(BASE_DIR)
                )
            )
            output = result.stdout.strip()
            if result.stderr.strip():
                output += f"\n[STDERR] {result.stderr.strip()}"
            if result.returncode != 0:
                output += f"\n[Exit Code: {result.returncode}]"
            return output or "(No output)"
        except subprocess.TimeoutExpired:
            return "Command timed out (30s limit)."
        except Exception as e:
            return f"Execution error: {e}"

    # ── SKILL: TASKS ────────────────────────────────────────────────────────

    def get_tasks(self, show_completed: bool = False) -> List[Dict]:
        tasks = _load_json(TASKS_FILE)
        if not show_completed:
            tasks = [t for t in tasks if not t.get('completed')]
        return tasks

    def add_task(self, title: str, desc: str = "", due: str = "") -> Dict:
        tasks = _load_json(TASKS_FILE)
        task = {
            'id': (max([t['id'] for t in tasks], default=0) + 1),
            'title': title, 'desc': desc, 'due': due,
            'completed': False,
            'created': datetime.now().isoformat()
        }
        tasks.append(task)
        _save_json(TASKS_FILE, tasks)
        return task

    def complete_task(self, task_id: int) -> bool:
        tasks = _load_json(TASKS_FILE)
        for t in tasks:
            if t.get('id') == task_id:
                t['completed'] = True
                t['completed_at'] = datetime.now().isoformat()
                _save_json(TASKS_FILE, tasks)
                return True
        return False

    def delete_task(self, task_id: int) -> bool:
        tasks = _load_json(TASKS_FILE)
        filtered = [t for t in tasks if t.get('id') != task_id]
        if len(filtered) < len(tasks):
            _save_json(TASKS_FILE, filtered)
            return True
        return False

    # ── SKILL: CALENDAR ─────────────────────────────────────────────────────

    def get_events(self, days: int = 7) -> List[Dict]:
        cal = _load_json(CALENDAR_FILE)
        now = datetime.now()
        end = now + timedelta(days=days)
        upcoming = []
        for event in cal:
            try:
                t = datetime.fromisoformat(event['start'])
                if now <= t <= end:
                    upcoming.append(event)
            except:
                continue
        return sorted(upcoming, key=lambda x: x.get('start', ''))

    def add_event(self, title: str, start: str, duration: int = 60, desc: str = "") -> Dict:
        cal = _load_json(CALENDAR_FILE)
        event = {
            'id': (max([e['id'] for e in cal], default=0) + 1),
            'title': title, 'start': start,
            'duration': duration, 'desc': desc,
            'created': datetime.now().isoformat()
        }
        cal.append(event)
        _save_json(CALENDAR_FILE, cal)
        return event

    # ── SKILL: DAILY BRIEF ──────────────────────────────────────────────────

    async def daily_brief(self) -> str:
        """Generate a daily briefing combining emails, tasks, and calendar"""
        lines = ["═══ DAILY BRIEF ═══\n"]

        # Emails
        try:
            emails = await self.fetch_emails(5)
            if emails and not emails[0].get("error"):
                lines.append(f"📧 INBOX: {len(emails)} unread email(s)")
                for em in emails[:3]:
                    lines.append(f"   • {em.get('from','?')[:30]}: {em.get('subject','?')}")
            else:
                lines.append("📧 INBOX: Unable to fetch or no unread")
        except:
            lines.append("📧 INBOX: Not configured")

        lines.append("")

        # Tasks
        tasks = self.get_tasks()
        if tasks:
            lines.append(f"📋 TASKS: {len(tasks)} pending")
            for t in tasks[:5]:
                due = f" (due: {t['due']})" if t.get('due') else ""
                lines.append(f"   • {t['title']}{due}")
        else:
            lines.append("📋 TASKS: All clear!")

        lines.append("")

        # Calendar
        events = self.get_events(1)
        if events:
            lines.append(f"📅 TODAY: {len(events)} event(s)")
            for e in events:
                lines.append(f"   • {e['title']} at {e['start']}")
        else:
            lines.append("📅 TODAY: No events")

        return "\n".join(lines)

    # ── SKILL: WHATSAPP ─────────────────────────────────────────────────────

    _wa_process = None
    _wa_reader_task = None
    _wa_event_queue = None
    _wa_response_queue = None
    _wa_ready = False
    _wa_qr_text = None

    async def whatsapp_start(self) -> str:
        """Start the WhatsApp bridge Node.js process"""
        if self._wa_process and self._wa_process.returncode is None:
            return "WhatsApp bridge is already running."

        bridge_path = BASE_DIR / "whatsapp_bridge.js"
        if not bridge_path.exists():
            return "whatsapp_bridge.js not found."

        # Check node is available
        try:
            subprocess.run(["node", "--version"], capture_output=True, timeout=5)
        except:
            return "Node.js not found. Install it from https://nodejs.org/"

        # Check if whatsapp-web.js is installed
        node_modules = BASE_DIR / "node_modules" / "whatsapp-web.js"
        if not node_modules.exists():
            return "whatsapp-web.js not installed. Run: npm install whatsapp-web.js qrcode-terminal"

        self._wa_event_queue = asyncio.Queue()
        self._wa_response_queue = asyncio.Queue()

        try:
            self._wa_process = await asyncio.create_subprocess_exec(
                "node", str(bridge_path),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(BASE_DIR)
            )
        except Exception as e:
            return f"Failed to launch WhatsApp bridge: {e}"

        # Start reader tasks
        self._wa_reader_task = asyncio.create_task(self._wa_read_loop())
        self._wa_stderr_task = asyncio.create_task(self._wa_stderr_loop())
        
        return "WhatsApp bridge starting... Scan QR code when prompted."

    async def _wa_read_loop(self):
        """Read JSON lines from the bridge stdout"""
        try:
            while self._wa_process and self._wa_process.returncode is None:
                line = await self._wa_process.stdout.readline()
                if not line:
                    break
                try:
                    data = json.loads(line.decode().strip())
                    if "event" in data:
                        # Events: qr, ready, authenticated, message, loading, error, state_change
                        if data["event"] == "ready":
                            self._wa_ready = True
                        elif data["event"] == "qr":
                            self._wa_qr_text = data.get("qrText", "")
                        elif data["event"] == "disconnected":
                            self._wa_ready = False
                        await self._wa_event_queue.put(data)
                    else:
                        # Response to a command
                        await self._wa_response_queue.put(data)
                except Exception as e:
                    # Log parsing error
                    error_event = {"event": "error", "message": f"Bridge output parse error: {e}", "raw": line.decode()}
                    await self._wa_event_queue.put(error_event)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            await self._wa_event_queue.put({"event": "error", "message": f"Read loop fatal error: {e}"})

    async def _wa_stderr_loop(self):
        """Read debug logs from the bridge stderr"""
        try:
            while self._wa_process and self._wa_process.returncode is None:
                line = await self._wa_process.stderr.readline()
                if not line:
                    break
                # Log stderr line (could be written to a file or internal debug log)
                debug_line = line.decode().strip()
                if debug_line:
                    # For now we just put it into the event queue as a debug type
                    await self._wa_event_queue.put({"event": "debug", "message": debug_line})
        except asyncio.CancelledError:
            pass
        except:
            pass

    async def _wa_send_command(self, cmd: dict, timeout: float = 30) -> dict:
        """Send a command to the bridge and wait for response"""
        if not self._wa_process or self._wa_process.returncode is not None:
            return {"ok": False, "error": "WhatsApp bridge not running. Use /wa start"}

        line = json.dumps(cmd) + "\n"
        self._wa_process.stdin.write(line.encode())
        await self._wa_process.stdin.drain()

        try:
            response = await asyncio.wait_for(self._wa_response_queue.get(), timeout=timeout)
            return response
        except asyncio.TimeoutError:
            return {"ok": False, "error": "Bridge timeout"}

    async def whatsapp_status(self) -> dict:
        return await self._wa_send_command({"action": "status"})

    async def whatsapp_get_chats(self, limit: int = 20) -> dict:
        return await self._wa_send_command({"action": "get_chats", "limit": limit})

    async def whatsapp_get_messages(self, chat_id: str, limit: int = 20) -> dict:
        return await self._wa_send_command({"action": "get_messages", "chatId": chat_id, "limit": limit})

    async def whatsapp_send_message(self, chat_id: str, body: str) -> dict:
        return await self._wa_send_command({"action": "send_message", "chatId": chat_id, "body": body})

    async def whatsapp_search_contacts(self, query: str) -> dict:
        return await self._wa_send_command({"action": "search_contacts", "query": query})

    async def whatsapp_get_qr(self) -> str:
        """Get QR code text if available"""
        if self._wa_qr_text:
            return self._wa_qr_text
        # Drain event queue looking for QR
        try:
            while not self._wa_event_queue.empty():
                event = await asyncio.wait_for(self._wa_event_queue.get(), 0.1)
                if event.get("event") == "qr":
                    self._wa_qr_text = event.get("qrText", "")
                    return self._wa_qr_text
        except:
            pass
        return "No QR code available yet. Wait a moment and try again."

    async def whatsapp_drain_events(self) -> List[dict]:
        """Drain and return all pending events"""
        events = []
        while not self._wa_event_queue.empty():
            try:
                events.append(await asyncio.wait_for(self._wa_event_queue.get(), 0.1))
            except:
                break
        return events

    async def whatsapp_stop(self) -> str:
        if self._wa_process and self._wa_process.returncode is None:
            try:
                await self._wa_send_command({"action": "shutdown"}, timeout=5)
            except:
                pass
            
            if self._wa_reader_task:
                self._wa_reader_task.cancel()
            if self._wa_stderr_task:
                self._wa_stderr_task.cancel()
                
            try:
                self._wa_process.terminate()
                await asyncio.wait_for(self._wa_process.wait(), timeout=5)
            except:
                if self._wa_process:
                    self._wa_process.kill()
            
            self._wa_process = None
            self._wa_ready = False
            self._wa_qr_text = None
            return "WhatsApp bridge stopped."
        return "WhatsApp bridge is not running."

    async def whatsapp_summarize_chat(self, chat_id: str) -> str:
        """Fetch recent messages from a chat and summarize with AI"""
        result = await self.whatsapp_get_messages(chat_id, limit=30)
        if not result.get("ok"):
            return f"Error: {result.get('error', 'Unknown')}"

        messages = result.get("messages", [])
        if not messages:
            return "No messages to summarize."

        msg_texts = []
        for m in messages[-30:]:
            sender = "You" if m.get("fromMe") else m.get("from", "?")
            body = m.get("body", "")
            if body:
                msg_texts.append(f"{sender}: {body[:200]}")

        prompt = ("Summarize this WhatsApp conversation concisely. "
                  "Highlight key topics, action items, and important info.\n\n"
                  f"MESSAGES:\n" + "\n".join(msg_texts) + "\n\nSUMMARY:")
        return await self.generate_response(prompt)

    # ── SKILL: OSINT RECON ──────────────────────────────────────────────────

    async def osint_recon(self, target: str) -> Dict[str, Any]:
        """Perform OSINT reconnaissance on a domain or IP address"""
        import socket
        results = {"target": target, "dns": {}, "whois": {}, "ports": [], "geo": {}, "headers": {}}

        # 1. DNS resolution
        try:
            ip_list = socket.getaddrinfo(target, None, socket.AF_INET)
            ips = list(set(addr[4][0] for addr in ip_list))
            results["dns"]["ips"] = ips
            try:
                hostname = socket.getfqdn(target)
                results["dns"]["fqdn"] = hostname
            except:
                pass
            # Reverse DNS
            for ip in ips[:3]:
                try:
                    rev = socket.gethostbyaddr(ip)
                    results["dns"].setdefault("reverse", []).append({"ip": ip, "hostname": rev[0]})
                except:
                    pass
        except Exception as e:
            results["dns"]["error"] = str(e)

        # 2. WHOIS lookup
        try:
            proc = await asyncio.create_subprocess_exec(
                "powershell", "-Command", f"nslookup {target}",
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=10)
            results["whois"]["nslookup"] = stdout.decode("utf-8", errors="ignore").strip()
        except Exception as e:
            results["whois"]["error"] = str(e)

        # 3. Quick port scan (common ports)
        common_ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 993, 995, 3306, 3389, 5432, 8080, 8443]
        scan_target = results["dns"].get("ips", [target])[0] if results["dns"].get("ips") else target
        open_ports = []
        
        async def check_port(port):
            try:
                _, writer = await asyncio.wait_for(asyncio.open_connection(scan_target, port), timeout=1.0)
                writer.close()
                await writer.wait_closed()
                return port
            except:
                return None

        port_results = await asyncio.gather(*[check_port(p) for p in common_ports])
        open_ports = [p for p in port_results if p is not None]
        results["ports"] = open_ports

        # 4. HTTP headers (if 80 or 443 is open)
        if aiohttp and (80 in open_ports or 443 in open_ports):
            scheme = "https" if 443 in open_ports else "http"
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.head(f"{scheme}://{target}", timeout=aiohttp.ClientTimeout(total=5), ssl=False) as resp:
                        results["headers"] = dict(resp.headers)
                        results["headers"]["status_code"] = resp.status
            except:
                pass

        # 5. Shodan API (if key configured)
        shodan_key = self.get_setting("shodan_api_key", "")
        if shodan_key and aiohttp:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"https://api.shodan.io/shodan/host/{scan_target}?key={shodan_key}",
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as resp:
                        if resp.status == 200:
                            results["shodan"] = await resp.json()
            except:
                pass

        return results

    async def osint_recon_with_ai(self, target: str) -> str:
        """Full OSINT recon with AI-generated analysis report"""
        results = await self.osint_recon(target)

        report_lines = [f"Target: {target}"]
        if results["dns"].get("ips"):
            report_lines.append(f"IPs: {', '.join(results['dns']['ips'])}")
        if results["dns"].get("reverse"):
            for r in results["dns"]["reverse"]:
                report_lines.append(f"Reverse DNS: {r['ip']} -> {r['hostname']}")
        if results["ports"]:
            svc_map = {21:"FTP",22:"SSH",23:"Telnet",25:"SMTP",53:"DNS",80:"HTTP",
                       110:"POP3",143:"IMAP",443:"HTTPS",445:"SMB",993:"IMAPS",
                       995:"POP3S",3306:"MySQL",3389:"RDP",5432:"PostgreSQL",
                       8080:"HTTP-ALT",8443:"HTTPS-ALT"}
            for p in results["ports"]:
                report_lines.append(f"Open Port: {p} ({svc_map.get(p, 'Unknown')})")
        if results.get("headers"):
            for k in ["Server", "X-Powered-By", "Content-Security-Policy"]:
                if k in results["headers"]:
                    report_lines.append(f"Header {k}: {results['headers'][k]}")
        if results.get("whois", {}).get("nslookup"):
            report_lines.append(f"NSLookup:\n{results['whois']['nslookup']}")
        if results.get("shodan"):
            sd = results["shodan"]
            report_lines.append(f"Shodan OS: {sd.get('os', '?')}")
            report_lines.append(f"Shodan Org: {sd.get('org', '?')}")
            for v in sd.get("vulns", [])[:10]:
                report_lines.append(f"Shodan CVE: {v}")

        raw_data = "\n".join(report_lines)

        prompt = (
            "You are an expert cybersecurity analyst. Analyze this OSINT reconnaissance data and provide:\n"
            "1. A threat assessment (LOW/MEDIUM/HIGH/CRITICAL)\n"
            "2. Attack surface summary\n"
            "3. Notable findings and potential vulnerabilities\n"
            "4. Recommendations for further investigation\n\n"
            f"RECON DATA:\n{raw_data}\n\nANALYSIS:"
        )
        return await self.generate_response(prompt)

    async def osint_leak_check(self, query: str) -> str:
        """Use AI to discuss potential leak exposure for a given email/domain"""
        prompt = (
            "You are a cybersecurity OSINT analyst. The user wants to check if the following "
            "identifier has been involved in any known data breaches or leaks. Provide general "
            "guidance on how to check for leaks using legitimate services like HaveIBeenPwned, "
            "DeHashed, and IntelX. Do NOT fabricate breach data.\n\n"
            f"QUERY: {query}\n\n"
            "Provide:\n1. Which legitimate services to check\n"
            "2. General risk assessment based on the type of identifier\n"
            "3. Steps to protect the account if compromised\n\nRESPONSE:"
        )
        return await self.generate_response(prompt)

    # ── SKILL: VULNERABILITY X-RAY ──────────────────────────────────────────

    async def xray_analyze_scan(self, scan_type: str, data: str) -> str:
        """AI-powered analysis of scan results (portscan, webscan, sniffer)"""
        prompt = (
            "You are an expert penetration tester. Analyze the following scan results and provide:\n"
            "1. Risk level for each finding (LOW/MEDIUM/HIGH/CRITICAL)\n"
            "2. Known CVEs that may apply to the identified services/versions\n"
            "3. Suggested exploitation paths (for educational/authorized testing only)\n"
            "4. Remediation recommendations\n\n"
            f"SCAN TYPE: {scan_type}\n"
            f"DATA:\n{data}\n\n"
            "ANALYSIS:"
        )
        return await self.generate_response(prompt)

    async def xray_audit_config(self, config_text: str, config_type: str = "unknown") -> str:
        """AI-powered security audit of a configuration file"""
        prompt = (
            f"You are a security auditor. Analyze this {config_type} configuration file for "
            "security misconfigurations and vulnerabilities. For each finding provide:\n"
            "1. Severity (LOW/MEDIUM/HIGH/CRITICAL)\n"
            "2. What's wrong and why it's dangerous\n"
            "3. The fix (show the corrected config line)\n\n"
            f"CONFIG ({config_type}):\n{config_text}\n\n"
            "AUDIT RESULTS:"
        )
        return await self.generate_response(prompt)

    # ── SKILL: MALWARE SANDBOX ──────────────────────────────────────────────

    # Heuristic patterns for static analysis
    _MALWARE_INDICATORS = {
        "registry_access": [
            r"reg\s+add", r"reg\s+delete", r"HKLM\\", r"HKCU\\",
            r"Set-ItemProperty.*Registry", r"New-ItemProperty",
            r"winreg", r"RegOpenKey", r"RegSetValue"
        ],
        "persistence": [
            r"\\Startup\\", r"\\Run\\", r"schtasks", r"at\s+\d+:\d+",
            r"crontab", r"systemctl\s+enable", r"/etc/init\.d",
            r"HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run"
        ],
        "network_c2": [
            r"socket\.connect", r"urllib\.request", r"requests\.get",
            r"requests\.post", r"http\.client", r"Invoke-WebRequest",
            r"curl\s+", r"wget\s+", r"nc\s+-", r"ncat\s+",
            r"reverse.shell", r"bind.shell"
        ],
        "credential_theft": [
            r"mimikatz", r"lsass", r"SAM\s+dump", r"hashdump",
            r"credential", r"password.*file", r"keylog",
            r"Get-Credential", r"ConvertTo-SecureString"
        ],
        "evasion": [
            r"base64.*decode", r"fromCharCode", r"-enc\s+", r"-EncodedCommand",
            r"iex\s*\(", r"Invoke-Expression", r"eval\s*\(",
            r"exec\s*\(", r"compile\s*\(", r"__import__"
        ],
        "file_ops": [
            r"Remove-Item.*-Recurse", r"del\s+/[sS]", r"rmdir.*\/[sS]",
            r"shutil\.rmtree", r"os\.remove", r"cipher\s+/w:",
            r"shred\s+", r"wipe"
        ],
        "privilege_escalation": [
            r"runas\s+/user", r"sudo\s+", r"chmod\s+[4267]",
            r"setuid", r"setgid", r"SeDebugPrivilege",
            r"AdjustTokenPrivileges", r"Enable-PSRemoting"
        ]
    }

    def malware_heuristic_scan(self, code: str) -> Dict[str, Any]:
        """Static heuristic analysis of code for malicious patterns"""
        findings = []
        severity_weights = {
            "registry_access": 3, "persistence": 4, "network_c2": 5,
            "credential_theft": 5, "evasion": 4, "file_ops": 3,
            "privilege_escalation": 5
        }

        for category, patterns in self._MALWARE_INDICATORS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, code, re.IGNORECASE)
                for match in matches:
                    # Get surrounding context (the line)
                    start = code.rfind('\n', 0, match.start()) + 1
                    end = code.find('\n', match.end())
                    if end == -1:
                        end = len(code)
                    line = code[start:end].strip()
                    line_num = code[:match.start()].count('\n') + 1

                    findings.append({
                        "category": category,
                        "pattern": pattern,
                        "match": match.group(),
                        "line": line_num,
                        "context": line[:120],
                        "severity": severity_weights.get(category, 2)
                    })

        # Calculate overall threat score
        if not findings:
            threat_level = "CLEAN"
            score = 0
        else:
            score = sum(f["severity"] for f in findings)
            if score >= 15:
                threat_level = "CRITICAL"
            elif score >= 10:
                threat_level = "HIGH"
            elif score >= 5:
                threat_level = "MEDIUM"
            else:
                threat_level = "LOW"

        # Deduplicate by category+line
        seen = set()
        unique_findings = []
        for f in findings:
            key = (f["category"], f["line"])
            if key not in seen:
                seen.add(key)
                unique_findings.append(f)

        return {
            "threat_level": threat_level,
            "score": score,
            "findings": unique_findings[:30],  # Cap at 30
            "total_findings": len(unique_findings),
            "categories_hit": list(set(f["category"] for f in unique_findings))
        }

    async def malware_analyze(self, code: str) -> str:
        """Full malware analysis: heuristic scan + AI assessment"""
        # Step 1: Static heuristic scan
        heuristics = self.malware_heuristic_scan(code)

        # Build heuristic report
        report_lines = [
            f"HEURISTIC RESULT: {heuristics['threat_level']} (Score: {heuristics['score']})",
            f"Categories: {', '.join(heuristics['categories_hit']) or 'None'}",
            ""
        ]
        for f in heuristics["findings"][:15]:
            report_lines.append(
                f"[{f['category'].upper()}] Line {f['line']}: {f['context']}"
            )

        heuristic_report = "\n".join(report_lines)

        # Step 2: AI deep analysis
        prompt = (
            "You are an expert malware analyst. A script has been submitted for analysis. "
            "Below are the heuristic scan findings and the code itself. Provide:\n"
            "1. VERDICT: MALICIOUS / SUSPICIOUS / BENIGN\n"
            "2. Summary of what the code does\n"
            "3. Explanation of each suspicious pattern found\n"
            "4. Potential impact if executed\n"
            "5. IOCs (Indicators of Compromise) if any\n\n"
            f"HEURISTIC REPORT:\n{heuristic_report}\n\n"
            f"CODE (first 3000 chars):\n{code[:3000]}\n\n"
            "MALWARE ANALYSIS REPORT:"
        )
        return await self.generate_response(prompt)

    async def malware_deobfuscate(self, code: str) -> str:
        """AI-driven code de-obfuscation"""
        prompt = (
            "You are an expert reverse engineer and malware analyst. "
            "The following code appears to be obfuscated. Please:\n"
            "1. Identify the obfuscation technique(s) used\n"
            "2. Provide the fully de-obfuscated, human-readable version\n"
            "3. Explain what the de-obfuscated code actually does\n"
            "4. Identify any malicious intent\n\n"
            f"OBFUSCATED CODE:\n{code[:4000]}\n\n"
            "DE-OBFUSCATION REPORT:"
        )
        return await self.generate_response(prompt)

    # ── SKILL: PROXY CHAIN ──────────────────────────────────────────────────

    async def test_proxy_chain(self, proxies: List[str]) -> List[Dict[str, Any]]:
        """Test latency and availability of a chain of proxies
        Each proxy string format: host:port or socks5://host:port
        """
        results = []
        for proxy_str in proxies:
            # Parse proxy
            host, port_str = proxy_str.replace("socks5://", "").replace("http://", "").rsplit(":", 1)
            port = int(port_str)

            result = {"proxy": proxy_str, "host": host, "port": port, "status": "UNKNOWN", "latency_ms": None, "geo": None}

            # Test connection and latency
            start_time = asyncio.get_event_loop().time()
            try:
                _, writer = await asyncio.wait_for(
                    asyncio.open_connection(host, port), timeout=3.0
                )
                latency = (asyncio.get_event_loop().time() - start_time) * 1000
                writer.close()
                await writer.wait_closed()
                result["status"] = "ONLINE"
                result["latency_ms"] = round(latency, 1)
            except asyncio.TimeoutError:
                result["status"] = "TIMEOUT"
            except ConnectionRefusedError:
                result["status"] = "REFUSED"
            except Exception as e:
                result["status"] = f"ERROR: {str(e)[:50]}"

            results.append(result)

        return results
