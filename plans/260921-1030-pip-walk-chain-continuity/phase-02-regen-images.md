---
phase: 2
title: Image waves ROOT then EDIT
status: pending
priority: P1
effort: 1h
dependencies: [1]
---

# Phase 2: Regen images

## Overview
Shot 0 GENERATE_IMAGE. Shots 1–6 EDIT_IMAGE in waves (parent COMPLETED + UUID first).

## Requirements
- All refs have UUID media_id before start
- Orientation HORIZONTAL
- After each child completes, parent `horizontal_end_scene_media_id` = child image UUID (worker usually sets this; verify)

## Architecture
Batch `/api/requests/batch`. Waves: [0] → [1] → [2] → [3] → [4] → [5] → [6]. Never EDIT before parent image UUID.

## Related Code Files
- API only

## Implementation Steps
1. Confirm 5 entity media_ids UUID
2. Batch GENERATE_IMAGE scene 0
3. Poll; abort on FAILED / CAMS id
4. EDIT_IMAGE 1 through 6 sequential waves
5. Table: order, type, status, media_id

## Success Criteria
- [ ] 7 COMPLETED horizontal image UUIDs
- [ ] Parents 0–5 have end_scene_media_id = next shot image

## Risk Assessment
Look drift on EDIT → REGENERATE_IMAGE that shot only, keep refs. UNSAFE_GENERATION → strip identifying words, retry that id only.
