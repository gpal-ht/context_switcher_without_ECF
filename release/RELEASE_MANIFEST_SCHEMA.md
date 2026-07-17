# Context Switcher — Release Manifest Schema

Status: Draft foundation (v0.2.0)
Describes `release/release-manifest.json`, produced by
`scripts/build-release-manifest.py` and validated by `scripts/validate-release.py`.

- **schema_version:** `0.1.0`
- **Encoding:** UTF-8 JSON, 2-space indent, trailing newline.
- **Determinism:** every field is a pure function of repository state **except**
  `generated_at`, which is excluded from all drift comparisons.

## Top-level fields

| Field | Type | Meaning |
|---|---|---|
| `schema_version` | string | Manifest schema version (`0.1.0`). |
| `manifest_kind` | string | Constant `context_switcher_release_manifest`. |
| `generated_at` | string (UTC ISO-8601) | Build timestamp. **Informational only**; ignored by drift checks. |
| `project` | object | Context Switcher project identity. |
| `acceptance_level` | object | Honest statement of what has been proven. |
| `bundled_ecf` | object | Bundled ECF identity + strategy. |
| `bundled_ekb` | object | Nested EKB identity + ECF-recorded EKB identity. |
| `compatibility` | object | Workflow, consumer scripts, required capabilities. |
| `baselines` | object | ADR and Work Request baselines. |

### `project`

| Field | Source |
|---|---|
| `name`, `version`, `private` | `package.json` |
| `commit` | `git rev-parse HEAD` (best-effort; `null` if unavailable) |
| `commit_policy` | `ecf-version.yaml` `commit_policy` (default `best_effort`) |

### `acceptance_level`

| Field | Value |
|---|---|
| `single_live_task_proven` | `true` |
| `full_workflow_proven` | `false` |
| `statement` | `"single live task proven; full workflow not yet proven"` |

### `bundled_ecf`

| Field | Source |
|---|---|
| `strategy` | Constant `included_self_contained_bundle` (Option A; see `COMPATIBILITY.md`). |
| `canonical_version`, `canonical_schema_version`, `commit_policy` | `vendor/ecf/ecf-version.yaml` |
| `bundle_version`, `source`, `source_commit`, `bundle_date`, `status` | `vendor/ecf/VERSION` |

### `bundled_ekb`

| Field | Source |
|---|---|
| `version`, `source`, `source_commit` | `vendor/ecf/vendor/engineering_kb/VERSION` |
| `ecf_recorded_ekb_version`, `ecf_recorded_ekb_source`, `ecf_recorded_ekb_commit` | `vendor/ecf/VERSION` (`ekb_*`) |

`ecf_recorded_ekb_commit` **must equal** `source_commit` (ECF↔EKB agreement, Gate 4).

### `compatibility`

| Field | Meaning |
|---|---|
| `workflow` | Targeted reasoning workflow (`WF-REASON-0001`). |
| `consumer_scripts` | Shipped `scripts/*.ps1` wrappers that exist. |
| `required_capabilities` | Array of `{path, present}` under `vendor/ecf/`; mirrors `check_bundle_integrity.sh`. |
| `required_capabilities_present` | `true` iff every required capability is present. |

### `baselines`

| Field | Source |
|---|---|
| `architecture_decisions` | Sorted `decisions/ADR-*.md` stems. |
| `accepted_work_requests` | Sorted `work_requests/WR-*.md` stems. |

## Validation

`scripts/validate-release.py` rebuilds the manifest in memory, compares it to the
on-disk file (ignoring `generated_at`) to detect staleness, and enforces the
identity/compatibility/packaging gates in `release/RELEASE_CHECKLIST.md`.

To refresh after any relevant change: `npm run release:manifest`.
To check freshness without writing: `python scripts/build-release-manifest.py --check`.

Related: `release/COMPATIBILITY.md`, `release/VERSIONING_POLICY.md`.
