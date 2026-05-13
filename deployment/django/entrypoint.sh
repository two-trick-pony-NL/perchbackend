#!/bin/sh
set -e

uv run python manage.py migrate --noinput
uv run python manage.py schedule_jobs
exec uv run gunicorn core.wsgi:application --bind 0.0.0.0:8000