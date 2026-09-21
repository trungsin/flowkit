"""radar_digest filter: usable topics only, no network in CI."""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load_mod():
    spec = importlib.util.spec_from_file_location(
        "radar_digest", ROOT / "scripts" / "radar_digest.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


digest = load_mod()


def _ev(n):
    return json.dumps([
        {"claim": "claim %s" % i, "url": "https://ex/%s" % i, "source": "src"}
        for i in range(n)
    ])


def _topic(heat, n_ev, label, insight="insight text", key=None):
    return {
        "heat": heat,
        "size": 2,
        "label_vi": label,
        "insight": insight,
        "counter": "counter",
        "stable_key": key or label,
        "evidence_json": _ev(n_ev),
    }


def test_filter_keeps_seven_drops_bare_tags_sorts_heat():
    raw = {
        "status": "ok",
        "run_day": "2026-09-19",
        "question": "AI news?",
        "communities": [
            _topic(51.17, 3, "DeepSeek"),
            _topic(43.42, 3, "Ma nguon"),
            _topic(43.2, 0, "llama", insight=""),
            _topic(42.79, 3, "Khuếch tán"),
            _topic(42.3, 3, "Ngu canh"),
            _topic(35.17, 3, "Ha tang agent"),
            _topic(18.29, 0, "flux", insight=""),
            _topic(16.49, 0, "mistral", insight=""),
            _topic(13.03, 3, "Voice AI"),
            _topic(12.77, 3, "An ninh agent"),
            _topic(3.81, 0, "mcp", insight=""),
            _topic(1.61, 0, "reasoning", insight=""),
        ],
    }
    out = digest.filter_usable(raw)
    assert out["count"] == 7
    assert [t["label_vi"] for t in out["topics"]] == [
        "DeepSeek", "Ma nguon", "Khuếch tán", "Ngu canh",
        "Ha tang agent", "Voice AI", "An ninh agent",
    ]
    bare = {"llama", "flux", "mistral", "mcp", "reasoning"}
    assert not bare.intersection(t["label_vi"] for t in out["topics"])
    assert all(2 <= len(t["evidence"]) <= 3 and t["insight"] for t in out["topics"])


def test_filter_caps_evidence_at_three():
    raw = {
        "status": "ok",
        "communities": [_topic(9, 6, "many-claims")],
    }
    out = digest.filter_usable(raw)
    assert out["count"] == 1
    assert len(out["topics"][0]["evidence"]) == 3


def test_status_not_ok_exits_clean_with_reason():
    out = digest.filter_usable({"status": "pending", "communities": [_topic(9, 3, "x")]})
    assert out["count"] == 0
    assert out["topics"] == []
    assert "reason" in out


def test_empty_communities_count_zero():
    out = digest.filter_usable({"status": "ok", "communities": []})
    assert out["count"] == 0
    assert out["reason"] == "no communities"


def test_broken_evidence_json_drops_topic_no_raise():
    raw = {
        "status": "ok",
        "communities": [
            {
                "heat": 9,
                "label_vi": "broken",
                "insight": "has insight",
                "counter": "",
                "evidence_json": "{not-json",
            },
            _topic(8, 3, "ok"),
        ],
    }
    out = digest.filter_usable(raw)
    assert out["count"] == 1
    assert out["topics"][0]["label_vi"] == "ok"


def test_missing_heat_sorts_last():
    a = _topic(5, 3, "mid")
    b = _topic(9, 3, "high")
    c = _topic(1, 3, "noheat")
    del c["heat"]
    out = digest.filter_usable({"status": "ok", "communities": [a, c, b]})
    assert [t["label_vi"] for t in out["topics"]] == ["high", "mid", "noheat"]


def test_fetch_sends_user_agent(monkeypatch):
    captured = {}

    class Resp:
        def read(self):
            return b'{"status":"ok","communities":[]}'

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake_urlopen(request, timeout=15):
        captured["ua"] = request.get_header("User-agent")
        return Resp()

    monkeypatch.setattr(digest.urllib.request, "urlopen", fake_urlopen)
    digest.fetch("2026-09-19")
    assert "FlowKit-radar-digest" in (captured["ua"] or "")


def test_fetch_wraps_network_errors(monkeypatch):
    def boom(*_a, **_k):
        raise digest.urllib.error.URLError("down")

    monkeypatch.setattr(digest.urllib.request, "urlopen", boom)
    with pytest.raises(RuntimeError, match="digest fetch failed"):
        digest.fetch("2026-09-19")
