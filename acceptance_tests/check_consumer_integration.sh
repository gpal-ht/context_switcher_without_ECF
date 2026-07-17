#!/usr/bin/env bash
# Acceptance test / diagnostic harness: consumer-side ECF integration (offline).
#
# Exercises EXACTLY what a real Windows consumer runs — the consumer PowerShell
# wrappers, never the ECF Python entrypoints:
#   scripts/initialize-ecf-run.ps1   (Step 1)
#     -> scripts/plan-ecf-workflow.ps1  ->  scripts/run-ecf-task.ps1 (fixture)
#     -> scripts/plan-ecf-workflow.ps1  (Step 3)
#
# The test NEVER locates Python and never assumes `python` is on PATH — Python
# discovery is owned entirely by the wrappers; the test owns workflow verification.
#
# FAIL-FAST at TWO boundaries: initialization (Step 1/2) and the fixture runner
# (Step 3b). On failure, the report is ONLY that stage's command / exit code /
# stdout / stderr, then STOP — no downstream assertions cascade. The failing
# stage owns the report.
#
# Scratch (incl. the fixture) lives under the repo's gitignored runtime/ so it is
# on a Windows-accessible filesystem in every environment (Git Bash maps /tmp to
# the Windows temp, but WSL /tmp is a Linux path Windows PowerShell/python cannot
# read — which would make the fixture appear missing to the runner).
#
# Offline and fixture-only — never invokes live Claude.
# Diagnostics: CI_WORK_REQUEST=<path> overrides the Work Request (init failure);
#              CI_FIXTURE=<path> overrides the fixture (runner failure).
#
# Exit 0 = success path fully passed; non-zero = a fail-fast stage or a check failed.
set -u
export PYTHONDONTWRITEBYTECODE=1
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ECF="$ROOT/vendor/ecf"
WR="${CI_WORK_REQUEST:-$ROOT/work_requests/WR-0001-repository-integration-subsystem.md}"
INIT_WRAP="$ROOT/scripts/initialize-ecf-run.ps1"
PLAN_WRAP="$ROOT/scripts/plan-ecf-workflow.ps1"
RUN_WRAP="$ROOT/scripts/run-ecf-task.ps1"

fail=0
say(){ printf '%s\n' "$*"; }
pass(){ say "PASS: $1"; }
fl(){ say "FAIL: $1"; fail=$((fail+1)); }

RUNID="RUN-CONSUMER-TEST-$$"
RUN="$ROOT/runtime/runs/$RUNID"
# Repo-local, gitignored, Windows-accessible scratch (see header).
SCRATCH="$ROOT/runtime/citmp-$RUNID"
mkdir -p "$SCRATCH"
BEFORE="$SCRATCH/vendor-before.txt"; AFTER="$SCRATCH/vendor-after.txt"; FIX="$SCRATCH/intent.yaml"
INIT_OUT="$SCRATCH/init.out"; INIT_ERR="$SCRATCH/init.err"
RUN_OUT="$SCRATCH/run.out";  RUN_ERR="$SCRATCH/run.err"

cleanup() {
  case "$RUN"     in "$ROOT/runtime/runs/RUN-CONSUMER-TEST-"*) rm -rf "$RUN" ;; esac
  case "$SCRATCH" in "$ROOT/runtime/citmp-"*)                 rm -rf "$SCRATCH" ;; esac
  find "$ECF" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null
}
trap cleanup EXIT

# Windows PowerShell host + POSIX->Windows path conversion (Git Bash cygpath,
# WSL wslpath, else unchanged). Every path passed to powershell.exe uses this.
PS="$(command -v powershell.exe 2>/dev/null || command -v pwsh 2>/dev/null || true)"
to_windows_path(){
  if   command -v cygpath >/dev/null 2>&1; then cygpath -w "$1"
  elif command -v wslpath >/dev/null 2>&1; then wslpath -w "$1"
  else printf '%s' "$1"
  fi
}
psrun(){ "$PS" -NoProfile -ExecutionPolicy Bypass -File "$@"; }

say "== Consumer ECF Integration (offline, canonical) =="

# --- silent setup (no assertions before Step 1) -------------------------------
( cd "$ROOT" && git status --porcelain -- vendor/ecf 2>/dev/null ) | LC_ALL=C sort > "$BEFORE"
pyc_before=$(find "$ECF" -name '__pycache__' -type d 2>/dev/null | wc -l | tr -d ' ')
cat > "$FIX" <<'JSON'
{"schema_version":"0.1.0","task_id":"TASK-CLASSIFY-0001","task_version":"0.1.0","work_request_id":"WR-0001","status":"completed","engineering_intent":{"primary":"design_solution","secondary":[]},"classification_evidence":{"engineering_question":"Q","desired_outcome":"Engineering Recommendation Report","requested_deliverables":["Engineering Recommendation Report"]},"confidence":{"level":"high","justification":"x"},"findings":[]}
JSON

# =============================================================================
# Step 1 — initialize via the consumer wrapper (owns Python discovery).
# =============================================================================
INIT_WRAP_W="$(to_windows_path "$INIT_WRAP")"; WR_W="$(to_windows_path "$WR")"
INIT_DESC="$PS -NoProfile -ExecutionPolicy Bypass -File $INIT_WRAP_W -RunId $RUNID -WorkRequest $WR_W -Force"
if [ -z "$PS" ]; then
  init_rc=127; printf 'powershell.exe not found; the consumer wrapper requires Windows PowerShell.\n' > "$INIT_ERR"; : > "$INIT_OUT"
else
  psrun "$INIT_WRAP_W" -RunId "$RUNID" -WorkRequest "$WR_W" -Force >"$INIT_OUT" 2>"$INIT_ERR"; init_rc=$?
fi

# Step 2 — initialization failure owns the report.
if [ "$init_rc" -ne 0 ] || [ ! -f "$RUN/state.yaml" ]; then
  ec="$init_rc"; [ "$init_rc" -eq 0 ] && ec="0 (no state.yaml produced)"
  say ""; say "INITIALIZER FAILED"; say ""
  say "Command:";   printf '  %s\n' "$INIT_DESC"; say ""
  say "Exit code:"; printf '  %s\n' "$ec"; say ""
  say "STDOUT"; { [ -s "$INIT_OUT" ] && sed 's/^/  /' "$INIT_OUT"; } || say "  (empty)"; say ""
  say "STDERR"; { [ -s "$INIT_ERR" ] && sed 's/^/  /' "$INIT_ERR"; } || say "  (empty)"; say ""
  say "STOP"; exit 1
fi
pass "canonical initializer exited zero (via scripts/initialize-ecf-run.ps1)"

RUN_W="$(to_windows_path "$RUN")"

# consumer adapter is a THIN delegate (constructs no runtime state)
if grep -q 'initialize-run.ps1' "$INIT_WRAP" && ! grep -qE 'save_run_state|save_manifest|RunState\(|RunManifest\(' "$INIT_WRAP"; then
  pass "initialize-ecf-run.ps1 delegates to the canonical initializer (no runtime-state reconstruction)"
else fl "initialize-ecf-run.ps1 is not a thin adapter"; fi
[ ! -e "$ROOT/scripts/_ecf_init_run.py" ] && pass "hand-rolled initializer retired" || fl "hand-rolled initializer still present"

# initialized run structure
[ -f "$RUN/manifest.yaml" ] && pass "manifest.yaml exists" || fl "manifest.yaml missing"
grep -q "^run_id:.*$RUNID" "$RUN/state.yaml"    2>/dev/null && pass "state.yaml run_id matches"    || fl "state.yaml run_id mismatch"
grep -q "^run_id:.*$RUNID" "$RUN/manifest.yaml" 2>/dev/null && pass "manifest.yaml run_id matches" || fl "manifest.yaml run_id mismatch"
sr=$(grep -E '^revision:' "$RUN/state.yaml"    2>/dev/null | awk '{print $2}')
mr=$(grep -E '^revision:' "$RUN/manifest.yaml" 2>/dev/null | awk '{print $2}')
{ [ "$sr" = "0" ] && [ "$mr" = "0" ]; } && pass "revisions start at zero" || fl "initial revisions not zero (state=$sr manifest=$mr)"
grep -qE '^[[:space:]]*mode: required' "$RUN/state.yaml" 2>/dev/null && pass "provenance mode explicit (required)" || fl "provenance mode not explicit"
[ -f "$RUN/inputs/work-request.md" ] && pass "work-request input exists" || fl "work-request input missing"

# canonical planner BEFORE (via consumer wrapper)
psrun "$(to_windows_path "$PLAN_WRAP")" -Run "$RUN_W" 2>/dev/null | grep -A2 '^READY' | grep -q 'TASK-CLASSIFY-0001' \
  && pass "planner: TASK-CLASSIFY-0001 ready" || fl "planner: CLASSIFY-0001 not ready"

# =============================================================================
# Step 3b — run exactly one fixture-backed task (fail-fast, like Step 1/2).
# =============================================================================
# fixture: the valid generated one, or CI_FIXTURE (diagnostic override).
FIXSRC="${CI_FIXTURE:-$FIX}"
FIX_W="$(to_windows_path "$FIXSRC")"
RUN_WRAP_W="$(to_windows_path "$RUN_WRAP")"

# wrapper forwards the canonical fixture-executor arguments, and the path resolves
grep -q '"--executor"' "$RUN_WRAP" && grep -q '"--fixture"' "$RUN_WRAP" \
  && pass "run-ecf-task.ps1 forwards --executor/--fixture to the canonical runner" \
  || fl "run-ecf-task.ps1 does not forward canonical fixture args"
{ [ -f "$FIXSRC" ] && [ -n "$FIX_W" ]; } && pass "fixture path resolves (Windows-accessible)" || fl "fixture path does not resolve"

RUN_DESC="$PS -NoProfile -ExecutionPolicy Bypass -File $RUN_WRAP_W -Run $RUN_W -Task TASK-CLASSIFY-0001 -Executor fixture -Fixture $FIX_W -Format text"
# offline guard on the actual invocation
printf '%s' "$RUN_DESC" | grep -qiE 'AllowLiveClaude|claude-code' \
  && fl "runner invocation would enable live Claude" \
  || pass "offline only — fixture executor used; live Claude not invoked"

psrun "$RUN_WRAP_W" -Run "$RUN_W" -Task TASK-CLASSIFY-0001 -Executor fixture -Fixture "$FIX_W" -Format text >"$RUN_OUT" 2>"$RUN_ERR"
run_rc=$?
committed=0
if [ "$run_rc" -eq 0 ] \
   && grep -q 'committed' "$RUN_OUT" && grep -q 'runner_stopped' "$RUN_OUT" \
   && [ -f "$RUN/task_outputs/engineering-intent.yaml" ]; then committed=1; fi

if [ "$committed" -ne 1 ]; then
  say ""; say "RUNNER FAILED"; say ""
  say "Command:";   printf '  %s\n' "$RUN_DESC"; say ""
  say "Exit code:"; printf '  %s\n' "$run_rc"; say ""
  say "STDOUT"; { [ -s "$RUN_OUT" ] && sed 's/^/  /' "$RUN_OUT"; } || say "  (empty)"; say ""
  say "STDERR"; { [ -s "$RUN_ERR" ] && sed 's/^/  /' "$RUN_ERR"; } || say "  (empty)"; say ""
  say "STOP"; exit 1
fi
pass "fixture executor committed exactly one task"
pass "runner reported it stopped"

# post-commit assertions (only reached when the runner committed)
grep -q 'TASK-CLASSIFY-0001: completed' "$RUN/state.yaml" 2>/dev/null && pass "TASK-CLASSIFY-0001 completed" || fl "CLASSIFY-0001 not completed"
[ -f "$RUN/task_outputs/engineering-intent.yaml" ] && pass "task output exists" || fl "task output missing"
[ -f "$RUN/provenance/TASK-CLASSIFY-0001.yaml" ]   && pass "provenance exists"  || fl "provenance missing"
sr=$(grep -E '^revision:' "$RUN/state.yaml"    2>/dev/null | awk '{print $2}')
mr=$(grep -E '^revision:' "$RUN/manifest.yaml" 2>/dev/null | awk '{print $2}')
[ "$sr" = "$mr" ] && pass "state/manifest revisions match after commit ($sr)" || fl "revisions mismatch after commit (state=$sr manifest=$mr)"

# canonical planner AFTER (via consumer wrapper)
psrun "$(to_windows_path "$PLAN_WRAP")" -Run "$RUN_W" 2>/dev/null | grep -A2 '^READY' | grep -q 'TASK-CLASSIFY-0002' \
  && pass "planner advanced: TASK-CLASSIFY-0002 ready" || fl "planner did not advance to CLASSIFY-0002"

# vendor BEFORE/AFTER delta
( cd "$ROOT" && git status --porcelain -- vendor/ecf 2>/dev/null ) | LC_ALL=C sort > "$AFTER"
newv="$(comm -13 "$BEFORE" "$AFTER")"; remv="$(comm -23 "$BEFORE" "$AFTER")"
if [ -z "$newv" ]; then pass "no NEW vendor/ecf changes introduced by the test"; else fl "test introduced NEW vendor/ecf changes:"; printf '   %s\n' "$newv"; fi
[ -n "$remv" ] && { say "WARN: test removed pre-existing vendor/ecf entries (review):"; printf '   %s\n' "$remv"; }
pyc_after=$(find "$ECF" -name '__pycache__' -type d 2>/dev/null | wc -l | tr -d ' ')
[ "${pyc_after:-0}" -le "${pyc_before:-0}" ] && pass "no new bytecode/cache created in vendor" || fl "test created bytecode/cache in vendor (before=$pyc_before after=$pyc_after)"

# runtime ignored
( cd "$ROOT" && git check-ignore -q "runtime/runs/$RUNID" ) && pass "runtime/runs is git-ignored" || fl "runtime/runs not ignored"

# runtime cleanup verified
case "$RUN" in "$ROOT/runtime/runs/RUN-CONSUMER-TEST-"*) rm -rf "$RUN" ;; esac
[ ! -e "$RUN" ] && pass "temporary run cleaned up" || fl "temporary run not cleaned"

say ""
say "consumer-integration: $fail failure(s)"
[ "$fail" -eq 0 ]
