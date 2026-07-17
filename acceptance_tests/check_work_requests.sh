#!/usr/bin/env bash
# Acceptance test: Work Request completeness (read-only).
# Verifies each work_requests/WR-*.md has the six WR-spec-required elements.
# Exit 0 = all hard checks pass; non-zero = at least one FAIL.
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WRDIR="$ROOT/work_requests"
fail=0
say(){ printf '%s\n' "$*"; }
pass(){ say "PASS: $1"; }
fl(){ say "FAIL: $1"; fail=$((fail+1)); }

say "== Work Request Completeness =="

if [ -f "$WRDIR/WORK_REQUEST_CATALOG.md" ]; then
  pass "Work Request Catalog present"
else
  fl "Work Request Catalog missing (work_requests/WORK_REQUEST_CATALOG.md)"
fi

shopt -s nullglob
wrs=( "$WRDIR"/WR-*.md )
if [ "${#wrs[@]}" -eq 0 ]; then
  fl "no Work Requests found under work_requests/"
else
  for f in "${wrs[@]}"; do
    name="$(basename "$f")"
    # Required-for-validity elements per WORK_REQUEST_SPECIFICATION.md > Validation
    for section in "Engineering Question" "Desired Outcome" \
                   "Engineering Context Reference" "Constraints" \
                   "Requested Deliverables" "Success Criteria"; do
      if grep -qi "$section" "$f"; then
        pass "$name: $section"
      else
        fl "$name: missing '$section'"
      fi
    done
  done
fi

say ""
say "work-requests: $fail failure(s)"
[ "$fail" -eq 0 ]
