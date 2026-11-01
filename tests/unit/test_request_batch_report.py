"""batch-status reporting, retry-failed requeueing, and the shared error classes."""
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from agent.api import requests as requests_api
from agent.db import crud
from agent.worker import request_error_classes as errc
from agent.worker.processor import _handle_failure

HOLD_MSG = "PUBLIC_ERROR_UNUSUAL_ACTIVITY local cooldown active; retry in about 50s"
GOOGLE_BLOCK = ("ogiZ0b failed: [7, None, [['type.googleapis.com/google.rpc.ErrorInfo', "
                "['PUBLIC_ERROR_UNUSUAL_ACTIVITY']]]] reCAPTCHA evaluation failed")


class _FakeFlow:
    def __init__(self, hold_s: float = 0.0, connected: bool = True):
        self.connected = connected
        self.generation_guard_status = {
            "cooldown_active": hold_s > 0,
            "cooldown_remaining_s": hold_s,
            "cooldown_reason": "unusual_activity" if hold_s else None,
        }


@pytest.fixture
def make_client(test_db, monkeypatch):
    def _make(hold_s: float = 0.0, connected: bool = True) -> TestClient:
        monkeypatch.setattr(requests_api, "get_flow_client",
                            lambda: _FakeFlow(hold_s, connected))
        app = FastAPI()
        app.include_router(requests_api.router, prefix="/api")
        return TestClient(app)
    return _make


async def _video_with_scenes(n: int):
    proj = await crud.create_project(name="Batch report")
    video = await crud.create_video(project_id=proj["id"], title="V", orientation="VERTICAL")
    scenes = [await crud.create_scene(video_id=video["id"], display_order=i, prompt=f"s{i}")
              for i in range(n)]
    return proj, video, scenes


async def _req(proj, video, scene, status="PENDING", error=None, retry_count=0,
               provider="flow"):
    row = await crud.create_request(req_type="GENERATE_IMAGE", orientation="VERTICAL",
                                    scene_id=scene["id"], project_id=proj["id"],
                                    video_id=video["id"], provider=provider)
    return await crud.update_request(row["id"], status=status, error_message=error,
                                     retry_count=retry_count)


# ── classification ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("message, expected", [
    (HOLD_MSG, errc.FLOW_HOLD),                 # names UNUSUAL_ACTIVITY but never reached Google
    (GOOGLE_BLOCK, errc.ACCOUNT_BLOCKED),       # mentions reCAPTCHA, still a block
    ("[HIJACK] extension_hijack_detected", errc.CAPTCHA_HIJACK),
    ("Request blocked [PUBLIC_ERROR_UNSAFE_GENERATION]", errc.CONTENT_POLICY),
    ("PUBLIC_ERROR_USER_QUOTA_REACHED", errc.QUOTA),
    ("MEDIA_REMOVED_BY_FLOW: media x for operation y was listed", errc.GENERATION_REMOVED),
    ("403 PUBLIC_ERROR_MODEL_ACCESS_DENIED", errc.CONFIG),
    ("UNSUPPORTED_ON_BATCH_API: upscale", errc.CONFIG),
    ("Extension disconnected", errc.EXTENSION),
    ("reCAPTCHA token mint failed", errc.CAPTCHA),
    ("Internal error encountered", errc.TRANSIENT),
    (None, errc.TRANSIENT),
])
def test_classify_error(message, expected):
    assert errc.classify_error(message) == expected


@pytest.mark.asyncio
@pytest.mark.parametrize("message", [
    "Request blocked [PUBLIC_ERROR_UNSAFE_GENERATION]",
    "PUBLIC_ERROR_USER_QUOTA_REACHED",
    HOLD_MSG,
])
async def test_worker_does_not_resend_terminal_classes(message):
    req = {"id": "r1", "type": "GENERATE_IMAGE", "scene_id": "s1",
           "orientation": "VERTICAL", "retry_count": 0}
    with patch("agent.worker.processor.crud") as mock_crud:
        mock_crud.update_request = AsyncMock()
        mock_crud.update_scene = AsyncMock()
        await _handle_failure("r1", req, {"error": message})
    kwargs = mock_crud.update_request.call_args[1]
    assert kwargs["status"] == "FAILED"
    assert "retry_count" not in kwargs


# ── batch-status ────────────────────────────────────────────────────────────

async def test_resubmitted_target_counts_by_latest_attempt(make_client):
    proj, video, (s0, s1) = await _video_with_scenes(2)
    await _req(proj, video, s0, status="FAILED", error="Internal error encountered")
    await _req(proj, video, s0, status="COMPLETED")      # resubmission succeeded
    await _req(proj, video, s1, status="COMPLETED")
    body = make_client().get(f"/api/requests/batch-status?video_id={video['id']}").json()
    assert (body["total"], body["failed"], body["superseded"]) == (2, 0, 1)
    assert body["all_succeeded"] is True
    assert body["next_action"] == "done"


async def test_wait_paces_by_flow_interval(make_client, monkeypatch):
    monkeypatch.setattr(requests_api, "FLOW_GENERATION_MIN_INTERVAL_S", 20.0)
    proj, video, (s0, s1) = await _video_with_scenes(2)
    await _req(proj, video, s0, status="PROCESSING")
    await _req(proj, video, s1, status="PENDING", retry_count=2)
    body = make_client().get(f"/api/requests/batch-status?video_id={video['id']}").json()
    assert body["next_action"] == "wait"
    assert body["poll_after_s"] == 20.0
    assert body["retrying"] == 1


async def test_pending_flow_without_extension_waits_for_it(make_client):
    proj, video, (s0,) = await _video_with_scenes(1)
    await _req(proj, video, s0)
    body = make_client(connected=False).get(
        f"/api/requests/batch-status?video_id={video['id']}").json()
    assert body["next_action"] == "wait_extension"


async def test_hold_stops_flow_batch(make_client):
    proj, video, (s0, s1) = await _video_with_scenes(2)
    await _req(proj, video, s0, status="FAILED", error=GOOGLE_BLOCK)
    await _req(proj, video, s1, status="FAILED", error=HOLD_MSG)
    body = make_client(hold_s=3000).get(
        f"/api/requests/batch-status?video_id={video['id']}").json()
    assert body["next_action"] == "stop"
    assert body["poll_after_s"] == 3000
    classes = {f["scene_id"]: f["error_class"] for f in body["failed_items"]}
    assert classes == {s0["id"]: errc.ACCOUNT_BLOCKED, s1["id"]: errc.FLOW_HOLD}


async def test_hold_does_not_stop_other_providers(make_client):
    proj, video, (s0,) = await _video_with_scenes(1)
    await _req(proj, video, s0, provider="assistant")
    body = make_client(hold_s=3000).get(
        f"/api/requests/batch-status?video_id={video['id']}").json()
    assert body["next_action"] == "wait"


async def test_account_block_keeps_stop_after_hold_expires(make_client):
    proj, video, (s0,) = await _video_with_scenes(1)
    await _req(proj, video, s0, status="FAILED", error=GOOGLE_BLOCK)
    body = make_client().get(f"/api/requests/batch-status?video_id={video['id']}").json()
    assert body["next_action"] == "stop"
    assert body["poll_after_s"] is None


@pytest.mark.parametrize("error, action", [
    ("Internal error encountered", "retry_failed"),
    ("Request blocked [PUBLIC_ERROR_UNSAFE_GENERATION]", "fix_failed"),
])
async def test_finished_batch_with_failures(make_client, error, action):
    proj, video, (s0,) = await _video_with_scenes(1)
    await _req(proj, video, s0, status="FAILED", error=error)
    body = make_client().get(f"/api/requests/batch-status?video_id={video['id']}").json()
    assert body["next_action"] == action


# ── retry-failed ────────────────────────────────────────────────────────────

async def test_retry_failed_refused_during_hold(make_client):
    proj, video, (s0,) = await _video_with_scenes(1)
    row = await _req(proj, video, s0, status="FAILED", error=HOLD_MSG)
    res = make_client(hold_s=120).post("/api/requests/retry-failed",
                                       json={"video_id": video["id"]})
    assert res.status_code == 409
    assert (await crud.get_request(row["id"]))["status"] == "FAILED"


async def test_retry_failed_default_skips_account_safety_and_policy(make_client):
    proj, video, scenes = await _video_with_scenes(4)
    held = await _req(proj, video, scenes[0], status="FAILED", error=HOLD_MSG)
    flaky = await _req(proj, video, scenes[1], status="FAILED",
                       error="Internal error encountered", retry_count=4)
    await _req(proj, video, scenes[2], status="FAILED", error=GOOGLE_BLOCK)
    await _req(proj, video, scenes[3], status="FAILED", error="[PUBLIC_ERROR_UNSAFE_GENERATION]")
    client = make_client()
    res = client.post("/api/requests/retry-failed", json={"video_id": video["id"]})
    assert res.status_code == 200
    requeued = {r["replaces"]: r["id"] for r in res.json()["requeued"]}
    assert set(requeued) == {held["id"], flaky["id"]}
    fresh = await crud.get_request(requeued[flaky["id"]])
    assert (fresh["status"], fresh["retry_count"], fresh["request_id"]) == ("PENDING", 0, None)
    assert (await crud.get_request(flaky["id"]))["status"] == "FAILED"   # kept as history
    body = client.get(f"/api/requests/batch-status?video_id={video['id']}").json()
    assert (body["total"], body["pending"], body["failed"], body["superseded"]) == (4, 2, 2, 2)


async def test_retry_failed_named_class_and_superseded_rows(make_client):
    proj, video, (s0, s1) = await _video_with_scenes(2)
    blocked = await _req(proj, video, s0, status="FAILED", error=GOOGLE_BLOCK)
    await _req(proj, video, s1, status="FAILED", error=GOOGLE_BLOCK)
    await _req(proj, video, s1, status="COMPLETED")      # already redone
    res = make_client().post("/api/requests/retry-failed",
                             json={"video_id": video["id"], "classes": ["account_blocked"]})
    assert [r["replaces"] for r in res.json()["requeued"]] == [blocked["id"]]


REMOVED = ("MEDIA_REMOVED_BY_FLOW: media b908 for operation d250 was listed, then "
           "answered NOT_FOUND for 90s. Same input usually repeats it: change the start image or prompt.")


async def test_removed_generation_needs_a_fix_then_named_retry(make_client):
    proj, video, (s0,) = await _video_with_scenes(1)
    failed = await _req(proj, video, s0, status="FAILED", error=REMOVED)
    await crud.update_request(failed["id"], request_id="d2501684-dead-op")
    client = make_client()
    body = client.get(f"/api/requests/batch-status?video_id={video['id']}").json()
    assert body["next_action"] == "fix_failed"
    assert body["failed_items"][0]["error_class"] == errc.GENERATION_REMOVED
    assert client.post("/api/requests/retry-failed",
                       json={"video_id": video["id"]}).json()["requeued"] == []
    res = client.post("/api/requests/retry-failed",
                      json={"video_id": video["id"], "classes": ["generation_removed"]})
    fresh = await crud.get_request(res.json()["requeued"][0]["id"])
    assert fresh["request_id"] is None        # resubmits instead of re-polling the dead op


async def test_history_lists_every_attempt_per_target(make_client):
    proj, video, (s0, s1) = await _video_with_scenes(2)
    first = await _req(proj, video, s1, status="FAILED", error=REMOVED)
    second = await _req(proj, video, s1, status="COMPLETED")
    await _req(proj, video, s0, status="COMPLETED")
    res = make_client().get(f"/api/requests/history?video_id={video['id']}")
    targets = {t["scene_id"]: t for t in res.json()}
    s1_hist = targets[s1["id"]]
    assert s1_hist["display_order"] == 1 and s1_hist["latest_status"] == "COMPLETED"
    assert [(a["id"], a["error_class"]) for a in s1_hist["attempts"]] == [
        (first["id"], errc.GENERATION_REMOVED), (second["id"], None)]
    assert make_client().get("/api/requests/history").status_code == 422


@pytest.mark.parametrize("payload", [
    {"classes": ["transient"]},                          # no scope
    {"video_id": "v", "classes": ["nonsense"]},
])
def test_retry_failed_rejects_bad_input(make_client, payload):
    assert make_client().post("/api/requests/retry-failed", json=payload).status_code == 422
