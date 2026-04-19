from core.settings import redis_host

STREAM_KEY = "gps:stream"
r = redis_host


def _to_str(v):
    if v is None:
        return ""
    if hasattr(v, "isoformat"):
        return v.isoformat()
    return str(v)


def publish_gps_batch(user_id: int, locations: list[dict]):
    for loc in locations:
        entry = {
            # core identity
            "user_id": str(user_id),
            "timestamp": _to_str(loc.get("timestamp")),

            # core geo
            "lat": _to_str(loc.get("lat")),
            "lon": _to_str(loc.get("lon")),

            # sensor signals (IMPORTANT — previously lost)
            "accuracy": _to_str(loc.get("accuracy")),
            "speed": _to_str(loc.get("speed")),
            "heading": _to_str(loc.get("heading")),
            "altitude": _to_str(loc.get("altitude")),
            "altitude_accuracy": _to_str(loc.get("altitude_accuracy")),
        }

        try:
            r.xadd(STREAM_KEY, entry)
        except Exception as e:
            print("🔥 XADD FAILED:", e)
            raise