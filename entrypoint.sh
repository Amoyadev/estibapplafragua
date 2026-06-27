#!/bin/sh
# ===== Estiba — entrypoint =====
set -e

echo "[entrypoint] Esperando a la base de datos..."
python manage.py wait_for_db

echo "[entrypoint] Aplicando migraciones..."
python manage.py migrate --noinput

echo "[entrypoint] Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

WORKERS="${GUNICORN_WORKERS:-3}"
echo "[entrypoint] Iniciando Gunicorn con ${WORKERS} workers..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${WORKERS}" \
    --access-logfile - \
    --error-logfile -
