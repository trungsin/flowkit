"""Shared HTTP + .env helpers for Radar daily scripts."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE = "http://127.0.0.1:8100"
DEFAULT_PROJECT = "ef10b9d7-925c-4306-add6-a6c3f5a73da0"


def load_dotenv() -> None:
    env_path = ROOT / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def api_base() -> str:
    load_dotenv()
    return os.environ.get("FLOWKIT_BASE", DEFAULT_BASE).rstrip("/")


def project_id() -> str:
    load_dotenv()
    return os.environ.get("FLOW_PROJECT_ID", DEFAULT_PROJECT)


def req(method: str, path: str, body: dict | None = None, timeout: int = 180):
    data = None if body is None else json.dumps(body).encode()
    request = urllib.request.Request(api_base() + path, data=data, method=method)
    request.add_header("X-FlowKit-Caller", "radar-daily")
    if body is not None:
        request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode()), 200
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode()
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = {"detail": raw}
        raise RuntimeError("%s %s %s %s" % (exc.code, method, path, parsed)) from exc


def health() -> dict:
    data, _ = req("GET", "/health", timeout=15)
    return data
