#!/usr/bin/env bash
set -euo pipefail
source .venv/bin/activate 2>/dev/null || true

tmp=$(mktemp -d)
echo "hello-foritech" > "$tmp/a.txt"
foritech wrap --in "$tmp/a.txt" --out "$tmp/a.enc" --recipient raw:pubkey.bin --aad "demo" --kid "kid-123"
foritech unwrap --in "$tmp/a.enc" --out "$tmp/a.out"
echo ">>> out:"; cat "$tmp/a.out"
rm -rf "$tmp"
