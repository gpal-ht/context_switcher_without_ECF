#!/usr/bin/env bash
# Acceptance test: Vendor integrity (read-only).
# Confirms key bundled ECF/EKB files are present, and reports working-tree
# changes under vendor/. Project batches must never modify vendor/.
#   Default:  vendor working-tree changes are advisory (WARN) — parallel
#             re-bundling may legitimately touch the bundle.
#   STRICT=1: any vendor working-tree change is a FAIL.
# Exit 0 = all hard checks pass; non-zero = at least one FAIL.
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VECF="$ROOT/vendor/ecf"
VKB="$ROOT/vendor/ecf/vendor/engineering_kb"
STRICT="${STRICT:-0}"
fail=0; warn=0
say(){ printf '%s\n' "$*"; }
pass(){ say "PASS: $1"; }
fl(){ say "FAIL: $1"; fail=$((fail+1)); }
wn(){ say "WARN: $1"; warn=$((warn+1)); }

say "== Vendor Integrity =="

key_files=(
  "$VECF/VERSION"
  "$VKB/VERSION"
  "$VECF/tasks/TASK_EXECUTION_SPECIFICATION.md"
  "$VECF/execution/EXECUTION_TRACE_CONTRACT.md"
  "$VECF/work_requests/WORK_REQUEST_SPECIFICATION.md"
  "$VKB/artifacts/ENGINEERING_KNOWLEDGE_PACKAGE_CONTRACT.md"
  "$VKB/decision_guides/architecture/should_introduce_another_subsystem.md"
  "$VKB/foundations/ENGINEERING_INTENT_MODEL.md"
  "$VKB/foundations/ENGINEERING_PROCESS_MAP.md"
)
for f in "${key_files[@]}"; do
  if [ -f "$f" ]; then pass "present: ${f#$ROOT/}"; else fl "missing bundled file: ${f#$ROOT/}"; fi
done

# Working-tree changes under vendor/
if command -v git >/dev/null 2>&1 && git -C "$ROOT" rev-parse >/dev/null 2>&1; then
  changed="$(git -C "$ROOT" status --porcelain -- vendor/ 2>/dev/null)"
  n=$(printf '%s' "$changed" | grep -c . || true)
  if [ "$n" -eq 0 ]; then
    pass "no working-tree changes under vendor/"
  elif [ "$STRICT" = "1" ]; then
    fl "vendor/ has $n working-tree change(s) [STRICT]"
    printf '%s\n' "$changed" | sed 's/^/       /'
  else
    wn "vendor/ has $n working-tree change(s) — must originate ONLY from re-bundling, not project edits"
    printf '%s\n' "$changed" | sed 's/^/       /'
  fi
else
  wn "git unavailable — skipped vendor working-tree change detection"
fi

say ""
say "vendor-integrity: $fail failure(s), $warn warning(s)"
[ "$fail" -eq 0 ]
