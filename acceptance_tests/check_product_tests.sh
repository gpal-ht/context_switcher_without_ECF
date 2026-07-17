#!/usr/bin/env bash
# Acceptance test: Work Engine product build + deterministic test suite
# (ADR-0008). Requires no network and no NuGet packages (pure-BCL policy).
# The .NET SDK is required toolchain for the product; its absence is an
# honest FAIL, never a silent skip.
# Exit 0 = build succeeded and every product test passed.
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export DOTNET_NOLOGO=1 DOTNET_CLI_TELEMETRY_OPTOUT=1
fail=0
say(){ printf '%s\n' "$*"; }
pass(){ say "PASS: $1"; }
fl(){ say "FAIL: $1"; fail=$((fail+1)); }

say "== Work Engine Product Build + Tests =="

if ! command -v dotnet >/dev/null 2>&1; then
  fl "the .NET SDK is required to build Context Switcher product code (ADR-0008) but 'dotnet' was not found on PATH"
  say ""
  say "product-tests: $fail failure(s)"
  exit 1
fi

# Build the test project (also builds the Work library) and the CLI harness.
for proj in "src/Work/ContextSwitcher.Work.Tests" "src/App/ContextSwitcher.Cli"; do
  if dotnet build "$ROOT/$proj" -v q >/dev/null 2>&1; then
    pass "build succeeded: $proj"
  else
    fl "build FAILED: $proj (re-run 'dotnet build $proj' for details)"
  fi
done

if [ "$fail" -ne 0 ]; then
  say ""
  say "product-tests: $fail failure(s)"
  exit 1
fi

# Run the deterministic Work Engine suite; its own PASS/FAIL lines stream through.
if dotnet run --project "$ROOT/src/Work/ContextSwitcher.Work.Tests" --no-build; then
  pass "work engine test suite passed"
else
  fl "work engine test suite FAILED"
fi

say ""
say "product-tests: $fail failure(s)"
[ "$fail" -eq 0 ]
