fk-radar-daily — Daily AI-news Shorts from a Radar News digest (Grok via CLIProxyAPI)

Usage: `/fk-radar-daily <date>`

Turns that day's Radar digest into one VERTICAL ~60s Short per **usable** topic
(evidence≥2 and non-empty insight). Script-gen is **Grok through CLIProxyAPI**
(ClipProxyAL), not the driving CLI. Scenes are independent ROOT cuts. Material:
realistic. Project: `ef10b9d7-925c-4306-add6-a6c3f5a73da0`.

Do **not** write a looping generate script. Images/videos go through
`POST /api/requests/batch`. On pipeline errors invoke `/fk-doctor`.

---

## Step 0 — Preflight

```bash
curl -s http://127.0.0.1:8100/health
curl -s http://127.0.0.1:8100/api/flow/status
```

Need `extension_connected: true` and a pinned `flow_project_id`. If either is
missing: start the agent, reload the Chrome extension, leave one signed-in
`https://flow.google.com/` tab open, pin `FLOW_PROJECT_ID=ef10b9d7-925c-4306-add6-a6c3f5a73da0`.
Flow Kit cannot create the Flow project.

```bash
curl -s -o /tmp/radar_project.json -w "%{http_code}" \
  http://127.0.0.1:8100/api/projects/ef10b9d7-925c-4306-add6-a6c3f5a73da0
```

HTTP 404 → `radar_build_short.py` will `POST /api/projects` with
`flow_project_id` + `material: realistic`. Confirm that POST succeeds before
spending captcha. Export CLIPROXY_* from `.env` if the shell has not.

Grok/CLIProxyAPI (script-gen agent):

```bash
echo "${CLIPROXY_BASE_URL:-http://127.0.0.1:8317}"
echo "${CLIPROXY_MODEL:-grok-4}"
```

If CLIPROXY is down, stop and tell the user to start CLIProxyAPI (ClipProxyAL)
with a Grok account. Do not fall back to writing the short-spec yourself.

---

## Step 1 — Chọn tin khả dụng

```bash
python3 scripts/radar_digest.py <date>
```

Stdout JSON: `{run_day, question, count, topics:[...]}`.

- `count == 0` → print `reason`, stop clean (day not run / no usable topics).
- Bare tags (llama/mistral/mcp/reasoning/flux, evidence 0) never appear.

---

## Step 2 — In kế hoạch, confirm

Print a table: `# | heat | label_vi | claims`. Shorts to create = `count`.
Ask before spending captcha. No daily cap — do every usable topic.

---

## Step 3 — Ensure MC + voice (idempotent)

MC entity name is **Friendly Expert** (English). `scripts/radar_build_short.py`
creates it once per project (skips if the name exists).

Voice template: `/fk-gen-tts-template` once, close conversational male. Reuse
the template id for every topic. If templates already exist, reuse.

Project material must be `realistic`.

---

## Step 4 — Per topic (sequential, never parallel)

For each topic, in heat order:

### 4a. Script-gen (Grok via CLIProxyAPI)

Write the topic JSON, then the short-spec file (do not leave the spec on stdin):

```bash
python3 scripts/radar_digest.py <date> > /tmp/radar_digest.json
python3 -c "import json; d=json.load(open('/tmp/radar_digest.json')); json.dump(d['topics'][N], open('/tmp/radar_topic.json','w'), ensure_ascii=False)"
python3 scripts/radar_scriptgen.py /tmp/radar_topic.json > /tmp/radar_spec.json
```

Grok returns 5–6 scenes: hook (MC) → one B-roll per claim (max 3) → counter → outro (MC).
`narrator_text` Vietnamese 18–22 words. Prompts English, action only. B-roll names
a concrete artifact from the claim.

### 4b. Video + scenes

```bash
python3 scripts/radar_build_short.py /tmp/radar_spec.json \
  --project-id ef10b9d7-925c-4306-add6-a6c3f5a73da0 --run-day <date>
```

Creates `POST /api/videos` `orientation:VERTICAL` (reuses title+day if present),
ROOT scenes, PATCH `narrator_text`, PUT active-project. Save `video_id`.

### 4c. Generate (fail loud, then `/fk-doctor`)

1. `/fk-gen-refs` for **every** project entity missing `media_id` (not only MC).
   `/fk-gen-images` aborts if any linked entity lacks a UUID.
2. `/fk-gen-images <PID> <VID>` — all ROOT, GENERATE_IMAGE wave. Orientation
   from the video (`VERTICAL`).
3. `/fk-gen-videos <PID> <VID>`. If worker Veo hits `MODEL_ACCESS_DENIED` or
   `UNSUPPORTED_ON_BATCH_API`, Omni Flash i2v per scene:

```bash
curl -X POST http://127.0.0.1:8100/api/flow/generate-video \
  -H "Content-Type: application/json" \
  -d '{"model_family":"omni_flash","start_image_media_id":"<vertical_image_media_id>","prompt":"<video_prompt>","project_id":"<PID>","scene_id":"<SID>","duration_s":8,"resolution":"720p","aspect_ratio":"VIDEO_ASPECT_RATIO_PORTRAIT","user_paygate_tier":"PAYGATE_TIER_TWO"}'
```

   Poll `POST /api/flow/check-status` until a signed `flow-content.google/video/`
   URL exists, then PATCH `vertical_video_media_id` / `vertical_video_url` /
   `vertical_video_status=COMPLETED`. Do not PATCH on mediaId without URL.
   "Media not found" while PENDING is not fatal.
4. `/fk-gen-narrator <VID>` — **do not `--force`**. Existing `narrator_text` stays.
5. `/fk-gen-text-overlays <VID> --language vi` — headline + evidence `source`.
6. `/fk-concat-fit-narrator <VID>` — trim to narrator, burn overlay, hard cuts
   (all ROOT, no xfade chain). Then **copy** off the shared slug path so the next
   topic does not clobber this Short:

```bash
OUTDIR=$(curl -s http://127.0.0.1:8100/api/projects/<PID>/output-dir | python3 -c "import sys,json; print(json.load(sys.stdin)['path'])")
SLUG=$(python3 -c "import json; print(json.load(open('$OUTDIR/meta.json')).get('slug',''))" 2>/dev/null)
# fallback: basename of OUTDIR
cp "$OUTDIR/${SLUG:-$(basename "$OUTDIR")}_narrator_cut.mp4" \
   "$OUTDIR/radar_<date>_<stable_key>_narrator_cut.mp4"
```

   Deliverable = `radar_<date>_<stable_key>_narrator_cut.mp4`, not the slug file.

If a step FAILED: `/fk-doctor`, record the topic, continue to the next topic.
Do not rerun the whole day. Signed URL expired at concat → `/fk-refresh-urls`.

One topic at a time (captcha / `MAX_CONCURRENT_REQUESTS=5`). Optional `/fk-monitor`.

---

## Step 5 — Tổng kết

Print:

```
Radar daily <date>
  Usable topics: N
  Shorts ok:     M  path...
  Failed:        K  label + reason
```

Paths live under the project output dir (`GET /api/projects/<PID>/output-dir`).

---

## Env

| Variable | Default | Use |
|---|---|---|
| `CLIPROXY_BASE_URL` | `http://127.0.0.1:8317` | CLIProxyAPI origin |
| `CLIPROXY_API_KEY` | empty | Bearer if the proxy requires it |
| `CLIPROXY_MODEL` | `grok-4` | Grok model id on the proxy |
| `FLOWKIT_BASE` | `http://127.0.0.1:8100` | Flow Kit API |
| `FLOW_PROJECT_ID` | `ef10b9d7-…` | pin Radar Flow project |
