# Tester: unit suite + radar tests

**Date:** 2026-09-21
**Command:** `.venv/bin/python -m pytest tests/unit -q`
**Exit code:** 0
**Result:** PASS

## Diff-aware mapping

Diff-aware mode: analyzed untracked radar + existing unit tree
  Changed (focus): `scripts/radar_digest.py`, `scripts/radar_scriptgen.py`, `scripts/radar_build_short.py`
  Mapped (Strategy A co-located):
    - `tests/unit/test_radar_digest.py`
    - `tests/unit/test_radar_scriptgen.py`
    - `tests/unit/test_radar_build_short.py`
  Also ran: full `tests/unit` (explicit required command)
  Unmapped radar: CLI `main()` in all 3 scripts (no tests)

Ran 393/393 tests (full unit): 393 passed, 0 failed, 0 skipped
Radar subset: 16/16 passed in 0.04s

## Test Results Overview

| Scope | Collected | Passed | Failed | Skipped | Time |
|---|---|---|---|---|---|
| `tests/unit` | 393 | 393 | 0 | 0 | 7.49s (repeat 7.17s) |
| radar 3 files | 16 | 16 | 0 | 0 | 0.04s |

**Failed tests:** none
**Exit code:** 0

Radar tests (all PASS):
- digest (7): keep-7/drop-bare-tags, status-not-ok, empty communities, broken evidence_json, missing heat, fetch UA, fetch URLError
- scriptgen (7): word_count, 5-scene validate, short narrator + broll count, fence parse, chat_url, generate retry, grok bearer
- build_short (2): ensure_mc skip-if-exists, VERTICAL+ROOT+PATCH+active-project

## Coverage Metrics

`pytest-cov` / `coverage` **not installed** (`requirements-dev.txt` has pytest, pytest-asyncio, pytest-mock only). No line/branch/function %. Qualitative gaps below.

### Covered (radar)

- `filter_usable`: status gate, empty communities, evidence≥2+insight, heat desc, missing heat→0, bad JSON drop
- `fetch`: User-Agent `FlowKit-radar-digest`, URLError → RuntimeError
- `validate_spec` happy 5-scene; narrator too short; broll count mismatch
- `generate_short_spec` retry-then-accept; `grok_chat` Authorization Bearer
- `ensure_mc` GET-and-skip; `build_short` VERTICAL, ROOT, PATCH narrator, PUT `/api/active-project`

### Uncovered / weak (radar)

| File | Gap | Suggested test (do not skip existing) |
|---|---|---|
| `radar_digest.py` | `evidence_list` already-list / non-list JSON / non-dict items | fixture evidence_json as list vs `"[]"` vs `"{}"` |
| `radar_digest.py` | `fetch` JSONDecodeError / TimeoutError | monkeypatch urlopen return `b'not-json'` |
| `radar_digest.py` | `main()` default UTC date, `run_day` fallback, exit 0 | `capsys` + argv |
| `radar_scriptgen.py` | validate: hook/outro order, counter≠1, missing prompt/video_prompt, names not list, hook without MC, broll with names, 6-scene, narrator >22 | extra invalid specs |
| `radar_scriptgen.py` | `parse_json_object` non-object / bad JSON | `pytest.raises(RuntimeError)` |
| `radar_scriptgen.py` | `grok_chat` no key, missing choices, URLError | env + fake payload |
| `radar_scriptgen.py` | generate both attempts fail | two bad contents → RuntimeError |
| `radar_scriptgen.py` | `main` / `Path_read` | tmp_path JSON in |
| `radar_build_short.py` | `ensure_mc` create+attach path | GET empty list then POST character + POST attach |
| `radar_build_short.py` | `req` HTTPError JSON vs raw | fake HTTPError |
| `radar_build_short.py` | empty `scenes`, `main` stdin/`-` | argparse + monkeypatch |

## Failed Tests

None.

## Performance Metrics

- Full unit: ~7.2–7.5s
- Radar: 0.04s, all <0.005s
- Slow (pre-existing, not radar):
  - `test_video_reviewer.py::TestCreateContactSheetsChunking` 0.34–1.16s (chunking/layout)
- No flakes observed (2 consecutive full runs both 393 passed)

## Build Status

- Pytest collection OK (`pytest.ini` `testpaths = tests`)
- Warning: Starlette TestClient `anyio.abc.BlockingPortal` deprecation (1 warning, pre-existing, not radar)
- No production build / dashboard compile in this task
- `pytest-cov` absent → no numeric coverage in CI

## Critical Issues

None blocking. Suite green.

## Recommendations

1. Keep assertions; add tests for `ensure_mc` **create** path (currently only skip-if-exists — production attach/POST untested).
2. Add `generate_short_spec` double-fail + `validate_spec` role/MC/prompt errors (contract is the main safety net vs Grok).
3. Optional: add `pytest-cov` to `requirements-dev.txt` if CI wants line %.
4. `radar_scriptgen.main` / `radar_digest.main` / `radar_build_short.main` untested — CLI default date + stdin `-` are easy regressions.

## Next Steps

1. (P1) Test `ensure_mc` POST create + project attach.
2. (P1) Test scriptgen validate error matrix + generate raise after 2 fails.
3. (P2) Test digest `evidence_list` list-typed evidence + fetch JSON decode fail.
4. (P3) CLI `main()` smoke for all 3 scripts.
5. (P3) Coverage tool in dev deps if required.

## Unresolved questions

- Should radar CLI `main()` be in unit tests or treated as integration-only?
- Numeric coverage target? Repo has none configured.
- Other untracked tests (`test_dashboard_static.py`, `test_extension_bridge.py`) ran in the 393 and passed; not the focus of this run.
