#!/usr/bin/env bash
set -euo pipefail

# Път до проекта
PROJECT_DIR="$HOME/foritech-secure-system"

# Папка за локални архиви
BACKUP_DIR="$HOME/git_backups"
mkdir -p "$BACKUP_DIR"

# Remote за backup (например GitLab)
BACKUP_REMOTE="backup"

echo "[i] Starting backup of $PROJECT_DIR"

cd "$PROJECT_DIR"

# 1) Push --mirror към backup remote (ако е настроен)
if git remote get-url "$BACKUP_REMOTE" &>/dev/null; then
    echo "[i] Pushing mirror to remote '$BACKUP_REMOTE'..."
    git push --mirror "$BACKUP_REMOTE"
else
    echo "[!] Backup remote '$BACKUP_REMOTE' is not set. Skipping remote mirror."
fi

# 2) Локален архив tar.gz
DATE=$(date +%F_%H-%M-%S)
ARCHIVE="$BACKUP_DIR/foritech-secure-system_$DATE.tar.gz"

echo "[i] Creating local archive $ARCHIVE ..."
tar czf "$ARCHIVE" .

echo "[✅] Backup complete!"
echo " - Remote mirror: $( [ -n "$(git remote get-url backup 2>/dev/null || true)" ] && echo OK || echo skipped )"
echo " - Local archive: $ARCHIVE"
