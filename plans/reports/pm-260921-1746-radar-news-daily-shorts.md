# PM sync-back: Radar News daily Shorts

**Plan:** `plans/260921-1717-radar-news-daily-shorts/`
**When:** 2026-09-21 17:46
**Status:** in-progress (12/17 boxes). **Not complete.**

## Progress vs plan

| Phase | Frontmatter | Boxes | Evidence |
|---|---|---|---|
| 01 digest | completed | 5/5 | live 19/09 count=7 heat desc; 8 unit tests |
| 02 script-gen + VERTICAL + MC | completed | 4/4 | `radar_scriptgen.py` + `radar_build_short.py`; 12 unit tests |
| 03 gen loop + concat | in-progress | 1/4 | skill 4c written; **no mp4** |
| 04 orchestrator | in-progress | 2/4 | skill+setup.py+preflight; **live run never** |
| **Plan** | **in-progress** | **12/17 = 71%** | journal: never `/fk-radar-daily 2026-09-19` |

Swept all 4 phase files. Did not mark live E2E done.

## Verified this session

- Live digest 2026-09-19: 7 topics, heats 51.17→12.77, ev=3 each, no bare tags.
- `.venv/bin/python -m pytest tests/unit`: **397 passed** (20 radar) in 5.89s.
- Review must-fixes in code: unique concat copy; spec **file** not 2nd stdin; Grok `{`…`}` extract + parse retry; evidence cap 3; preflight GET project; Omni `start_image_media_id`.
- Register: `AGENTS.md`, `.claude/commands/fk-radar-daily.md` (setup.py), CLAUDE.md row (hand; setup.py does not write that table).
- Env: `.env.example` + `docs/deployment.md` CLIPROXY_*.

## Scope logged

| Original | Actual | Impact |
|---|---|---|
| Claude writes spec in skill | Grok via CLIProxyAPI `radar_scriptgen.py` | need CLIPROXY `:8317` grok-4 |
| no evidence cap | cap 3 claims | 5–6 scene contract holds |
| optional build helper | `radar_build_short.py` required | ensure_project, reuse video by title |
| concat slug path | copy `radar_{date}_{stable_key}_narrator_cut.mp4` | else topic 2 clobbers topic 1 |

## Remaining (owner: **main agent** — finish the plan)

DoD = files exist, not "skill written".

| # | Action | DoD |
|---|---|---|
| 1 | Bring up agent `:8100` + extension + signed `flow.google.com` tab + pin `ef10b9d7…` + CLIPROXY | `/health` extension_connected true; GET project 200; CLIPROXY answers |
| 2 | Voice template MC (close conversational male) | template id recorded; reuse every topic |
| 3 | `/fk-radar-daily 2026-09-19` sequential | 7 paths `radar_2026-09-19_<stable_key>_narrator_cut.mp4`; failed topics listed not abort-all |
| 4 | First topic quality gate | VERTICAL ~60s, TTS 18–22, overlay source, no slug clobber, narrator_text not overwritten |
| 5 | `/fk-doctor` on FAILED | do not guess |

**This plan is the product.** Code without 7 Shorts = 0 daily factory. Do not start a new topic. Finish phase 03+04 live.

## Risks (open)

| Risk | Owner path |
|---|---|
| Leftover entities on `ef10b9d7…` abort `/fk-gen-images` | gen-refs **every** missing media_id (skill 4c) |
| Voice template id unknown | `/fk-gen-tts-template` once |
| CLIPROXY down / wrong model | stop; no Claude fallback |
| Grok real-person names in prompts → UNSAFE_GENERATION | inspect spec before gen; no validate_spec name check |
| Retry `build_short` POSTs extra scenes on reused video | skip scene create if video already has scenes |
| Runtime trắng | preflight must stop early |

Closed: concat overwrite (copy path); stdin disconnect (spec file); Grok trailing prose (brace extract); 4+ claims (cap 3); Omni 422 missing start image.

## Tests

| Suite | Result |
|---|---|
| radar 3 files | 20/20 pass 0.03s |
| tests/unit | 397 pass, 1 starlette deprecation (pre-existing) |
| live Grok | **not run** |
| live Flow gen/concat | **not run** |

## Docs impact

minor. `docs/deployment.md` CLIPROXY already. No `docs/project-roadmap.md` in repo. Journal exists.

## Blockers

None in code. Live blocked on **runtime the cook never started**: agent, extension, Flow tab, CLIPROXY, voice template.

## Next actions (concrete)

1. **Main agent** — run remaining plan to DoD. Owner: main. Done = 7 unique 19/09 Shorts + summary table.
2. **Main agent** — if preflight fails, fix runtime first; do not rewrite digest/scriptgen.
3. **Main agent** — after 1 live topic mp4, then continue heat-order remaining 6. Fail loud per topic.

## Unresolved questions

- CLIPROXY actually on `:8317` with `grok-4` here?
- Project `ef10b9d7-925c-4306-add6-a6c3f5a73da0` in local/VPS DB, material=realistic, leftover entities?
- Voice template id for close conversational male?
- Run `/fk-review-video` despite plan skip (AGENTS.md says review before upscale; plan skipped upscale)?
- Should `build_short` skip scene POST when title already has scenes?
