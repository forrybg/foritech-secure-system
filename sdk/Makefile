VENV_BIN=../.venv/bin
PIP=$(VENV_BIN)/pip
PYTEST=$(VENV_BIN)/pytest
FORITECH=$(VENV_BIN)/foritech

ALG?=Dilithium2
DATA?=foritech-demo
BUNDLE=/tmp/foritech_bundle.txt
RSA_PEM=/tmp/rsa_pub.pem
HK=/tmp/hk.txt

.PHONY: help
help:
	@echo "make dev        - install editable + dev deps"
	@echo "make keys       - generate public keys (RSA PEM + PQC b64)"
	@echo "make sign       - hybrid-sign (prints RSA/PQC signatures)"
	@echo "make bundle     - create one-file bundle (keys + signatures)"
	@echo "make check      - verify the bundle"
	@echo "make test       - run pytest"

.PHONY: dev
dev:
	$(PIP) install -e .[dev]

.PHONY: keys
keys:
	$(FORITECH) hybrid-keys --alg $(ALG) > $(HK) && \
	awk '/^RSA_PEM_BEGIN/,/^RSA_PEM_END/' $(HK) | sed '1d;$$d' > $(RSA_PEM) && \
	echo "PQC_PUB_B64=$$(awk '/^PQC_B64/{print $$2}' $(HK))" && \
	echo "RSA_PEM=$(RSA_PEM)"

.PHONY: sign
sign:
	$(FORITECH) hybrid-sign --data "$(DATA)" --alg $(ALG)

.PHONY: bundle
bundle:
	$(FORITECH) hybrid-sign-bundle --data "$(DATA)" --alg $(ALG) --out-file $(BUNDLE) && \
	echo "WROTE $(BUNDLE)"

.PHONY: check
check:
	$(FORITECH) hybrid-verify-bundle $(BUNDLE)

.PHONY: test
test:
	$(PYTEST) -q

.PHONY: bundle-json
bundle-json:
	$(FORITECH) hybrid-sign-json --data "$(DATA)" --alg $(ALG) --out-file $(BUNDLE).json && \
	echo "WROTE $(BUNDLE).json"

.PHONY: check-json
check-json:
	$(FORITECH) hybrid-verify-json $(BUNDLE).json
