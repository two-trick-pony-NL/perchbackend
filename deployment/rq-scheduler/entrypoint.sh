#!/bin/sh
set -e

# default fallback
HOST="localhost"
PORT="6379"
DB="0"

exec rqscheduler --host "$REDIS_URL"  --interval 30