#!/usr/bin/env bash
# Rsync Flow Kit to len-vps and (re)start the user systemd unit.
# Tunnel/DNS: pass --tunnel to create Cloudflare route (needs ~/.cloudflared/cert.pem on the VPS).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOST="${FLOWKIT_SSH_HOST:-len-vps}"
REMOTE="${FLOWKIT_REMOTE_DIR:-/home/lesin/apps/flowkit}"
CREATE_TUNNEL=0

for arg in "$@"; do
  case "$arg" in
    --tunnel) CREATE_TUNNEL=1 ;;
    *) echo "Unknown arg: $arg" >&2; exit 2 ;;
  esac
done

if [[ ! -d "$ROOT/dashboard/dist" ]]; then
  echo "Missing dashboard/dist — run: (cd dashboard && npm ci && npm run build)" >&2
  exit 1
fi

ssh -o BatchMode=yes "$HOST" "mkdir -p '$REMOTE'"

rsync -az --delete \
  --exclude '.git/' \
  --exclude 'venv/' \
  --exclude '.venv/' \
  --exclude 'node_modules/' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  --exclude '.env' \
  --exclude 'output/' \
  --exclude '*.db' \
  --exclude '*.db-wal' \
  --exclude '*.db-shm' \
  --exclude '.omc/' \
  --exclude '.agentkit/' \
  --exclude 'youtube/' \
  --exclude 'dashboard/node_modules/' \
  "$ROOT/" "$HOST:$REMOTE/"

ssh -o BatchMode=yes "$HOST" "REMOTE='$REMOTE' CREATE_TUNNEL='$CREATE_TUNNEL' bash -s" <<'REMOTE_SCRIPT'
set -euo pipefail
cd "$REMOTE"

python3 -m venv venv
./venv/bin/pip install -q --upgrade pip
./venv/bin/pip install -q -r requirements.txt

if [[ ! -f .env ]]; then
  cp .env.example .env
fi

mkdir -p "$HOME/.config/systemd/user"
cp deploy/flowkit.service "$HOME/.config/systemd/user/flowkit.service"
cp deploy/flowkit-cloudflared.service "$HOME/.config/systemd/user/flowkit-cloudflared.service"

if [[ "$CREATE_TUNNEL" == "1" ]]; then
  set +o pipefail
  if ! cloudflared tunnel list 2>/dev/null | awk 'NR>1 {print $2}' | grep -qx flowkit; then
    cloudflared tunnel create flowkit
  fi
  TUNNEL_ID="$(cloudflared tunnel list 2>/dev/null | awk '$2=="flowkit" {print $1; exit}')"
  set -o pipefail
  if [[ -z "$TUNNEL_ID" ]]; then
    echo "Could not resolve tunnel id for name=flowkit" >&2
    exit 1
  fi
  sed -e "s/REPLACE_TUNNEL_ID/$TUNNEL_ID/g" deploy/cloudflared.yml \
    > "$HOME/.cloudflared/flowkit.yml"
  chmod 600 "$HOME/.cloudflared/flowkit.yml"
  cloudflared tunnel route dns --overwrite-dns flowkit flowkit.datxanhmientrung.ai || true
fi

systemctl --user daemon-reload
systemctl --user enable --now flowkit.service
if [[ -f "$HOME/.cloudflared/flowkit.yml" ]]; then
  systemctl --user enable --now flowkit-cloudflared.service
  systemctl --user restart flowkit-cloudflared.service
fi
systemctl --user restart flowkit.service
systemctl --user --no-pager --full status flowkit.service | head -20 || true
REMOTE_SCRIPT
