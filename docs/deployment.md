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
Units: `~/.config/systemd/user/flowkit.service` and `flowkit-cloudflared.service`.

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
| `CLIPROXY_MODEL` | Grok model id on the proxy (default `grok-4`) | No |
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
- `/fk-radar-daily` is semi-automatic: one signed-in `flow.google.com` tab must stay open. Not a headless cron. Script-gen talks to CLIProxyAPI (`CLIPROXY_BASE_URL`, default `:8317`), not the FastAPI agent.

## Troubleshooting
- `systemctl --user status flowkit.service` / `flowkit-cloudflared.service`
- `journalctl --user -u flowkit.service -n 100`
- `curl -s http://127.0.0.1:8100/health` on the VPS
- `curl -sI https://flowkit.datxanhmientrung.ai/health`
- CLIProxyAPI down (`CLIPROXY_BASE_URL`, default `:8317`) → `/fk-radar-daily` script-gen stops. Start ClipProxyAL with a Grok account; do not write the short-spec by hand.
