---
phase: 1
title: "Digest fetch + filter (chọn tin khả dụng)"
status: completed
priority: P1
effort: "3h"
dependencies: []
progress: 5/5
verified: 2026-09-21
---

# Phase 1: Digest fetch + filter

## Overview
Lấy digest JSON của một ngày, lọc ra các topic **khả dụng** để làm video, emit JSON
sạch cho các phase sau. Đây là bước "check tin nào khả dụng" — chạy được độc lập,
không cần agent/Flow.

## Requirements
- Functional:
  - Fetch `GET https://radarnews-pipeline.dxmt.workers.dev/digest/{date}?format=json`.
  - Gate ngày: `status=="ok"` và `communities` không rỗng → nếu không, exit sạch với
    lý do (không crash), phù hợp ngày chưa có run.
  - Lọc topic khả dụng: `len(parse(evidence_json))>=2` **AND** `insight.strip()!=""`.
    (Tự loại tag-trần ev=0: llama/mistral/mcp/reasoning/flux.)
  - Xếp theo `heat` giảm dần. Không cap.
  - Emit JSON: `{run_day, question, count, topics:[{stable_key, heat, size, label_vi,
    insight, counter, evidence:[{claim,url,source}]}]}`.
- Non-functional: parse phòng thủ (evidence_json là **string** chứa JSON; có thể lỗi
  → coi như 0 evidence, không raise). Timeout HTTP. Không phụ thuộc agent.

## Architecture
Script thuần: `scripts/radar_digest.py`, hàm tách bạch `fetch(date) -> raw`,
`filter_usable(raw) -> topics`, `main()` in JSON ra stdout. `filter_usable` nhận dict
(không network) → test dễ. `stable_key` giữ để dedup/đặt tên video về sau.

## Related Code Files
- Create: `scripts/radar_digest.py` (done)
- Create: `tests/unit/test_radar_digest.py` (done, 8 tests)
- Read: `plans/reports/260921-1717-radar-news-daily-shorts.md` (schema + ranh giới)

## Sync-back 2026-09-21
Shipped. Live `python3 scripts/radar_digest.py 2026-09-19` → count=7, heat desc,
ev capped 3/topic, no llama/mistral/mcp/reasoning/flux. UA `FlowKit-radar-digest/1.0`.
`filter_usable` no-network. Scope add: evidence[:3] (review 5–6 scene contract).

## Implementation Steps
1. `fetch(date, timeout=15)` — urllib/requests GET `?format=json`, trả dict; lỗi mạng
   → raise RuntimeError có message rõ.
2. `_evidence(topic) -> list` — `json.loads(topic["evidence_json"])` bọc try, non-list
   → `[]`.
3. `filter_usable(raw) -> list` — gate status/communities; giữ topic đạt evidence≥2 +
   insight≠""; map sang shape gọn; sort heat desc.
4. `main()` — argv `date` (mặc định hôm nay UTC), gọi fetch+filter, `json.dumps(...,
   ensure_ascii=False, indent=2)`; nếu 0 topic → in `{count:0, reason:...}` exit 0.
5. Tests: fixture nhỏ mô phỏng 19/09 (mix ev=3 và ev=0, một tag-trần) → assert 7 giữ,
   5 loại, đúng thứ tự heat; status!="ok" → count 0; evidence_json hỏng → topic bị loại
   chứ không raise.

## Success Criteria
- [x] `python scripts/radar_digest.py 2026-09-19` in ra 7 topic đúng thứ tự heat.
- [x] Tag-trần (llama/mistral/mcp/reasoning/flux) không lọt.
- [x] `status` chưa-run → exit 0, count 0, có `reason`.
- [x] `evidence_json` lỗi cú pháp → topic loại, không crash.
- [x] Test mới xanh; không chạm code hiện có.

## Risk Assessment
- Digest đổi schema (thêm/bớt field) → parse theo `.get`, chỉ hard-depend `status`,
  `communities`, `heat`, `insight`, `evidence_json`. Nếu thiếu `heat` → coi 0, sort cuối.
- `?format=json` đổi contract → test dùng fixture tĩnh, không gọi mạng trong CI.
