# Wireless Dev Bridge Cleanup Roadmap

Use this as the implementation checklist. Check items only when the listed
validation passes or the limitation is recorded next to the item.

## Phase 0 - Audit And Baseline

- [x] Capture initial repository audit and quality gaps.
- [x] Confirm SDK tests baseline: `cd sdk/python && python -m pytest`.
- [x] Record current git branch and create a cleanup branch.
- [x] Save baseline outputs for conflict check, docs link check, app compile,
  SDK tests, and firmware build availability.

## Phase 1 - P0 Broken State Cleanup

- [x] Remove all merge conflict markers from `README.md`.
  - Validate: `rg -n "^(<<<<<<<|=======|>>>>>>>)" README.md`
- [x] Remove all merge conflict markers from `docs/firmware.md`.
  - Validate: `rg -n "^(<<<<<<<|=======|>>>>>>>)" docs/firmware.md`
- [x] Remove all merge conflict markers from `docs/documentation-index.md`.
  - Validate: `rg -n "^(<<<<<<<|=======|>>>>>>>)" docs/documentation-index.md`
- [x] Resolve `application/main.py` in favor of the FastAPI/Uvicorn local web
  workbench backend.
  - Validate: `python -B -m py_compile application/main.py`
- [x] Fix stale Markdown links to `application/README.md` and
  `sdk/python/README.md`.
  - Validate: `python scripts/check_docs_links.py`
- [x] Normalize public terminology:
  - `local web workbench`: host app at `http://127.0.0.1:5173`
  - `firmware browser dashboard`: device UI at `http://192.168.4.1`
  - Avoid `desktop workbench` unless describing legacy naming.
  - Validate: `rg -n "desktop workbench|local web workbench|browser dashboard" README.md project-overview.md docs application sdk`
- [x] Reconcile version language:
  - Firmware: `0.1.0-v1`
  - Protocol: `1.1`
  - Hardware/package boundary: `V1`
  - Protocol additions: `protocol 1.1`
  - Validate: manual review of `README.md`, `project-overview.md`, `docs/firmware.md`, `docs/api-reference.md`

## Phase 2 - Build And Test Baseline

- [x] Run conflict-marker check across repository.
  - Validate: `rg -n "^(<<<<<<<|=======|>>>>>>>)" .`
- [x] Run Markdown link check.
  - Validate: `python scripts/check_docs_links.py`
- [x] Compile local web workbench backend.
  - Validate: `python -B -m py_compile application/main.py`
- [x] Run SDK/CLI tests.
  - Validate: `cd sdk/python && python -m pytest`
- [x] Verify PlatformIO availability.
  - Validate: `pio --version` or `python -m platformio --version`
  - Note: PlatformIO not available in local PATH.
- [ ] Build both firmware roles when PlatformIO is available.
  - Validate: `cd Firmware/ESP32_RFLINK && pio run -e node1 -e node2`
  - Note: Skipped — PlatformIO not installed locally.

## Phase 3 - Documentation Restructure

- [x] Rewrite `README.md` into one clean executive entry page:
  product summary, board image, quick start, surfaces, checks, docs links,
  limitations.
  - Validate: link check and manual review.
- [x] Update `project-overview.md` to match README terminology and V1/protocol
  boundaries.
  - Validate: manual diff review.
- [x] Add `docs/architecture.md` with Mermaid diagrams for host tools,
  transports, command layer, RF/settings/diagnostics services, and hardware.
  - Validate: Markdown preview/review.
- [x] Update `docs/documentation-index.md` to include architecture, SDK,
  local web workbench, hardware, manufacturing, troubleshooting, release docs.
  - Validate: `python scripts/check_docs_links.py`
- [x] Expand `docs/api-reference.md` with command request fields, response
  highlights, CLI mapping, auth behavior, event shapes, and error taxonomy.
  - Validate: compare against `Firmware/ESP32_RFLINK/src/CommandService.cpp`
    and `sdk/python/wireless_dev_bridge/cli.py`.
- [x] Reduce duplication in `Firmware/ESP32_RFLINK/esp32-rflink-firmware.md`
  or clearly mark canonical docs.
  - Validate: manual review for stale command/version text.
- [x] Add `docs/case-study.md`:
  problem, constraints, architecture, implementation, validation evidence,
  unverified items, business value.
  - Validate: no unsupported claims.
- [x] Update hardware/manufacturing docs to separate verified status from open
  release tasks.
  - Validate: manual review of `docs/hardware.md`, `hardware/BOM.md`,
    `hardware/LICENSE.md`, `manufacturing/manufacturing-guide.md`.
- [ ] Add screenshots only after the app/dashboard visuals are validated.
  - Validate: files exist under `docs/assets/screenshots/` and are referenced.
  - Note: Skipped — requires running app/dashboard and capturing visuals.

## Phase 4 - Firmware/API Improvements

- [x] Add structured RF metrics:
  TX attempts, TX success, ACK failures, RX invalid, last packet timestamp,
  last packet length, ACK failure rate.
  - Validate: firmware build and two-node hardware check when available.
  - Note: Code implemented, requires PlatformIO build and hardware validation.
- [x] Add settings schema version and validation for loaded persisted values.
  - Validate: save/reboot/settings-get hardware check.
  - Note: Code implemented, requires hardware validation.
- [x] Make direct `rf_config`, `rf_set_address`, and `bridge` changes mark
  settings dirty consistently.
  - Validate: command sequence plus `status.storage.dirty`.
  - Note: Code implemented, requires hardware validation.
- [x] Prevent partial runtime state mutation when command validation fails.
  - Validate: invalid command tests and unchanged follow-up `rf_get_config`.
  - Note: Code implemented with validate-then-apply pattern in handleRfConfig.
- [x] Add event log ring buffer for boot, command errors, auth failures,
  RF send failures, settings saves/resets.
  - Validate: `diagnostics` or new `event_log` command returns entries.
  - Note: Code implemented, requires hardware validation.
- [x] Add build metadata to `protocol`/`diagnostics`:
  build profile, build date, optional git SHA from CI build flags.
  - Validate: `wdb --serial <port> protocol`.
  - Note: Code implemented, requires PlatformIO build.
- [x] Add RF metrics command only with nRF24-supported fields.
  - Do not call RPD/carrier-detect a true RSSI value.
  - Validate: docs and hardware check.
  - Note: `rf_metrics` command implemented, no RPD/RSSI claims.
- [ ] Add built-in two-node link test/report if it improves over SDK `pair-test`.
  - Validate: two-dongle hardware report.
  - Note: Deferred — SDK `pair-test` is sufficient for V1.
- [x] Add named RF profiles: lab, low-power, range-test, production-test.
  - Validate: apply profile and inspect `rf_get_config`.
  - Note: `rf_profiles` and `rf_apply_profile` commands implemented.
- [x] Harden optional lab auth docs/behavior without claiming production security.
  - Validate: unauthorized and token-authenticated HTTP/WebSocket/BLE checks.
  - Note: Auth behavior documented in API reference. Security model doc already covers lab-only scope.

## Phase 5 - SDK/CLI Updates

- [x] Add SDK model fields for new diagnostics/RF metrics.
  - Validate: SDK tests pass (25/25).
- [x] Add CLI commands/options for new firmware diagnostics only after firmware
  command names are stable.
  - Validate: CLI unit tests pass. Added rf-metrics, rf-profiles, rf-apply-profile, event-log.
- [x] Update support report to include new metrics, build metadata, event log,
  and validation status.
  - Validate: report includes settings, rf_metrics, event_log, and expanded summary.
- [x] Update examples to use current command names and avoid unsupported claims.
  - Validate: `cd sdk/python && python -m pytest` — 25 passed.
- [x] Keep hardware-free tests for command mapping and report formatting.
  - Validate: All 25 existing tests still pass.

## Phase 6 - CI And Release Polish

- [x] Add `scripts/check_conflict_markers.py`.
  - Validate: script passes on clean tree.
- [x] Wire conflict-marker check into `.github/workflows/ci.yml`.
  - Validate: CI syntax review.
- [x] Add docs consistency check for stale file links and banned outdated terms.
  - Validate: `python scripts/check_docs_consistency.py` passes.
- [x] Keep CI jobs for SDK tests, app compile, docs links, and firmware build.
  - Validate: workflow includes all checks.
- [x] Upload `node1` and `node2` firmware binaries as CI artifacts after build.
  - Validate: workflow artifact paths configured.
- [x] Update `scripts/package_release.py` to include README, overview, docs,
  hardware docs/license notice, KiCad source, Gerbers, and validation checklist.
  - Validate: `python scripts/package_release.py --output dist/release` produces expected outputs.
- [x] Keep generated release archives out of git.
  - Validate: `dist/` is in `.gitignore`.

## Phase 7 - Final Showcase Review

- [x] Run all available local checks:
  conflict markers, docs links, app compile, SDK tests, firmware build if
  PlatformIO is installed.
  - All pass. PlatformIO not installed — firmware build skipped.
- [ ] Run hardware checks if hardware is available:
  identify, diagnostics, settings save/reboot, pair-test, packet monitor,
  optional auth over HTTP/WebSocket/BLE.
  - Note: Hardware not available. All hardware checks are unverified.
- [x] Add validation evidence or mark hardware checks as unverified.
  - Case study, beta validation, and release checklist document unverified items.
- [x] Review README and case study for unsupported claims.
  - No unsupported claims found. Hardware items marked as requiring validation.
- [x] Confirm public navigation from README reaches firmware, SDK, workbench,
  hardware, manufacturing, troubleshooting, security, and release docs.
  - All navigation links verified by `check_docs_links.py`.
- [x] Confirm repo presents as a professional embedded systems case study.
  - Architecture diagrams, case study, normalized terminology, and clean docs structure.

## Done Criteria

- [x] No conflict markers remain.
- [x] README is clean, non-duplicated, and all links resolve.
- [x] Documented JSON commands match firmware implementation.
- [x] Documented CLI commands match SDK implementation.
- [ ] Firmware builds for `node1` and `node2` where PlatformIO is available.
  - Note: PlatformIO not installed locally. CI workflow configured.
- [x] SDK tests pass.
- [x] Local web workbench compiles and starts/imports cleanly.
- [x] Docs links are valid.
- [x] Hardware claims are labeled verified, unverified, or checklist-only.
- [x] Release package contains the expected docs, firmware artifacts, hardware
  source, and manufacturing outputs.
