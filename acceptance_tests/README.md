# Context Switcher — Project Acceptance Tests

Read-only project-side checks for a standalone .NET application repository
(ADR-0010: ECF removed). They validate project artifacts and the product
build/tests; they never modify tracked files. There is a single operating
mode — no backend selection.

## Tests

| Script | Verifies |
|--------|----------|
| `check_product_tests.sh` | Work Engine product code builds offline (pure BCL, no packages) and its deterministic test suite passes (ADR-0008). Requires the .NET SDK — absence is an honest FAIL, not a skip. |
| `check_engineering_context.sh` | `docs/engineering/ENGINEERING_CONTEXT.md` exists, is non-empty, has the required sections, and reports engineering-information coverage gaps (stakeholders, quality goals, security, performance, deployment, testing, operations). |
| `check_architecture_consistency.sh` | **Severity-aware.** The subsystem-model decision gate — the canonical 6-subsystem model per ADR-0005 enumerated in SYSTEM_ARCHITECTURE + ENGINEERING_CONTEXT; SYSTEM_VISION reconciled; Runtime not a subsystem; historical ADRs clarified — fails only on `blocking`. Empty/stub docs and other gaps are reported as `warning`/`informational` and never fail the gate. |
| `check_ignore_boundaries.sh` | `runtime/` and `generated/` (and `runtime/runs/<RUN_ID>/`) are git-ignored, so runs and generated output can never be committed. |
| `run_all.sh` | Runs all of the above and aggregates results. |

## Running

From the repository root (Git Bash / any bash):

```bash
bash acceptance_tests/run_all.sh    # or: npm test
```

Windows PowerShell mirror (delegates to bash):

```powershell
powershell -File acceptance_tests/run_all.ps1
```

Run a single test:

```bash
bash acceptance_tests/check_architecture_consistency.sh
```

## Conventions

- **Exit code `0`** = all hard checks passed; **non-zero** = at least one hard failure.
- Most tests use `PASS` / `FAIL` lines. `check_architecture_consistency.sh` is **severity-aware** and uses `BLOCKING` / `MAJOR` / `WARNING` / `INFORMATIONAL`; it fails (non-zero) **only on `BLOCKING`** findings so the subsystem decision is not held hostage to unrelated coverage gaps.
- Advisory lines (`WARN` / `WARNING` / `INFORMATIONAL` / `ok`) do not fail the run.
- Tests are **read-only** and safe to run repeatedly.
