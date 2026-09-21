---
title: Scene continuity — one walk chain
date: 2026-09-21
status: agreed
project: 6dbe4d91-8287-4177-98dd-5feb0578244d
video: 52e48fa6-c8c4-49ed-bf6b-fa83deaa70fa
---

# Scene continuity: one walk chain

## Summary

TTS/concat OK. Visual cuts fail eyeline: Pip faces water (cannot see lantern lighter) then next shot shows stall. User approved **B — one walk chain**. Lock geography on one pier axis. Regen images+videos. Keep TTS unless shot count/duration changes.

## Problem

Tap 1 has 3 ROOT chains. Concat hard-cuts 3→4 (dock→stall) and 6→7 (stall→night water). CONTINUATION stills jump camera (empty wide → Pip looking at water → stall). Omni first+last morphs between those stills — cannot invent a head-turn that the stills do not contain.

User example: frontal dock look ≠ line of sight to keeper.

## Approaches

| | A keep 8 slots | **B one walk (chosen)** | C recut only |
|---|---|---|---|
| Idea | Patch eyeline, keep 3 blocks | One CONTINUATION after establish | Trim/xfade existing |
| Pros | Less structure change | Geography correct | Cheap |
| Cons | ROOT stall still teleports without arrival beat | Regen most shots | Cannot fix stills |
| Pick | no | **yes** | no |

INSERT close-ups deferred (YAGNI until axis locked).

## Agreed solution

**One camera axis: looking down the pier.** Stall/lanterns always in deep background until arrival. No ROOT jump into stall. Release lantern = walk **back** along same dock, not new location.

### Beat sheet (7 shots, 1 chain)

| # | Type | Beat | Last frame (handoff) |
|---|---|---|---|
| 0 | ROOT | Wide down pier, golden hour. Stall+unlit lanterns at vanishing point. No Pip or tiny silhouette. | Same axis, stall still in frame |
| 1 | CONT | Pip at crate, **same axis**, looking **toward lanterns** (3/4 or over-shoulder). Water is side, not eyeline. | Pip looking down pier |
| 2 | CONT | Pip walks toward stall. Camera behind/slightly side. Stall grows. Face glance-back optional if 3/4. | Pip closer, stall readable |
| 3 | CONT | Arrival: keeper already on this axis, lighting. Two-shot width, both faces. | Pip at stall, keeper in frame |
| 4 | CONT | Keeper hands Paper Lantern. Close two-shot. | Pip holding lantern, facing stall then start turn |
| 5 | CONT | Pip turns back toward water, walks **same boards**. Lantern in paws. | Pip at water edge |
| 6 | CONT | Kneel, set lantern on water. Blue hour on **same dock**. | Lantern drifting, Pip watching |

Old mapping: 0 keep/rewrite axis; 1 rewrite eyeline (not water); 2–3 walk; 4+5 merge into 3; 6→4; 7→5–6.

### Regen

- PATCH `prompt` / `video_prompt` / `transition_prompt` to beat sheet. Camera movement = own sentence. Prompt = action+axis only.
- Images: GENERATE/REGENERATE shot 0 if axis wrong. EDIT_IMAGE 1→6 **in wave order**. Parent last still = child first still.
- Videos: Omni **first+last** for 0–5 (end = child image). Shot 6 leaf = first-frame i2v.
- Cascade: regen parent image → must regen child images then videos.
- TTS: keep NamMinh lines if 7 shots; merge two narrator lines (old 0+1 setup, old 4+5 arrival) to 18–22 words. Re-concat with xfade **one** chain.
- Do not FLOW_ALLOW_DEGRADED Veo path. Do not INSERT yet.

### Keep

- Entities + refs (Pip, Harbor Dock, Stall, Keeper, Paper Lantern)
- Material `3d_pixar`, HORIZONTAL, Flow UUID
- Voice `vi-VN-NamMinhNeural` unless duration breaks

## Risks

- EDIT_IMAGE may still drift look — fail = tighter prompt + same refs, not new character.
- 7 vs 8 TTS files — remap then concat-fit.
- First+last still morphs if last frame of N is not child’s still — **must** set `horizontal_end_scene_media_id` after each child image.

## Success

- Watch 0→6: never lose stall on the pier until arrival; never see keeper until Pip could see them.
- No hard cut to a new set.
- TTS still readable; concat one chain xfade.

## Next

Implement: PATCH scenes → image waves → Omni videos → remap TTS → concat.
Optional: `/ck:plan` for phase files.
