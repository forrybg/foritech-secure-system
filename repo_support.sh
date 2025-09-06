#!/usr/bin/env bash
set -euo pipefail
OUT="/tmp/repo_bundle_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUT"

# Основна мета-информация (без секрети)
{
  echo "== GIT =="
  git rev-parse --is-inside-work-tree 2>/dev/null || true
  git status -sb 2>/dev/null || true
  git log --oneline -n 20 2>/dev/null || true
  git remote -v 2>/dev/null | sed 's/@.*:/@REDACTED:/g' || true
  echo
  echo "== PYTHON =="
  command -v python || true
  python --version 2>/dev/null || true
  command -v python3 || true
  python3 --version 2>/dev/null || true
  echo
  echo "== PIP =="
  pip --version 2>/dev/null || true
  pip list 2>/dev/null | head -n 100 || true
  echo
  echo "== OPENSSL =="
  openssl version 2>/dev/null || true
} > "$OUT/overview.txt"

# Конфигурационни файлове (типични)
for f in pyproject.toml poetry.lock requirements*.txt setup.cfg setup.py \
         pytest.ini tox.ini .env.example .python-version \
         README* LICENSE .gitignore .gitattributes ; do
  [ -f "$f" ] && cp -v "$f" "$OUT/" || true
done

# Структура (без .git, venv и кешове)
tar -czf "$OUT/tree.tgz" \
  --exclude .git --exclude .venv --exclude venv --exclude .pytest_cache \
  --exclude __pycache__ --exclude .mypy_cache --exclude node_modules \
  --transform 's,^\.,project_tree,' \
  -C . .

echo "Bundle at: $OUT"
