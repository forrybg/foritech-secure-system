#!/usr/bin/env bash
set -euo pipefail
ts=$(date +%s)
backup="repo_backup_$ts"
echo ">>> Backup dir: $backup"
mkdir -p "$backup"

# 0) Увери се, че сме в корена (има pyproject.toml)
test -f pyproject.toml || { echo "❌ Пусни това от корена на репото"; exit 1; }

# 1) Създай tests/ ако липсва
mkdir -p tests

# 2) Събери всички „чужди“ tests/ и ги слей в корена
mapfile -t TDIRS < <(find . -mindepth 1 -maxdepth 4 -type d -name tests ! -path "./tests")
echo ">>> Намерени външни tests/: ${#TDIRS[@]}"
for d in "${TDIRS[@]}"; do
  echo "   - merge $d -> ./tests"
  rsync -a "$d"/ ./tests/ 2>/dev/null || true
  # премести стария tests/ в backup, за да не пречи
  newname="$(echo "$d" | sed 's#^\./##; s#[/\.]#_#g')"
  mv "$d" "$backup/$newname" || true
done

# 3) Премести разпилени пакети/файлове към backup (канон е sdk/src/foritech)
for path in src/foritech crypto pki api.py cli.py; do
  if [ -e "$path" ]; then
    echo ">>> move $path -> $backup/"
    mv "$path" "$backup/" || true
  fi
done

# 4) Чисти egg-info в sdk/src/
find sdk/src -maxdepth 1 -type d -name "*egg-info" -print -exec mv {} "$backup/" \; 2>/dev/null || true

# 5) pytest.ini (указваме да гледа само кореновия tests/)
cat > pytest.ini <<'INI'
[pytest]
testpaths = tests
INI

# 6) .gitignore — добави игнори за случайни дубликати
if [ -f .gitignore ]; then cp .gitignore "$backup/.gitignore.bak.$ts"; fi
cat > .gitignore <<'GI'
__pycache__/
*.pyc
*.pyo
*.swp
.build/
dist/
*.egg-info/
.venv/
.env
.mypy_cache/
.pytest_cache/
.coverage

# избягваме втори layout в корена
src/
foritech-secure-system/

GI

# 7) Преинсталирай и тестове
if [ -z "${VIRTUAL_ENV-}" ]; then
  python3 -m venv .venv
  . .venv/bin/activate
fi
pip install -e ".[dev]" -q
pytest -q || true

echo ">>> Готово. Backup: $backup"
