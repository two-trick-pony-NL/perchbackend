#!/bin/sh
set -e

# default fallback
HOST="localhost"
PORT="6379"
DB="0"

if [ -n "$REDIS_URL" ]; then
  # supports redis://host:port/db
  # example: redis://redis:6379/0
  HOST=$(echo "$REDIS_URL" | sed -E 's#redis://([^:/]+):[0-9]+/.*#\1#')
  PORT=$(echo "$REDIS_URL" | sed -E 's#redis://[^:/]+:([0-9]+)/.*#\1#')
  DB=$(echo "$REDIS_URL" | sed -E 's#redis://[^:/]+:[0-9]+/([0-9]+)#\1#')
fi

exec rqscheduler --host "$HOST" --port "$PORT" --db "$DB" --interval 30