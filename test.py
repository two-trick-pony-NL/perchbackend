import random
import time
import requests
import math
from datetime import datetime, timedelta

URL = "http://localhost:8000/api/v1/ingestion/ingest/"

# ---------------------------------------------------------
# USERS (PASTE YOUR TOKENS HERE)
# ---------------------------------------------------------
USERS = [
    {
        "user_id": 1,
        "username": "pvandoorn",
        "token": "1e886a6d7c97cbfd156e710583b475937017cdc9",
        "lat": 52.3702,
        "lon": 4.8952,
    },
    {
        "user_id": 2,
        "username": "test2",
        "token": "6cc90f6f4c4c0e601fa3e7d51a6611507ab63181",
        "lat": 52.3676,
        "lon": 4.9041,
    },
    {
        "user_id": 3,
        "username": "test3",
        "token": "0f7a483bcbfdcb15013ec48844d7dbf9864e1625",
        "lat": 52.3791,
        "lon": 4.9000,
    },
]


# ---------------------------------------------------------
# CORE HELPERS
# ---------------------------------------------------------
def generate_point(user_id, lat, lon, t):
    return {
        "user_id": user_id,
        "lat": lat,
        "lon": lon,
        "timestamp": t.isoformat(),
    }


def send_points(points, token):
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json",
    }

    try:
        r = requests.post(
            URL,
            json={"locations": points},
            headers=headers,
            timeout=10,
        )
        print("SEND:", r.status_code)
    except Exception as e:
        print("send failed:", e)


# ---------------------------------------------------------
# MOTION MODELS
# ---------------------------------------------------------
def stationary(lat, lon):
    # mostly identical points (REAL STOP)
    if random.random() < 0.9:
        return lat, lon

    return (
        lat + random.uniform(-0.00001, 0.00001),
        lon + random.uniform(-0.00001, 0.00001),
    )


def walking(lat, lon):
    step = random.uniform(0.00005, 0.0002)
    angle = random.uniform(0, 2 * math.pi)

    lat += step * math.cos(angle)
    lon += step * math.sin(angle)

    lat += random.uniform(-0.00003, 0.00003)
    lon += random.uniform(-0.00003, 0.00003)

    return lat, lon


def driving(lat, lon, target_lat, target_lon, steps):
    for _ in range(steps):
        lat += (target_lat - lat) / steps
        lon += (target_lon - lon) / steps

        lat += random.uniform(-0.00005, 0.00005)
        lon += random.uniform(-0.00005, 0.00005)

        yield lat, lon


# ---------------------------------------------------------
# STREAMING (PER USER TOKEN)
# ---------------------------------------------------------
def stream(all_points, batch_size=25):
    buffers = {u["user_id"]: [] for u in USERS}
    token_map = {u["user_id"]: u["token"] for u in USERS}

    for p in all_points:
        uid = p["user_id"]
        buffers[uid].append(p)

        if len(buffers[uid]) >= batch_size:
            send_points(buffers[uid], token_map[uid])
            buffers[uid] = []

        time.sleep(0.02)

    for uid, buf in buffers.items():
        if buf:
            send_points(buf, token_map[uid])


# ---------------------------------------------------------
# SINGLE USER DAY SIMULATION
# ---------------------------------------------------------
def run_full_day(user):
    t = datetime.utcnow()
    points = []

    uid = user["user_id"]
    lat, lon = user["lat"], user["lon"]

    # ---------------- HOME STOP ----------------
    for _ in range(180):
        lat, lon = stationary(lat, lon)
        points.append(generate_point(uid, lat, lon, t))
        t += timedelta(seconds=30)

    # ---------------- COMMUTE ----------------
    for lat, lon in driving(lat, lon, 52.3791, 4.9000, 80):
        points.append(generate_point(uid, lat, lon, t))
        t += timedelta(seconds=30)

    # traffic stop
    for _ in range(10):
        lat, lon = stationary(lat, lon)
        points.append(generate_point(uid, lat, lon, t))
        t += timedelta(seconds=30)

    # ---------------- WORK STOP ----------------
    lat, lon = 52.3791, 4.9000

    for _ in range(360):
        lat, lon = stationary(lat, lon)
        points.append(generate_point(uid, lat, lon, t))
        t += timedelta(seconds=30)

    # ---------------- LUNCH WALK ----------------
    for lat, lon in driving(lat, lon, 52.3780, 4.9100, 30):
        points.append(generate_point(uid, lat, lon, t))
        t += timedelta(seconds=30)

    # ---------------- LUNCH STOP ----------------
    for _ in range(90):
        lat, lon = stationary(lat, lon)
        points.append(generate_point(uid, lat, lon, t))
        t += timedelta(seconds=30)

    # ---------------- RETURN ----------------
    for lat, lon in driving(lat, lon, 52.3702, 4.8952, 100):
        points.append(generate_point(uid, lat, lon, t))
        t += timedelta(seconds=25)

    # ---------------- EVENING STOP ----------------
    for _ in range(240):
        lat, lon = stationary(lat, lon)
        points.append(generate_point(uid, lat, lon, t))
        t += timedelta(seconds=30)

    return points


# ---------------------------------------------------------
# MULTI USER SCENARIO
# ---------------------------------------------------------
def run_multi_user():
    all_points = []
    base_time = datetime.utcnow()

    for user in USERS:
        t = base_time
        lat, lon = user["lat"], user["lon"]

        for _ in range(600):
            if random.random() < 0.75:
                lat, lon = stationary(lat, lon)
            else:
                lat, lon = walking(lat, lon)

            all_points.append(generate_point(user["user_id"], lat, lon, t))
            t += timedelta(seconds=30)

    random.shuffle(all_points)
    stream(all_points)


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
if __name__ == "__main__":
    print("Running FULL DAY (user 1)")
    points = run_full_day(USERS[0])

    print("Streaming FULL DAY")
    stream(points)

    print("Running MULTI USER")
    run_multi_user()