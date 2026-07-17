#!/usr/bin/env bash
# Acceptance test: Architecture consistency (read-only), severity-aware.
#
# Severity levels: blocking | major | warning | informational
#
# Two separate outcomes are reported:
#   (1) "Architecture consistency for WR-0002" — the subsystem-model decision gate.
#       Fails (non-zero exit) ONLY on BLOCKING findings.
#   (2) "Overall project architecture coverage" — general coverage findings
#       (e.g. empty docs). These are WARNING/INFORMATIONAL and never fail the gate.
#
# Canonical subsystem model source of truth: ADR-0005 / SYSTEM_ARCHITECTURE.md.
# Exit 0 = no blocking findings; non-zero = >=1 blocking finding.
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARCH="$ROOT/docs/architecture"
DEC="$ROOT/decisions"
CTX="$ROOT/docs/engineering/ENGINEERING_CONTEXT.md"
SYS="$ARCH/SYSTEM_ARCHITECTURE.md"
VIS="$ARCH/SYSTEM_VISION.md"
ADR2="$DEC/ADR-0002-modular-platform-architecture.md"
ADR4="$DEC/ADR-0004-event-driven-application-design.md"
ADR5="$DEC/ADR-0005-canonical-subsystem-model.md"

b=0; m=0; w=0; i=0
say(){ printf '%s\n' "$*"; }
BLOCK(){ say "BLOCKING:      $1"; b=$((b+1)); }
MAJOR(){ say "MAJOR:         $1"; m=$((m+1)); }
WARN(){ say "WARNING:       $1"; w=$((w+1)); }
INFO(){ say "INFORMATIONAL: $1"; i=$((i+1)); }
OK(){ say "ok:            $1"; }

CANON=("Experience" "Work" "Knowledge" "AI" "Integration" "Productivity Intelligence")

say "=============================================================="
say "Outcome 1 — Architecture Consistency for WR-0002 (blocking gate)"
say "=============================================================="

# ADR-0005 (canonical subsystem model) must exist.
if [ -f "$ADR5" ]; then OK "ADR-0005 canonical subsystem model present"; else BLOCK "ADR-0005 canonical subsystem model missing"; fi

# The six canonical subsystems must each be enumerated in SYSTEM_ARCHITECTURE and ENGINEERING_CONTEXT.
for doc in "$SYS" "$CTX"; do
  name="$(basename "$doc")"
  for s in "${CANON[@]}"; do
    if grep -qiw "$s" "$doc"; then OK "$name enumerates canonical subsystem: $s"
    else BLOCK "$name is missing canonical subsystem: $s"; fi
  done
done

# SYSTEM_VISION must reconcile: either enumerate all six, or explicitly reference ADR-0005.
vis_all=1
for s in "${CANON[@]}"; do grep -qiw "$s" "$VIS" || vis_all=0; done
if [ "$vis_all" -eq 1 ] || grep -qi "ADR-0005" "$VIS"; then
  OK "SYSTEM_VISION reconciled with canonical registry (enumerates all six or references ADR-0005)"
else
  BLOCK "SYSTEM_VISION subsystem enumeration inconsistent with canonical registry and does not reference ADR-0005"
fi

# Runtime must NOT be enumerated as a Core Subsystem heading in the current architecture.
if grep -qiE "^##[[:space:]]+Runtime([[:space:]]|$|[[:space:]]Engine)" "$SYS"; then
  BLOCK "SYSTEM_ARCHITECTURE lists 'Runtime' as a Core Subsystem (should be a cross-cutting concern per ADR-0005)"
else
  OK "Runtime is not enumerated as a subsystem in SYSTEM_ARCHITECTURE (treated as a concern)"
fi

# Historical ADRs must retain their lists but carry an ADR-0005 clarification.
if grep -qi "ADR-0005" "$ADR4"; then INFO "ADR-0004 retains its historical 7-item list, clarified by ADR-0005"
else MAJOR "ADR-0004 lists Runtime/Integration as subsystems with no ADR-0005 clarification"; fi
if grep -qi "ADR-0005" "$ADR2"; then INFO "ADR-0002 retains its historical 5-engine list, clarified by ADR-0005"
else MAJOR "ADR-0002 lists 5 engines with no ADR-0005 clarification"; fi

say ""
say "=============================================================="
say "Outcome 2 — Overall Project Architecture Coverage (non-blocking)"
say "=============================================================="

shopt -s nullglob
for f in "$ARCH"/*.md; do
  lines=$(wc -l < "$f" | tr -d ' ')
  if [ -s "$f" ] && [ "${lines:-0}" -gt 3 ]; then
    OK "non-empty: $(basename "$f") (${lines} lines)"
  else
    WARN "empty/stub architecture doc (coverage gap; non-blocking for WR-0002): $(basename "$f")"
  fi
done

say ""
say "severity summary: blocking=$b major=$m warning=$w informational=$i"
if [ "$b" -eq 0 ]; then
  say "WR-0002 architecture-consistency gate: PASS (no blocking findings)"
else
  say "WR-0002 architecture-consistency gate: FAIL ($b blocking finding(s))"
fi
[ "$b" -eq 0 ]
