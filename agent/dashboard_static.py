"""Serve the built React dashboard and gate its WebSocket origin."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.types import ASGIApp, Receive, Scope, Send

from agent.config import DASHBOARD_DIST, DASHBOARD_ORIGIN_PREFIXES

_RESERVED_PREFIXES = ("api/", "ws/")
_RESERVED_EXACT = frozenset({"health", "api", "ws"})


def origin_allowed(origin: str | None, prefixes: tuple[str, ...] | None = None) -> bool:
    """Empty Origin is allowed (non-browser clients). Otherwise prefix-match."""
    if not origin:
        return True
    allowed = prefixes if prefixes is not None else DASHBOARD_ORIGIN_PREFIXES
    lowered = origin.lower()
    return any(lowered.startswith(prefix) for prefix in allowed)


class HeadAsGetMiddleware:
    """FastAPI GET routes reject HEAD (405). Map HEAD→GET and strip the body."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope.get("method") != "HEAD":
            await self.app(scope, receive, send)
            return
        scope = dict(scope)
        scope["method"] = "GET"

        async def send_head(message: dict) -> None:
            if message["type"] == "http.response.body":
                message = {**message, "body": b"", "more_body": False}
            await send(message)

        await self.app(scope, receive, send_head)


def _reserved_path(full_path: str) -> bool:
    path = full_path.lstrip("/")
    return path in _RESERVED_EXACT or path.startswith(_RESERVED_PREFIXES)


def mount_dashboard(app: FastAPI, dist: Path | None = None) -> bool:
    """Serve dashboard/dist. Call after API routes so `/api` and `/health` win."""
    root = (dist if dist is not None else DASHBOARD_DIST).resolve()
    if not (root / "index.html").is_file():
        return False

    assets = root / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets)), name="dashboard-assets")

    @app.api_route("/{full_path:path}", methods=["GET", "HEAD"])
    async def dashboard_spa(full_path: str):
        if _reserved_path(full_path):
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        if full_path:
            candidate = (root / full_path).resolve()
            try:
                candidate.relative_to(root)
            except ValueError:
                return FileResponse(root / "index.html")
            if candidate.is_file():
                return FileResponse(candidate)
        return FileResponse(root / "index.html")

    return True
