# ADR-0007: Optional ECF Integration Behind an Engineering-Backend Boundary

**Status:** Accepted

**Date:** 2026-07-16

**Approved by:** Project Owner

**Related Work:** refactor/optional-ecf-integration; ADR-0006 (Release and
Bundling Strategy)

## Context

ECF is still under active development. Before this ADR, Context Switcher's
test harness (`acceptance_tests/run_all.sh`) unconditionally executed three
ECF-bound checks, `scripts/validate-release.py` failed its gates without the
bundled ECF, and `scripts/bundle-ecf.ps1` hardcoded machine-local sibling
paths (`C:\Dev\ecf`, `C:\Dev\context_switcher`). In an environment without
ECF, Context Switcher could not be tested, release-validated, or honestly
packaged. ECF availability had become an implicit, mandatory dependency of
ordinary Context Switcher development — with no explicit configuration and
no defined standalone behavior.

## Decision

### Two explicit engineering backends

Context Switcher supports exactly two backends, selected by explicit
configuration — never inferred from what happens to exist on disk:

```
engineering_backend = standalone | ecf
```

Resolution order (first match wins):

1. `CONTEXT_SWITCHER_ENGINEERING_BACKEND` environment variable
2. `config/engineering-backend.yaml` (`engineering_backend:` key)
3. default: `standalone`

| Configuration | Result |
| --- | --- |
| unset | standalone |
| `standalone` | standalone |
| `ecf`, valid bundle | ECF-integrated |
| `ecf`, ECF unavailable/incompatible | hard configuration failure — **never** a silent fallback |
| unknown value | validation failure |

This repository commits `engineering_backend: ecf` because it ships a pinned,
validated bundle; consumers and environments without ECF run standalone.

### Ports and adapters, allowlisted backend registry

- **Port 1 — backend resolver.** One contract, three thin language bindings
  (this is a bash/PowerShell/Python repository):
  `scripts/engineering_backend.py` (canonical; owns the allowed-backend set,
  the supported ECF schema line, and the required-capability list),
  `scripts/lib/Resolve-EngineeringBackend.ps1`, and
  `acceptance_tests/lib/backend.sh`. `acceptance_tests/check_backend_boundary.sh`
  asserts the three bindings agree, so they cannot drift silently.
- **Port 2 — engineering workflow execution.** The existing thin wrappers
  (`initialize-ecf-run.ps1`, `plan-ecf-workflow.ps1`, `run-ecf-task.ps1`,
  `bundle-ecf.ps1`) are the **approved ECF adapter set**. They resolve the
  backend first; in standalone mode they return a typed
  `UNSUPPORTED_CAPABILITY` refusal (they never fabricate ECF results).
  No other file may reference `vendor/ecf` — enforced by the boundary test.
- **Port 3 — release identity.** The release manifest records the active
  backend and a truthful capability matrix; ECF/EKB provenance and
  acceptance-level claims are made only in `ecf` mode. `validate-release.py`
  enforces ECF gates in `ecf` mode and, in standalone mode, enforces that no
  ECF guarantee is claimed.
- The backend registry is a **fixed allowlist**. Configuration selects a
  name, never a module path — no dynamic code loading.

### Compatibility policy (ecf backend)

Selecting `ecf` validates, at composition-root time:

1. `vendor/ecf/` exists (availability);
2. `vendor/ecf/ecf-version.yaml` declares a `schema_version` on the supported
   `0.1` line (compatibility anchor);
3. `vendor/ecf/VERSION` carries a valid 40-hex `source_commit` (identity);
4. all required bundled capabilities are present.

Any failure names the requested mode, the missing/incompatible piece, and the
remediation. **Known risk, isolated here:** ECF publishes no formally
versioned integration contract beyond `schema_version`; the required-
capability path list is the de-facto contract and lives in one Python module.

### Standalone is a product mode, not a mock

Standalone mode runs every native Context Switcher gate (governance
acceptance checks, project release identity, packaging) with real behavior
and truthful capability reporting. It claims no ECF validation, governance,
provenance, or reproducibility guarantees.

## Consequences

- Context Switcher can be developed, tested, release-validated, and packaged
  with no ECF checkout, bundle, or environment present.
- ECF-integrated behavior is unchanged when `engineering_backend: ecf` is
  configured with the pinned bundle (the default committed state).
- `bundle-ecf.ps1` no longer hardcodes machine paths; the ECF source is an
  operator-supplied, validated parameter.
- The required test gate for ordinary development is the standalone suite;
  ECF gates run in `ecf` mode and are mandatory for changes to the adapter
  set or the bundle (see `docs/engineering/ENGINEERING_BACKENDS.md`).
- Cross-language resolver duplication (bash/PS/Python) is accepted and
  guarded by an agreement test, rather than forcing every surface through a
  single interpreter.
