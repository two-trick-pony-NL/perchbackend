#!/bin/sh
set -e

if [ -z "$REDIS_URL" ]; then
  echo "REDIS_URL is not set"
  exit 1
fi

# strip scheme (redis:// or rediss://)
URL="${REDIS_URL#*://}"

# extract password and host part
AUTH="${URL%%@*}"
HOSTPORTDB="${URL#*@}"

PASSWORD="${AUTH#*:}"

# split host:port/db safely
HOSTPORT="${HOSTPORTDB%/*}"
DB="${HOSTPORTDB##*/}"
DB="${DB:-0}"

HOST="${HOSTPORT%%:*}"
PORT="${HOSTPORT##*:}"

exec rqscheduler \
  --host "$HOST" \
  --port "$PORT" \
  --db "$DB" \
  --password "$PASSWORD" \
  --interval 30