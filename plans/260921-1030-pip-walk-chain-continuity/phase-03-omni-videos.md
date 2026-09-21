---
phase: 3
title: Omni first+last videos
status: pending
priority: P1
effort: 1.5h
dependencies: [2]
---

# Phase 3: Omni videos

## Overview
Do **not** queue GENERATE_VIDEO (Veo chain UNSUPPORTED / MODEL_ACCESS_DENIED). Use `POST /api/flow/generate-video` `model_family=omni_flash`.

## Requirements
- Shots 0–5: start=own image, end=child image, prompt=`transition_prompt`
- Shot 6: start=own image, no end, prompt=`video_prompt`
- duration_s=8, 720p, LANDSCAPE, TIER_TWO
- PATCH scene horizontal_video_* on SUCCESS

## Architecture
Throttle ~8s between submits (extension captcha). Poll `/api/flow/check-status` with operations.

## Related Code Files
- API only. Worker queue unused for this phase.

## Implementation Steps
1. Health + extension_connected
2. Submit 7 Omni jobs
3. Poll until SUCCESS/FAIL
4. PATCH media_id + fifeUrl + COMPLETED
5. Retry FAILED once; then stop and report

## Success Criteria
- [ ] 7 COMPLETED video UUIDs
- [ ] No Veo UNSUPPORTED errors

## Risk Assessment
Captcha / NO_FLOW_TAB → open flow.google.com. MODEL_ACCESS_DENIED on Omni → try TIER_ONE once.
