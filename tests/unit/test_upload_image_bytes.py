"""/api/flow/upload-image-bytes: inline uploads for callers on another host."""

import base64
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from agent.api import flow as flow_api

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


def _client(connected: bool = True, result: dict | None = None):
    fake = MagicMock()
    fake.connected = connected
    fake.upload_image = AsyncMock(return_value=result or {"_mediaId": "media-1", "data": {"media": {"name": "media-1"}}})
    app = FastAPI()
    app.include_router(flow_api.router, prefix="/api")
    return TestClient(app), fake


def _post(test_client, **body):
    return test_client.post("/api/flow/upload-image-bytes", json=body)


def test_uploads_inline_png_and_returns_media_id():
    tc, fake = _client()
    with patch.object(flow_api, "get_flow_client", return_value=fake):
        resp = _post(tc, image_b64=base64.b64encode(PNG).decode(), project_id="p1", file_name="frame.png")
    assert resp.status_code == 200
    assert resp.json()["media_id"] == "media-1"
    args, kwargs = fake.upload_image.call_args
    assert base64.b64decode(args[0]) == PNG
    assert kwargs == {"mime_type": "image/png", "project_id": "p1", "file_name": "frame.png"}


@pytest.mark.parametrize("body, status", [
    ({"image_b64": base64.b64encode(PNG).decode(), "mime_type": "image/gif"}, 400),
    ({"image_b64": "not base64 !!"}, 400),
    ({"image_b64": ""}, 400),
    ({"image_b64": base64.b64encode(b"x" * (flow_api.UPLOAD_BYTES_MAX + 1)).decode()}, 413),
])
def test_rejects_bad_input_without_calling_flow(body, status):
    tc, fake = _client()
    with patch.object(flow_api, "get_flow_client", return_value=fake):
        resp = _post(tc, **body)
    assert resp.status_code == status
    fake.upload_image.assert_not_called()


def test_extension_disconnected_is_503():
    tc, fake = _client(connected=False)
    with patch.object(flow_api, "get_flow_client", return_value=fake):
        resp = _post(tc, image_b64=base64.b64encode(PNG).decode())
    assert resp.status_code == 503


def test_flow_error_is_propagated_like_file_upload():
    tc, fake = _client(result={"error": "FlowBatchError: upload: NO_FLOW_TAB", "status": 502})
    with patch.object(flow_api, "get_flow_client", return_value=fake):
        resp = _post(tc, image_b64=base64.b64encode(PNG).decode())
    assert resp.status_code == 502
    assert "NO_FLOW_TAB" in resp.json()["detail"]


def test_file_upload_endpoint_still_reads_host_path(tmp_path):
    path = tmp_path / "frame.png"
    path.write_bytes(PNG)
    tc, fake = _client()
    with patch.object(flow_api, "get_flow_client", return_value=fake):
        resp = tc.post("/api/flow/upload-image", json={"file_path": str(path)})
    assert resp.status_code == 200 and resp.json()["media_id"] == "media-1"
    assert base64.b64decode(fake.upload_image.call_args.args[0]) == PNG
