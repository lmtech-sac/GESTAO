#!/usr/bin/env bash
set -Eeuo pipefail

export PYTHONUNBUFFERED=1

echo "[LM TECH] Python: $(python --version 2>&1)"
echo "[LM TECH] Inicializando/verificando PostgreSQL..."
python init_db.py

echo "[LM TECH] Banco pronto. Iniciando Gunicorn em 0.0.0.0:${PORT:-10000}..."
exec gunicorn app:app \
  --bind "0.0.0.0:${PORT:-10000}" \
  --workers "${WEB_CONCURRENCY:-1}" \
  --threads "${GUNICORN_THREADS:-4}" \
  --timeout "${GUNICORN_TIMEOUT:-120}" \
  --keep-alive 5 \
  --access-logfile - \
  --error-logfile - \
  --capture-output
