# syntax=docker/dockerfile:1

FROM debian:12-slim AS builder

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates git cmake ninja-build gfortran gcc g++ make \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src
COPY . /src

RUN cmake -S /src -B /build -G Ninja \
      -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_INSTALL_PREFIX=/opt/dssat \
    && cmake --build /build --parallel

RUN git clone --depth 1 https://github.com/DSSAT/dssat-csm-data.git /tmp/dssat-csm-data \
    && mkdir -p /opt/dssat \
    && cp -a /tmp/dssat-csm-data/. /opt/dssat/ \
    && cp -a /src/Data/. /opt/dssat/ \
    && cp /build/bin/dscsm048 /opt/dssat/dscsm048 \
    && chmod +x /opt/dssat/dscsm048 \
    && if [ -f /src/Data/DSSATPRO.L48 ]; then cp /src/Data/DSSATPRO.L48 /opt/dssat/DSSATPRO.L48; fi

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DSSAT_ROOT=/opt/dssat \
    DSSAT_EXE=/opt/dssat/dscsm048 \
    DSSAT_RUNS=/app/runs \
    HOST=0.0.0.0 \
    PORT=8765

WORKDIR /app

COPY --from=builder /opt/dssat /opt/dssat
COPY services /app/services
COPY docs /app/docs

RUN mkdir -p /app/runs \
    && useradd -r -u 10001 dssat \
    && chown -R dssat:dssat /app/runs /opt/dssat

USER dssat
EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/health', timeout=3).read()"

CMD ["python", "-m", "services.dssat_api"]
