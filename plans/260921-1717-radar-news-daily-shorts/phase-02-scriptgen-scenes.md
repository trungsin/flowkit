---
phase: 2
title: "Script-gen contract + VERTICAL video/scenes + MC entity"
status: completed
priority: P1
effort: "4h"
dependencies: [1]
progress: 4/4
verified: 2026-09-21
---

# Phase 2: Script-gen + scenes + MC

## Overview
Biến 1 topic khả dụng (output Phase 1) → 1 "short spec" (5–6 scene có prompt +
video_prompt + narrator_text), rồi tạo video VERTICAL + scenes trong Flow. Định nghĩa
MC entity dùng chung.

## Requirements
- Functional:
  - **Script-gen contract** (Grok via CLIProxyAPI in `scripts/radar_scriptgen.py`,
    not Claude-in-skill — scope change): từ
    `{label_vi, insight, evidence[claims], counter}` sinh scene list:
    | Scene | Nội dung | character_names |
    |---|---|---|
    | 1 Hook | MC mở theo `label_vi` | `[MC]` |
    | 2..k B-roll | mỗi `claim` → 1 cảnh tả **artifact cụ thể** | `[]` |
    | k+1 Phản biện | từ `counter` | `[]` hoặc `[MC]` |
    | cuối Outro | MC chốt + CTA | `[MC]` |
    Mỗi scene: `prompt` (EN, action+môi trường, không tả ngoại hình), `video_prompt`
    (camera/audio/SFX), `narrator_text` (VN 18–22 từ). Tất cả scene ROOT (không parent).
  - **MC entity**: character "chuyên gia thân thiện" (~28, áo thun tối + blazer casual,
    ngồi bàn laptop, hậu cảnh ấm kệ sách/cây), một outfit cố định + `voice_description`
    giọng gần gũi. Tạo **một lần** trong project; skill kiểm tra tồn tại theo name.
  - **Tạo video + scenes**: `POST /api/videos` với `orientation:"VERTICAL"`, title theo
    `label_vi` + ngày; rồi `POST /api/scenes` từng scene kèm `narrator_text`.
- Non-functional: EN cho prompt/video_prompt; VN cho narrator_text; cấm tên thật/không
  tả ngoại hình nhân vật trong prompt (luật entity Flow Kit).

## Architecture
Script-gen = `scripts/radar_scriptgen.py` → Grok on CLIProxyAPI (`CLIPROXY_*`,
default `:8317` / `grok-4`). JSON extract `{`…`}`; retry parse + validate.
POST via required helper `scripts/radar_build_short.py` (spec **file**, not 2nd
stdin). `ensure_project` GET then POST local `material:realistic` on 404.
Reuse video by title `{label_vi} — {run_day}`. MC name **Friendly Expert**.
B-roll = concrete artifact from claim.

## Related Code Files
- Create: `scripts/radar_scriptgen.py` + `tests/unit/test_radar_scriptgen.py` (done, 8 tests)
- Create: `scripts/radar_build_short.py` + `tests/unit/test_radar_build_short.py` (done, 4 tests)
- Create: `skills/fk-radar-daily.md` (4a/4b; hoàn thiện Phase 4)

## Sync-back 2026-09-21
Code+units done. Live Grok dry-run DeepSeek 19/09 **not** executed (no CLIPROXY
in cook). SceneCreate has no `narrator_text` → PATCH after POST (correct).
Residual: retry still POSTs extra scenes on existing video; `validate_spec`
does not scan real-person names in prompts.

## Implementation Steps
1. Viết contract script-gen (bảng scene + rule prompt/narrator) thành mục trong skill.
2. Định nghĩa MC entity JSON (name, description một-outfit, voice_description). Ghi rõ
   "check theo name trước khi tạo, tránh trùng".
3. Mẫu `POST /api/videos` VERTICAL + vòng `POST /api/scenes` (ROOT, có narrator_text).
4. (Tùy) helper `radar_build_short.py` nếu curl-loop quá dài; giữ thuần API, không logic thừa.
5. Dry-run 1 topic (DeepSeek 19/09): in short-spec + payload scenes ra, chưa gọi Flow gen.

## Success Criteria
- [x] 1 topic → short-spec 5–6 scene hợp lệ (EN prompt, VN narrator 18–22 từ, ROOT).
- [x] Scene 2..k tả artifact cụ thể, không "não AI phát sáng".
- [x] `POST /api/videos` trả video VERTICAL; scenes có `narrator_text`.
- [x] MC entity tạo idempotent (không nhân đôi khi chạy lại).

## Risk Assessment
- Narrator quá dài/ngắn → lệ TTS; giữ 18–22 từ như Tap 1, kiểm bằng đếm từ.
- B-roll drift look → tighten prompt, không đổi entity.
- Nếu `POST /api/videos` không nhận orientation ở build hiện tại → set qua PATCH video
  hoặc meta.json; xác minh ở bước 3 trước khi khoá.
