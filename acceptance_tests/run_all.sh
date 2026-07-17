#!/usr/bin/env bash
# Runs all Context Switcher project acceptance tests and aggregates results.
# Exit 0 = every selected test passed; non-zero = at least one FAIL.
#
# Test selection is backend-aware (ADR-0007):
#   * The STANDALONE suite always runs — it is Context Switcher's required gate
#     and needs no ECF bundle, checkout, or environment.
#   * The ECF suite additionally runs when engineering_backend resolves to
#     `ecf`. If `ecf` is configured but the bundle is missing or incompatible,
#     the run FAILS immediately — an explicitly requested backend never
#     silently degrades to standalone.
set -u
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$DIR/.." && pwd)"
# shellcheck source=lib/backend.sh
. "$DIR/lib/backend.sh"

# Optional explicit override: run_all.sh --backend <standalone|ecf>
# (equivalent to setting CONTEXT_SWITCHER_ENGINEERING_BACKEND; the value is
# validated by the resolver like any other configuration source).
if [ "${1:-}" = "--backend" ]; then
  if [ -z "${2:-}" ]; then
    printf 'ERROR: --backend requires a value (standalone|ecf)\n' >&2
    exit 2
  fi
  export CONTEXT_SWITCHER_ENGINEERING_BACKEND="$2"
fi

standalone_tests=(
  check_engineering_context.sh
  check_work_requests.sh
  check_architecture_consistency.sh
  check_ignore_boundaries.sh
  check_backend_boundary.sh
  check_product_tests.sh
)
ecf_tests=(
  check_vendor_integrity.sh
  check_bundle_integrity.sh
  check_consumer_integration.sh
)

backend="$(resolve_engineering_backend "$ROOT")"
rc=$?
if [ "$rc" -ne 0 ]; then
  printf 'engineering_backend configuration is invalid (rc=%s); see the error above.\n' "$rc"
  printf 'RESULT: CONFIGURATION FAILURE\n'
  exit "$rc"
fi

tests=("${standalone_tests[@]}")
if [ "$backend" = "ecf" ]; then
  tests+=("${ecf_tests[@]}")
fi

printf 'Active engineering backend: %s\n' "$backend"
if [ "$backend" = "standalone" ]; then
  printf 'ECF suite (%s) skipped: unavailable in standalone mode (no ECF guarantees claimed).\n' \
    "$(IFS=', '; printf '%s' "${ecf_tests[*]}")"
fi

overall=0
results=()
for t in "${tests[@]}"; do
  printf '\n--------------------------------------------------------------\n'
  bash "$DIR/$t"
  rc=$?
  if [ "$rc" -eq 0 ]; then results+=("PASS  $t"); else results+=("FAIL  $t"); overall=1; fi
done

printf '\n==============================================================\n'
printf 'Acceptance Test Summary (backend: %s)\n' "$backend"
printf -- '--------------------------------------------------------------\n'
for r in "${results[@]}"; do printf '  %s\n' "$r"; done
if [ "$backend" = "standalone" ]; then
  for t in "${ecf_tests[@]}"; do printf '  SKIP  %s (requires ecf backend)\n' "$t"; done
fi
printf -- '--------------------------------------------------------------\n'
if [ "$overall" -eq 0 ]; then
  printf 'RESULT: ALL SELECTED TESTS PASSED\n'
else
  printf 'RESULT: FAILURES PRESENT (see PROJECT_ECF_ADOPTION_REPORT.md open findings)\n'
fi
exit "$overall"
