# Guyline D+E Execution Plan

Goal: finish the authorized installer, frontend, packaging, CI and product cleanup.
Execute inline; preserve dirty layers, banner edits and interview docs. No Git
mutations, supervisor script edits, baseline rerun or invented product URL.

- [x] Installers: regress local source/wheel, quoted paths, failure propagation,
  Guyline-only launcher; implement all three scripts using installed interpreter
  for verification, frontend discovery and config paths.
- [x] Terminal: protocol producer/consumer/tests to GUYLINEJSON; delayed-backend
  readiness red/green; banner narrow fallback, 0.2.0 and clipboard/package names.
- [x] Packaging: npm ci with lock/fallback without; wheel includes lock;
  regenerate both npm locks using npm; track uv.lock by removing ignore only.
- [x] CI: retain lint gate, new native Windows 3.10/3.11 migration copy/conflict/
  preservation/idempotence/junction tests, subprocess module replacements.
- [x] Documentation/product: README source/wheel/commands/migration policy;
  contributing/showcase/changelog/releases/skills/support cleanup; remove
  authorized root license/lineage metadata and four obsolete unreferenced assets.
- [x] Dashboard: structured sample JSON path sanitation, branding and production
  build into docs/autopilot. Retain neutral assets and third-party provenance.
- [x] Validate isolated focused/full pytest, terminal npm ci/type/node tests/
  readiness, dashboard npm ci/build, basic/full Ruff, clean external wheel smoke.
  Complete all processes, bounded outputs and /tmp logs with real exits.
- [x] Update checkpoint and stop for independent review. Native Windows/pwsh
  execution remains CI-only; conservative 150k checkpoint/190k hard limit.

Final bounded repair evidence: /tmp/guyline-de-repair-pre.log (2 failed/2 passed),
/tmp/guyline-de-repair.log (73 passed/5 skipped), /tmp/guyline-de-final-full.log
(1241 passed/11 skipped); basic lint/diff check and final wheel build exit0.
Fresh wheel: /tmp/guyline-de-final-dist/guyline-0.2.0-py3-none-any.whl. Root's
installed-wheel acceptance preceded the final Agent lock-selection repair;
fresh artifact inspected, independent review pending. Full Ruff remains710
inherited findings; no native Windows/PowerShell execution claimed.
