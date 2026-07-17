#!/usr/bin/env bash
# Acceptance test: runtime / generated ignore boundaries (read-only).
# Runtime runs and generated output must never be committable.
# Exit 0 = all checks pass; non-zero = at least one FAIL.
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fail=0
say(){ printf '%s\n' "$*"; }
pass(){ say "PASS: $1"; }
fl(){ say "FAIL: $1"; fail=$((fail+1)); }

say "== Runtime / Generated Ignore Boundaries =="
cd "$ROOT" || { fl "cannot cd to repo root"; exit 1; }

for d in runtime generated; do
  if git check-ignore -q "$d/probe.txt" 2>/dev/null; then
    pass "$d/ is git-ignored (runs/output cannot be committed)"
  else
    fl "$d/ is NOT git-ignored"
  fi
done

# A concrete runtime run path must also be ignored.
if git check-ignore -q "runtime/runs/RUN-EXAMPLE/state.yaml" 2>/dev/null; then
  pass "runtime/runs/<RUN_ID>/ paths are ignored"
else
  fl "runtime/runs/<RUN_ID>/ paths are NOT ignored"
fi

say ""
say "ignore-boundaries: $fail failure(s)"
[ "$fail" -eq 0 ]
