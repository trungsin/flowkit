"""What a client needs to pace a batch: progress, why items failed, the Flow
hold, and the next thing to do.

Counts cover the latest request per target (scene or character + type +
orientation), so a target resubmitted after a failure counts once, by its
newest attempt.
"""
from __future__ import annotations

from typing import Iterable

from agent.worker import request_error_classes as errc
from agent.worker.processor import _request_provider_name

ERROR_PREVIEW_CHARS = 300
EXTENSION_WAIT_POLL_S = 30.0


def _target_key(row: dict) -> tuple:
    if not row.get("scene_id") and not row.get("character_id"):
        return ("id", row["id"])
    return (row.get("scene_id") or "", row.get("character_id") or "",
            row.get("type") or "", row.get("orientation") or "")


def _recency(row: dict) -> tuple:
    # created_at has one-second resolution. On a tie the non-FAILED row wins:
    # a resubmission is never older than the failure it replaces.
    return (row.get("created_at") or "", row.get("status") != "FAILED")


def latest_per_target(rows: Iterable[dict]) -> list[dict]:
    """Newest request per target; ``rows`` in any order."""
    latest: dict[tuple, dict] = {}
    for row in rows:
        key = _target_key(row)
        kept = latest.get(key)
        if kept is None or _recency(row) > _recency(kept):
            latest[key] = row
    return list(latest.values())


def _failed_item(row: dict) -> dict:
    error_class = errc.classify_error(row.get("error_message"))
    return {
        "id": row["id"],
        "type": row.get("type"),
        "scene_id": row.get("scene_id"),
        "character_id": row.get("character_id"),
        "orientation": row.get("orientation"),
        "provider": _request_provider_name(row),
        "retry_count": row.get("retry_count") or 0,
        "error_class": error_class,
        "requeue_by_default": error_class in errc.REQUEUE_BY_DEFAULT,
        "error_message": (row.get("error_message") or "")[:ERROR_PREVIEW_CHARS],
        "updated_at": row.get("updated_at"),
    }


def build_report(rows: list[dict], *, guard: dict, extension_connected: bool,
                 min_interval_s: float, poll_interval_s: float) -> dict:
    """``guard`` is ``FlowClient.generation_guard_status``."""
    latest = latest_per_target(rows)
    counts = {"PENDING": 0, "PROCESSING": 0, "COMPLETED": 0, "FAILED": 0}
    for row in latest:
        status = row.get("status") or "PENDING"
        counts[status] = counts.get(status, 0) + 1
    failed_items = [_failed_item(r) for r in latest if r.get("status") == "FAILED"]
    active = [r for r in latest if r.get("status") in ("PENDING", "PROCESSING")]
    retrying = sum(1 for r in active if (r.get("retry_count") or 0) > 0)

    hold_active = bool(guard.get("cooldown_active"))
    flow_active = any(_request_provider_name(r) == "flow" for r in active)
    flow_failed = [f for f in failed_items if f["provider"] == "flow"]
    account_safety = [f for f in flow_failed if f["error_class"] in errc.ACCOUNT_SAFETY]
    requeueable = [f for f in failed_items if f["requeue_by_default"]]
    hold_blocks = hold_active and (flow_active or any(f["requeue_by_default"] for f in flow_failed))

    poll_after_s = None
    if hold_blocks or account_safety:
        next_action = "stop"
        if hold_active:
            poll_after_s = guard.get("cooldown_remaining_s")
    elif active:
        if flow_active and not extension_connected:
            next_action, poll_after_s = "wait_extension", EXTENSION_WAIT_POLL_S
        else:
            next_action = "wait"
            poll_after_s = max(poll_interval_s, min_interval_s if flow_active else 0.0)
    elif requeueable:
        next_action = "retry_failed"
    elif failed_items:
        next_action = "fix_failed"
    elif latest:
        next_action = "done"
    else:
        next_action = "empty"

    total = len(latest)
    return {
        "total": total,
        "pending": counts["PENDING"],
        "processing": counts["PROCESSING"],
        "completed": counts["COMPLETED"],
        "failed": counts["FAILED"],
        "done": counts["PENDING"] == 0 and counts["PROCESSING"] == 0,
        "all_succeeded": counts["COMPLETED"] == total and total > 0,
        "retrying": retrying,
        "superseded": len(rows) - total,
        "failed_items": failed_items,
        "flow_guard": {
            "extension_connected": extension_connected,
            "cooldown_active": hold_active,
            "cooldown_remaining_s": guard.get("cooldown_remaining_s", 0.0),
            "cooldown_reason": guard.get("cooldown_reason"),
            "min_interval_s": min_interval_s,
        },
        "next_action": next_action,
        "poll_after_s": poll_after_s,
    }


def select_requeue(rows: list[dict], classes: frozenset[str]) -> list[tuple[dict, str]]:
    """FAILED latest-attempt rows whose error class is in ``classes``."""
    picked = []
    for row in latest_per_target(rows):
        if row.get("status") != "FAILED":
            continue
        error_class = errc.classify_error(row.get("error_message"))
        if error_class in classes:
            picked.append((row, error_class))
    return picked
