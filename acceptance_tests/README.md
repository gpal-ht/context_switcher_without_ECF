# Context Switcher — Project Acceptance Tests

Read-only project-side checks. They validate **project artifacts only** and
never modify anything (including `vendor/`).

Test selection is **backend-aware** (ADR-0007, `docs/engineering/ENGINEERING_BACKENDS.md`):
the STANDALONE suite always runs and needs no ECF anywhere; the ECF suite
additionally runs when `engineering_backend` resolves to `ecf`. An explicitly
configured `ecf` backend with a missing/incompatible bundle fails the run —
it never silently degrades to standalone.

- **Standalone suite (required gate):** `check_engineering_context.sh`,
  `check_work_requests.sh`, `check_architecture_consistency.sh`,
  `check_ignore_boundaries.sh`, `check_backend_boundary.sh`,
  `check_product_tests.sh`
- **ECF suite (ecf backend only):** `check_vendor_integrity.sh`,
  `check_bundle_integrity.sh`, `check_consumer_integration.sh`

## Tests

| Script | Verifies |
|--------|----------|
| `check_product_tests.sh` | Work Engine product code builds offline (pure BCL, no packages) and its deterministic test suite passes (ADR-0008). Requires the .NET SDK — absence is an honest FAIL, not a skip. |
| `check_backend_boundary.sh` | The engineering-backend contract (default standalone; unknown values rejected; explicit `ecf` with a missing/incompatible bundle fails clearly, no silent fallback; env var overrides config); agreement of the bash/Python/PowerShell resolver bindings; and the dependency boundary — no executable file outside the approved ECF adapter set references `vendor/ecf`, and no executable file hardcodes machine-local paths. |
| `check_engineering_context.sh` | `docs/engineering/ENGINEERING_CONTEXT.md` exists, is non-empty, has the required sections, and reports engineering-information coverage gaps (stakeholders, quality goals, security, performance, deployment, testing, operations). |
| `check_work_requests.sh` | Every `work_requests/WR-*.md` contains the six WR-spec–required elements; the Work Request Catalog exists. |
| `check_architecture_consistency.sh` | **Severity-aware.** Two outcomes: **(1) Architecture consistency for WR-0002** — the subsystem-model decision gate (canonical 6-subsystem model per ADR-0005 enumerated in SYSTEM_ARCHITECTURE + ENGINEERING_CONTEXT; SYSTEM_VISION reconciled; Runtime not a subsystem; historical ADRs clarified) — fails only on `blocking`. **(2) Overall project architecture coverage** — empty/stub docs and other gaps as `warning`/`informational`, never failing the WR-0002 gate. |
| `check_vendor_integrity.sh` | Key bundled ECF/EKB files are present; reports (or, in strict mode, fails on) working-tree changes under `vendor/`. |
| `check_bundle_integrity.sh` | Refreshed ECF bundle contains the expected framework capabilities (WF-REASON-0001, TASK-DECIDE-0002, TASK-PRODUCE-0001, validator/planner/runtime_state/runner/executor, runtime schemas); VERSION carries a machine-path-free ECF `source_commit` + nested EKB commit, and the top-level `ekb_commit` **matches** the nested EKB `source_commit`; bundled EKB keeps canonical `type: decision_guide`; no `__pycache__`/`*.pyc` in the bundle. Metadata is parsed LF/CRLF-safe (`read_version_value`). Run `check_bundle_integrity.sh --self-test` to unit-test the parser/validators. |
| `check_ignore_boundaries.sh` | `runtime/` and `generated/` (and `runtime/runs/<RUN_ID>/`) are git-ignored, so runs and generated output can never be committed. |
| `check_consumer_integration.sh` | Offline consumer pipeline against **canonical ECF**: consumer adapter (`initialize-ecf-run.ps1`) → canonical `run_initializer` → canonical planner → fixture task runner → canonical planner. Verifies schema-valid run (run_id, provenance `required`, revisions 0→1), `TASK-CLASSIFY-0001` ready → committed → `TASK-CLASSIFY-0002` ready, and a **before/after vendor delta** (a pre-existing uncommitted bundle refresh is fine; only NEW vendor changes fail). Unique `RUN-CONSUMER-TEST-*` run, always cleaned. Never invokes Claude. |
| `run_all.sh` | Resolves the engineering backend, runs the selected suites, and aggregates results. |

## Running

From the repository root (Git Bash / any bash):

```bash
bash acceptance_tests/run_all.sh                        # configured backend
bash acceptance_tests/run_all.sh --backend standalone   # force standalone suite
bash acceptance_tests/run_all.sh --backend ecf          # force ecf (fails if unavailable)
# npm equivalents: npm test / npm run test:standalone / npm run test:ecf
```

Windows PowerShell mirror (delegates to bash):

```powershell
pwsh acceptance_tests/run_all.ps1   # or: powershell -File acceptance_tests/run_all.ps1
```

Run a single test:

```bash
bash acceptance_tests/check_architecture_consistency.sh
```

Strict vendor integrity (fails on any vendor working-tree change):

```bash
STRICT=1 bash acceptance_tests/check_vendor_integrity.sh
```

## Conventions

- **Exit code `0`** = all hard checks passed; **non-zero** = at least one hard failure.
- Most tests use `PASS` / `FAIL` lines. `check_architecture_consistency.sh` is **severity-aware** and uses `BLOCKING` / `MAJOR` / `WARNING` / `INFORMATIONAL`; it fails (non-zero) **only on `BLOCKING`** findings so that the WR-0002 subsystem decision is not held hostage to unrelated coverage gaps.
- Advisory lines (`WARN` / `WARNING` / `INFORMATIONAL` / `ok`) do not fail the run.
- Tests are **read-only** and safe to run repeatedly.
- A `FAIL` documents a real, reconcilable project defect — see `PROJECT_ECF_ADOPTION_REPORT.md` for known open findings and their remediation.

## Run initialization ownership

- **Canonical ECF owns run initialization** (`vendor/ecf/tools/run_initializer/`, via `vendor/ecf/scripts/initialize-run.ps1`). There is exactly one initialization implementation.
- **Context Switcher provides only a thin adapter**, `scripts/initialize-ecf-run.ps1`, which resolves project paths and forwards consumer-friendly defaults (WF-REASON-0001; runs under the gitignored `runtime/runs/`). It constructs no `state.yaml`/`manifest.yaml` and imports no runtime-state models.
- **`check_consumer_integration.sh` compares vendor state before/after** the run and fails only on **new** vendor changes it introduced. A **pre-existing uncommitted bundle refresh does not fail the test.**
- The integration test is **offline and fixture-only** — it never invokes live Claude.
- **Fail-fast at two boundaries** — initialization and the fixture runner. If either fails, the report is **only** that stage's command / exit code / stdout / stderr, then `STOP`; no downstream assertions cascade. Diagnostic overrides: `CI_WORK_REQUEST=<path>` forces an init failure; `CI_FIXTURE=<path>` forces a runner failure (e.g. a directory → `fixture_missing`).
- The test's scratch and fixture live under the gitignored `runtime/` so they are on a **Windows-accessible** filesystem in every environment (Git Bash maps `/tmp` to the Windows temp, but WSL `/tmp` is a Linux path Windows PowerShell/Python cannot read — which would make the fixture look missing to the runner).
