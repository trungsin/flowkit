---
date: 2026-09-21
topic: radar news daily shorts
---

# Journal: /fk-radar-daily cook

## Context
Wanted daily AI-news Shorts from Radar digest into Flow project
`ef10b9d7-925c-4306-add6-a6c3f5a73da0`. Cooked
`plans/260921-1717-radar-news-daily-shorts/`. Live 2026-09-19: 12 communities,
**7 usable** (evidence≥2 + insight). Heat is a trap — llama heat 43, ev=0, junk.

## What happened
Shipped `scripts/radar_digest.py`, `radar_scriptgen.py`, `radar_build_short.py`,
`skills/fk-radar-daily.md`. Review scored **6/10**. First cut would have
destroyed the day's work: `/fk-concat-fit-narrator` always writes
`${OUTDIR}/${SLUG}_narrator_cut.mp4`, one project → one slug → topic 2
clobbers topic 1. Skill 4a piped Grok spec to stdout, 4b read stdin again —
literal follow hangs. Grok trailing prose (`Hope this helps!`) blew
`json.loads`. Omni fallback omitted `start_image_media_id` → 422.
Fixed those, then stopped. Never ran live `/fk-radar-daily 2026-09-19`.

## Decisions
- Script-gen = **Grok via CLIProxyAPI/ClipProxyAL** (`CLIPROXY_BASE_URL`
  `:8317`, `CLIPROXY_MODEL=grok-4`). Plan still said Claude. User override wins.
- One Short per usable topic, VERTICAL ~60s, ROOT cuts, no continuity-chain.
- Filter evidence≥2, not heat. Cap evidence at 3 so 5–6 scene contract holds.
- Spec file `/tmp/radar_spec.json`, not a second stdin.
- Concat copy to `radar_{date}_{stable_key}_narrator_cut.mp4`.
- `ensure_project` on 404 POST local row with `material: realistic`.
- Omni i2v body includes `start_image_media_id` = scene `vertical_image_media_id`.
- Rejected: Claude-as-script-gen, one mashup video, Veo r2v/upscale, real cron
  (Flow signs in-tab; headless is a lie).

## Brutal truth
We almost shipped a "daily pipeline" that could not produce seven files and
could not even connect Grok output to scene create. Review caught it. Units
are green; Flow, extension, CLIPROXY, and the project tab were never in the
loop. That is not a daily Shorts factory. It is a dry-run with a skill on top.

## Next
Owner: whoever runs the first live day. Need agent `:8100` + extension
connected + CLIPROXY up + signed-in `flow.google.com` tab pinned to
`ef10b9d7…`. Then `/fk-radar-daily 2026-09-19`. Still open: voice template id,
leftover entities blocking `/fk-gen-images`, real-name check on Grok prompts.
