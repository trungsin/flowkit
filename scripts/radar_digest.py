#!/usr/bin/env python3
"""Fetch a Radar News digest and emit usable topics as JSON."""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

DIGEST_TMPL = "https://radarnews-pipeline.dxmt.workers.dev/digest/{date}?format=json"


def evidence_list(topic: dict) -> list:
    raw = topic.get("evidence_json")
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    if not isinstance(raw, str) or not raw.strip():
        return []
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [item for item in parsed if isinstance(item, dict)]


def filter_usable(raw: dict | None) -> dict:
    data = raw or {}
    status = data.get("status")
    communities = data.get("communities") or []
    if not isinstance(communities, list):
        communities = []
    run_day = data.get("run_day")
    question = data.get("question")
    if status != "ok" or not communities:
        reason = "digest not ready" if status != "ok" else "no communities"
        return {
            "run_day": run_day,
            "question": question,
            "count": 0,
            "reason": reason,
            "topics": [],
        }

    topics = []
    for community in communities:
        evidence = evidence_list(community)
        insight = (community.get("insight") or "").strip()
        if len(evidence) < 2 or not insight:
            continue
        try:
            heat = float(community.get("heat") or 0)
        except (TypeError, ValueError):
            heat = 0.0
        try:
            size = int(community.get("size") or 0)
        except (TypeError, ValueError):
            size = 0
        topics.append({
            "stable_key": community.get("stable_key") or community.get("label_vi") or "",
            "heat": heat,
            "size": size,
            "label_vi": community.get("label_vi") or "",
            "insight": insight,
            "counter": community.get("counter") or "",
            "evidence": [
                {
                    "claim": item.get("claim") or "",
                    "url": item.get("url") or "",
                    "source": item.get("source") or "",
                }
                for item in evidence[:3]
            ],
        })
    topics.sort(key=lambda item: item["heat"], reverse=True)
    return {
        "run_day": run_day,
        "question": question,
        "count": len(topics),
        "topics": topics,
    }


def fetch(date: str, timeout: int = 15) -> dict:
    url = DIGEST_TMPL.format(date=date)
    request = urllib.request.Request(url, headers={
        "Accept": "application/json",
        "User-Agent": "FlowKit-radar-digest/1.0",
    })
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode())
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        raise RuntimeError("digest fetch failed for %s: %s" % (date, exc)) from exc


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    date = args[0] if args else datetime.now(timezone.utc).strftime("%Y-%m-%d")
    payload = filter_usable(fetch(date))
    if not payload.get("run_day"):
        payload["run_day"] = date
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
