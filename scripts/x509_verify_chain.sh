#!/usr/bin/env bash
set -euo pipefail
# Verify a leaf + optional chain + optional root

LEAF="${LEAF:-$1}"
CHAIN="${CHAIN:-${2:-}}"
ROOT="${ROOT:-${3:-}}"

if [[ -z "$LEAF" ]]; then
  echo "Usage: $0 <leaf.pem> [chain.pem] [root.pem]" >&2
  exit 2
fi

args=( x509-verify --leaf "$LEAF" )
[[ -n "$CHAIN" ]] && args+=( --chain "$CHAIN" )
[[ -n "$ROOT"  ]] && args+=( --root  "$ROOT" )

exec foritech "${args[@]}"
