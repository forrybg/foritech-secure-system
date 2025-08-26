# ===== Foritech Quick Ops =====
PY ?= python
CLI ?= foritech

HOST ?= 127.0.0.1
PORT ?= 8443

# Демо артефакти (не се комитват; .gitignore покрива)
CERT ?= spki_self.pem
KEY  ?= spki_self.key
CA_CERT ?= ca.pem
CA_KEY  ?= ca.key

# Kyber ключове (генерирани с scripts/kyber-keygen.py)
PUB ?= $(HOME)/.foritech/keys/kyber768_pub.bin
SK  ?= $(HOME)/.foritech/keys/kyber768_sec.bin

export FORITECH_SK ?= $(SK)

.PHONY: help gen-keys x509-self-raw x509-self-spki x509-ca x509-leaf-raw x509-leaf-spki \
        run-server run-client ping \
        wrap-demo stream-demo meta test fmt lint typecheck clean

help:
	@echo "Targets:"
	@echo "  gen-keys         - generate Kyber keys (PUB/SK) into ~/.foritech/keys/"
	@echo "  x509-self-raw    - self-signed X.509 with raw PQC ext (Kyber pub)"
	@echo "  x509-self-spki   - self-signed X.509 with SPKI PQC ext (Kyber pub)"
	@echo "  x509-ca          - self-signed CA (ECDSA P-256)"
	@echo "  x509-leaf-raw    - leaf from CA with raw PQC ext"
	@echo "  x509-leaf-spki   - leaf from CA with SPKI PQC ext (and fullchain)"
	@echo "  run-server       - start TLS-PQC demo server (uses $(CERT)/$(KEY))"
	@echo "  run-client       - run TLS-PQC demo client to $(HOST):$(PORT)"
	@echo "  ping             - handshake + send batches + bye (client)"
	@echo "  wrap-demo        - small-file wrap/unwrap demo"
	@echo "  stream-demo      - 128MiB streaming wrap/unwrap demo"
	@echo "  meta FILE=...    - print container metadata for a file"
	@echo "  test             - pytest -q"
	@echo "  fmt / lint       - ruff fix / check"
	@echo "  typecheck        - mypy over sdk/src/foritech"
	@echo "  clean            - remove local demo artifacts (pem/key/bin/enc/out)"

gen-keys:
	$(PY) scripts/kyber-keygen.py
	@echo "export FORITECH_SK=\"$(SK)\""

x509-self-raw:
	$(CLI) x509-make --cn raw-demo --format raw \
	  --pqc-pub "$(PUB)" --cert-out raw.pem --key-out raw.key
	$(CLI) x509-info --in raw.pem

x509-self-spki:
	$(CLI) x509-make --cn spki-demo --format spki \
	  --pqc-pub "$(PUB)" --cert-out $(CERT) --key-out $(KEY)
	$(CLI) x509-info --in $(CERT)

x509-ca:
	$(CLI) x509-make-ca --cn demo-ca --cert-out $(CA_CERT) --key-out $(CA_KEY)

x509-leaf-raw: x509-ca
	$(CLI) x509-issue --cn leaf-raw --kem Kyber768 --format raw \
	  --pqc-pub "$(PUB)" --ca-cert $(CA_CERT) --ca-key $(CA_KEY) \
	  --cert-out leaf_raw.pem --chain-out fullchain_raw.pem
	$(CLI) x509-info --in leaf_raw.pem

x509-leaf-spki: x509-ca
	$(CLI) x509-issue --cn leaf-spki --kem Kyber768 --format spki \
	  --pqc-pub "$(PUB)" --ca-cert $(CA_CERT) --ca-key $(CA_KEY) \
	  --cert-out leaf_spki.pem --chain-out fullchain.pem
	$(CLI) x509-info --in leaf_spki.pem

run-server:
	$(PY) scripts/tls_pqc_server.py --host $(HOST) --port $(PORT) \
	  --cert $(CERT) --key $(KEY)

run-client:
	$(PY) scripts/tls_pqc_client.py --host $(HOST) --port $(PORT)

# едно-натискане: handshake, batch1, rotate, batch2, single, bye
ping:
	$(PY) - <<'PY'
from foritech.tlspqc import TLSPQCClient
c = TLSPQCClient("$(HOST)", int("$(PORT)"))
hs = c.handshake()
s = c.session(hs)
p1, rot1 = s.send_many([b"m1", b"m2", b"m3"], key_update=False); print("Batch1:", [x.decode() for x in p1], "rot?", rot1, "epoch", s.epoch)
p2, rot2 = s.send_many([b"m4", b"m5"], key_update=True);  print("Batch2:", [x.decode() for x in p2], "rot?", rot2, "epoch", s.epoch)
one, rot3 = s.send_one(b"last");                                  print("Single:", one.decode(), "rot?", rot3, "epoch", s.epoch)
print("Bye deleted:", s.bye())
PY

wrap-demo:
	echo "small" > s.txt
	$(CLI) wrap --in s.txt --out s.enc --recipient raw:"$(PUB)" --kid kid-s
	$(CLI) meta --in s.enc
	$(CLI) unwrap --in s.enc --out s.out
	diff -u s.txt s.out && echo "OK small ✅"

stream-demo:
	fallocate -l 128M big.bin 2>/dev/null || head -c 128M </dev/urandom > big.bin
	$(CLI) wrap --in big.bin --out big.enc --recipient raw:"$(PUB)" --kid kid-b
	$(CLI) meta --in big.enc
	$(CLI) unwrap --in big.enc --out big.out
	cmp -s big.bin big.out && echo "OK big (stream) ✅"

meta:
	@test -n "$(FILE)" || (echo "usage: make meta FILE=path/to/file" && exit 2)
	$(CLI) meta --in "$(FILE)"

test:
	pytest -q

fmt:
	ruff check --fix .

lint:
	ruff check .

typecheck:
	mypy sdk/src/foritech

clean:
	rm -f *.pem *.key fullchain*.pem pqc_*.bin spki_*.bin \
	      s.txt s.enc s.out big.bin big.enc big.out a.* *.enc *.out 2>/dev/null || true
