#!/usr/bin/env bash
set -euo pipefail

echo "== Repo =="
echo "- branch:  $(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?')"
echo "- commit:  $(git log -1 --oneline 2>/dev/null || echo '?')"
echo "- remote:"
git remote -v 2>/dev/null | sed -n '1,2p' || true
echo "- last tags:"
git tag --list 'v*' 2>/dev/null | tail -n 5 || true
echo

echo "== Python / Packages =="
python3 -c 'import sys; print("Python:", sys.version.split()[0])' || true
python3 - <<'PY' || true
try:
    import oqs
    v = getattr(oqs, "__version__", "unknown")
    print("liboqs-python:", v)
except Exception:
    print("liboqs-python: MISSING")
try:
    from cryptography import __version__ as cv
    print("cryptography:", cv)
except Exception:
    print("cryptography: MISSING")
try:
    import foritech, foritech.cli.main as m
    print("foritech CLI:", m.__file__)
except Exception as e:
    print("foritech: import ERROR:", e)
PY
echo

echo "== Foritech CLI (top help) =="
foritech --help 2>/dev/null | sed -n '1,120p' || echo "foritech CLI not available"
echo

echo "== Keys (~/.foritech/keys) =="
KEYDIR="$HOME/.foritech/keys"
if [ -d "$KEYDIR" ]; then
  ls -l "$KEYDIR" | awk '{print $9, $5}' || true
else
  echo "No keys dir."
fi
echo

echo "== PKI (repo ./pki) =="
for p in pki/root/root.pem pki/subca/subca.pem pki/issued; do
  [ -e "$p" ] && echo "FOUND $p" || echo "MISS  $p"
done
echo

echo "Tip: run './scripts/backup_snapshot.sh' to create a fresh backup."
