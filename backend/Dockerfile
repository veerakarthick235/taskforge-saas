# ─────────────────────────────────────────────
#  TaskForge Backend — Production Dockerfile
#  Multi-stage build for minimal image size
# ─────────────────────────────────────────────

# Stage 1: Build dependencies
FROM python:3.12-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Production image
FROM python:3.12-slim AS production

# Security: run as non-root
RUN groupadd -r taskforge && useradd -r -g taskforge -d /app -s /sbin/nologin taskforge

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY app/ ./app/

# Ownership
RUN chown -R taskforge:taskforge /app

USER taskforge

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Gunicorn with Uvicorn workers (production ASGI server)
# Workers = (2 * CPU cores) + 1 — adjust via GUNICORN_WORKERS env var
ENV GUNICORN_WORKERS=4
ENV GUNICORN_TIMEOUT=120

EXPOSE 8000

CMD ["sh", "-c", "gunicorn app.main:app -w ${GUNICORN_WORKERS} -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 --timeout ${GUNICORN_TIMEOUT} --access-logfile - --error-logfile -"]
