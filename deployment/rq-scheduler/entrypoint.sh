#!/bin/sh
set -e

if [ -z "$REDIS_URL" ]; then
  echo "REDIS_URL is not set"
  exit 1
fi

# remove scheme
URL="${REDIS_URL#*://}"

# split auth and host
AUTH="${URL%%@*}"
HOSTPORTDB="${URL#*@}"

PASSWORD="${AUTH#*:}"

HOST="${HOSTPORTDB%%:*}"
PORT_DB="${HOSTPORTDB#*:}"

PORT="${PORT_DB%%/*}"
DB="${PORT_DB#*/}"
DB="${DB:-0}"

exec rqscheduler \
  --host "$HOST" \
  --port "$PORT" \
  --db "$DB" \
  --password "$PASSWORD" \
  --interval 30