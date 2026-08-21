#!/usr/bin/env bash
set -euo pipefail

echo "[LM TECH] Inicializando banco..."
python init_db.py

echo "[LM TECH] Iniciando Gunicorn na porta ${PORT:-10000}..."
exec gunicorn app:app \
  --bind "0.0.0.0:${PORT:-10000}" \
  --workers "${WEB_CONCURRENCY:-1}" \
  --threads "${GUNICORN_THREADS:-4}" \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
