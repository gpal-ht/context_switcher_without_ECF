#!/usr/bin/env bash
# Runs all Context Switcher project acceptance tests and aggregates results.
# Exit 0 = every test passed; non-zero = at least one FAIL.
#
# This is a standalone .NET application repository (ADR-0010: ECF removed).
# There is a single operating mode; no backend selection.
set -u
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
tests=(
  check_engineering_context.sh
  check_architecture_consistency.sh
  check_ignore_boundaries.sh
  check_product_tests.sh
)
overall=0
results=()
for t in "${tests[@]}"; do
  printf '\n--------------------------------------------------------------\n'
  bash "$DIR/$t"
  rc=$?
  if [ "$rc" -eq 0 ]; then results+=("PASS  $t"); else results+=("FAIL  $t"); overall=1; fi
done

printf '\n==============================================================\n'
printf 'Acceptance Test Summary\n'
printf -- '--------------------------------------------------------------\n'
for r in "${results[@]}"; do printf '  %s\n' "$r"; done
printf -- '--------------------------------------------------------------\n'
if [ "$overall" -eq 0 ]; then
  printf 'RESULT: ALL TESTS PASSED\n'
else
  printf 'RESULT: FAILURES PRESENT\n'
fi
exit "$overall"
