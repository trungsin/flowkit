---
title: Radar News → daily AI-news Shorts (/fk-radar-daily)
status: in-progress
date: 2026-09-21
source: plans/reports/260921-1717-radar-news-daily-shorts.md
project_id: ef10b9d7-925c-4306-add6-a6c3f5a73da0
digest: https://radarnews-pipeline.dxmt.workers.dev/digest/{date}?format=json
progress: 12/17
blockedBy: []
blocks: []
---

# /fk-radar-daily — daily AI-news Shorts

Biến digest AI-news mỗi ngày → nhiều Short dọc ~60s (mỗi topic khả dụng 1 Short) vào
Flow project `ef10b9d7…`. MC cố định "chuyên gia thân thiện" + B-roll. Realistic.
Scene ROOT cắt cứng (không continuity-chain). Deliverable = script `radar_digest.py`
+ skill `skills/fk-radar-daily.md`, ghép các fk-* sẵn có.

**Chốt thiết kế:** report `plans/reports/260921-1717-radar-news-daily-shorts.md`.

## Ràng buộc nền

- Flow ký request **trong tab** → không headless/cron thật. Bán tự động, giữ 1 tab
  `flow.google.com` đăng nhập suốt mẻ.
- Runtime hiện **trắng**: agent `:8100` down, không DB, `FLOW_PROJECT_ID` rỗng.
  → mỗi ngày bước 0: agent + extension connected + pin Flow project `ef10b9d7…`.
- `narrator_text` là field scene (set thẳng); `orientation:"VERTICAL"` set ở POST
  `/api/videos`; skill sinh AGENTS.md qua `setup.py` từ `skills/fk-*.md`.

## Phases

| Phase | File | Status |
|---|---|---|
| 01 Digest fetch + filter ("chọn tin khả dụng") + tests | [phase-01-digest-fetch-filter.md](phase-01-digest-fetch-filter.md) | completed (5/5) |
| 02 Script-gen contract + VERTICAL video/scenes + MC entity | [phase-02-scriptgen-scenes.md](phase-02-scriptgen-scenes.md) | completed (4/4) |
| 03 Per-topic generation pipeline + concat-fit-narrator | [phase-03-generation-pipeline.md](phase-03-generation-pipeline.md) | in-progress (1/4) |
| 04 Orchestrator skill /fk-radar-daily + register + preflight | [phase-04-orchestrator-skill.md](phase-04-orchestrator-skill.md) | in-progress (2/4) |

Sync-back 2026-09-21 17:46. Code 1–4 shipped. Live `/fk-radar-daily 2026-09-19`
**not run**. 12/17 success boxes. Tests: 20 radar + 397 unit pass.

**Scope:** script-gen = Grok/CLIProxyAPI (`radar_scriptgen.py`), not Claude.
Evidence claims cap 3. `radar_build_short.py` required. Concat copy unique
`radar_{date}_{stable_key}_narrator_cut.mp4`.

**MUST finish:** live 7 Shorts 19/09. Owner = main agent. Plan not done until
those mp4 exist.

## Dependencies

- Phase 2 dùng shape JSON output của Phase 1.
- Phase 3 dùng scenes tạo ở Phase 2.
- Phase 4 gói 1→3 thành 1 lệnh; cần runtime + Flow project pinned để chạy thật.

## Success

`/fk-radar-daily 2026-09-19` → đúng số topic khả dụng (7/12 hôm đó) Short dọc, mỗi
topic 1 cái, MC nhất quán + overlay nguồn, 0 tag-trần lọt lưới, TTS 18–22 từ/scene,
concat 1 mạch fit narrator.

## Non-goals

- Continuity-chain, INSERT close-up, Veo r2v/upscale (không cần cho news cuts).
- Cron/headless thật (Flow không cho).
- Cap số Short (user chọn làm hết topic khả dụng).
