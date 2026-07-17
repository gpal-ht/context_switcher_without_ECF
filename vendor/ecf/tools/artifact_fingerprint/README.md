# Artifact Fingerprint

Read-only SHA-256 fingerprinting of ECF runtime artifacts. Standard library
only; no third-party dependencies, no network.

It exists so the workflow planner can decide whether a completed task output is
still valid for the exact inputs and versions it was produced from (see
`tools/workflow_planner` and `runtime_schemas/TASK_PROVENANCE_SCHEMA.md`).

## Guarantees

- **SHA-256**, lowercase hexadecimal digests.
- Files are hashed in **binary mode** and **streamed** in 64 KiB chunks — large
  files are never loaded whole.
- The hashed file is **never modified** (opened read-only).
- **Missing paths** raise `FingerprintError` (CLI exit code 2).
- **Directories are rejected** — directory hashing is intentionally not
  implemented.

## Library

```python
from tools.artifact_fingerprint import sha256_file, sha256_bytes, FingerprintError

sha256_file("runtime/runs/RUN-.../task_outputs/engineering-forces.yaml")
sha256_bytes(b"abc")  # ba7816bf...15ad
```

## CLI

```bash
python -m tools.artifact_fingerprint.fingerprint <path>
python -m tools.artifact_fingerprint.fingerprint <path> --format json
```

Text output is `"<sha256>  <path>"`. JSON output is
`{"path": ..., "algorithm": "sha256", "sha256": ...}`.

Exit codes: `0` success, `2` error (missing path, directory, unreadable file).

## Tests

```bash
python -m unittest discover -s tools/artifact_fingerprint/tests
```

Covers a known-value digest, read-only behavior, streaming equivalence, missing
path, directory rejection, and the CLI (text + JSON + exit codes).
