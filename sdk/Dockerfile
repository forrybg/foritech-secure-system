  GNU nano 7.2                              /home/forybg/foritech-secure-system/sdk/Dockerfile
FROM python:3.12-slim AS base
ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 LC_ALL=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl git build-essential cmake ninja-build libssl-dev \
 && rm -rf /var/lib/apt/lists/*

# ---- Build & install liboqs ----
WORKDIR /opt
RUN git clone --depth=1 https://github.com/open-quantum-safe/liboqs.git \
 && mkdir -p liboqs/build && cd liboqs/build \
 && cmake -GNinja -DCMAKE_INSTALL_PREFIX=/usr/local -DOQS_USE_OPENSSL=OFF .. \
 && ninja && ninja install \
 && ldconfig

# ---- Build & install liboqs-python (module 'oqs') ----
RUN git clone --depth=1 https://github.com/open-quantum-safe/liboqs-python.git \
 && cd liboqs-python \
 && pip install --no-cache-dir -U pip wheel setuptools \
 && python -m pip install .

# ---- Install our SDK (editable) and run tests ----
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -e .[dev] \
 && pytest -q

ENTRYPOINT ["foritech"]
CMD ["--help"]

