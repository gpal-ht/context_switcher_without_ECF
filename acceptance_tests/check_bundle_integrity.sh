#!/usr/bin/env bash
# Acceptance test: ECF bundle integrity (read-only).
# Verifies the refreshed bundle contains the expected framework capabilities,
# carries machine-path-free provenance metadata (ECF + nested EKB) whose commits
# agree, keeps the canonical EKB decision_guide type, and is free of dev artifacts.
#
# Cross-platform note: VERSION metadata files may use LF, CRLF, or mixed line
# endings. All metadata is parsed through read_version_value(), which strips any
# trailing carriage return so 40-char hashes validate identically on every OS.
# The VERSION files themselves are never modified.
#
# Usage:
#   check_bundle_integrity.sh              # validate the real bundle
#   check_bundle_integrity.sh --self-test  # unit-test the parser/validators
#
# Exit 0 = all checks pass; non-zero = at least one FAIL.
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# ---------------------------------------------------------------------------
# Reusable metadata helpers (LF/CRLF/mixed safe; portable Bash only)
# ---------------------------------------------------------------------------

# read_version_value KEY FILE
#   Prints the normalized scalar value for `KEY:` in FILE.
#   Strips the key, optional surrounding whitespace, and any trailing CR.
#   Prints nothing (empty) and succeeds when the file or key is absent.
read_version_value() {
  local key="$1" file="$2"
  [ -f "$file" ] || return 0
  grep -E "^${key}:" "$file" 2>/dev/null \
    | head -n 1 \
    | sed -E "s/^${key}:[[:space:]]*//" \
    | tr -d '\r'
}

# is_sha40 VALUE  -> true iff VALUE is exactly 40 lowercase hex characters.
is_sha40() {
  printf '%s' "${1-}" | grep -qE '^[0-9a-f]{40}$'
}

# has_machine_path VALUE -> true iff VALUE looks like a local machine path
#   (Windows drive path 'C:\...' or 'C:/...', a git-bash mount '/c/...', or any
#    backslash). Repository URLs (https://, git@...) return false.
has_machine_path() {
  printf '%s' "${1-}" | grep -qE '^[A-Za-z]:[\\/]|^/[A-Za-z]/|\\'
}

# ---------------------------------------------------------------------------
# Self-test: exercises the helper + validators against LF/CRLF fixtures created
# in a temp dir OUTSIDE the repository, cleaned up on return.
# ---------------------------------------------------------------------------
run_self_test() {
  local t; t="$(mktemp -d)"
  trap 'rm -rf "$t"' RETURN
  local p=0 f=0
  local H1="608494862613fa7da587d28b4d985d7e86692bed"     # valid 40-hex
  local H2="0123456789abcdef0123456789abcdef01234567"     # different valid 40-hex
  local ok bad
  ok(){ echo "  ok:   $1"; p=$((p+1)); }
  bad(){ echo "  FAIL: $1"; f=$((f+1)); }
  eq(){ [ "$1" = "$2" ] && ok "$3" || bad "$3 (got '$1' want '$2')"; }

  # Fixtures ---------------------------------------------------------------
  printf 'dependency: ecf\nsource: https://github.com/gpal-ht/ecf.git\nsource_commit: %s\nekb_commit: %s\n' "$H1" "$H1" > "$t/lf"
  printf 'dependency: ecf\r\nsource: https://github.com/gpal-ht/ecf.git\r\nsource_commit: %s\r\nekb_commit: %s\r\n' "$H1" "$H1" > "$t/crlf"
  printf 'source_commit: %s\n'   "$H1" > "$t/nested_lf"
  printf 'source_commit: %s\r\n' "$H1" > "$t/nested_crlf"
  printf 'source_commit: %s\n'   "$H2" > "$t/nested_bad"
  printf 'dependency: engineering_kb\n'  > "$t/nested_missing"
  printf 'source_commit: %s\nekb_commit: NOTHASH\n' "$H1" > "$t/badekb"

  echo "-- read_version_value: parsing --"
  eq "$(read_version_value source_commit "$t/lf")"   "$H1" "1  LF metadata parses correctly"
  eq "$(read_version_value source_commit "$t/crlf")" "$H1" "2  CRLF metadata parses correctly (CR stripped)"

  echo "-- validators --"
  is_sha40 "$(read_version_value source_commit "$t/crlf")" && ok "3  valid 40-char source_commit passes" || bad "3  valid source_commit should pass"
  is_sha40 "$(read_version_value ekb_commit   "$t/crlf")" && ok "4  valid 40-char ekb_commit passes"    || bad "4  valid ekb_commit should pass"
  # 5 missing ekb_commit fails (nested_lf has source_commit but no ekb_commit key)
  is_sha40 "$(read_version_value ekb_commit "$t/nested_lf")" && bad "5  missing ekb_commit should FAIL" || ok "5  missing ekb_commit fails"
  # 6 malformed ekb_commit fails
  is_sha40 "$(read_version_value ekb_commit "$t/badekb")" && bad "6  malformed ekb_commit should FAIL" || ok "6  malformed ekb_commit fails"
  # 7 nested EKB commit missing fails
  is_sha40 "$(read_version_value source_commit "$t/nested_missing")" && bad "7  nested commit missing should FAIL" || ok "7  nested EKB commit missing fails"

  echo "-- top-level vs nested match --"
  local top nst
  top="$(read_version_value ekb_commit "$t/crlf")"
  # 8 mismatch fails
  nst="$(read_version_value source_commit "$t/nested_bad")"
  [ -n "$top" ] && [ -n "$nst" ] && [ "$top" != "$nst" ] && ok "8  top-level vs nested mismatch is detected" || bad "8  mismatch should be detected"
  # 9 matching commits pass (nested provided as CRLF to prove normalization)
  nst="$(read_version_value source_commit "$t/nested_crlf")"
  [ "$top" = "$nst" ] && ok "9  matching top-level and nested EKB commits pass (nested CRLF)" || bad "9  matching commits should pass"

  echo "-- source machine-path detection --"
  has_machine_path 'C:\Dev\ecf'      && ok "10 machine-local Windows path is rejected"   || bad "10 Windows path should be rejected"
  has_machine_path '/c/Dev/ecf'      && ok "10 git-bash mount path is rejected"           || bad "10 mount path should be rejected"
  has_machine_path 'https://github.com/gpal-ht/ecf.git' && bad "11 repo URL should pass" || ok "11 repository URL source passes"

  echo ""
  echo "self-test: $p passed, $f failed"
  [ "$f" -eq 0 ]
}

if [ "${1:-}" = "--self-test" ]; then
  echo "== check_bundle_integrity.sh self-test =="
  run_self_test
  exit $?
fi

# ---------------------------------------------------------------------------
# Main: validate the real bundle
# ---------------------------------------------------------------------------
B="$ROOT/vendor/ecf"
V="$B/VERSION"
EKBV="$B/vendor/engineering_kb/VERSION"
fail=0
say(){ printf '%s\n' "$*"; }
pass(){ say "PASS: $1"; }
fl(){ say "FAIL: $1"; fail=$((fail+1)); }

say "== ECF Bundle Integrity =="

# Framework capabilities that must now be present in the bundle.
req=(
  "workflows/reasoning/WF-REASON-0001-engineering-recommendation.md"
  "tasks/decision_support/TASK-DECIDE-0002-generate-engineering-recommendation.md"
  "tasks/production/TASK-PRODUCE-0001-generate-engineering-recommendation-report.md"
  "tools/workflow_validator/validate_workflow.py"
  "tools/workflow_planner/plan_workflow.py"
  "tools/runtime_state"
  "tools/task_runner/run_task.py"
  "tools/task_runner/executors/claude_code.py"
  "tools/artifact_fingerprint"
  "runtime_schemas/RUN_STATE_SCHEMA.md"
)
for f in "${req[@]}"; do
  if [ -e "$B/$f" ]; then pass "capability present: $f"; else fl "capability MISSING: $f"; fi
done

# --- VERSION metadata (parsed via read_version_value; LF/CRLF/mixed safe) -----
if [ -f "$V" ]; then pass "vendor/ecf/VERSION present"; else fl "vendor/ecf/VERSION missing"; fi

commit="$(read_version_value source_commit "$V")"
if is_sha40 "$commit"; then pass "ECF source_commit present ($commit)"; else fl "ECF source_commit missing/invalid"; fi

src="$(read_version_value source "$V")"
if [ -z "$src" ]; then
  fl "VERSION 'source' missing"
elif has_machine_path "$src"; then
  fl "VERSION 'source' embeds a machine path: $src"
else
  pass "VERSION 'source' has no machine path ($src)"
fi

ekbc="$(read_version_value ekb_commit "$V")"
if is_sha40 "$ekbc"; then pass "EKB commit recorded in ECF VERSION ($ekbc)"; else fl "EKB commit missing/invalid in ECF VERSION"; fi

# --- Nested EKB identity (existence + hash) -----------------------------------
if [ -f "$EKBV" ]; then
  nested="$(read_version_value source_commit "$EKBV")"
  if is_sha40 "$nested"; then
    pass "nested EKB VERSION present with commit ($nested)"
  else
    nested=""
    fl "nested EKB VERSION present but source_commit missing/invalid"
  fi
else
  nested=""
  fl "nested EKB VERSION missing"
fi

# --- Top-level ekb_commit must match nested EKB source_commit -----------------
if is_sha40 "$ekbc" && is_sha40 "$nested"; then
  if [ "$ekbc" = "$nested" ]; then
    pass "top-level and nested EKB commits match"
  else
    fl "top-level EKB commit does not match nested EKB VERSION"
  fi
fi

# --- Canonical EKB decision_guide type ----------------------------------------
dg="$B/vendor/engineering_kb/decision_guides/architecture/should_introduce_another_subsystem.md"
if [ -f "$dg" ] && grep -qE '^type:[[:space:]]*decision_guide' "$dg"; then
  pass "bundled EKB uses canonical type: decision_guide"
else
  fl "bundled EKB decision guide type not canonical"
fi

# --- Hygiene: no dev/transient artifacts --------------------------------------
pyc=$(find "$B" \( -name '__pycache__' -o -name '*.pyc' -o -name '*.pyo' \) 2>/dev/null | wc -l | tr -d ' ')
if [ "${pyc:-0}" -eq 0 ]; then pass "no __pycache__/*.pyc/*.pyo in bundle"; else fl "$pyc dev artifact(s) present in bundle (hygiene)"; fi

say ""
say "bundle-integrity: $fail failure(s)"
[ "$fail" -eq 0 ]
