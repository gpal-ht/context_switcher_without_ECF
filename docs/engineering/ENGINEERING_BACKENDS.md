# Engineering Backends — Standalone and ECF-Integrated Modes

Canonical decision: [ADR-0007 — Optional ECF Integration](../../decisions/ADR-0007-optional-ecf-integration.md).
Compatibility policy details: [release/COMPATIBILITY.md](../../release/COMPATIBILITY.md).

**ECF is optional for Context Switcher.** Context Switcher builds, tests,
release-validates, packages, and runs its native behavior with no ECF
repository, bundle, artifact, environment variable, service, or CLI present.
ECF is an integration enabled by explicit configuration behind a stable
boundary — never inferred from what happens to exist on disk.

## Mode selection

```text
engineering_backend = standalone | ecf
```

Resolution order (first match wins):

1. `CONTEXT_SWITCHER_ENGINEERING_BACKEND` environment variable
2. `config/engineering-backend.yaml` — `engineering_backend:` key
3. default: `standalone`

| Configuration | Result |
| --- | --- |
| unset | standalone |
| `standalone` | standalone |
| `ecf`, valid bundle | ECF-integrated |
| `ecf`, bundle missing | hard failure (exit 3) — never a silent fallback |
| `ecf`, bundle incompatible | hard failure (exit 4) |
| any other value | validation failure (exit 2) |

Inspect the active backend and its capability report:

```bash
npm run backend        # python scripts/engineering_backend.py --describe
```

This repository commits `engineering_backend: ecf` because it ships a pinned,
validated ECF bundle. Working trees or packages without ECF run standalone.

## Standalone mode

### Installation

No ECF is needed. Requirements: Git for Windows (Git Bash), Python 3, npm.

```bash
git clone <context_switcher>   # vendor/ecf may be absent entirely
```

### Build / test / package

```bash
npm run test:standalone        # required gate — runs with no ECF anywhere
npm run release:manifest       # records engineering_backend + honest capabilities
npm run release:validate       # project identity/packaging gates; ECF gates skip
npm run release:pack           # packaging succeeds without vendor/ecf
```

Standalone mode is a legitimate product mode, not a mock: every governance
acceptance check, the release identity tooling, and packaging run with real
behavior. It claims **no** ECF validation, governance, provenance, or
reproducibility guarantees — the release manifest records
`"claimed": false` for all ECF sections, and ECF-only operations refuse with
a typed `UNSUPPORTED_CAPABILITY` error instead of fabricating success.

## ECF-integrated mode

### Installation

1. Bundle a compatible ECF checkout (explicit, operator-supplied path):

   ```powershell
   powershell -File scripts/bundle-ecf.ps1 -Source <path-to-ecf-checkout>
   # or: set CONTEXT_SWITCHER_ECF_SOURCE and omit -Source
   ```

2. Select the backend in `config/engineering-backend.yaml`:

   ```yaml
   engineering_backend: ecf
   ```

Selecting `ecf` validates the bundle at composition-root time (availability,
`schema_version` line, 40-hex `source_commit`, required capabilities).

### Test / run

```bash
npm run test:ecf               # standalone suite + ECF suite (bundle, consumer)
npm test                       # honors the configured backend
```

```powershell
# ECF workflow execution (ecf backend only):
.\scripts\initialize-ecf-run.ps1 -RunId RUN-... -WorkRequest work_requests\WR-....md
.\scripts\plan-ecf-workflow.ps1 -Run runtime\runs\RUN-...
.\scripts\run-ecf-task.ps1 -Run runtime\runs\RUN-... -Executor fixture -Fixture <file>
```

## Capability matrix

| Capability | Standalone | ECF-integrated |
| --- | ---: | ---: |
| Governance acceptance checks (context, WRs, architecture, ignore boundaries, backend boundary) | Required | Required |
| Project release manifest + identity/packaging gates | Required | Required |
| npm packaging | Required | Required |
| ECF run initialization / planning / task execution | Unavailable (typed refusal) | Available |
| Vendor/bundle integrity + consumer-integration gates | Skipped (reported) | Required |
| ECF/EKB provenance pins and acceptance-level claims | Not claimed | Recorded & validated |
| ECF bundle refresh (`bundle-ecf.ps1`) | Unavailable (needs an ECF checkout) | Available |

The machine-readable form of this matrix is emitted into
`release/release-manifest.json` (`capabilities`) and by `npm run backend`.

## Failure behavior

- **Explicitly requested `ecf` never degrades to standalone.** Missing bundle →
  exit 3 with the requested mode, the missing dependency (`vendor/ecf`), and
  the install command. Incompatible bundle → exit 4 naming the incompatible
  field and the supported line.
- **Unknown backend values** fail validation (exit 2) naming the value, its
  source (env var or config file), and the allowed set.
- **ECF-only operations in standalone mode** throw
  `UNSUPPORTED_CAPABILITY: '<operation>' requires the ecf engineering backend…`
  with remediation steps. They never return fake ECF-grade results.

## Architecture (ports and adapters)

```text
        Context Switcher core (suite, release tooling, packaging)
                             │ depends only on
                             ▼
              Context Switcher-owned ports (ADR-0007)
        ┌────────────────────┴────────────────────┐
        ▼                                         ▼
  standalone adapter                        ecf adapter (approved set):
  native behavior +                         scripts/initialize-ecf-run.ps1
  typed UNSUPPORTED_CAPABILITY              scripts/plan-ecf-workflow.ps1
                                            scripts/run-ecf-task.ps1
                                            scripts/bundle-ecf.ps1
                                            + ECF-mode acceptance tests
```

- The backend registry is a **fixed allowlist** (`standalone | ecf`).
  Configuration selects a name, never a module path — no dynamic code loading.
- The resolver contract has three thin language bindings
  (`scripts/engineering_backend.py` — canonical; `scripts/lib/Resolve-EngineeringBackend.ps1`;
  `acceptance_tests/lib/backend.sh`), kept in agreement by
  `acceptance_tests/check_backend_boundary.sh`.
- The boundary test also enforces that **no executable file outside the
  approved adapter set references `vendor/ecf`** and that no executable file
  hardcodes a machine-local path.

### Adding or changing an adapter

1. Extend the allowed-backend set in `scripts/engineering_backend.py` first
   (single source), then mirror in the bash and PowerShell bindings.
2. Add the adapter's files to the approved set in
   `acceptance_tests/check_backend_boundary.sh`.
3. Update the capability matrix (`CAPABILITIES` in `engineering_backend.py`)
   truthfully — never advertise an unavailable operation.
4. Draft an ADR: backends are architecture.
5. Run `npm run test:boundary`, then both suite modes.

## Test gates

| Gate | Command | When required |
| --- | --- | --- |
| Standalone suite | `npm run test:standalone` | Always (required gate for every change) |
| Backend boundary | `npm run test:boundary` | Always (part of the standalone suite) |
| ECF suite | `npm run test:ecf` | Any change to the ECF adapter set, the bundle, or a release cut in ecf mode |
| Release gates | `npm run release:validate` | Every release, in the release's configured mode |

No CI system is currently configured for this repository. When one is
introduced, the required gate is the standalone suite + boundary check +
release validation; the ECF suite runs as a separate job that must pass
before merging changes touching the adapter set or `vendor/ecf`. Unfinished
upstream ECF work can never block the standalone gate: ECF checks run only
against the pinned, vendored bundle.

## Known risk

ECF publishes no formally versioned integration contract beyond
`ecf-version.yaml: schema_version`. The required-capability path list in
`scripts/engineering_backend.py` is the de-facto contract, deliberately
isolated there and mirrored by `check_bundle_integrity.sh`. If ECF later
ships a stable schema/CLI contract, the adapter should migrate to it.
