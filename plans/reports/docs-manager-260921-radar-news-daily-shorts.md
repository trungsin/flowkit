---
title: Docs update — /fk-radar-daily
date: 2026-09-21
status: done
---

# Docs: `/fk-radar-daily` daily AI-news Shorts

## Current state

`docs/` is thin: CAPTURE, IMAGE_API, OMNI_FLASH, deployment, journals. No
`project-changelog.md`, `development-roadmap.md`, or `system-architecture.md`
— not created (minor impact, no large new files).

Already in tree before this pass:
- `skills/fk-radar-daily.md` (recipe)
- `CLAUDE.md` / `AGENTS.md` skill tables
- `.env.example` `CLIPROXY_*` + `FLOWKIT_BASE`
- `docs/deployment.md` CLIPROXY env rows

Verified against code:
- `scripts/radar_digest.py` — digest `{date}?format=json`, evidence≥2 + insight
- `scripts/radar_scriptgen.py` — Grok via CLIProxyAPI (`CLIPROXY_*`), loads `.env`
- `scripts/radar_build_short.py` — VERTICAL + ROOT, MC `Friendly Expert`,
  default project `ef10b9d7-925c-4306-add6-a6c3f5a73da0`, `FLOWKIT_BASE`

## Changes made

| File | Edit |
|---|---|
| `README.md` | Skill row (Daily news), `CLIPROXY_*` in Quick Start config, changelog 2026-09-21 |
| `skills/README.md` | Daily news section → `fk-radar-daily.md` |
| `docs/deployment.md` | `FLOWKIT_BASE` env; note not a cron; CLIPROXY down troubleshooting |

Not touched: `CLAUDE.md`, `AGENTS.md` (already generated/updated), `.env.example`.

## Gaps

- `skills/README.md` still lists a subset of skills (pre-existing).
- Root `ARCHITECTURE.md` / `PLAN.md` describe pre-migration Flow REST; out of
  scope for this pass.
- No live `/fk-radar-daily` run documented in journals.

## Recommendations

1. After first real day (`2026-09-19` or today), journal N shorts + failures.
2. Keep CLIPROXY out of `agent/config.py` unless the FastAPI process starts
   calling Grok itself.

## Unresolved

- None for docs. CLIProxyAPI port/model on VPS still operator-owned.

**Status:** DONE
**Summary:** Catalog + env + changelog now name `/fk-radar-daily` (Grok/CLIProxyAPI). Did not invent changelog/roadmap/architecture files that do not exist.
