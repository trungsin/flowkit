# Calling Flow Kit from other tools — account safety

For any program that submits generations through Flow Kit: Stock Shorts
(`AUTOPOST_IMAGE_PROVIDER=flow`, `SHORT_PROVIDER=flow`), `scripts/radar_*`,
remote callers through `https://flowkit.datxanhmientrung.ai`, ad-hoc `curl`.

Every Flow generation runs on one signed-in Google account. When Google answers
`PUBLIC_ERROR_UNUSUAL_ACTIVITY`, more submits can turn a tool-only block into a
block of manual generation in the Flow UI as well
([crisng95/flowkit#67](https://github.com/crisng95/flowkit/issues/67)).
Flow Kit guards its side (see README → Account safety); clients must not work
around it.

## Rules

1. **Check before a run.** `GET /api/flow/status`. Submit nothing unless
   `connected` is `true` and `generation_throttle.cooldown_active` is `false`.
2. **Name yourself.** Send `X-FlowKit-Caller: <tool-name>` on every generation
   call. The agent logs `caller=<tool-name> path=… status=…`; without it the log
   says `caller=unknown` and nobody can tell which tool hit the block.
3. **Prefer the queue.** `POST /api/requests/batch` + `GET /api/requests/batch-status`
   lets the worker apply retry limits and the hold. Direct
   `/api/flow/generate-*` / `edit-image` calls get the same hold and pacing,
   but the retry policy is then yours.
4. **One at a time.** Do not run generation calls in parallel. The agent already
   serialises submits and spaces them by `FLOW_GENERATION_MIN_INTERVAL_S`;
   parallel clients only queue up behind each other and time out.
5. **Stop the whole run on an account-safety error.** Do not retry, do not move
   on to the next item:

   | Response | Meaning | Client action |
   |---|---|---|
   | body contains `PUBLIC_ERROR_UNUSUAL_ACTIVITY` (usually HTTP 502) | Google refused; the agent has started its hold | Stop. Alert a human. |
   | HTTP 429, `local cooldown active; retry in about Ns` | Hold active; nothing was sent to Google | Stop. Do not sleep N seconds and resubmit. |
   | body contains `[HIJACK]` / `extension_hijack_detected` | reCAPTCHA bypass failed | Stop. Alert a human. |
   | HTTP 503 `Extension not connected` | No Flow tab | Stop. A human must open the tab. |

   Retrying is only reasonable for a quota/rate answer that is not one of the
   above (`radar_render_short.py` waits 60s once on `QUOTA`), and at most once.
6. **Never call `POST /api/flow/clear-hijack` from a tool.** Only a human, and
   only after one image generates by hand in the Flow UI on the same account.
7. **Keep volume small.** Cap images/videos per run and per day in the tool.
   Run large batches only after small runs have gone through cleanly.

## Recovery after a block

1. Stop all tools and timers that submit to Flow
   (`systemctl --user stop flowkit-radar.timer`, Stock Shorts on `flow`).
2. Leave the hold alone. `GET /api/flow/status` shows `cooldown_remaining_s`.
3. After the hold, make **one** image by hand in the Flow UI on the same account.
   - Refused ("We noticed some unusual activity") → the account itself is held.
     Wait; try by hand at most once a day. Do not run tools.
   - Works → one test submit through Flow Kit (2026-10-31: a block at 12:51 UTC
     was clear by 15:32 UTC). Then resume small.
4. Run automation on a separate Google account, not one you need for daily work.

## Minimal client (Python)

```python
import json, urllib.error, urllib.request

BASE = "https://flowkit.datxanhmientrung.ai"   # or http://127.0.0.1:8100
CALLER = "my-tool"
STOP_MARKERS = ("PUBLIC_ERROR_UNUSUAL_ACTIVITY", "local cooldown active",
                "[HIJACK]", "extension_hijack_detected", "Extension not connected")


class FlowBlocked(RuntimeError):
    """Stop the whole run; a human has to look."""


def call(method, path, body=None, timeout=300):
    req = urllib.request.Request(
        BASE + path, method=method,
        data=None if body is None else json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "X-FlowKit-Caller": CALLER},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode(errors="replace")
        if exc.code in (429, 503) or any(m in raw for m in STOP_MARKERS):
            raise FlowBlocked(f"{exc.code} {raw[:300]}") from exc
        raise RuntimeError(f"{exc.code} {raw[:300]}") from exc


status = call("GET", "/api/flow/status", timeout=15)
if not status["connected"] or status["generation_throttle"]["cooldown_active"]:
    raise FlowBlocked(status["generation_throttle"])

image = call("POST", "/api/flow/generate-image",
             {"prompt": "a red apple on a wooden table", "count": 1})
```

## Clients in this repo

| Client | Path | Caller header | On account-safety error |
|---|---|---|---|
| Radar daily | `scripts/radar_http.py` (`radar_render_short.py`) | `radar-daily` | refs/images go through the queue; Omni videos fail the scene, later scenes get the local 429 without reaching Google |
| Stock Shorts | `stockshorts/drafts/flow_images.py` | none yet | raises, no retry |
