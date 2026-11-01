"""A video whose listed media answers NOT_FOUND fails as MEDIA_REMOVED_BY_FLOW
after the grace, instead of being polled to the timeout."""
import pytest

from agent.services import flow_batch as fb
from agent.services import flow_client as fc

OP = "d2501684-1a05-4396-bb73-802bb44310d4"


def _client(monkeypatch, listing, media):
    """``listing``/``media``: lists consumed one per poll round."""
    client = fc.FlowClient()

    async def find(op_id):
        return listing.pop(0), None

    async def urls(media_id):
        outcome = media.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr(client, "_find_operation_media", find)
    monkeypatch.setattr(client, "_batch_media_urls", urls)
    return client


@pytest.mark.asyncio
async def test_listed_then_not_found_fails_after_grace(monkeypatch):
    monkeypatch.setattr(fc, "FLOW_REMOVED_MEDIA_GRACE_S", 3600.0)
    client = _client(monkeypatch, listing=["m1", None], media=[fb.RpcError("as29s", [5])])
    first = await client._poll_batch_operation(OP)
    assert first["status"] == "MEDIA_GENERATION_STATUS_PENDING"

    monkeypatch.setattr(fc, "FLOW_REMOVED_MEDIA_GRACE_S", 0.0)
    second = await client._poll_batch_operation(OP)
    assert second["status"] == "MEDIA_GENERATION_STATUS_FAILED"
    assert second["error"].startswith("MEDIA_REMOVED_BY_FLOW: media m1")


@pytest.mark.asyncio
async def test_clip_that_reappears_is_not_failed(monkeypatch):
    monkeypatch.setattr(fc, "FLOW_REMOVED_MEDIA_GRACE_S", 0.0)
    client = _client(monkeypatch, listing=["m1", "m2"],
                     media=[fb.RpcError("as29s", [5]),
                            fb.MediaUrls(media_id="m2", video="https://v/m2.mp4")])
    await client._poll_batch_operation(OP)
    done = await client._poll_batch_operation(OP)
    assert done["status"] == "MEDIA_GENERATION_STATUS_SUCCESSFUL"
    assert OP not in client._operation_removed


@pytest.mark.asyncio
async def test_other_media_errors_still_raise(monkeypatch):
    client = _client(monkeypatch, listing=["m1"], media=[fb.RpcError("as29s", [13])])
    with pytest.raises(fb.RpcError):
        await client._poll_batch_operation(OP)
    assert OP not in client._operation_removed
