---
phase: 4
title: "Orchestrator skill /fk-radar-daily + register + preflight"
status: in-progress
priority: P2
effort: "3h"
dependencies: [1, 2, 3]
progress: 2/4
verified: 2026-09-21
---

# Phase 4: Orchestrator skill

## Overview
Gói Phase 1→3 thành một lệnh `/fk-radar-daily <date>` bán tự động, đăng ký vào bộ sinh
config, và tài liệu hoá preflight runtime.

## Requirements
- Functional — `skills/fk-radar-daily.md` gồm:
  - **Step 0 Preflight:** check `GET /health` (`extension_connected:true`),
    `GET /api/flow/status` có `flow_project_id`; nếu thiếu → hướng dẫn dựng agent +
    extension + pin `FLOW_PROJECT_ID=ef10b9d7…` (Flow Kit không tự tạo project). 1 tab
    `flow.google.com` đăng nhập phải mở.
  - **Step 1 Chọn tin:** chạy `scripts/radar_digest.py <date>` → danh sách topic khả
    dụng; nếu count 0 → dừng sạch (ngày chưa run).
  - **Step 2 In kế hoạch:** liệt kê topic (label, heat, số claim) + số Short sẽ tạo, xác
    nhận trước khi tốn captcha.
  - **Step 3 Ensure MC + voice template** (idempotent).
  - **Step 4 Vòng per-topic:** script-gen → tạo video VERTICAL + scenes → pipeline gen →
    concat-fit-narrator (Phase 2+3), tuần tự.
  - **Step 5 Tổng kết:** in đường dẫn mp4 mỗi topic + topic lỗi (nếu có).
- Non-functional: mô tả dòng-đầu skill = 1 câu (setup.py lấy làm description); tuân
  convention `skills/fk-*.md`.

## Architecture
Skill markdown thuần điều phối; logic nặng đã ở `radar_digest.py` + các fk-* có sẵn.
`setup.py` scan `skills/fk-*.md` → regenerate `AGENTS.md` + `.claude/commands/`
(not the CLAUDE.md table — that row was added by hand). Run `python setup.py`
after adding the skill.

## Related Code Files
- Create: `skills/fk-radar-daily.md` (done)
- Generated: `AGENTS.md` row + `.claude/commands/fk-radar-daily.md` via `setup.py`
- Hand row: `CLAUDE.md` skill table (`setup.py` does **not** rewrite that table)
- Env: `.env.example` CLIPROXY_*; `docs/deployment.md` CLIPROXY_*
- Journal: `docs/journals/260921-radar-news-daily-shorts.md`

## Sync-back 2026-09-21
Skill+register+preflight **code done**. Preflight: `/health`, `/api/flow/status`,
`GET /api/projects/ef10b9d7…`, CLIPROXY echo. 4a writes `/tmp/radar_spec.json`;
4b reads file. **Never ran** `/fk-radar-daily 2026-09-19` (journal).
**Remaining:** live preflight on white runtime; 7 unique Shorts for 19/09.

## Implementation Steps
1. Viết `skills/fk-radar-daily.md` (Step 0–5) tái dùng nội dung Phase 2/3.
2. `python setup.py` → xác nhận skill xuất hiện trong AGENTS.md + bảng CLAUDE.md; kiểm
   `git diff` chỉ đụng file generated mong đợi.
3. Chạy thật `/fk-radar-daily 2026-09-19` trên runtime sống → nghiệm thu N Short.
4. `/ck:journal` ghi lại quyết định + số liệu.

## Success Criteria
- [ ] `/fk-radar-daily <date>` chạy full: preflight → chọn tin → per-topic → tổng kết.
- [x] Skill đăng ký đúng qua `setup.py` (không sửa tay file generated).
- [x] Preflight bắt được runtime trắng và hướng dẫn khắc phục thay vì fail mờ.
- [ ] 19/09 ra 7 Short dọc; topic lỗi được report, không kéo sập cả mẻ.

## Risk Assessment
- Sửa tay AGENTS.md/CLAUDE.md → `setup.py sync` xoá mất (đã có tiền lệ trong repo). Luôn
  qua generator.
- Chạy thật phụ thuộc runtime người dùng dựng — preflight phải rõ ràng, dừng sớm.
- Mẻ lỗi giữa chừng → per-topic độc lập, ghi topic hỏng để chạy lại riêng, không rerun cả ngày.
