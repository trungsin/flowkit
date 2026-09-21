#!/usr/bin/env python3
"""Create a VERTICAL video + ROOT scenes from a Radar short-spec JSON."""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

DEFAULT_BASE = "http://127.0.0.1:8100"
DEFAULT_PROJECT = "ef10b9d7-925c-4306-add6-a6c3f5a73da0"
MC_NAME = "Friendly Expert"
MC_DESCRIPTION = (
    "About 28, short dark hair, dark t-shirt under a casual blazer, sitting at a "
    "laptop on a wooden desk, warm bookshelf and a plant behind, one fixed outfit."
)
MC_VOICE = "Warm close Vietnamese-friendly male, conversational, not a news anchor."
MC_IMAGE = (
    "Full body to seated three-quarter of a young expert at a laptop, dark t-shirt "
    "and casual blazer, warm bookshelf background, front-facing, one outfit."
)


def req(method: str, path: str, body: dict | None = None, base: str = DEFAULT_BASE):
    data = None if body is None else json.dumps(body).encode()
    request = urllib.request.Request(base.rstrip("/") + path, data=data, method=method)
    if body is not None:
        request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode()), 200
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode()
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = {"detail": raw}
        raise RuntimeError("%s %s %s %s" % (exc.code, method, path, parsed)) from exc


def ensure_project(project_id: str, base: str) -> dict:
    try:
        project, _ = req("GET", "/api/projects/%s" % project_id, base=base)
        return project
    except RuntimeError as exc:
        if "404" not in str(exc):
            raise
    project, _ = req("POST", "/api/projects", {
        "name": "Radar News Daily",
        "description": "Daily AI-news Shorts from Radar digest",
        "story": "A friendly expert explains usable AI-news topics with concrete B-roll.",
        "material": "realistic",
        "language": "vi",
        "flow_project_id": project_id,
    }, base=base)
    return project


def find_video(project_id: str, title: str, base: str) -> dict | None:
    videos, _ = req("GET", "/api/videos?project_id=%s" % project_id, base=base)
    for video in videos:
        if video.get("title") == title:
            return video
    return None


def ensure_mc(project_id: str, base: str) -> dict:
    characters, _ = req("GET", "/api/projects/%s/characters" % project_id, base=base)
    for character in characters:
        if character.get("name") == MC_NAME:
            return character
    created, _ = req("POST", "/api/characters", {
        "name": MC_NAME,
        "entity_type": "character",
        "description": MC_DESCRIPTION,
        "image_prompt": MC_IMAGE,
        "voice_description": MC_VOICE,
    }, base=base)
    req("POST", "/api/projects/%s/characters/%s" % (project_id, created["id"]), {}, base=base)
    return created


def build_short(spec: dict, project_id: str, run_day: str, base: str) -> dict:
    ensure_project(project_id, base)
    mc = ensure_mc(project_id, base)
    title = "%s — %s" % (spec.get("label_vi") or "Radar", run_day)
    video = find_video(project_id, title, base)
    if video is None:
        video, _ = req("POST", "/api/videos", {
            "project_id": project_id,
            "title": title,
            "orientation": "VERTICAL",
            "description": spec.get("stable_key") or "",
        }, base=base)
    scenes_out = []
    for index, scene in enumerate(spec.get("scenes") or []):
        names = scene.get("character_names") or []
        created, _ = req("POST", "/api/scenes", {
            "video_id": video["id"],
            "display_order": index,
            "prompt": scene["prompt"],
            "video_prompt": scene.get("video_prompt") or "",
            "character_names": names,
            "chain_type": "ROOT",
        }, base=base)
        patched, _ = req("PATCH", "/api/scenes/%s" % created["id"], {
            "narrator_text": scene.get("narrator_text") or "",
        }, base=base)
        scenes_out.append(patched)
    req("PUT", "/api/active-project", {"project_id": project_id}, base=base)
    return {
        "project_id": project_id,
        "video_id": video["id"],
        "orientation": video.get("orientation"),
        "mc_id": mc["id"],
        "title": title,
        "scenes": [
            {
                "id": scene.get("id"),
                "display_order": scene.get("display_order"),
                "narrator_text": scene.get("narrator_text"),
                "chain_type": scene.get("chain_type"),
            }
            for scene in scenes_out
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create VERTICAL Radar short scenes")
    parser.add_argument("spec", help="short-spec JSON path or - for stdin")
    parser.add_argument("--project-id", default=os.environ.get("FLOW_PROJECT_ID", DEFAULT_PROJECT))
    parser.add_argument("--run-day", default="")
    parser.add_argument("--base", default=os.environ.get("FLOWKIT_BASE", DEFAULT_BASE))
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    if args.spec == "-":
        spec = json.load(sys.stdin)
    else:
        with open(args.spec, encoding="utf-8") as handle:
            spec = json.load(handle)
    result = build_short(spec, args.project_id, args.run_day, args.base)
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
