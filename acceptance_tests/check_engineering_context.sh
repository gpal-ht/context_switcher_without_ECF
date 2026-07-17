#!/usr/bin/env bash
# Acceptance test: Engineering Context completeness (read-only).
# Exit 0 = all hard checks pass; non-zero = at least one FAIL.
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CTX="$ROOT/docs/engineering/ENGINEERING_CONTEXT.md"
ARCH="$ROOT/docs/architecture"
fail=0; warn=0
say(){ printf '%s\n' "$*"; }
pass(){ say "PASS: $1"; }
fl(){ say "FAIL: $1"; fail=$((fail+1)); }
wn(){ say "WARN: $1"; warn=$((warn+1)); }

say "== Engineering Context Completeness =="

if [ -f "$CTX" ]; then pass "ENGINEERING_CONTEXT.md exists"; else fl "ENGINEERING_CONTEXT.md missing"; fi
if [ -s "$CTX" ]; then pass "ENGINEERING_CONTEXT.md is non-empty"; else fl "ENGINEERING_CONTEXT.md is empty"; fi

if [ -f "$CTX" ]; then
  for h in "Project" "Current Phase" "Product Mission" "Current Architecture" \
           "Active Constraints" "Relevant ADRs" "Known Open Questions"; do
    if grep -qi "^#\{1,\} *$h" "$CTX"; then pass "section present: $h"; else fl "section missing: $h"; fi
  done

  # Engineering-information coverage advisories (missing areas do not fail the run).
  grep -qi "stakeholder"                       "$CTX" && say "ok:   coverage: stakeholders"            || wn "coverage gap: stakeholders"
  grep -qiE "quality goal|non-functional|NFR"  "$CTX" && say "ok:   coverage: quality goals / NFRs"    || wn "coverage gap: quality goals / NFRs"
  grep -qi  "security"                         "$CTX" && say "ok:   coverage: security"                || wn "coverage gap: security / privacy"
  grep -qi  "performance"                      "$CTX" && say "ok:   coverage: performance"             || wn "coverage gap: performance"
  grep -qi  "deployment"                       "$CTX" && say "ok:   coverage: deployment"              || wn "coverage gap: deployment"
  grep -qiE "testing|test strategy"            "$CTX" && say "ok:   coverage: testing"                 || wn "coverage gap: testing strategy"
  grep -qiE "operations|observability|monitor" "$CTX" && say "ok:   coverage: operations"             || wn "coverage gap: operations / observability"
  grep -qiE "data model|domain model"          "$CTX" && say "ok:   coverage: data/domain model ref"  || wn "coverage gap: data/domain model reference"
fi

say ""
say "engineering-context: $fail failure(s), $warn coverage warning(s)"
[ "$fail" -eq 0 ]
