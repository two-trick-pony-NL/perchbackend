from datetime import datetime, timezone
import json
from django.db import transaction

from core.settings import redis_host
from ingestion.models import GPSBatch

STREAM_KEY = "gps:stream"
GROUP = "gps-batch-group"
CONSUMER = "batch-worker-1"

r = redis_host


# ---------------------------------------------------------
# SETUP STREAM GROUP
# ---------------------------------------------------------

def ensure_group():
    try:
        r.xgroup_create(STREAM_KEY, GROUP, id="0", mkstream=True)
    except Exception:
        pass


# ---------------------------------------------------------
# NORMALIZE REDIS STREAM ENTRY
# ---------------------------------------------------------

def normalize(data):
    return {
        (k.decode() if isinstance(k, bytes) else k):
        (v.decode() if isinstance(v, bytes) else v)
        for k, v in data.items()
    }


# ---------------------------------------------------------
# PARSE STREAM ENTRY → PYTHON OBJECT
# ---------------------------------------------------------

def _parse(entry):
    try:
        def get(k):
            v = entry.get(k)
            return None if v in ("", "null", None) else v

        def f(k):
            v = get(k)
            return float(v) if v is not None else None

        return {
            "lat": float(get("lat")),
            "lon": float(get("lon")),
            "timestamp": datetime.fromisoformat(
                get("timestamp").replace("Z", "+00:00")
            ),

            "accuracy": f("accuracy"),
            "speed": f("speed"),
            "heading": f("heading"),
            "altitude": f("altitude"),
            "altitude_accuracy": f("altitude_accuracy"),
        }

    except Exception as e:
        print("❌ parse error:", entry, e)
        return None


# ---------------------------------------------------------
# SERIALIZE FOR REDIS (IMPORTANT FIX)
# ---------------------------------------------------------

def serialize_point(p):
    return {
        "lat": p["lat"],
        "lon": p["lon"],
        "timestamp": p["timestamp"].isoformat(),

        "accuracy": p["accuracy"],
        "speed": p["speed"],
        "heading": p["heading"],
        "altitude": p["altitude"],
        "altitude_accuracy": p["altitude_accuracy"],
    }


# ---------------------------------------------------------
# REDIS BUFFER KEYS
# ---------------------------------------------------------

def _buf_key(uid): return f"gps:buffer:{uid}"
def _flush_key(uid): return f"gps:buffer:last_flush:{uid}"


# ---------------------------------------------------------
# REDIS BUFFER OPS
# ---------------------------------------------------------

def add_to_buffer(uid, point):
    # FIX: ensure JSON-safe BEFORE storing
    r.rpush(_buf_key(uid), json.dumps(serialize_point(point)))


def get_buffer(uid):
    raw = r.lrange(_buf_key(uid), 0, -1)
    return [json.loads(x) for x in raw]


def clear_buffer(uid):
    r.delete(_buf_key(uid))


def get_last_flush(uid):
    v = r.get(_flush_key(uid))
    if not v:
        return None
    return datetime.fromisoformat(v)


def set_last_flush(uid):
    r.set(_flush_key(uid), datetime.now(timezone.utc).isoformat())


# ---------------------------------------------------------
# FLUSH TO DB
# ---------------------------------------------------------

def flush_user(uid, points):
    if not points:
        return

    # ensure correct ordering
    points.sort(key=lambda x: x["timestamp"])

    batch = GPSBatch(
        user_id=uid,
        start_time=points[0]["timestamp"],
        end_time=points[-1]["timestamp"],
        points=points,
        point_count=len(points),
    )

    with transaction.atomic():
        batch.save()
        print("💾 Saved batch:", batch.id)


# ---------------------------------------------------------
# MAIN LOOP
# ---------------------------------------------------------

def run():
    ensure_group()
    print("🚀 Redis-buffered GPS batch ingestor started")

    FLUSH_SIZE = 100
    FLUSH_SECONDS = 60

    while True:
        resp = r.xreadgroup(
            GROUP,
            CONSUMER,
            {STREAM_KEY: ">"},
            count=50,
            block=5000,
        )

        if not resp:
            continue

        for _, messages in resp:
            for msg_id, data in messages:

                try:
                    entry = normalize(data)
                    point = _parse(entry)

                    if not point:
                        r.xack(STREAM_KEY, GROUP, msg_id)
                        continue

                    user_id = int(entry["user_id"])

                    add_to_buffer(user_id, point)

                    buffer = get_buffer(user_id)
                    last_flush = get_last_flush(user_id)

                    now = datetime.now(timezone.utc)

                    should_flush = (
                        len(buffer) >= FLUSH_SIZE
                        or last_flush is None
                        or (now - last_flush).total_seconds() > FLUSH_SECONDS
                    )

                    if should_flush:
                        flush_user(user_id, buffer)
                        clear_buffer(user_id)
                        set_last_flush(user_id)

                    r.xack(STREAM_KEY, GROUP, msg_id)

                except Exception as e:
                    print("🔥 worker error:", e)
                    r.xack(STREAM_KEY, GROUP, msg_id)