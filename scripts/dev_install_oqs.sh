#!/usr/bin/env bash
set -euo pipefail

echo "== Foritech • local liboqs + liboqs-python installer (no sudo) =="
ROOT="$(pwd)"
PREFIX="$ROOT/third_party/oqs-local"
LIBDIR="$PREFIX/lib"
INCLUDEDIR="$PREFIX/include"

if [ ! -d ".venv" ]; then
  echo "[-] .venv не е намерен. Създай и активирай venv първо:"
  echo "    python3.12 -m venv .venv && source .venv/bin/activate"
  exit 1
fi
source .venv/bin/activate

python - <<'PY' || { echo "[-] Активирай venv преди скрипта."; exit 1; }
import sys
print("[+] Python in venv:", sys.prefix)
PY

mkdir -p third_party
cd third_party

echo "== 1) Fetch liboqs (OpenQuantumSafe) =="
if [ ! -d liboqs ]; then
  git clone --depth 1 https://github.com/open-quantum-safe/liboqs.git
fi
cd liboqs
mkdir -p build && cd build
cmake .. \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX="$PREFIX" \
  -DBUILD_SHARED_LIBS=ON \
  -DOQS_BUILD_ONLY_LIB=ON \
  -DOQS_ENABLE_KEM_KYBER=ON
make -j"$(nproc)"
make install
cd ../..

echo "== 2) Build & install liboqs-python into current venv =="
if [ ! -d liboqs-python ]; then
  git clone --depth 1 https://github.com/open-quantum-safe/liboqs-python.git
fi
cd liboqs-python
export CFLAGS="-I$INCLUDEDIR"
export LDFLAGS="-L$LIBDIR"
export LD_LIBRARY_PATH="$LIBDIR:${LD_LIBRARY_PATH:-}"
pip install -U pip wheel >/dev/null
pip install .
cd ..

echo "== 3) Inject runtime path into .venv/bin/activate (LD_LIBRARY_PATH) =="
ACTIVATE="$ROOT/.venv/bin/activate"
if ! grep -q '## foritech-oqs' "$ACTIVATE"; then
cat >> "$ACTIVATE" <<EOF

## foritech-oqs
export LD_LIBRARY_PATH="$LIBDIR:\${LD_LIBRARY_PATH:-}"
EOF
fi

echo "== 4) Quick check =="
python - <<'PY'
import oqs, sys
print("[+] oqs imported OK:", getattr(oqs, "__version__", "unknown"))
print("[+] Python:", sys.version.split()[0])
PY

echo "[✓] Done. Активирай отново venv и пробвай CLI."
