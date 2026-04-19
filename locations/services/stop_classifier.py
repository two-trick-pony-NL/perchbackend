import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from shapely.ops import unary_union
import movingpandas as mpd
import h3

from django.db import transaction
from locations.models import LocationEvent, TransitEvent


# ---------------------------------------------------------
# CONFIG
# ---------------------------------------------------------

STOP_RADIUS_M = 50
MIN_STOP_DURATION = "2min"
H3_RESOLUTION = 11

INTERPOLATION_INTERVAL = pd.Timedelta("30s")
STATIONARY_THRESHOLD_M = 100


# ---------------------------------------------------------
# BUILD TRAJECTORY GDF
# ---------------------------------------------------------

def build_gdf(points):
    rows = [
    {
        "lat": p["lat"],
        "lon": p["lon"],
        "timestamp": pd.to_datetime(p["timestamp"], utc=True)
        .tz_convert("UTC")
        .tz_localize(None),        "accuracy": p.get("accuracy", 50),
    }
    for p in points
]

    df = pd.DataFrame(rows)
    df = df.dropna(subset=["timestamp", "lat", "lon"])
    df = df.sort_values("timestamp")
    df = df.drop_duplicates(subset=["timestamp"], keep="last")
    df = df.set_index("timestamp")

    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["lon"], df["lat"]),
        crs="EPSG:4326",
    )

    gdf = gdf.to_crs(epsg=3857)
    gdf = interpolate_stationary_gaps(gdf)

    return gdf


# ---------------------------------------------------------
# INTERPOLATION
# ---------------------------------------------------------

def interpolate_stationary_gaps(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    For consecutive pings where displacement < STATIONARY_THRESHOLD_M,
    fill the gap with synthetic points at INTERPOLATION_INTERVAL.

    No upper bound on gap duration — a user stationary for days
    produces one long stop, which is correct.
    """
    if len(gdf) < 2:
        return gdf

    synthetic_rows = []
    coords = list(zip(gdf.index, gdf.geometry))

    for (t0, geom0), (t1, geom1) in zip(coords, coords[1:]):
        gap = t1 - t0
        displacement_m = geom0.distance(geom1)

        if displacement_m < STATIONARY_THRESHOLD_M and gap > INTERPOLATION_INTERVAL:
            synthetic_time = t0 + INTERPOLATION_INTERVAL
            while synthetic_time < t1:
                synthetic_rows.append({
                    "timestamp": synthetic_time,
                    "geometry": geom0,
                    "accuracy": gdf.loc[t0, "accuracy"] if "accuracy" in gdf.columns else 50,
                    "synthetic": True,
                })
                synthetic_time += INTERPOLATION_INTERVAL

    if not synthetic_rows:
        return gdf

    gdf = gdf.copy()
    gdf["synthetic"] = False

    synth_df = pd.DataFrame(synthetic_rows).set_index("timestamp")
    synth_gdf = gpd.GeoDataFrame(synth_df, geometry="geometry", crs=gdf.crs)

    combined = pd.concat([gdf, synth_gdf])
    combined = combined.sort_index()
    combined = combined[~combined.index.duplicated(keep="first")]

    return combined


# ---------------------------------------------------------
# STOP DETECTION
# ---------------------------------------------------------

def detect_stops(gdf):
    traj = mpd.Trajectory(gdf, traj_id="user_traj")
    detector = mpd.TrajectoryStopDetector(traj)
    stops = detector.get_stop_segments(
        max_diameter=STOP_RADIUS_M,
        min_duration=pd.Timedelta(MIN_STOP_DURATION),
    )
    return stops, traj


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

def to_h3(lat, lon, res=H3_RESOLUTION):
    return h3.latlng_to_cell(lat, lon, res)


def get_center(segment):
    """
    Return (lat, lon) centroid of a stop segment.
    Segment geometry is in EPSG:3857 — reproject to 4326 first.
    """
    gdf = gpd.GeoDataFrame(segment.df.copy(), geometry="geometry", crs="EPSG:3857")
    gdf_wgs = gdf.to_crs(epsg=4326)
    centroid = unary_union(gdf_wgs.geometry).centroid
    return centroid.y, centroid.x  # lat, lon


# ---------------------------------------------------------
# STOP EVENT CREATION (with deduplication)
# ---------------------------------------------------------

def create_stop_event(user_id, segment):
    df = segment.df
    start_time = df.index.min()
    end_time = df.index.max()
    lat, lon = get_center(segment)

    # Deduplicate: skip if a stop already exists in this time window
    overlap = LocationEvent.objects.filter(
        user_id=user_id,
        event_type=LocationEvent.Type.STOP,
        start_time__lt=end_time,
        end_time__gt=start_time,
    ).exists()

    if overlap:
        return None

    return LocationEvent.objects.create(
        user_id=user_id,
        event_type=LocationEvent.Type.STOP,
        start_time=start_time,
        end_time=end_time,
        duration_seconds=int((end_time - start_time).total_seconds()),
        h3=to_h3(lat, lon),
        center_lat=lat,
        center_lon=lon,
        confidence=0.9,
        avg_accuracy_m=df["accuracy"].mean() if "accuracy" in df.columns else None,
        radius_m=STOP_RADIUS_M,
        features={"point_count": len(df)},
    )


# ---------------------------------------------------------
# TRANSIT CREATION (with deduplication)
# ---------------------------------------------------------

def create_transits(user_id, events):
    events = sorted(events, key=lambda e: e.start_time)

    for a, b in zip(events, events[1:]):
        exists = TransitEvent.objects.filter(
            user_id=user_id,
            start_event=a,
            end_event=b,
        ).exists()

        if exists:
            continue

        TransitEvent.objects.create(
            user_id=user_id,
            start_event=a,
            end_event=b,
            start_h3=a.h3,
            end_h3=b.h3,
            start_time=a.end_time,
            end_time=b.start_time,
            duration_seconds=max(int((b.start_time - a.end_time).total_seconds()), 0),
            distance_meters=0,
            speed_mps=0,
            metadata={},
        )


# ---------------------------------------------------------
# PIPELINE
# ---------------------------------------------------------

def process_trajectory(user_id, points):
    gdf = build_gdf(points)

    if len(gdf) < 10:
        print(f"⚠️  Too few points ({len(gdf)}), skipping.")
        return

    stops, traj = detect_stops(gdf)

    print(f"📦 GDF points : {len(gdf)}")
    print(f"🧭 Traj points: {len(traj.df)}")
    print(f"🛑 Stops found: {len(stops)}")

    if not stops:
        return

    created_events = []

    with transaction.atomic():
        for segment in stops:
            event = create_stop_event(user_id, segment)
            if event:
                created_events.append(event)

        if len(created_events) > 1:
            create_transits(user_id, created_events)

    print(f"✅ Created {len(created_events)} stop(s)")