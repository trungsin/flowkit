---
phase: 1
title: Rewrite 7-beat script + PATCH scenes
status: pending
priority: P1
effort: 1h
dependencies: []
---

# Phase 1: Rewrite beats

## Overview
Replace 8-scene / 3-ROOT structure with 7 shots on one axis. PATCH prompts; archive or leave unused old scenes unused (new video preferred).

## Requirements
- Functional: 7 scenes, shot 0 ROOT, 1–6 CONTINUATION, parent links 0→1→…→6
- `character_names` match who is on axis that shot
- `transition_prompt` on 0–5 (parent has child). Leaf 6 = `video_prompt` only
- Prompt = action + axis. No appearance. Camera = own sentence

## Architecture
New video `Tap 1: Long Den Tren Song (walk)` HORIZONTAL on same project, keep old video as archive. Avoid mutating smoke-test video `e935ad53`.

## Related Code Files
- Modify: scene rows via API only (`PATCH`/`POST /api/scenes`, `POST /api/videos`)
- No app code

## Implementation Steps
1. `POST /api/videos` title `Tap 1 walk-chain`, orientation HORIZONTAL
2. Create 7 scenes in order with parent_scene_id chain
3. Beat copy from report table (0 establish down-pier → 6 lantern on water)
4. PUT active-project
5. Print order table

## Success Criteria
- [ ] 7 scenes, one parent chain, no extra ROOT after 0
- [ ] Shot 1 eyeline = toward stall, not open water
- [ ] Shot 3 first visible keeper is on same pier axis

## Risk Assessment
Old 8-scene video remains; do not delete until new concat signed off.
