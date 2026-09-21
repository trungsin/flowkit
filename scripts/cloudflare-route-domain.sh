#!/usr/bin/env bash
# Create proxied CNAME flowkit.datxanhmientrung.ai -> <tunnel>.cfargotunnel.com
# Requires CLOUDFLARE_API_TOKEN with Zone.DNS Edit on datxanhmientrung.ai
set -euo pipefail

TOKEN="${CLOUDFLARE_API_TOKEN:?set CLOUDFLARE_API_TOKEN}"
ZONE_NAME="${CLOUDFLARE_ZONE:-datxanhmientrung.ai}"
RECORD_NAME="${CLOUDFLARE_RECORD:-flowkit}"
TUNNEL_ID="${CLOUDFLARE_TUNNEL_ID:-c9388a7a-c22c-47aa-8d75-4f9948a2d3b4}"
TARGET="${TUNNEL_ID}.cfargotunnel.com"
FQDN="${RECORD_NAME}.${ZONE_NAME}"

auth=( -H "Authorization: Bearer ${TOKEN}" -H "Content-Type: application/json" )

zone_json="$(curl -sS "${auth[@]}" "https://api.cloudflare.com/client/v4/zones?name=${ZONE_NAME}")"
zone_id="$(python3 -c 'import json,sys; d=json.load(sys.stdin); r=d.get("result") or [];
print(r[0]["id"] if r else "")' <<<"$zone_json")"
if [[ -z "$zone_id" ]]; then
  echo "Zone ${ZONE_NAME} not found or token lacks Zone.Read" >&2
  echo "$zone_json" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("errors") or d.get("messages") or d)' >&2
  exit 1
fi

list_json="$(curl -sS "${auth[@]}" \
  "https://api.cloudflare.com/client/v4/zones/${zone_id}/dns_records?name=${FQDN}")"
record_id="$(python3 -c 'import json,sys; d=json.load(sys.stdin); r=d.get("result") or [];
print(r[0]["id"] if r else "")' <<<"$list_json")"

body="$(python3 -c "import json; print(json.dumps({
  'type':'CNAME','name':'${RECORD_NAME}','content':'${TARGET}',
  'proxied':True,'ttl':1,'comment':'flowkit cloudflare tunnel'
}))")"

if [[ -n "$record_id" ]]; then
  curl -sS "${auth[@]}" -X PUT \
    "https://api.cloudflare.com/client/v4/zones/${zone_id}/dns_records/${record_id}" \
    --data "$body" | python3 -c 'import json,sys; d=json.load(sys.stdin); print("updated", d.get("success"), d.get("result",{}).get("name"), d.get("errors"))'
else
  curl -sS "${auth[@]}" -X POST \
    "https://api.cloudflare.com/client/v4/zones/${zone_id}/dns_records" \
    --data "$body" | python3 -c 'import json,sys; d=json.load(sys.stdin); print("created", d.get("success"), d.get("result",{}).get("name"), d.get("errors"))'
fi

echo "CNAME ${FQDN} -> ${TARGET} (proxied)"
echo "Check: curl -sS https://${FQDN}/health"
