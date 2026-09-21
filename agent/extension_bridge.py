"""FastAPI adapter so the Chrome extension can reach the agent over the public host."""
from __future__ import annotations

import json
import logging

from fastapi import WebSocket, WebSocketDisconnect

from agent.dashboard_static import origin_allowed
from agent.services.flow_client import get_flow_client

logger = logging.getLogger(__name__)


class ExtensionSocket:
    """Match the `websockets` send/remote_address surface flow_client uses."""

    def __init__(self, ws: WebSocket):
        self._ws = ws
        client = ws.client
        self.remote_address = (client.host, client.port) if client else ("unknown", 0)

    async def send(self, data: str | bytes) -> None:
        if isinstance(data, bytes):
            await self._ws.send_bytes(data)
        else:
            await self._ws.send_text(data)


async def extension_ws_endpoint(websocket: WebSocket, callback_secret: str) -> None:
    origin = websocket.headers.get("origin") or ""
    if not origin_allowed(origin):
        await websocket.close(code=4003, reason="Origin not allowed")
        return
    await websocket.accept()
    sock = ExtensionSocket(websocket)
    client = get_flow_client()
    client.set_extension(sock)
    logger.info("Extension connected via /ws/extension from %s", sock.remote_address)
    await sock.send(json.dumps({"type": "callback_secret", "secret": callback_secret}))
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
                await client.handle_message(data, sock)
            except json.JSONDecodeError:
                logger.warning("Invalid JSON from extension")
            except Exception:
                logger.exception("Error handling extension message")
    except WebSocketDisconnect:
        pass
    finally:
        client.clear_extension(sock)
        logger.info("Extension disconnected from /ws/extension")
