#!/usr/bin/env bash
set -euo pipefail
f="${1:?usage: backup_file.sh <path>}"
ts="$(date +%s)"
if [[ -f "$f" ]]; then
  cp -a -- "$f" "${f}.bak.${ts}"
  echo "Backed up: ${f} -> ${f}.bak.${ts}"
else
  echo "WARN: not a regular file: $f" >&2
fi
