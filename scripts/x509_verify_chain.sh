#!/usr/bin/env bash
set -euo pipefail
LEAF="${1:-pki/issued/leaf-sub1.pem}"
CHAIN="${2:-pki/issued/leaf-sub1_fullchain.pem}"
ROOT="${3:-pki/root/root.pem}"

if [ ! -f "$LEAF" ]; then echo "ERR: missing leaf: $LEAF" >&2; exit 2; fi
if [ ! -f "$CHAIN" ]; then echo "ERR: missing chain: $CHAIN" >&2; exit 2; fi
if [ ! -f "$ROOT" ];  then echo "ERR: missing root:  $ROOT" >&2; exit 2; fi

foritech x509-verify --leaf "$LEAF" --chain "$CHAIN" --root "$ROOT"
