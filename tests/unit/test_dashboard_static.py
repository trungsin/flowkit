"""Dashboard SPA mount + WebSocket origin allowlist."""
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from agent.config import parse_dashboard_origin_prefixes
from agent.dashboard_static import HeadAsGetMiddleware, mount_dashboard, origin_allowed


def test_parse_prefixes_always_includes_localhost():
    prefixes = parse_dashboard_origin_prefixes("")
    assert "http://127.0.0.1" in prefixes
    assert "chrome-extension://" in prefixes
    assert len(prefixes) == 5


def test_parse_prefixes_appends_production_domains():
    prefixes = parse_dashboard_origin_prefixes(
        "https://flowkit.datxanhmientrung.ai, https://flowkit.example.com/"
    )
    assert "https://flowkit.datxanhmientrung.ai" in prefixes
    assert "https://flowkit.example.com" in prefixes


def test_origin_allowed_empty_and_localhost():
    prefixes = parse_dashboard_origin_prefixes("https://flowkit.datxanhmientrung.ai")
    assert origin_allowed("", prefixes)
    assert origin_allowed("http://127.0.0.1:5173", prefixes)
    assert origin_allowed("http://localhost:8100", prefixes)
    assert origin_allowed("chrome-extension://abcdef", prefixes)
    assert origin_allowed("https://flowkit.datxanhmientrung.ai", prefixes)


def test_origin_rejects_other_sites():
    prefixes = parse_dashboard_origin_prefixes("https://flowkit.datxanhmientrung.ai")
    assert not origin_allowed("https://evil.example", prefixes)
    assert not origin_allowed("https://datxanhmientrung.ai", prefixes)


def test_mount_skipped_when_dist_missing(tmp_path: Path):
    app = FastAPI()
    assert mount_dashboard(app, tmp_path) is False


def test_mount_serves_spa_index(tmp_path: Path):
    (tmp_path / "index.html").write_text("<html>flowkit</html>", encoding="utf-8")
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "app.js").write_text("ok", encoding="utf-8")
    app = FastAPI()

    @app.get("/health")
    def health():
        return {"status": "ok"}

    assert mount_dashboard(app, tmp_path) is True
    app.add_middleware(HeadAsGetMiddleware)
    client = TestClient(app)
    assert client.get("/health").json() == {"status": "ok"}
    assert client.head("/health").status_code == 200
    assert client.head("/").status_code == 200
    assert "flowkit" in client.get("/").text
    assert "flowkit" in client.get("/projects").text
    assert client.get("/assets/app.js").text == "ok"
    assert client.get("/ws/dashboard").status_code == 404
