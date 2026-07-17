# Context Switcher — Release Manifest Schema

Status: App-only foundation (ADR-0010; ECF removed)
Describes `release/release-manifest.json`, produced by
`scripts/build-release-manifest.py` and validated by `scripts/validate-release.py`.

- **schema_version:** `1.0.0`
- **Encoding:** UTF-8 JSON, 2-space indent, trailing newline.
- **Determinism:** every field is a pure function of repository state **except**
  `generated_at`, which is excluded from all drift comparisons.

## Top-level fields

| Field | Type | Meaning |
|---|---|---|
| `schema_version` | string | Manifest schema version (`1.0.0`). |
| `manifest_kind` | string | Constant `context_switcher_release_manifest`. |
| `generated_at` | string (UTC ISO-8601) | Build timestamp. **Informational only**; ignored by drift checks. |
| `project` | object | Context Switcher project identity. |
| `application` | object | The .NET application projects a release is built from. |
| `baselines` | object | ADR decision baseline. |

### `project`

| Field | Source |
|---|---|
| `name`, `version`, `private` | `package.json` |
| `commit` | `git rev-parse HEAD` (best-effort; `null` if unavailable) |
| `commit_policy` | Constant `best_effort` |
| `platform`, `stack` | Constants describing the target (`Windows`; `.NET / WinUI 3`). |

### `application`

| Field | Meaning |
|---|---|
| `projects` | Array of `{path, present}` for each `src/**/*.csproj` a release builds. |
| `projects_present` | `true` iff every application project is present. |

### `baselines`

| Field | Source |
|---|---|
| `architecture_decisions` | Sorted `decisions/ADR-*.md` stems. |

## Validation

`scripts/validate-release.py` rebuilds the manifest in memory, compares it to the
on-disk file (ignoring `generated_at`) to detect staleness, and enforces the
identity/application/packaging gates in `release/RELEASE_CHECKLIST.md`.

To refresh after any relevant change: `npm run release:manifest`.
To check freshness without writing: `python scripts/build-release-manifest.py --check`.

Related: `release/COMPATIBILITY.md`, `release/VERSIONING_POLICY.md`.
