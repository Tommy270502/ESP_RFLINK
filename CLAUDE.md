# Claude Implementation Guide

Use this file before making changes. Keep outputs short. Update `ROADMAP.md`
checkboxes only after the matching validation step passes or the limitation is
recorded.

## Mission

Make this repository a professional public showcase for an embedded engineering
services office. Preserve working behavior. Do not invent hardware validation,
RF range, compliance, production readiness, or reliability claims.

## Source Of Truth

- Roadmap and task status: `ROADMAP.md`
- Product entry point: `README.md`
- Product overview: `project-overview.md`
- Protocol reference: `docs/api-reference.md`
- Firmware: `Firmware/ESP32_RFLINK/`
- Python SDK/CLI/tests: `sdk/python/`
- Local web workbench: `application/main.py`, `application/static/index.html`,
  `application/desktop-workbench.md`
- Hardware/manufacturing: `hardware/`, `manufacturing/`

## Immediate Rules

- Fix P0 items first.
- Do not edit KiCad, Gerber, drill, PNG, or manufacturing files unless the task
  explicitly requires hardware/manufacturing changes.
- Do not rename public commands, response fields, BLE UUIDs, HTTP routes, or
  PlatformIO environments unless docs and tests are updated in the same change.
- Canonical terms:
  - `local web workbench`: host app at `http://127.0.0.1:5173`
  - `firmware browser dashboard`: device UI at `http://192.168.4.1`
  - `firmware 0.1.0-v1`
  - `protocol 1.1`
- Mark any untested hardware behavior as `unverified` or `requires hardware validation`.
- Prefer small commits by phase. Do not mix cleanup, firmware behavior, SDK API,
  and CI changes unless required.

## Work Loop

1. Read only the relevant `ROADMAP.md` phase and target files.
2. Run a narrow baseline check before edits when useful.
3. Make the smallest correct change.
4. Run the validation listed in `ROADMAP.md`.
5. If validation passes, change the task checkbox to `[x]`.
6. If validation cannot run, leave the task unchecked and add a short note.

## Required Baseline Checks

Run these while clearing P0/P1 items:

```bash
rg -n "^(<<<<<<<|=======|>>>>>>>)" .
python scripts/check_docs_links.py
python -B -m py_compile application/main.py
cd sdk/python && python -m pytest
```

Run firmware build when PlatformIO is installed:

```bash
cd Firmware/ESP32_RFLINK
pio run -e node1 -e node2
```

## Current Known Failures

- Merge conflict markers exist in `README.md`, `application/main.py`,
  `docs/firmware.md`, and `docs/documentation-index.md`.
- `application/main.py` does not compile until conflict markers are resolved.
- Markdown link check fails on stale `application/README.md` and
  `sdk/python/README.md` links.
- PlatformIO was not available in the audited local PATH.
- SDK tests passed during audit: 25 tests passed.

## Starter Prompt For Claude

```text
You are implementing the Wireless Dev Bridge cleanup roadmap.

Read CLAUDE.md and ROADMAP.md. Start with Phase 1 P0 items only:
1. Resolve all merge conflict markers.
2. Restore application/main.py as the FastAPI local web workbench backend.
3. Fix stale README/docs links.
4. Normalize terminology to local web workbench vs firmware browser dashboard.

After each completed task, run the listed validation command and update the
matching checkbox in ROADMAP.md. Keep diffs minimal. Do not change firmware
behavior in Phase 1. Do not claim hardware validation unless evidence is in the
repo or you ran it.
```
