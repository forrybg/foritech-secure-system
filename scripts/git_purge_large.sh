#!/usr/bin/env bash
set -euo pipefail
THRESH="${1:-95M}"
echo "[1/4] .gitignore & untrack…"
grep -q 'big\.' .gitignore || printf "big.*\n*.enc\n*.out\n*.bin\ns.txt\ns.enc\ns.out\n" >> .gitignore
echo "liboqs-python/" >> .gitignore
git add .gitignore
git rm -r --cached --ignore-unmatch big* s.* a.* *.enc *.out liboqs-python || true
git commit -m "chore: ignore large/test artifacts; untrack liboqs-python and blobs" || true
echo "[2/4] install git-filter-repo if missing…"
python -c "import git_filter_repo" 2>/dev/null || pip install git-filter-repo
echo "[3/4] filter history (>${THRESH})…"
python -m git_filter_repo --force --strip-blobs-bigger-than "$THRESH"
echo "[4/4] push…"
git push --force-with-lease origin main
echo "Done."
