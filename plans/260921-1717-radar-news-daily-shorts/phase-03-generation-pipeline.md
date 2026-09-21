---
phase: 3
title: "Per-topic generation pipeline + concat-fit-narrator"
status: in-progress
priority: P2
effort: "3h"
dependencies: [2]
progress: 1/4
verified: 2026-09-21
---

# Phase 3: Generation pipeline

## Overview
Với mỗi topic đã có video+scenes (Phase 2), chạy chuỗi gen của Flow Kit đến ra file
Short cuối, tuần tự từng topic để không nghẽn captcha.

## Requirements
- Functional (mỗi topic, đúng thứ tự):
  1. `/fk-gen-images <PID> <VID>` — scene ROOT → toàn bộ Wave 1 GENERATE_IMAGE.
  2. `/fk-gen-videos <PID> <VID>` — i2v từ ảnh scene.
  3. `/fk-gen-narrator <VID>` — narrator_text đã set sẵn → **skip auto-gen**, chỉ TTS
     bằng voice template MC (giọng gần gũi).
  4. `/fk-gen-text-overlays <VID>` — overlay headline + `source` từ narrator/evidence.
  5. `/fk-concat-fit-narrator <VID>` — trim mỗi scene theo narrator + burn overlay →
     Short dọc ~60s.
- Non-functional: chạy **tuần tự topic-này-xong-mới-topic-sau** (không bung song song),
  tôn trọng `MAX_CONCURRENT_REQUESTS=5`; dùng `/fk-monitor` theo dõi; lỗi pipeline →
  `/fk-doctor` trước khi đoán.

## Architecture
Không code mới — orchestration bằng cách gọi các skill fk-* sẵn có theo thứ tự. Voice
template MC tạo một lần (`/fk-gen-tts-template`) rồi tái dùng. Concat dùng bản
*fit-narrator* (không phải `/fk-concat` thường) vì cần tight + overlay.

## Related Code Files
- Read/orchestrate: `skills/fk-gen-images.md`, `fk-gen-videos.md`, `fk-gen-narrator.md`,
  `fk-gen-text-overlays.md`, `fk-concat-fit-narrator.md`, `fk-gen-tts-template.md`,
  `fk-monitor.md`, `fk-doctor.md`
- Create: phần "generation loop" trong `skills/fk-radar-daily.md` (done, step 4c)

## Sync-back 2026-09-21
Loop **written**, not **run**. Skill 4c: gen-refs all missing `media_id` → images
→ videos (Omni fallback **with** `start_image_media_id`) → narrator no `--force`
→ overlays vi → concat-fit-narrator → copy
`radar_<date>_<stable_key>_narrator_cut.mp4` (review: slug path would clobber).
`fk-gen-narrator` skip if `narrator_text` set. Journal: never live 19/09.
**Remaining:** 1 topic E2E mp4; concat-fit on real TTS; sequential 7 topics.

## Implementation Steps
1. Tạo/chọn voice template MC (một lần); ghi id để narrator TTS dùng lại.
2. Xác nhận `/fk-gen-narrator` bỏ qua scene đã có `narrator_text` (đọc skill: có, trừ
   `--force`) → không ghi đè script tin tức bằng narrator suy từ video_prompt.
3. Viết vòng lặp per-topic gọi 5 bước; dừng-và-báo nếu một bước FAILED (fail loud).
4. Nghiệm thu 1 topic end-to-end trên runtime thật (agent+extension+tab) → ra 1 mp4 dọc.

## Success Criteria
- [ ] 1 topic chạy trọn 5 bước ra Short dọc ~60s có TTS + overlay nguồn.
- [x] `/fk-gen-narrator` không ghi đè narrator_text đã set.
- [ ] Concat fit theo narrator (không thừa đuôi im lặng).
- [ ] Nhiều topic chạy tuần tự, không nghẽn/không đua captcha.

## Risk Assessment
- Volume ~7/ngày × ~5 scene image+video → mẻ dài; tuần tự + monitor, chấp nhận thời gian.
- URL signed hết hạn giữa mẻ dài → `/fk-refresh-urls` khi concat báo hết hạn.
- i2v ra tĩnh/nhợt cho cảnh abstract → tighten video_prompt (camera là 1 câu riêng).
