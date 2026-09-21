"""radar_build_short posts VERTICAL video + ROOT scenes, MC once."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_mod():
    spec = importlib.util.spec_from_file_location(
        "radar_build_short", ROOT / "scripts" / "radar_build_short.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


bs = load_mod()

SPEC = {
    "label_vi": "DeepSeek",
    "stable_key": "deepseek",
    "scenes": [
        {
            "role": "hook",
            "prompt": "Expert opens on the news.",
            "video_prompt": "The camera dollies in.",
            "narrator_text": "A" * 5 + " mot hai ba bon nam sau bay tam chin muoi mot",
            "character_names": [bs.MC_NAME],
        },
        {
            "role": "broll",
            "prompt": "Hugging Face model card on a monitor.",
            "video_prompt": "The camera holds.",
            "narrator_text": "Broll text here with enough words one two three four five six seven eight",
            "character_names": [],
        },
    ],
}


def test_ensure_project_creates_on_404(monkeypatch):
    calls = []

    def fake_req(method, path, body=None, base=bs.DEFAULT_BASE):
        calls.append((method, path))
        if method == "GET":
            raise RuntimeError("404 GET /api/projects/proj")
        assert body["flow_project_id"] == "proj"
        assert body["material"] == "realistic"
        return ({"id": "proj", "material": "realistic"}, 200)

    monkeypatch.setattr(bs, "req", fake_req)
    out = bs.ensure_project("proj", bs.DEFAULT_BASE)
    assert out["id"] == "proj"
    assert ("POST", "/api/projects") in calls


def test_ensure_mc_creates_and_links_when_missing(monkeypatch):
    calls = []

    def fake_req(method, path, body=None, base=bs.DEFAULT_BASE):
        calls.append((method, path))
        if method == "GET":
            return ([], 200)
        if path == "/api/characters":
            assert body["name"] == bs.MC_NAME
            return ({"id": "new-mc", "name": bs.MC_NAME}, 200)
        if "/characters/" in path:
            return ({"ok": True}, 200)
        raise AssertionError(path)

    monkeypatch.setattr(bs, "req", fake_req)
    mc = bs.ensure_mc("proj", bs.DEFAULT_BASE)
    assert mc["id"] == "new-mc"
    assert ("POST", "/api/characters") in calls
    assert ("POST", "/api/projects/proj/characters/new-mc") in calls


def test_ensure_mc_skips_when_name_exists(monkeypatch):
    calls = []

    def fake_req(method, path, body=None, base=bs.DEFAULT_BASE):
        calls.append((method, path, body))
        if method == "GET":
            return ([{"id": "mc1", "name": bs.MC_NAME}], 200)
        raise AssertionError("should not create")

    monkeypatch.setattr(bs, "req", fake_req)
    mc = bs.ensure_mc("proj", bs.DEFAULT_BASE)
    assert mc["id"] == "mc1"
    assert calls == [("GET", "/api/projects/proj/characters", None)]


def test_build_short_posts_vertical_root_and_patches_narrator(monkeypatch):
    posts = []

    def fake_req(method, path, body=None, base=bs.DEFAULT_BASE):
        posts.append((method, path, body))
        if "/projects/" in path and path.endswith("/characters") and method == "GET":
            return ([{"id": "mc1", "name": bs.MC_NAME}], 200)
        if path.endswith("/projects/proj") and method == "GET":
            return ({"id": "proj", "material": "realistic"}, 200)
        if path.startswith("/api/videos?project_id=") and method == "GET":
            return ([], 200)
        if path == "/api/videos":
            assert body["orientation"] == "VERTICAL"
            return ({"id": "vid1", "orientation": "VERTICAL"}, 200)
        if path == "/api/scenes":
            assert body["chain_type"] == "ROOT"
            order = body["display_order"]
            return ({"id": "s%s" % order, "display_order": order, "chain_type": "ROOT"}, 200)
        if method == "PATCH":
            return ({
                "id": path.rsplit("/", 1)[-1],
                "display_order": 0 if path.endswith("s0") else 1,
                "narrator_text": body["narrator_text"],
                "chain_type": "ROOT",
            }, 200)
        if path == "/api/active-project":
            return ({"project_id": "proj"}, 200)
        raise AssertionError(path)

    monkeypatch.setattr(bs, "req", fake_req)
    out = bs.build_short(SPEC, "proj", "2026-09-19", bs.DEFAULT_BASE)
    assert out["video_id"] == "vid1"
    assert out["orientation"] == "VERTICAL"
    assert len(out["scenes"]) == 2
    methods = [item[0] for item in posts]
    assert methods.count("POST") >= 3
    assert "PATCH" in methods
    assert ("PUT", "/api/active-project", {"project_id": "proj"}) in posts
