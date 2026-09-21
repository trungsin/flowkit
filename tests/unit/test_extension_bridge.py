"""Extension socket adapter + origin gate."""
from agent.dashboard_static import origin_allowed
from agent.extension_bridge import ExtensionSocket


def test_chrome_extension_origin_allowed():
    prefixes = origin_allowed.__defaults__  # unused; use parse
    from agent.config import parse_dashboard_origin_prefixes
    p = parse_dashboard_origin_prefixes("https://flowkit.datxanhmientrung.ai")
    assert origin_allowed("chrome-extension://abcdef", p)
    assert origin_allowed("https://flowkit.datxanhmientrung.ai", p)


class _DummyClient:
    host = "1.2.3.4"
    port = 9


class _DummyWs:
    client = _DummyClient()

    def __init__(self):
        self.sent = []

    async def send_text(self, data):
        self.sent.append(data)

    async def send_bytes(self, data):
        self.sent.append(data)


def test_extension_socket_remote_address():
    sock = ExtensionSocket(_DummyWs())
    assert sock.remote_address == ("1.2.3.4", 9)
