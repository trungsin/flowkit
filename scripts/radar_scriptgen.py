#!/usr/bin/env python3
"""Turn one usable Radar topic into a Short spec via Grok on CLIProxyAPI."""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

MC_NAME = "Friendly Expert"
DEFAULT_BASE = "http://127.0.0.1:8317"
DEFAULT_MODEL = "grok-4"
NARRATOR_MIN, NARRATOR_MAX = 18, 22

SYSTEM = """You write VERTICAL news-short scripts for Flow Kit.
Return ONLY JSON: {"scenes":[{"role":"hook|broll|counter|outro","prompt":"","video_prompt":"","narrator_text":"","character_names":[]}]}
Rules:
- 5 or 6 scenes: hook, one broll per evidence claim (2-3), one counter, outro.
- prompt and video_prompt: English ACTION + environment. Never describe appearance.
- B-roll must name a concrete artifact from the claim (model card, OCR text, scrolling code, terminal, paper figure). Never "glowing AI brain".
- narrator_text: Vietnamese, 18-22 words, 2-3 short sentences. Context/stakes, not "we see".
- hook and outro character_names: ["Friendly Expert"]. B-roll: []. Counter: [] or ["Friendly Expert"].
- video_prompt: camera as its own sentence. End with Audio / SFX / Negative: subtitles, watermark, text overlay.
- All scenes are independent ROOT cuts. No real-person names in prompts."""


def word_count(text: str) -> int:
    return len([part for part in (text or "").split() if part])


def chat_url(base: str) -> str:
    trimmed = (base or DEFAULT_BASE).rstrip("/")
    if trimmed.endswith("/v1"):
        return trimmed + "/chat/completions"
    return trimmed + "/v1/chat/completions"


def grok_chat(messages: list, timeout: int = 120) -> str:
    body = {
        "model": os.environ.get("CLIPROXY_MODEL", DEFAULT_MODEL),
        "messages": messages,
        "temperature": 0.3,
    }
    data = json.dumps(body).encode()
    request = urllib.request.Request(
        chat_url(os.environ.get("CLIPROXY_BASE_URL", DEFAULT_BASE)),
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    api_key = os.environ.get("CLIPROXY_API_KEY", "").strip()
    if api_key:
        request.add_header("Authorization", "Bearer " + api_key)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode())
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        raise RuntimeError("CLIProxyAPI/Grok request failed: %s" % exc) from exc
    try:
        return payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("CLIProxyAPI/Grok returned no content: %s" % payload) from exc


def load_dotenv() -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def parse_json_object(text: str) -> dict:
    blob = (text or "").strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", blob, re.DOTALL)
    if fenced:
        blob = fenced.group(1)
    start, end = blob.find("{"), blob.rfind("}")
    if start == -1 or end <= start:
        raise RuntimeError("Grok did not return JSON: %s" % blob[:240])
    try:
        parsed = json.loads(blob[start:end + 1])
    except json.JSONDecodeError as exc:
        raise RuntimeError("Grok did not return JSON: %s" % blob[:240]) from exc
    if not isinstance(parsed, dict):
        raise RuntimeError("Grok JSON must be an object")
    return parsed


def validate_spec(spec: dict, topic: dict) -> list[str]:
    errors = []
    scenes = spec.get("scenes") if isinstance(spec, dict) else None
    if not isinstance(scenes, list) or not 5 <= len(scenes) <= 6:
        return ["need 5-6 scenes"]
    claims = topic.get("evidence") or []
    roles = [scene.get("role") for scene in scenes]
    if roles[0] != "hook" or roles[-1] != "outro":
        errors.append("first scene must be hook, last must be outro")
    if roles.count("counter") != 1:
        errors.append("need exactly one counter scene")
    if roles.count("broll") != len(claims):
        errors.append("broll count must match evidence claims (%s)" % len(claims))
    for index, scene in enumerate(scenes):
        narrator = scene.get("narrator_text") or ""
        count = word_count(narrator)
        if not (NARRATOR_MIN <= count <= NARRATOR_MAX):
            errors.append("scene %s narrator_text has %s words" % (index, count))
        if not (scene.get("prompt") or "").strip():
            errors.append("scene %s missing prompt" % index)
        if not (scene.get("video_prompt") or "").strip():
            errors.append("scene %s missing video_prompt" % index)
        names = scene.get("character_names")
        if not isinstance(names, list):
            errors.append("scene %s character_names must be a list" % index)
            continue
        if scene.get("role") in ("hook", "outro") and MC_NAME not in names:
            errors.append("scene %s must include %s" % (index, MC_NAME))
        if scene.get("role") == "broll" and names:
            errors.append("broll scene %s must have empty character_names" % index)
    return errors


def generate_short_spec(topic: dict) -> dict:
    load_dotenv()
    capped = dict(topic)
    capped["evidence"] = list(topic.get("evidence") or [])[:3]
    user = json.dumps({
        "label_vi": capped.get("label_vi"),
        "insight": capped.get("insight"),
        "counter": capped.get("counter"),
        "evidence": capped["evidence"],
    }, ensure_ascii=False)
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user},
    ]
    try:
        spec = parse_json_object(grok_chat(messages))
    except RuntimeError:
        messages.append({"role": "user", "content": "Return JSON only. No prose."})
        spec = parse_json_object(grok_chat(messages))
    errors = validate_spec(spec, capped)
    if errors:
        messages.append({"role": "assistant", "content": json.dumps(spec, ensure_ascii=False)})
        messages.append({"role": "user", "content": "Fix these errors and return JSON only: " + "; ".join(errors)})
        spec = parse_json_object(grok_chat(messages))
        errors = validate_spec(spec, capped)
    if errors:
        raise RuntimeError("Grok short-spec invalid: " + "; ".join(errors))
    spec["label_vi"] = topic.get("label_vi")
    spec["stable_key"] = topic.get("stable_key")
    spec["mc_name"] = MC_NAME
    return spec


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args and args[0] != "-":
        topic = json.loads(Path_read(args[0]))
    else:
        topic = json.load(sys.stdin)
    json.dump(generate_short_spec(topic), sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


def Path_read(path: str) -> str:
    with open(path, encoding="utf-8") as handle:
        return handle.read()


if __name__ == "__main__":
    raise SystemExit(main())
