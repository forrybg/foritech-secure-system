# ForiTech PQC TLS PoC — Makefile (вариант A, чист)

SHARED      := $(HOME)/foritech-secure-system/pqc-tls/shared
IMAGE       := openquantumsafe/oqs-ossl3
OPENSSL     := /opt/openssl/bin/openssl
SDK_DIR     := $(HOME)/foritech-secure-system/sdk
FORITECH    := $(HOME)/foritech-secure-system/.venv/bin/foritech
PORT        ?= 9443

CERT        := $(SHARED)/cert.pem
KEY         := $(SHARED)/key.pem
BUNDLE      := $(SHARED)/bundle.json
INBOX_HTTP  := $(SHARED)/inbox.http
INBOX_JSON  := $(SHARED)/inbox.json
FILE        ?= /shared/bundle.json

.PHONY: all tls-clean tls-server-www tls-server-falcon tls-post-bundle tls-post-file \
        extract-body verify-inbox tls-server-raw tls-send-raw \
        tls-post-bundle-verbose tls-dump-inbox tls-e2e-www

all: verify-inbox

tls-clean:
	@rm -f $(CERT) $(KEY) $(INBOX_HTTP) $(INBOX_JSON) $(BUNDLE)

$(BUNDLE):
	@mkdir -p $(SHARED)
	@cd $(SDK_DIR) && $(FORITECH) hybrid-sign-json --data "hello-pqc" --out-file $(BUNDLE)
	@ls -lh $(BUNDLE)

tls-server-www:
	@mkdir -p $(SHARED)
	docker run --rm --network host -v $(SHARED):/shared $(IMAGE) \
	  sh -lc '$(OPENSSL) req -x509 -new -newkey mldsa44 \
	    -keyout /shared/key.pem -out /shared/cert.pem -days 30 -nodes \
	    -subj "/C=BG/ST=Sofia/L=Sofia/O=ForiTech/CN=localhost" >/dev/null 2>&1 && \
	    echo "[*] waiting on $(PORT)..." && \
	    $(OPENSSL) s_server -WWW -cert /shared/cert.pem -key /shared/key.pem \
	      -accept 0.0.0.0:$(PORT) -naccept 1 > /shared/inbox.http'

tls-server-falcon:
	@mkdir -p $(SHARED)
	docker run --rm --network host -v $(SHARED):/shared $(IMAGE) \
	  sh -lc '$(OPENSSL) req -x509 -new -newkey falcon512 \
	    -keyout /shared/key.pem -out /shared/cert.pem -days 30 -nodes \
	    -subj "/C=BG/ST=Sofia/L=Sofia/O=ForiTech/CN=localhost" >/dev/null 2>&1 && \
	    echo "[*] waiting on $(PORT) (falcon512)..." && \
	    $(OPENSSL) s_server -WWW -cert /shared/cert.pem -key /shared/key.pem \
	      -accept 0.0.0.0:$(PORT) -naccept 1 > /shared/inbox.http'

tls-post-bundle: $(BUNDLE) $(CERT)
	docker run --rm --network host -v $(SHARED):/shared $(IMAGE) \
	  sh -lc 'LEN=$$(wc -c </shared/bundle.json); \
	    { printf "POST / HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/json\r\nContent-Length: %s\r\n\r\n" "$$LEN"; \
	      cat /shared/bundle.json; } | \
	    $(OPENSSL) s_client -connect 127.0.0.1:$(PORT) -quiet -ign_eof -CAfile /shared/cert.pem >/dev/null'

tls-post-bundle-verbose: $(BUNDLE) $(CERT)
	docker run --rm --network host -v $(SHARED):/shared $(IMAGE) \
	  sh -lc 'LEN=$$(wc -c </shared/bundle.json); \
	    { printf "POST / HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/json\r\nContent-Length: %s\r\n\r\n" "$$LEN"; \
	      cat /shared/bundle.json; } | \
	    $(OPENSSL) s_client -connect 127.0.0.1:$(PORT) -ign_eof -CAfile /shared/cert.pem'

tls-post-file:
	@echo "[*] POST $(FILE) -> inbox.http"
	docker run --rm --network host -e FILE=$(FILE) -v $(SHARED):/shared $(IMAGE) \
	  sh -lc 'LEN=$$(wc -c < $$FILE); \
	    { printf "POST / HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/octet-stream\r\nContent-Length: %s\r\n\r\n" "$$LEN"; \
	      cat $$FILE; } | \
	    $(OPENSSL) s_client -connect 127.0.0.1:$(PORT) -quiet -ign_eof -CAfile /shared/cert.pem >/dev/null'

$(INBOX_JSON): $(INBOX_HTTP)
	@awk 'p{print} /^$$/{p=1}' $< > $@
	@ls -lh $@
	@head -c 120 $@ ; echo

verify-inbox: $(INBOX_JSON)
	@cd $(SDK_DIR) && $(FORITECH) hybrid-verify-json $(INBOX_JSON)

tls-server-raw:
	@mkdir -p $(SHARED)
	docker run --rm --network host -v $(SHARED):/shared $(IMAGE) \
	  sh -lc '$(OPENSSL) req -x509 -new -newkey mldsa44 \
	    -keyout /shared/key.pem -out /shared/cert.pem -days 30 -nodes \
	    -subj "/C=BG/ST=Sofia/L=Sofia/O=ForiTech/CN=localhost" >/dev/null 2>&1 && \
	    echo "[*] waiting on $(PORT)..." && \
	    $(OPENSSL) s_server -cert /shared/cert.pem -key /shared/key.pem \
	      -accept 0.0.0.0:$(PORT) -quiet -naccept 1 > /shared/inbox.json'

tls-send-raw: $(BUNDLE) $(CERT)
	docker run --rm --network host -v $(SHARED):/shared $(IMAGE) \
	  sh -lc 'cat /shared/bundle.json | $(OPENSSL) s_client \
	      -connect 127.0.0.1:$(PORT) -ign_eof -CAfile /shared/cert.pem >/dev/null'

tls-dump-inbox:
	@ls -lh $(INBOX_HTTP) || true
	@head -n 20 $(INBOX_HTTP) || true
	@echo '---- BODY (first 160 bytes) ----'
	@awk 'p{print} /^$$/{p=1}' $(INBOX_HTTP) | head -c 160 ; echo

tls-e2e-www:
	@mkdir -p $(SHARED)
	-@docker rm -f oqs_www >/dev/null 2>&1 || true
	docker run -d --name oqs_www --network host -v $(SHARED):/shared $(IMAGE) \
	  sh -lc '$(OPENSSL) req -x509 -new -newkey mldsa44 \
	    -keyout /shared/key.pem -out /shared/cert.pem -days 30 -nodes \
	    -subj "/C=BG/ST=Sofia/L=Sofia/O=ForiTech/CN=localhost" >/dev/null 2>&1 && \
	    echo "[*] waiting on $(PORT)..." && \
	    $(OPENSSL) s_server -WWW -cert /shared/cert.pem -key /shared/key.pem \
	      -accept 0.0.0.0:$(PORT) -naccept 1 > /shared/inbox.http'
	@timeout 8 bash -lc 'until ss -ltn 2>/dev/null | grep -q "LISTEN .*:$(PORT) "; do sleep 0.2; done'
	$(MAKE) PORT=$(PORT) tls-post-bundle
	$(MAKE) extract-body
	$(MAKE) verify-inbox
	-@docker logs oqs_www --tail 50 || true
	-@docker rm -f oqs_www >/dev/null 2>&1 || true
