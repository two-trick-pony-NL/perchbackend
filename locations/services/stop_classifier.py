import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import movingpandas as mpd
import h3

from django.db import transaction

from locations.models import LocationEvent, TransitEvent
from ingestion.models import GPSBatch


STOP_RADIUS_M = 50
MIN_STOP_DURATION = "5min"


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

def build_gdf(points):
    rows = []

    for p in points:
        rows.append({
            "geometry": Point(p["lon"], p["lat"]),
            "timestamp": pd.to_datetime(p["timestamp"], utc=True),
            "accuracy": p.get("accuracy", 0),
        })

    gdf = gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326")
    gdf = gdf.sort_values("timestamp")
    return gdf


def detect_stops(gdf):
    traj = mpd.Trajectory(gdf, obj_id=1, t="timestamp")

    detector = mpd.TrajectoryStopDetector(
        traj,
        max_diameter=STOP_RADIUS_M,
        min_duration=pd.Timedelta(MIN_STOP_DURATION),
    )

    return detector.get_stop_segments()


def to_h3(lat, lon, res=11):
    return h3.geo_to_h3(lat, lon, res)


def get_center(segment):
    c = segment.get_center()
    return c.y, c.x


# ---------------------------------------------------------
# EVENT CREATION
# ---------------------------------------------------------

def create_stop_event(user, segment):
    df = segment.df

    start_time = df["timestamp"].min()
    end_time = df["timestamp"].max()

    lat, lon = get_center(segment)

    return LocationEvent.objects.create(
        user=user,
        event_type=LocationEvent.Type.STOP,
        status=LocationEvent.Status.CONFIRMED,
        start_time=start_time,
        end_time=end_time,
        duration_seconds=int((end_time - start_time).total_seconds()),
        h3=to_h3(lat, lon, 11),
        confidence=0.9,
        avg_accuracy_m=df["accuracy"].mean() if "accuracy" in df else None,
        metadata={
            "center_lat": lat,
            "center_lon": lon,
        },
    )


def create_transits(user, events):
    events = sorted(events, key=lambda e: e.start_time)

    for i in range(len(events) - 1):
        a = events[i]
        b = events[i + 1]

        TransitEvent.objects.create(
            user=user,
            start_event=a,
            end_event=b,
            start_h3=a.h3,
            end_h3=b.h3,
            start_time=a.end_time,
            end_time=b.start_time,
            duration_seconds=int((b.start_time - a.end_time).total_seconds()),
            distance_meters=0,
            speed_mps=0,
            metadata={},
        )


# ---------------------------------------------------------
# MAIN PIPELINE
# ---------------------------------------------------------

def process_batch(batch: GPSBatch):
    try:
        if not batch.points:
            batch.status = GPSBatch.Status.DONE
            batch.save()
            return

        gdf = build_gdf(batch.points)

        stop_segments = detect_stops(gdf)

        created_events = []

        with transaction.atomic():
            # 1. Create STOP events
            for segment in stop_segments:
                event = create_stop_event(batch.user, segment)
                created_events.append(event)

            # 2. Create transits between stops
            if len(created_events) > 1:
                create_transits(batch.user, created_events)

            # 3. finalize batch
            batch.status = GPSBatch.Status.DONE
            batch.save()

    except Exception as e:
        batch.status = GPSBatch.Status.FAILED
        batch.last_error = str(e)
        batch.attempts += 1
        batch.save()

        raise