#!/bin/sh
# Arranque del backend en Render (o en local con: sh start.sh)
set -e
python manage.py migrate --noinput
python manage.py ensure_admin
python manage.py purge_old_conversations
python manage.py setup_telegram || true
python manage.py check_config
exec uvicorn core.asgi:application --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips="*"
