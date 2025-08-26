#!/usr/bin/env bash
set -euo pipefail
ts="$(date +%Y%m%d_%H%M%S)"
out="repo_backups/backup_${ts}.tar.gz"
tar --exclude='.git' --exclude='.venv' -czf "$out" .
echo "Snapshot saved -> $out"
git status --porcelain > "repo_backups/status_${ts}.txt" || true
echo "Git status -> repo_backups/status_${ts}.txt"
