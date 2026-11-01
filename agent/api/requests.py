from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, model_validator
from typing import Optional
from agent.config import FLOW_GENERATION_MIN_INTERVAL_S, POLL_INTERVAL
from agent.models.request import Request, RequestCreate
from agent.models.enums import StatusType
from agent.db import crud
from agent.services.flow_client import get_flow_client
from agent.services import request_batch_report as report
from agent.worker import request_error_classes as errc

router = APIRouter(prefix="/requests", tags=["requests"])


class RequestUpdate(BaseModel):
    status: Optional[StatusType] = None
    media_id: Optional[str] = None
    output_url: Optional[str] = None
    error_message: Optional[str] = None
    request_id: Optional[str] = None


class BatchRequestCreate(BaseModel):
    requests: list[RequestCreate]


class FailedItem(BaseModel):
    id: str
    type: Optional[str] = None
    scene_id: Optional[str] = None
    character_id: Optional[str] = None
    orientation: Optional[str] = None
    provider: str
    retry_count: int
    error_class: str
    requeue_by_default: bool
    error_message: str
    updated_at: Optional[str] = None


class FlowGuard(BaseModel):
    extension_connected: bool
    cooldown_active: bool
    cooldown_remaining_s: float
    cooldown_reason: Optional[str] = None
    min_interval_s: float


class BatchStatus(BaseModel):
    total: int
    pending: int
    processing: int
    completed: int
    failed: int
    done: bool
    all_succeeded: bool
    orientation: Optional[str] = None
    retrying: int
    superseded: int
    failed_items: list[FailedItem]
    flow_guard: FlowGuard
    next_action: str
    poll_after_s: Optional[float] = None


class RetryFailedRequest(BaseModel):
    video_id: Optional[str] = None
    project_id: Optional[str] = None
    type: Optional[str] = None
    orientation: Optional[str] = None
    # Error classes to requeue; default: flow_hold, transient, captcha, extension.
    classes: Optional[list[str]] = None

    @model_validator(mode="after")
    def _scoped_and_known(self):
        if not self.video_id and not self.project_id:
            raise ValueError("video_id or project_id is required")
        unknown = set(self.classes or ()) - errc.ALL_CLASSES
        if unknown:
            raise ValueError(f"unknown error classes: {sorted(unknown)}")
        return self


class RequeuedItem(BaseModel):
    id: str              # the new attempt
    replaces: str        # the FAILED attempt it supersedes
    type: Optional[str] = None
    scene_id: Optional[str] = None
    character_id: Optional[str] = None
    error_class: str


class RetryFailedResult(BaseModel):
    requeued: list[RequeuedItem]


class Attempt(BaseModel):
    id: str
    status: str
    operation_id: Optional[str] = None
    media_id: Optional[str] = None
    retry_count: int = 0
    error_class: Optional[str] = None
    error_message: Optional[str] = None
    provider: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class TargetHistory(BaseModel):
    type: Optional[str] = None
    scene_id: Optional[str] = None
    character_id: Optional[str] = None
    orientation: Optional[str] = None
    display_order: Optional[int] = None
    latest_status: str
    attempts: list[Attempt]   # oldest first


async def _filtered_rows(video_id, project_id, type, orientation) -> list[dict]:
    rows = await crud.list_requests(video_id=video_id, project_id=project_id)
    if type:
        rows = [r for r in rows if r.get("type") == type]
    if orientation:
        rows = [r for r in rows if r.get("orientation") == orientation]
    return rows


@router.post("", response_model=Request)
async def create(body: RequestCreate):
    data = body.model_dump(exclude_none=True)
    data["req_type"] = data.pop("type")

    scene_id = data.get("scene_id")
    req_type = data.get("req_type")
    orient = data.get("orientation")
    if scene_id and req_type:
        existing = await crud.list_requests(scene_id=scene_id)
        active = [r for r in existing
                  if r.get("type") == req_type
                  and (not orient or r.get("orientation") == orient)
                  and r.get("status") in ("PENDING", "PROCESSING")]
        if active:
            raise HTTPException(
                409,
                f"Active {req_type} request already exists for scene {scene_id[:8]} "
                f"(status={active[0]['status']}, id={active[0]['id'][:8]})"
            )

    # Auto-set video orientation (symmetric with batch endpoint)
    vid = data.get("video_id")
    orient = data.get("orientation")
    if vid and orient:
        await crud.update_video(vid, orientation=orient)

    return await crud.create_request(**data)


@router.post("/batch", response_model=list[Request])
async def create_batch(body: BatchRequestCreate):
    """Submit multiple requests atomically. Server handles throttling (max 5 concurrent, 10s cooldown).
    Duplicate active requests for the same scene+type are skipped (not errors)."""
    # Auto-set video orientation from the batch (tracks current active orientation)
    _seen_vids: set[str] = set()
    for item in body.requests:
        vid = item.video_id
        orient = item.orientation
        if vid and orient and vid not in _seen_vids:
            _seen_vids.add(vid)
            await crud.update_video(vid, orientation=orient)
    results = []
    for item in body.requests:
        data = item.model_dump(exclude_none=True)
        data["req_type"] = data.pop("type")
        scene_id = data.get("scene_id")
        character_id = data.get("character_id")
        req_type = data.get("req_type")
        orient = data.get("orientation")
        # Idempotent: skip if active request already exists
        if scene_id and req_type:
            existing = await crud.list_requests(scene_id=scene_id)
            active = [r for r in existing
                      if r.get("type") == req_type
                      and (not orient or r.get("orientation") == orient)
                      and r.get("status") in ("PENDING", "PROCESSING")]
            if active:
                results.append(active[0])
                continue
        if character_id and req_type:
            existing = await crud.list_requests(project_id=data.get("project_id"))
            active = [r for r in existing
                      if r.get("character_id") == character_id
                      and r.get("type") == req_type
                      and r.get("status") in ("PENDING", "PROCESSING")]
            if active:
                results.append(active[0])
                continue
        results.append(await crud.create_request(**data))
    return results


@router.get("", response_model=list[Request])
async def list_all(scene_id: str = None, status: str = None,
                   video_id: str = None, project_id: str = None):
    return await crud.list_requests(scene_id=scene_id, status=status,
                                    video_id=video_id, project_id=project_id)


@router.get("/pending", response_model=list[Request])
async def list_pending():
    return await crud.list_pending_requests()


@router.get("/batch-status", response_model=BatchStatus)
async def batch_status(video_id: str = None, project_id: str = None,
                       type: str = None, orientation: str = None):
    """Aggregate status for all requests matching the filter, by latest attempt
    per target. Poll this instead of polling N individual request IDs; follow
    ``next_action`` and wait ``poll_after_s`` between polls."""
    rows = await _filtered_rows(video_id, project_id, type, orientation)
    client = get_flow_client()
    data = report.build_report(
        rows,
        guard=client.generation_guard_status,
        extension_connected=client.connected,
        min_interval_s=FLOW_GENERATION_MIN_INTERVAL_S,
        poll_interval_s=float(POLL_INTERVAL),
    )
    return BatchStatus(orientation=orientation, **data)


@router.post("/retry-failed", response_model=RetryFailedResult)
async def retry_failed(body: RetryFailedRequest):
    """Submit a new attempt for each FAILED latest attempt whose error class is
    in ``classes``. The FAILED row stays as history (``superseded`` in
    batch-status, listed in /requests/history). Refused while the Flow
    generation hold is active. Account-safety classes (account_blocked,
    captcha_hijack) run only when named in ``classes`` — do that only after one
    image generated by hand in the Flow UI."""
    guard = get_flow_client().generation_guard_status
    if guard.get("cooldown_active"):
        raise HTTPException(409, {
            "error": "flow_generation_hold_active",
            "cooldown_remaining_s": guard.get("cooldown_remaining_s"),
            "cooldown_reason": guard.get("cooldown_reason"),
        })
    classes = frozenset(body.classes) if body.classes else errc.REQUEUE_BY_DEFAULT
    rows = await _filtered_rows(body.video_id, body.project_id, body.type, body.orientation)
    result = RetryFailedResult(requeued=[])
    for row, error_class in report.select_requeue(rows, classes):
        new = await crud.create_request(
            req_type=row["type"], orientation=row.get("orientation"),
            scene_id=row.get("scene_id"), character_id=row.get("character_id"),
            project_id=row.get("project_id"), video_id=row.get("video_id"),
            source_media_id=row.get("source_media_id"), provider=row.get("provider"))
        result.requeued.append(RequeuedItem(
            id=new["id"], replaces=row["id"], type=row.get("type"),
            scene_id=row.get("scene_id"), character_id=row.get("character_id"),
            error_class=error_class))
    return result


@router.get("/history", response_model=list[TargetHistory])
async def history(video_id: str = None, project_id: str = None,
                  type: str = None, orientation: str = None):
    """Every attempt per target (scene or character + type + orientation),
    with its error class: the trace behind batch-status."""
    if not video_id and not project_id:
        raise HTTPException(422, "video_id or project_id is required")
    rows = await _filtered_rows(video_id, project_id, type, orientation)
    orders = {}
    if video_id:
        orders = {s["id"]: s.get("display_order") for s in await crud.list_scenes(video_id)}
    return [
        TargetHistory(
            type=t["type"], scene_id=t["scene_id"], character_id=t["character_id"],
            orientation=t["orientation"], display_order=orders.get(t["scene_id"]),
            latest_status=t["latest_status"],
            attempts=[Attempt(**a) for a in t["attempts"]],
        )
        for t in report.history(rows)
    ]


@router.get("/{rid}", response_model=Request)
async def get(rid: str):
    r = await crud.get_request(rid)
    if not r:
        raise HTTPException(404, "Request not found")
    return r


@router.patch("/{rid}", response_model=Request)
async def update(rid: str, body: RequestUpdate):
    data = body.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(400, "No fields to update")
    r = await crud.update_request(rid, **data)
    if not r:
        raise HTTPException(404, "Request not found")
    return r
