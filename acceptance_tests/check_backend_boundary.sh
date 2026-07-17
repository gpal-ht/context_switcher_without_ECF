#!/usr/bin/env bash
# Acceptance test: engineering-backend configuration + ECF dependency boundary
# (ADR-0007). Read-only over the repository; fixtures live in a temp dir.
#
# Verifies, deterministically:
#   A. Backend resolution contract — default standalone; explicit standalone;
#      unknown value rejected; explicit ecf with a missing bundle fails clearly
#      (exit 3, never a silent fallback); incompatible bundle fails clearly
#      (exit 4); env var overrides the config file; standalone resolution never
#      requires vendor/ecf.
#   B. Cross-language resolver agreement — the bash, Python, and PowerShell
#      bindings of the Port-1 contract produce the same outcomes. (Python and
#      PowerShell scenarios are skipped with a WARN where the interpreter is
#      genuinely unavailable; bash scenarios always run.)
#   C. Dependency boundary — no executable file outside the approved ECF
#      adapter/composition-root set references vendor/ecf; no executable file
#      hardcodes a machine-local C:\Dev path.
#
# Exit 0 = all hard checks pass; non-zero = at least one FAIL.
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=lib/backend.sh
. "$ROOT/acceptance_tests/lib/backend.sh"

fail=0; warn=0
say(){ printf '%s\n' "$*"; }
pass(){ say "PASS: $1"; }
fl(){ say "FAIL: $1"; fail=$((fail+1)); }
wn(){ say "WARN: $1"; warn=$((warn+1)); }

say "== Engineering Backend Boundary (ADR-0007) =="

# ---------------------------------------------------------------------------
# Fixture roots (created OUTSIDE the repository, removed on exit)
# ---------------------------------------------------------------------------
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT

mkfix() { # NAME [engineering_backend value]  (no arg = no config file)
  local d="$T/$1"; mkdir -p "$d/config"
  if [ "$#" -ge 2 ]; then printf 'engineering_backend: %s\n' "$2" > "$d/config/engineering-backend.yaml"; fi
  printf '%s' "$d"
}
FIX_DEFAULT="$(mkfix default)"
FIX_STANDALONE="$(mkfix standalone standalone)"
FIX_UNKNOWN="$(mkfix unknown sideways)"
FIX_ECF_MISSING="$(mkfix ecf_missing ecf)"
# ecf configured; bundle present but incompatible schema line
FIX_ECF_BAD="$(mkfix ecf_bad ecf)"
mkdir -p "$FIX_ECF_BAD/vendor/ecf"
printf 'schema_version: "9.9.0"\n' > "$FIX_ECF_BAD/vendor/ecf/ecf-version.yaml"
printf 'source_commit: 0123456789abcdef0123456789abcdef01234567\n' > "$FIX_ECF_BAD/vendor/ecf/VERSION"

# Interpreters for the sibling bindings
PY="$(command -v python 2>/dev/null || command -v python3 2>/dev/null || true)"
PS="$(command -v powershell.exe 2>/dev/null || command -v pwsh 2>/dev/null || true)"
PYRES="$ROOT/scripts/engineering_backend.py"
PSLIB="$ROOT/scripts/lib/Resolve-EngineeringBackend.ps1"
to_windows_path(){
  if   command -v cygpath >/dev/null 2>&1; then cygpath -w "$1"
  elif command -v wslpath >/dev/null 2>&1; then wslpath -w "$1"
  else printf '%s' "$1"
  fi
}

# run_binding LANG ROOT -> stdout=mode, rc=resolver rc (env is inherited)
run_binding() {
  local lang="$1" r="$2"
  case "$lang" in
    bash) resolve_engineering_backend "$r" 2>/dev/null ;;
    py)   "$PY" "$PYRES" --print --root "$(to_windows_path "$r")" 2>/dev/null ;;
    ps)   "$PS" -NoProfile -ExecutionPolicy Bypass -Command \
            ". '$(to_windows_path "$PSLIB")'; Resolve-EngineeringBackend -RepoRoot '$(to_windows_path "$r")'" 2>/dev/null ;;
  esac
}

# expect LANG ROOT WANT_MODE WANT_RC LABEL   (WANT_MODE '-' = don't care)
expect() {
  local lang="$1" r="$2" want_mode="$3" want_rc="$4" label="$5" out rc
  out="$(run_binding "$lang" "$r")"; rc=$?
  out="$(printf '%s' "$out" | tr -d '\r' | tail -n 1)"
  if [ "$want_rc" = "0" ]; then
    if [ "$rc" -eq 0 ] && [ "$out" = "$want_mode" ]; then pass "$label [$lang]"
    else fl "$label [$lang] (rc=$rc out='$out')"; fi
  else
    # Non-zero expected. bash/python carry the exact contract code; PowerShell
    # signals failure via a thrown error (any non-zero).
    if [ "$lang" = "ps" ]; then
      [ "$rc" -ne 0 ] && pass "$label [$lang]" || fl "$label [$lang] (rc=0, expected failure)"
    else
      [ "$rc" -eq "$want_rc" ] && pass "$label [$lang]" || fl "$label [$lang] (rc=$rc want=$want_rc)"
    fi
  fi
}

# scenarios LANG — runs the full contract matrix for one binding
scenarios() {
  local lang="$1"
  unset CONTEXT_SWITCHER_ENGINEERING_BACKEND
  expect "$lang" "$FIX_DEFAULT"     standalone 0 "unset configuration defaults to standalone"
  expect "$lang" "$FIX_STANDALONE"  standalone 0 "explicit standalone resolves"
  expect "$lang" "$FIX_UNKNOWN"     -          2 "unknown value is a validation failure"
  expect "$lang" "$FIX_ECF_MISSING" -          3 "ecf with missing bundle fails (no silent fallback)"
  expect "$lang" "$FIX_ECF_BAD"     -          4 "ecf with incompatible bundle fails clearly"
  CONTEXT_SWITCHER_ENGINEERING_BACKEND=standalone \
    expect "$lang" "$FIX_ECF_MISSING" standalone 0 "env var overrides config; standalone needs no vendor/ecf"
  CONTEXT_SWITCHER_ENGINEERING_BACKEND=sideways \
    expect "$lang" "$FIX_DEFAULT" - 2 "unknown env value is a validation failure"
}

say "-- A/B. resolution contract per binding --"
scenarios bash
if [ -n "$PY" ] && [ -f "$PYRES" ]; then scenarios py; else wn "python unavailable — python binding scenarios skipped"; fi
if [ -n "$PS" ] && [ -f "$PSLIB" ]; then scenarios ps; else wn "PowerShell unavailable — PowerShell binding scenarios skipped"; fi

# Real repository state: whatever is configured must resolve identically in
# every available binding (agreement on live config, not just fixtures).
say "-- B. live-repository agreement --"
unset CONTEXT_SWITCHER_ENGINEERING_BACKEND
live_bash="$(run_binding bash "$ROOT")"; rc_bash=$?
if [ $rc_bash -ne 0 ]; then
  fl "live repository configuration does not resolve (bash rc=$rc_bash)"
else
  pass "live repository resolves to '$live_bash' (bash)"
  for lang in py ps; do
    case "$lang" in
      py) [ -n "$PY" ] || continue ;;
      ps) [ -n "$PS" ] || continue ;;
    esac
    got="$(run_binding "$lang" "$ROOT" | tr -d '\r' | tail -n 1)"
    [ "$got" = "$live_bash" ] && pass "live agreement: $lang -> '$got'" \
                              || fl "live disagreement: $lang -> '$got' vs bash '$live_bash'"
  done
fi

# ---------------------------------------------------------------------------
# C. Dependency boundary — approved ECF adapter / composition-root set only
# ---------------------------------------------------------------------------
say "-- C. dependency boundary --"
# Files APPROVED to reference vendor/ecf (the ECF adapter set + composition
# roots + ECF-mode acceptance tests + the resolver bindings themselves).
approved='^(scripts/initialize-ecf-run\.ps1|scripts/plan-ecf-workflow\.ps1|scripts/run-ecf-task\.ps1|scripts/bundle-ecf\.ps1|scripts/lib/Resolve-EngineeringBackend\.ps1|scripts/engineering_backend\.py|scripts/build-release-manifest\.py|acceptance_tests/lib/backend\.sh|acceptance_tests/check_vendor_integrity\.sh|acceptance_tests/check_bundle_integrity\.sh|acceptance_tests/check_consumer_integration\.sh|acceptance_tests/check_backend_boundary\.sh)$'

violations=0
while IFS= read -r f; do
  case "$f" in vendor/*) continue ;; esac
  if grep -qE 'vendor[/\\]+ecf' "$ROOT/$f" 2>/dev/null; then
    if ! printf '%s' "$f" | grep -qE "$approved"; then
      fl "unapproved vendor/ecf reference in executable file: $f"
      violations=$((violations+1))
    fi
  fi
done < <(git -C "$ROOT" ls-files -- '*.sh' '*.ps1' '*.py' '*.cs' '*.csproj' 2>/dev/null)
[ "$violations" -eq 0 ] && pass "vendor/ecf references confined to the approved adapter set"

# No machine-local C:\Dev paths in executable code (check_bundle_integrity.sh
# legitimately embeds one as a NEGATIVE fixture asserting such paths are
# rejected; the boundary test itself documents the same string).
mp_violations=0
while IFS= read -r f; do
  case "$f" in
    vendor/*) continue ;;
    acceptance_tests/check_bundle_integrity.sh|acceptance_tests/check_backend_boundary.sh) continue ;;
  esac
  if grep -q 'C:[\\/]Dev' "$ROOT/$f" 2>/dev/null; then
    fl "machine-local C:\\Dev path in executable file: $f"
    mp_violations=$((mp_violations+1))
  fi
done < <(git -C "$ROOT" ls-files -- '*.sh' '*.ps1' '*.py' '*.cs' '*.csproj' 2>/dev/null)
[ "$mp_violations" -eq 0 ] && pass "no machine-local C:\\Dev paths in executable files"

say ""
say "backend-boundary: $fail failure(s), $warn warning(s)"
[ "$fail" -eq 0 ]
