#!/usr/bin/env bash
# Engineering-backend resolver — bash binding of the Port-1 contract.
# Canonical contract: scripts/engineering_backend.py (ADR-0007). The bindings
# are kept in agreement by acceptance_tests/check_backend_boundary.sh.
#
# Resolution order: CONTEXT_SWITCHER_ENGINEERING_BACKEND env var ->
# config/engineering-backend.yaml -> default "standalone".
#
# resolve_engineering_backend ROOT
#   Prints the resolved backend name and returns 0, or prints an ERROR line
#   to stderr and returns: 2 invalid value; 3 ecf unavailable; 4 ecf
#   incompatible. NEVER silently falls back from ecf to standalone.
#
# Pure bash + grep/sed; no Python required (standalone environments may
# resolve the backend before any tooling check).

CS_BACKEND_ENV_VAR="CONTEXT_SWITCHER_ENGINEERING_BACKEND"
CS_BACKEND_CONFIG="config/engineering-backend.yaml"
CS_BACKEND_SUPPORTED_ECF_SCHEMA_LINE="0.1"

_cs_read_kv() { # KEY FILE -> normalized value (LF/CRLF safe), empty if absent
  local key="$1" file="$2"
  [ -f "$file" ] || return 0
  grep -E "^[[:space:]]*${key}:" "$file" 2>/dev/null \
    | grep -vE '^[[:space:]]*#' \
    | head -n 1 \
    | sed -E "s/^[[:space:]]*${key}:[[:space:]]*//" \
    | tr -d '\r' \
    | sed -E "s/^[\"']//; s/[\"']$//"
}

# _cs_validate_ecf ROOT -> 0 ok; 3 unavailable; 4 incompatible (message on stderr)
_cs_validate_ecf() {
  local root="$1" ecf="$1/vendor/ecf"
  if [ ! -d "$ecf" ]; then
    echo "ERROR: engineering_backend=ecf was requested but vendor/ecf is missing." \
         "Refresh the bundle (scripts/bundle-ecf.ps1 -Source <ecf-repo>) or select" \
         "the standalone backend (${CS_BACKEND_ENV_VAR}=standalone or ${CS_BACKEND_CONFIG})." >&2
    return 3
  fi
  local schema commit
  schema="$(_cs_read_kv schema_version "$ecf/ecf-version.yaml")"
  case "$schema" in
    "$CS_BACKEND_SUPPORTED_ECF_SCHEMA_LINE"|"$CS_BACKEND_SUPPORTED_ECF_SCHEMA_LINE".*) : ;;
    *)
      echo "ERROR: engineering_backend=ecf: bundled ECF schema_version '${schema:-missing}'" \
           "is not on the supported line '${CS_BACKEND_SUPPORTED_ECF_SCHEMA_LINE}'" \
           "(release/COMPATIBILITY.md)." >&2
      return 4 ;;
  esac
  commit="$(_cs_read_kv source_commit "$ecf/VERSION")"
  if ! printf '%s' "$commit" | grep -qE '^[0-9a-f]{40}$'; then
    echo "ERROR: engineering_backend=ecf: vendor/ecf/VERSION has no valid 40-hex" \
         "source_commit — bundle identity is unverifiable. Refresh the bundle." >&2
    return 4
  fi
  return 0
}

resolve_engineering_backend() { # ROOT
  local root="$1" value source
  value="$(printenv "$CS_BACKEND_ENV_VAR" 2>/dev/null || true)"
  if [ -n "${value:-}" ]; then
    source="environment variable $CS_BACKEND_ENV_VAR"
  else
    value="$(_cs_read_kv engineering_backend "$root/$CS_BACKEND_CONFIG")"
    source="$CS_BACKEND_CONFIG"
  fi
  if [ -z "${value:-}" ]; then
    echo "standalone"
    return 0
  fi
  case "$value" in
    standalone)
      echo "standalone"; return 0 ;;
    ecf)
      _cs_validate_ecf "$root" || return $?
      echo "ecf"; return 0 ;;
    *)
      echo "ERROR: invalid engineering_backend '$value' (from $source);" \
           "allowed values: standalone, ecf" >&2
      return 2 ;;
  esac
}
