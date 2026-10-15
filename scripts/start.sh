#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "Running migrations..."
python manage.py migrate --noinput

echo "Seeding RBAC defaults..."
python manage.py seed_rbac

echo "Collecting static files..."
python manage.py collectstatic --noinput

PORT="${PORT:-8080}"
WORKERS="${WEB_CONCURRENCY:-2}"

echo "Starting Gunicorn on 0.0.0.0:${PORT} (${WORKERS} workers)..."
exec gunicorn config.wsgi:application \
  --bind "0.0.0.0:${PORT}" \
  --workers "${WORKERS}" \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
