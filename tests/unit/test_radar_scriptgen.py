"""Grok/CLIProxyAPI short-spec contract — no live proxy in CI."""
import importlib.util
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]


def load_mod():
    spec = importlib.util.spec_from_file_location(
        "radar_scriptgen", ROOT / "scripts" / "radar_scriptgen.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sg = load_mod()

NARR = "Tin nay doi cach lab chay mo hinh mo. Nhom so sanh the model card roi cong khai."

TOPIC = {
    "label_vi": "DeepSeek",
    "insight": "insight",
    "counter": "counter",
    "evidence": [
        {"claim": "HF model card lists new weights", "url": "https://hf.co/x", "source": "hf"},
        {"claim": "OCR of a paper table", "url": "https://arx", "source": "arxiv"},
    ],
}


def _scene(role, names, narrator=NARR):
    return {
        "role": role,
        "prompt": "Action in a lab, medium shot.",
        "video_prompt": "The camera dollies in. Audio: room tone. Negative: subtitles, watermark, text overlay.",
        "narrator_text": narrator,
        "character_names": names,
    }


def valid_spec():
    return {"scenes": [
        _scene("hook", [sg.MC_NAME]),
        _scene("broll", []),
        _scene("broll", []),
        _scene("counter", []),
        _scene("outro", [sg.MC_NAME]),
    ]}


def test_word_count_splits_on_whitespace():
    assert sg.word_count(NARR) == 18
    assert sg.word_count("") == 0


def test_validate_accepts_five_scene_contract():
    assert sg.validate_spec(valid_spec(), TOPIC) == []


def test_validate_rejects_short_narrator_and_wrong_broll_count():
    spec = valid_spec()
    spec["scenes"][1]["narrator_text"] = "qua ngan"
    spec["scenes"][2]["role"] = "counter"
    errors = sg.validate_spec(spec, TOPIC)
    assert any("narrator_text" in err for err in errors)
    assert any("broll count" in err for err in errors)


def test_parse_json_object_strips_fence():
    parsed = sg.parse_json_object("```json\n{\"scenes\": []}\n```")
    assert parsed == {"scenes": []}


def test_parse_json_object_strips_trailing_prose():
    parsed = sg.parse_json_object('Here you go:\n{"scenes": []}\nHope this helps!')
    assert parsed == {"scenes": []}


def test_chat_url_normalizes_base():
    assert sg.chat_url("http://127.0.0.1:8317").endswith("/v1/chat/completions")
    assert sg.chat_url("http://x/v1") == "http://x/v1/chat/completions"


def test_generate_retries_then_accepts(monkeypatch):
    bad = valid_spec()
    bad["scenes"][1]["narrator_text"] = "ngan"
    good = valid_spec()
    contents = [json.dumps(bad), json.dumps(good)]

    def fake_chat(_messages, timeout=120):
        return contents.pop(0)

    monkeypatch.setattr(sg, "grok_chat", fake_chat)
    spec = sg.generate_short_spec(TOPIC)
    assert len(spec["scenes"]) == 5
    assert spec["mc_name"] == sg.MC_NAME
    assert spec["label_vi"] == "DeepSeek"


def test_grok_chat_sends_bearer(monkeypatch):
    captured = {}

    class Resp:
        def read(self):
            return json.dumps({
                "choices": [{"message": {"content": "{\"ok\":true}"}}]
            }).encode()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake_urlopen(request, timeout=120):
        captured["url"] = request.full_url
        captured["auth"] = request.get_header("Authorization")
        return Resp()

    monkeypatch.setenv("CLIPROXY_API_KEY", "abc")
    monkeypatch.setenv("CLIPROXY_BASE_URL", "http://127.0.0.1:8317")
    monkeypatch.setattr(sg.urllib.request, "urlopen", fake_urlopen)
    text = sg.grok_chat([{"role": "user", "content": "hi"}])
    assert json.loads(text) == {"ok": True}
    assert captured["url"].endswith("/v1/chat/completions")
    assert captured["auth"] == "Bearer abc"
