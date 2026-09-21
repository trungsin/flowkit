---
title: Radar News → daily AI-news Shorts
date: 2026-09-21
status: agreed
project: ef10b9d7-925c-4306-add6-a6c3f5a73da0
source_digest: https://radarnews-pipeline.dxmt.workers.dev/digest/{date}?format=json
---

# Radar News → Shorts hằng ngày

## Problem

Muốn ra video AI-news **hàng ngày** vào Flow project `ef10b9d7…`, nguồn = digest
`radarnews-pipeline.dxmt.workers.dev/digest/{date}`. Cần: (1) chọn tin **khả dụng**,
(2) biến tin **trừu tượng** (AI/model, không nhân vật/cảnh) thành video.

## Input thật (digest JSON, `?format=json`)

```
question · run_day · status ("ok" | chưa run) · documents[]
communities[] = cụm tin, mỗi cái:
  heat(float) · size(int) · label_vi · insight · counter · evidence_json[{claim,url,source}]
```

Ngày 19/09: 12 communities. Ranh giới data tự nhiên = topic **có evidence** vs
**tag trần** (ev=0: llama/mistral/mcp/reasoning/flux). Heat cao KHÔNG đủ (llama
heat 43, ev=0 → vô dụng). **7/12 khả dụng.**

## Approaches (đã cân nhắc)

| Trục | Chọn | Loại |
|---|---|---|
| Hình hóa tin trừu tượng | **MC cố định + B-roll** | Cinematic khái niệm (dễ AI-slop); MC+minh họa (đắt/ngày) |
| Phạm vi | **Mỗi topic 1 Short** | 1 video tổng hợp; nhiều video/topic |
| Kênh | **Short ~60s dọc (VERTICAL)** | Long-form; cả hai |
| Lọc tin | **evidence≥2 + insight≠""** | heat threshold; Top-K thô |
| Cap/ngày | **Không cap (hết topic khả dụng ~7)** | Top3 / Top5 |
| Style | **Realistic (tin tức)** | 3D Pixar; anime |
| MC | **C — chuyên gia thân thiện** | A anchor pro; B dẫn trẻ |

## Giải pháp chốt

**Pipeline "Radar → Shorts", gói thành skill mới `/fk-radar-daily <date>`**, ghép
các fk-* sẵn có. Continuity-chain BỎ (news = cắt cứng, scene ROOT độc lập).

### 1. Chọn tin khả dụng
- `GET /digest/{date}?format=json`
- Gate ngày: `status=="ok"` và `communities` không rỗng.
- Lọc topic: `len(evidence_json)>=2` AND `insight` không rỗng (tự loại tag trần).
- Xếp `heat` giảm dần. Không cap.

### 2. Cấu trúc 1 Short ~60s (~5–6 scene, VERTICAL)
| Scene | Nội dung | Field |
|---|---|---|
| 1 Hook | MC mở theo `label_vi` | `character_names=[MC]` |
| 2–4 Thân | mỗi `claim` → 1 B-roll **artifact cụ thể** | `character_names=[]`, ROOT |
| 5 Phản biện | beat từ `counter` | B-roll / MC |
| 6 Outro | MC chốt + CTA | `character_names=[MC]` |

### 3. Sinh kịch bản (tiền-Flow, dùng Claude)
`{insight, evidence[claims], counter}` → kịch bản VN **18–22 từ/scene** → sinh:
`narrator_text` (TTS) + `prompt`/`video_prompt` mỗi scene + text-overlay
(headline + `source`). Overlay nguồn = độ tin cậy tin tức.

### 4. MC entity (tạo 1 lần, tái dùng mọi ngày)
`character` "chuyên gia thân thiện": ~28, áo thun tối + blazer casual, ngồi bàn
laptop, hậu cảnh ấm (kệ sách/cây); giọng gần gũi. Một outfit cố định (luật entity).

### 5. Dựng
`POST /api/videos` (VERTICAL) → scenes → `/fk-gen-images` → `/fk-gen-videos`
→ `/fk-gen-narrator` → `/fk-gen-text-overlays` → `/fk-concat`. Chạy **tuần tự
từng topic** để không nghẽn (`MAX_CONCURRENT_REQUESTS=5`, captcha mỗi gen).

## Ràng buộc & rủi ro

- **Không headless/cron thật.** Flow ký request trong tab → "hàng ngày" = lệnh
  bán tự động, người **giữ 1 tab `flow.google.com` đăng nhập** suốt mẻ.
- **Runtime hiện TRẮNG:** agent `:8100` down, không DB, `FLOW_PROJECT_ID` rỗng →
  bước 0 mọi ngày: agent + extension connected + pin Flow project.
- **B-roll AI-slop** → tả artifact cụ thể trong claim (model card HF, OCR trích
  chữ, code cuộn), cấm "não AI phát sáng chung chung".
- **Volume ~7/ngày** = ~35 scene image+video → mẻ dài; batch tuần tự + `/fk-monitor`.
- **Tin quá trừu tượng** vẫn khó hình → MC gánh phần kể, B-roll chỉ minh họa.

## Success

- Chạy `/fk-radar-daily 2026-09-19` → đúng 7 Short dọc, mỗi topic 1 cái, có MC
  nhất quán + overlay nguồn.
- 0 topic tag-trần lọt vào (evidence gate).
- TTS đọc mượt 18–22 từ/scene; concat 1 mạch/short.

## Next

- `/ck:plan` cho `/fk-radar-daily`: phase (a) fetch+filter, (b) script-gen từ
  evidence, (c) MC entity + tạo video/scenes VERTICAL, (d) pipeline gen+concat,
  (e) orchestrator skill.
- Trước chạy thật: dựng runtime + tạo/pin Flow project cho `ef10b9d7…`.

## Unresolved

- Voice ID cụ thể cho giọng "gần gũi" (chọn khi làm `/fk-gen-tts-template`).
- Digest có bao nhiêu ngày lịch sử / ngày thiếu run xử lý ra sao (skip có log).
- CTA/outro cố định nội dung gì (brand kênh).
