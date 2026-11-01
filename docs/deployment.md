# Deployment

## Platform
VPS (`len-vps` / `113.160.226.134:567`, user `lesin`) behind a Cloudflare Tunnel.

## Production URL
https://flowkit.datxanhmientrung.ai

## Deploy Command
```bash
cd dashboard && npm ci && npm run build && cd ..
bash scripts/deploy-vps.sh          # rsync + restart agent
bash scripts/deploy-vps.sh --tunnel # also create/reuse tunnel + DNS CNAME
```

SSH host alias: `len-vps` in `~/.ssh/config` (port 567, key `lesin_vps_mac_ed25519`).
Remote dir: `/home/lesin/apps/flowkit`.
Units: `~/.config/systemd/user/flowkit.service`, `flowkit-cloudflared.service`,
`cliproxyapi.service`. `flowkit-radar.timer` (08:00 Vietnam, `radar_daily_run.py`)
is **disabled since 2026-11-01**: it ran alongside phoikhi and the burst got the
Flow account held. Re-enable only when no other pipeline uses Flow:
`systemctl --user enable --now flowkit-radar.timer`.

## Environment Variables
| Variable | Description | Required |
|---|---|---|
| `API_HOST` / `API_PORT` | Bind FastAPI (keep `127.0.0.1:8100` behind the tunnel) | Yes |
| `WS_HOST` / `WS_PORT` | Chrome extension WS (`127.0.0.1:9222`) | Yes |
| `DASHBOARD_ORIGINS` | Extra allowed dashboard WS origins | Yes in prod |
| `FLOW_PROJECT_ID` | Pinned Flow project uuid | For generation |
| `FLOW_ALLOW_DEGRADED` | `1` falls chaining/r2v back to i2v | No |
| `CLIPROXY_BASE_URL` | CLIProxyAPI origin for Grok script-gen (`/fk-radar-daily`) | For news shorts |
| `CLIPROXY_API_KEY` | Bearer for CLIProxyAPI if required | No |
| `CLIPROXY_MODEL` | Script-gen model on the proxy (default `gpt-5.6-luna`; see model note below) | No |
| `FLOWKIT_BASE` | Flow Kit API origin for radar helper scripts (default `http://127.0.0.1:8100`) | No |

Copy `.env.example` → `/home/lesin/apps/flowkit/.env` on the VPS. Do not commit `.env`.

## Custom Domain
Tunnel name `flowkit`. Ingress: `flowkit.datxanhmientrung.ai` → `http://127.0.0.1:8100`.

Tunnel `flowkit` (`c9388a7a-c22c-47aa-8d75-4f9948a2d3b4`) is already running on the VPS.
VPS `cert.pem` can only write DNS on `leesun.space`, so `cloudflared tunnel route dns` created `flowkit.datxanhmientrung.ai.leesun.space` instead of the real hostname.

When you have a Cloudflare API token (Zone.Zone Read + Zone.DNS Edit on `datxanhmientrung.ai`):

```bash
CLOUDFLARE_API_TOKEN=... bash scripts/cloudflare-route-domain.sh
```

That creates a proxied CNAME:

`flowkit.datxanhmientrung.ai` → `c9388a7a-c22c-47aa-8d75-4f9948a2d3b4.cfargotunnel.com`

Or add the same CNAME by hand in the Cloudflare dashboard for `datxanhmientrung.ai`.

## Rollback
```bash
ssh len-vps 'systemctl --user restart flowkit.service'
# previous release: rsync an older tree to /home/lesin/apps/flowkit and restart
```

## Notes
- ffmpeg/ffprobe live in `/home/lesin/bin` (on the unit `PATH`).
- Chrome extension still connects to `ws://127.0.0.1:9222`. Remote dashboard can operate the API; Flow RPCs still need a signed-in `flow.google.com` tab + extension on a machine that can reach that WS.
- Dashboard has no app auth. Add Cloudflare Access later if the URL must not be public.
- `/fk-radar-daily` / `flowkit-radar.timer` is semi-automatic: one signed-in `flow.google.com` tab must stay open on **some** Chrome. The Grok TUI session does not need to stay open. Script-gen talks to CLIProxyAPI (`CLIPROXY_BASE_URL`, default `:8317`). Logs: `output/radar_daily/`.

### Script-gen model (CLIProxyAPI)

CLIProxyAPI (`cliproxyapi.service`, `:8317`) holds two logins in
`~/.cli-proxy-api/` (0600): xAI/Grok and Codex (ChatGPT **Plus**,
`lesin.newwayhub@…`). Add or renew Codex on the headless VPS with
`cd ~/apps/cliproxyapi && ./cli-proxy-api -config config.yaml -codex-device-login -no-browser`
(open the printed URL, enter the code). The running proxy picks new auth files up
without a restart.

`CLIPROXY_MODEL` in `~/apps/flowkit/.env` and `~/.config/stockshorts/service.env`
selects the model for Radar Shorts, Tạo Short and Autopost posts. Bench 2026-09-27,
3 real topics through `generate_short_spec` (strict 5–6 scenes, 18–22 VI words):

| Model | Passed | Note |
|---|---|---|
| `gpt-5.6-luna` | 3/3 | **default** — cheapest passing (~$0.003/topic at API prices) |
| `gpt-6-sol` | 3/3 | fewest retries, ~6× cost; use if luna starts failing |
| `gpt-5.6-terra` | 2/3 | word-count misses |
| `gpt-6-luna` | 1/3 | cheapest per token but overshoots 22 words |
| `grok-4` | — | xAI balance exhausted 2026-09-27 |

Re-bench before switching; a cheaper model that fails validation costs more in retries
and lost Shorts. Restart `stockshorts.service` after editing its env.

## Troubleshooting
- `systemctl --user status flowkit.service` / `flowkit-cloudflared.service`
- `journalctl --user -u flowkit.service -n 100`
- `curl -s http://127.0.0.1:8100/health` on the VPS
- `curl -sI https://flowkit.datxanhmientrung.ai/health`
- CLIProxyAPI down (`CLIPROXY_BASE_URL`, default `:8317`) → `/fk-radar-daily` script-gen stops. Start ClipProxyAL with a Grok account; do not write the short-spec by hand.

## Stock Shorts — isolated VPS service

Stock Shorts is deployed separately on the same VPS. It does not replace or
restart Flow Kit, Radar, or the Facebook sidecar.

- Service: `stockshorts.service` (user systemd, enabled; user lingering enabled).
- Application: `/home/lesin/apps/stockshorts`.
- Public URL: **https://flowkit.datxanhmientrung.ai/stockshorts/**
- Origin remains loopback-only at `http://127.0.0.1:8300`.
- Cloudflare Tunnel routes `^/stockshorts(/.*)?$` to port 8300 before the
  existing Flow catch-all on port 8100. No DNS changes.
- Opening `/stockshorts` redirects to `/stockshorts/` over HTTPS.
- Login is required. SSH forwarding is no longer needed for browser access.
- Autopost UI (login-gated): `/stockshorts/news`, `/hands-on`, `/deep-dives`,
  `/drafts`, `/queue`, `/runs` (Jobs). `/` and `/inbox` redirect to `/news`.
  Sources: Radar digest (News), Hugging Face `api/daily_papers` (Deep dives),
  `github.com/trending` HTML (Hands-on, today only). No crawler, no Pexels.
- `autopost-fetch.timer` (user unit) runs `python -m stockshorts fetch --feed all`
  daily 08:30 Asia/Ho_Chi_Minh. Manual: Jobs page Run button or
  `systemctl --user start autopost-fetch.service`. Parser/source failure = job
  `fail`; existing items are never overwritten.
- "Tạo bài": `CLIPROXY_MODEL` writes the post; images come from
  `AUTOPOST_IMAGE_PROVIDER` — `chatgpt` (default: `AUTOPOST_IMAGE_MODEL`,
  default `gpt-image-2`, via CLIProxyAPI's Codex/ChatGPT login, 1024², PNG, ~25 s,
  no Flow tab or captcha) or `flow` (`/api/flow/generate-image`, needs the
  extension). Deep dives carousel 2–4 images. `AUTOPOST_IMAGES_PER_DAY`
  (default 10, resets 00:00 Asia/Ho_Chi_Minh, reserved before any image call,
  not refunded on failure). Fails loud if the proxy is down.
- "Tạo Short" (News): reviewed checkbox → `SHORT_PROVIDER`:
  `stills` (default, no Flow): LLM factual script (≥1 source URL) → one ChatGPT
  9:16 image per scene (1 quota image each, checked before start) → Ken Burns
  zoom → Edge TTS (4 retries; the service intermittently returns
  `NoAudioReceived`) → karaoke → completed run in **Tạo job**. Runs in the
  background, one at a time; News shows "đang render / xong / lỗi". A failed
  attempt can be retried without "Render lại". `flow`: old Flow Kit scenes + Omni
  video (needs the Flow tab and captcha). `flowkit-radar.timer` (disabled since
  2026-11-01) also uses Flow.
- Nothing posts without the approve screen. Drafts → Queue (Facebook accounts
  only) → job detail consent → fbpublish.
- Rsync `scripts/radar_digest.py`, `radar_scriptgen.py`, `radar_build_short.py`,
  `radar_render_short.py`, `radar_http.py` next to the package; units
  `deploy/autopost-fetch.{service,timer}` to `~/.config/systemd/user/`.

### fbpublish sidecar (Facebook)

- Service `fbpublish.service` (user unit, `deploy/fbpublish.service`), app
  `~/apps/fbpublish`, loopback `127.0.0.1:8200` only (no public route).
- Secrets: `~/.config/fbpublish/service.env` (0600), login password in
  `~/.config/fbpublish/login-password`. `FBPUBLISH_EXTRA_ROOTS` allows
  `~/apps/stockshorts/output` images; DB `~/apps/fbpublish/data/fbpublish.db`.
- Formats: reels, video, photo (1 image), carousel (2–10). Photo/carousel
  publish timeouts are `AMBIGUOUS` → job `failed`, never auto-retried (the post
  may be live; check the Page first). Stuck photo/carousel jobs are failed,
  not re-queued.
- Connect a Page (manual, needs your Page token):
  `ssh -N -L 18200:127.0.0.1:8200 len-vps`, open `http://127.0.0.1:18200`,
  log in, add the Page. Then register it in Stock Shorts:
  `python -m stockshorts account add --id fb1 --platform facebook --account "<Page>" --credentials fb.json`
  with `{"base_url":"http://127.0.0.1:8200","password":"<fbpublish login>","page_id":"<fbpublish page id>"}`;
  delete `fb.json` afterwards.

Initial login password is stored owner-only on the VPS at
`~/.config/stockshorts/login-password`. Retrieve it privately through SSH, never
paste it into logs or commit it. Persistent encryption/session secrets and the
bcrypt password hash are in `~/.config/stockshorts/service.env` (mode 0600).
Back up this file securely: replacing the encryption key loses access to tokens.

### Updating the existing installation

```bash
rsync -az --exclude '__pycache__/' stockshorts len-vps:/home/lesin/apps/stockshorts/
rsync -az scripts/radar_scriptgen.py len-vps:/home/lesin/apps/stockshorts/scripts/
rsync -az deploy/stockshorts.service len-vps:/home/lesin/.config/systemd/user/
ssh len-vps '/home/lesin/apps/stockshorts/venv/bin/pip install --no-cache-dir -r /home/lesin/apps/stockshorts/stockshorts/requirements.txt'
ssh len-vps 'systemctl --user daemon-reload && systemctl --user restart stockshorts.service'
ssh len-vps 'curl --fail -s http://127.0.0.1:8300/stockshorts/health'
```

Do not use the Flow deployment script for this isolated service. Do not sync
local secrets, fake smoke accounts, or test output into production.

### Configuration and verification

The service uses `STOCKSHORTS_SECRET_KEY`, `STOCKSHORTS_SESSION_SECRET`,
`STOCKSHORTS_WEB_PASSWORD_HASH`, `STOCKSHORTS_STATE_DIR`,
`STOCKSHORTS_OUTPUT_ROOT`, `CLIPROXY_BASE_URL`, `CLIPROXY_API_KEY`,
`CLIPROXY_MODEL`, `FLOWKIT_BASE`, and `FLOW_PROJECT_ID`. Inbox video does not
use `PEXELS_API_KEY`.
Only those optional settings were copied when present in the existing VPS
environment; provider accounts were not imported.

Domain deployment additionally requires `STOCKSHORTS_BASE_PATH=/stockshorts`
and `STOCKSHORTS_SECURE_COOKIE=1`. The `stockshorts_session` cookie is HttpOnly,
Secure, SameSite=Lax, and scoped to `/stockshorts/`; it is not shared with Flow.
Template links, form actions, preview URLs, and redirects retain the prefix.
Local development defaults to no prefix and non-Secure cookies.

Tunnel source: `deploy/cloudflared.yml`. Validate the live configuration with
`cloudflared tunnel --config ~/.cloudflared/flowkit.yml ingress validate` before
restarting `flowkit-cloudflared.service`.

Verified through the public HTTPS domain: health, login/logout, CSRF session,
authenticated jobs/prepare pages, CSS/JavaScript, canonical trailing-slash
redirect, and jobs-page visual rendering. The original site root and Flow
health still work; the extension remains connected. No video was posted.
Login password and session secret were rotated after browser tooling exposed
the old password in its observation output; old sessions are invalid.

At deployment, disk free space was about 2.2 GB (93% used), and Pexels was not
configured. Do not start bulk rendering without sufficient storage. Live
rendering/publishing remains gated by API keys and provider onboarding.
TikTok's remote media URL is not yet cryptographically tied to the approved
local preview: do not enable production Direct Post until that is fixed.

### Stop / rollback

```bash
ssh len-vps 'systemctl --user disable --now stockshorts.service'
```

This stops only Stock Shorts and preserves its state and secrets. Remove its
tunnel ingress rule as well if retiring the public path.

Pre-subpath application and tunnel backups are on the VPS in
`~/apps/stockshorts-pre-subpath/`. To roll back routing, restore `flowkit.yml`
from that backup to `~/.cloudflared/flowkit.yml`, validate it, and restart the
tunnel. Preserve the current encryption key and rotated login/session secrets;
do not restore the old secret file. Application rollback must also reset
`STOCKSHORTS_BASE_PATH` and `STOCKSHORTS_SECURE_COOKIE` for localhost access.
