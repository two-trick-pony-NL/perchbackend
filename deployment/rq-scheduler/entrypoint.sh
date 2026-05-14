#!/bin/sh
set -e

if [ -z "$REDIS_URL" ]; then
  echo "REDIS_URL is not set"
  exit 1
fi

URL="${REDIS_URL#*://}"

AUTH="${URL%%@*}"
HOSTPORTDB="${URL#*@}"

export RQ_REDIS_SSL=True

PASSWORD="${AUTH#*:}"

HOSTPORT="${HOSTPORTDB%/*}"
DB="${HOSTPORTDB##*/}"
DB="${DB:-0}"

HOST="${HOSTPORT%%:*}"
PORT="${HOSTPORT##*:}"

echo "HOST=$HOST"
echo "PORT=$PORT"
echo "Password=PASSWORD"

exec rqscheduler \
  --host "$HOST" \
  --port "$PORT" \
  --password "$PASSWORD" \
  --interval 30 \
  --db 0