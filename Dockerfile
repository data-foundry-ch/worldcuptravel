# syntax=docker/dockerfile:1

FROM node:22-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci || npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim AS runtime
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*
RUN useradd -m -u 10001 appuser
COPY pyproject.toml README.md LICENSE ./
COPY app ./app
COPY analytics ./analytics
COPY scripts ./scripts
COPY start.sh ./start.sh
COPY data/bootstrap/worldcup.duckdb ./data/bootstrap/worldcup.duckdb
RUN pip install --no-cache-dir . "truststore>=0.10" "dbt-core>=1.8" "dbt-duckdb>=1.8"
COPY --from=frontend-build /app/frontend/dist ./frontend/dist
RUN sed -i 's/\r$//' /app/start.sh && chmod +x /app/start.sh && chown -R appuser:appuser /app
USER appuser
ENV APP_ENV=production
ENV PORT=10000
ENV DUCKDB_PATH=/tmp/worldcup.duckdb
ENV DUCKDB_BASELINE_PATH=/app/data/bootstrap/worldcup.duckdb
ENV REFRESH_DATA_ON_START=false
EXPOSE 10000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/healthz' % __import__('os').environ.get('PORT','10000'))"
ENTRYPOINT ["/app/start.sh"]
