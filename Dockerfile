# Multi-stage build → small, non-root, health-checked image (production hygiene).

# --- builder: install deps into an isolated venv -------------------------------
FROM python:3.12-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- runtime: copy only the venv + app, run as non-root ------------------------
FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH="/opt/venv/bin:$PATH" \
    CHROMA_PATH=/data/chroma
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY app ./app
COPY eval ./eval

# Non-root user; /data is the writable volume for the persistent vector index.
RUN useradd --create-home appuser \
    && mkdir -p /data/chroma && chown -R appuser /app /data
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health').status==200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
