---
phase: 4
title: Remap TTS + one-chain concat
status: pending
priority: P2
effort: 1h
dependencies: [3]
---

# Phase 4: TTS + concat

## Overview
7 narrator lines (18–22 VN words), same NamMinh voice, trim to TTS+0.5s, **one** xfade chain (no hard cut between locations).

## Requirements
- PATCH narrator_text for 7 beats (merge old 0+1 and old 4+5 as needed)
- edge-tts `vi-VN-NamMinhNeural` rate +10% (OmniVoice still not on VPS)
- Output `output/thu_nghiem_long_den/tap1_walk_narrator_cut.mp4`
- mean_volume not -inf

## Architecture
Download horizontal_video_url → mix SFX 0.3 + TTS 1.5 → xfade 0.5s across all 7 as one CONTINUATION chain → concat copy.

## Related Code Files
- VPS ffmpeg in `~/bin`. No dashboard change.

## Implementation Steps
1. Write 7 lines, word-count 18–22
2. Generate wavs `tts/scene_XXX_{sid}.wav`
3. Trim/mix per concat-fit-narrator
4. Single segment xfade (all CONTINUATION after 0)
5. ffprobe duration/res/volume

## Success Criteria
- [ ] One file, ~40–55s, 1280x720, AAC
- [ ] Eyeline watch pass: no keeper before pier-axis reveal
- [ ] TTS not clipped (cut >= tts+0.5 except 8s cap)

## Risk Assessment
Scene 3 old TTS was 8s clipped — keep new lines ≤7.5s spoken.
