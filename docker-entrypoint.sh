#!/bin/sh
set -eu
python manage.py migrate --noinput
export GUNICORN_CMD_ARGS="--workers ${GUNICORN_WORKERS:-2} --timeout 30 ${GUNICORN_CMD_ARGS:-}"
exec "$@"
