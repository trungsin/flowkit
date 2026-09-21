# Code Review — Radar News daily Shorts (`/fk-radar-daily`)

Date: 2026-09-21
Reviewer: staff-engineer (production-readiness)
Plan: `plans/260921-1717-radar-news-daily-shorts/`
Score: **6 / 10**

Grep-verified against live digest `2026-09-19` / `2026-09-21`, API models (`SceneCreate` has no `narrator_text`; `VideoCreate` accepts `orientation`), `fk-concat-fit-narrator` output path, and `POST /api/flow/generate-video` body. Unit tests: 17 passed.

---

## Code Review Summary

### Scope
- Files:
  - `scripts/radar_digest.py` (101)
  - `scripts/radar_scriptgen.py` (157)
  - `scripts/radar_build_short.py` (121)
  - `tests/unit/test_radar_digest.py` (142)
  - `tests/unit/test_radar_scriptgen.py` (122)
  - `tests/unit/test_radar_build_short.py` (110)
  - `skills/fk-radar-daily.md` (140)
  - `.env.example`, `docs/deployment.md`, `CLAUDE.md` (skill row)
- LOC: ~972 across listed files (implementation ~379)
- Focus: recent Radar Shorts feature (uncommitted)
- Scout findings: concat path collision; 4a/4b stdin disconnect; Grok JSON trailing-prose; 5–6 scene vs unbounded evidence; preflight misses local project; Omni fallback omits `start_image_media_id`; `fk-gen-images` aborts on any project entity without `media_id`

### Overall Assessment
Digest filter is the strongest piece: defensive parse, UA (workers.dev 403s Python-urllib default UA), live 19/09 shape still yields 7 usable topics with 3 claims each, unready days return `status=pending` and exit clean. Grok-via-CLIProxyAPI matches the user override (plan text still says Claude). Production path will lose Shorts and drop topics: concat writes one project-level mp4, script-gen contract cannot accept 4+ claims, skill 4b reads stdin that 4a already consumed, and Grok JSON is only retried on *validation* not *parse*.

### Critical Issues

1. **All topics overwrite one concat file (data loss)**
   - `/fk-concat-fit-narrator` always writes `${OUTDIR}/${SLUG}_narrator_cut.mp4`. Radar pins one project → one slug → topic 2 clobbers topic 1. Success criterion “7 Shorts” becomes 1 file.
   - Same dir also shares `text_overlays.json` (OK only if concat runs immediately after overlays, which the skill does).
   - Fix in `skills/fk-radar-daily.md` step 4c/5: after concat, copy/move to a unique path, e.g. `radar_{date}_{stable_key}_narrator_cut.mp4`. Do not leave the project-level name as the deliverable.

2. **Skill 4b will hang or get an empty spec**
   - 4a pipes digest → topic N → `radar_scriptgen.py -` (stdout = spec).
   - 4b is a *separate* command: `radar_build_short.py -` reading stdin again.
   - A literal follow of the skill does not connect those pipes. Agent must save a file; the skill never says so.
   - Fix: `... | python3 scripts/radar_scriptgen.py - > /tmp/radar_spec.json` then `python3 scripts/radar_build_short.py /tmp/radar_spec.json --project-id ... --run-day ...`

### High Priority

3. **Grok JSON parse is brittle; retry only runs after a successful parse**
   - `parse_json_object` is `json.loads` plus a greedy fenced-block regex. Trailing prose (`Hope this helps!`) or a leading sentence — common Grok — raises immediately. `generate_short_spec` only retries when `validate_spec` returns errors.
   - Fix: extract first `{`…matching `}`; retry parse failures once with “JSON only”.

4. **5–6 scene contract vs unbounded evidence**
   - `validate_spec` requires `5 <= len(scenes) <= 6` AND `broll count == len(claims)`.
   - 2 claims → 5 scenes, 3 claims → 6 scenes. 4+ claims cannot satisfy both. Live 19/09 and 21/09 are all 3 claims, so today it works; digest `size` already goes to 43.
   - Fix: `filter_usable` keep top 3 evidence items (or cap b-roll at 3 and relax the equality).

5. **Preflight does not prove the local project exists**
   - Checks `GET /health` + `GET /api/flow/status` (`flow_project_id` from env). Empty local DB still 404s `POST /api/videos`.
   - `ensure_mc` GETs project characters (empty if project missing), POSTs a global character, then `POST /api/projects/{pid}/characters/{cid}` — FK on → 400, orphan `Friendly Expert`. Next run creates another.
   - Fix: `GET /api/projects/ef10b9d7-…` must 200 before any POST. If 404, stop and tell the user to create/pin the project.

6. **Omni fallback payload is incomplete**
   - Skill says `POST /api/flow/generate-video` with `model_family=omni_flash` + `aspect_ratio=VIDEO_ASPECT_RATIO_PORTRAIT` only.
   - `GenerateVideoRequest` requires `start_image_media_id`, `prompt`, `project_id`, `scene_id`. Missing start frame → 422.
   - Fix: document the full body; use each scene’s `vertical_image_media_id`.

7. **No real-name / appearance check on Grok prompts**
   - News topics name labs, CEOs, products. System prompt says “No real-person names in prompts” but `validate_spec` does not check `prompt` / `video_prompt`. Flow `UNSAFE_GENERATION` is a known production failure mode (AGENTS.md rule 15).
   - `narrator_text` may use real names; image/video prompts must not.

8. **`/fk-gen-images` aborts if *any* project entity lacks `media_id`**
   - Skill only gens refs for Friendly Expert. Leftover entities on `ef10b9d7…` block the whole Short.
   - Fix: dedicated project, or gen-refs for every entity, or gen-images only for named characters.

### Medium Priority

9. **`float(heat)` / `int(size)` / `communities` not list** — schema drift raises and kills the whole digest instead of dropping the row. Wrap per-topic.
10. **`build_short` is not idempotent** — always `POST /api/videos`. Partial PATCH failure or a topic retry duplicates videos. Key on `stable_key` + `run_day` (already stored in `description`).
11. **Scripts do not load `.env`** — only `os.environ`. CLIPROXY_* in `.env.example` / VPS `.env` never reach `python3 scripts/radar_scriptgen.py` unless the shell exported them. Skill step 0 echoes defaults and looks “fine”.
12. **Material `realistic` is a comment, not a PATCH** — scene create auto-prepends whatever `project.material` is.
13. **`meta.json` orientation = `list_videos` `[0]` (`ORDER BY display_order`)** — all Radar videos use default `display_order=0`, so orientation comes from the first inserted video. Dedicated VERTICAL project is OK; a mixed project makes `fk-gen-images` read the wrong `ORI`.
14. **Plan/docs drift** — phase-02 still says Claude writes scenes; phase-04 says `setup.py` generates the CLAUDE.md table (it does not — only `AGENTS.md` + `.claude/commands/`). Plan TODOs still unchecked. CLAUDE.md row was hand-edited (harmless; `setup.py` will not wipe it).

### Low Priority

15. `Path_read` in `radar_scriptgen.py` — odd name, fine.
16. `req()` hardcodes status `200` on any success.
17. `grok_chat` HTTPError body not included in `RuntimeError` (harder to debug 401).
18. No date format check (`YYYY-MM-DD`). Live API returns `pending` for junk dates when UA is set.
19. `CLIPROXY_BASE_URL=http://host/v1/chat/completions` would double-append `/v1/chat/completions`.
20. Video `display_order` always 0 — dashboard order among ~7/day is insertion order.

### Edge Cases Found by Scout
- Workers.dev **403** if User-Agent is Python-urllib default; script sets `FlowKit-radar-digest/1.0` (tested). Unready dates are **200 + `status=pending`**, not 404 — filter handles this.
- Live 2026-09-19: 12 communities, 7 usable, every usable topic has **exactly 3** evidence rows → 6-scene spec is currently feasible.
- `SceneCreate` has no `narrator_text` → PATCH after POST is required (correct).
- `PUT /api/active-project` returns JSON — `req()` `json.loads` is safe here.
- Concat xfade only applies to CONTINUATION segments; all-ROOT → hard cuts (matches plan).
- `fk-gen-narrator` skips existing `narrator_text` unless `--force` (skill correctly forbids `--force`).
- Character slug is not UNIQUE; failed link leaves duplicate global “Friendly Expert” rows.

### Positive Observations
- Evidence gate matches the agreed ranh giới (ev≥2 + insight); bare tags (llama/mistral/mcp/reasoning/flux) drop without a denylist.
- Script-gen is Grok/CLIProxyAPI, not the driving CLI — matches the user override.
- VERTICAL on `POST /api/videos`, ROOT scenes, English MC name, Vietnamese narrator 18–22 words.
- Digest tests use fixtures (no network in CI). Fetch error wrapping and UA are tested.
- Scriptgen tests cover fence-strip, `/v1` URL normalize, Bearer, one validation retry.
- Build-short tests lock VERTICAL + ROOT + narrator PATCH + MC skip-if-exists + active-project PUT.
- 17 unit tests passed (`.venv` pytest, 0.04s).
- Files stay under 200 LOC. Skill first line is setup.py-compatible; `.claude/commands/fk-radar-daily.md` exists.

### Recommended Actions
1. **Must:** unique concat output per topic (`radar_{date}_{stable_key}_narrator_cut.mp4`).
2. **Must:** skill 4a write spec to a file; 4b read that file (not a second stdin).
3. **Must:** cap evidence at 3 *or* allow 7 scenes; retry Grok parse failures; extract JSON object from prose.
4. **Must:** preflight `GET /api/projects/{pid}`; Omni body includes `start_image_media_id`.
5. Should: reject real-person names in `prompt`/`video_prompt`; load `.env` or document `set -a; source .env`; PATCH material=realistic; idempotent video by `stable_key`+day.
6. Tests to add: 4+ claims, parse trailing prose, `ensure_mc` create+link, missing project 404, digest `status=pending` through `main()`.

### Metrics
- Type Coverage: n/a (plain Python scripts, no annotations beyond `__future__`)
- Test Coverage: 17 tests, all green; no live Grok/Flow; no concat-path test; no 4+ claim test
- Linting Issues: not run (scripts are small and compile)

### Unresolved Questions
- Is CLIProxyAPI actually on `:8317` with model id `grok-4` in this environment, or does ClipProxyAL use another port/id?
- Does project `ef10b9d7-925c-4306-add6-a6c3f5a73da0` exist in the local/VPS DB with `material=realistic` and no leftover entities?
- Voice template id for the “close conversational male” — still unresolved from the original research report.
- Should `/fk-review-video` run despite no upscale? AGENTS.md says review before upscale; plan explicitly skipped it.

### Plan TODO verification
Phase files still `status: pending` with unchecked success boxes. Implementation exists for 1–4 but is not production-ready until concat naming + 4a/4b wiring + Grok parse/cap are fixed. Do not mark phases complete.

**Status:** DONE_WITH_CONCERNS
**Summary:** Digest filter is sound and matches live Radar JSON; do not ship `/fk-radar-daily` until concat outputs are unique per topic and the skill actually pipes Grok specs into `radar_build_short`.
**Concerns/Blockers:** Concat overwrite (data loss); skill stdin disconnect; Grok JSON/5–6-scene contract; preflight/Omni payload gaps.
