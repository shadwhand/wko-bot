# wko5/routes.py
"""Route storage, GPS similarity matching, and activity linking."""

import json
import logging
import os
import re

import numpy as np

from wko5.db import get_connection

logger = logging.getLogger(__name__)

# Try to use Rust extension for Frechet distance (~158x faster)
try:
    import frechet_rs as _rust
    _USE_RUST = True
    logger.info("Using Rust frechet_rs extension")
except ImportError:
    _USE_RUST = False
    logger.info("Rust frechet_rs not available, using Python fallback")

SEMICIRCLE_TO_DEG = 180.0 / (2 ** 31)
EARTH_RADIUS_M = 6371000

ROUTES_DDL = """
CREATE TABLE IF NOT EXISTS routes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    source_file TEXT,
    total_distance_m REAL,
    total_elevation_m REAL,
    point_count INTEGER,
    bbox_lat_min REAL, bbox_lat_max REAL,
    bbox_lon_min REAL, bbox_lon_max REAL,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS route_points (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    route_id INTEGER NOT NULL,
    point_order INTEGER NOT NULL,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    elevation REAL,
    cumulative_distance_m REAL,
    FOREIGN KEY (route_id) REFERENCES routes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ride_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    route_id INTEGER NOT NULL,
    name TEXT,
    target_riding_hours REAL,
    rest_hours REAL DEFAULT 0,
    cda REAL,
    drafting_pct REAL DEFAULT 0,
    drafting_savings REAL DEFAULT 0.30,
    baseline_intake_g_hr REAL,
    starting_glycogen_g REAL,
    result_json TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (route_id) REFERENCES routes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS activity_routes (
    activity_id INTEGER NOT NULL,
    route_id INTEGER NOT NULL,
    frechet_distance_m REAL,
    match_confidence REAL,
    PRIMARY KEY (activity_id, route_id),
    FOREIGN KEY (activity_id) REFERENCES activities(id),
    FOREIGN KEY (route_id) REFERENCES routes(id) ON DELETE CASCADE
);
"""


def _ensure_tables(conn):
    """Create route tables if they don't exist."""
    conn.executescript(ROUTES_DDL)


def semicircles_to_degrees(semicircles):
    """Convert Garmin semicircle coordinates to decimal degrees."""
    return semicircles * SEMICIRCLE_TO_DEG


def _haversine(lat1, lon1, lat2, lon2):
    """Haversine distance in meters between two points (decimal degrees)."""
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dlat / 2) ** 2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon / 2) ** 2
    return EARTH_RADIUS_M * 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))


def _derive_name(gpx_path):
    """Derive a route name from a GPX filename."""
    basename = os.path.splitext(os.path.basename(gpx_path))[0]
    # Remove trailing numbers/IDs (e.g., __3090)
    name = re.sub(r'_+\d+$', '', basename)
    # Replace underscores with spaces
    name = name.replace('_', ' ').replace('-', '-').strip()
    return name


def downsample_track(lats, lons, target_spacing_m=1000):
    """Downsample a GPS track to approximately target_spacing_m between points.

    Args:
        lats: array of latitudes (decimal degrees)
        lons: array of longitudes (decimal degrees)
        target_spacing_m: target distance between points

    Returns: list of (lat, lon, cumulative_distance_m) tuples
    """
    result = [(float(lats[0]), float(lons[0]), 0.0)]
    cum_dist = 0.0
    last_dist = 0.0

    for i in range(1, len(lats)):
        d = _haversine(lats[i - 1], lons[i - 1], lats[i], lons[i])
        cum_dist += d

        if cum_dist - last_dist >= target_spacing_m:
            result.append((float(lats[i]), float(lons[i]), cum_dist))
            last_dist = cum_dist

    # Always include the last point
    if cum_dist - last_dist > target_spacing_m * 0.1:
        result.append((float(lats[-1]), float(lons[-1]), cum_dist))

    return result


def _parse_gpx_points(gpx_path):
    """Parse a GPX file and return (lats, lons, elevations, cumulative_distances)."""
    import defusedxml.ElementTree as ET

    tree = ET.parse(gpx_path)
    root = tree.getroot()

    lats, lons, elevations = [], [], []
    cum_dist = 0.0
    distances = [0.0]

    for trkpt in root.iter("{http://www.topografix.com/GPX/1/1}trkpt"):
        lat = float(trkpt.get("lat"))
        lon = float(trkpt.get("lon"))
        ele_elem = trkpt.find("{http://www.topografix.com/GPX/1/1}ele")
        ele = float(ele_elem.text) if ele_elem is not None else 0

        if lats:
            cum_dist += _haversine(lats[-1], lons[-1], lat, lon)
            distances.append(cum_dist)

        lats.append(lat)
        lons.append(lon)
        elevations.append(ele)

    return np.array(lats), np.array(lons), np.array(elevations), np.array(distances)


def save_route(gpx_path, name=None):
    """Save a GPX route to the database.

    Args:
        gpx_path: path to GPX file
        name: route name (derived from filename if not given)

    Returns: route_id
    """
    if name is None:
        name = _derive_name(gpx_path)

    lats, lons, elevations, distances = _parse_gpx_points(gpx_path)

    if len(lats) == 0:
        raise ValueError("GPX file has no trackpoints")

    total_distance = float(distances[-1])
    total_elevation = float(np.sum(np.maximum(0, np.diff(elevations))))

    # Downsample to ~1km for matching
    downsampled = downsample_track(lats, lons, target_spacing_m=1000)

    conn = get_connection()
    _ensure_tables(conn)

    # Insert route
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO routes (name, source_file, total_distance_m, total_elevation_m,
                           point_count, bbox_lat_min, bbox_lat_max, bbox_lon_min, bbox_lon_max)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        name, os.path.basename(gpx_path), total_distance, total_elevation,
        len(downsampled),
        float(lats.min()), float(lats.max()),
        float(lons.min()), float(lons.max()),
    ))
    route_id = cursor.lastrowid

    # Insert downsampled points
    for i, (lat, lon, cum_dist) in enumerate(downsampled):
        cursor.execute("""
            INSERT INTO route_points (route_id, point_order, lat, lon, cumulative_distance_m)
            VALUES (?, ?, ?, ?, ?)
        """, (route_id, i, lat, lon, cum_dist))

    conn.commit()
    conn.close()

    logger.info(f"Saved route '{name}': {total_distance / 1000:.0f}km, {total_elevation:.0f}m, {len(downsampled)} points")
    return route_id


def get_route(route_id):
    """Get a stored route by ID."""
    conn = get_connection()
    _ensure_tables(conn)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM routes WHERE id = ?", (route_id,))
    row = cursor.fetchone()
    if row is None:
        conn.close()
        return None

    columns = [desc[0] for desc in cursor.description]
    route = dict(zip(columns, row))
    conn.close()
    return route


def get_all_routes():
    """Get all stored routes."""
    conn = get_connection()
    _ensure_tables(conn)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM routes ORDER BY created_at DESC")
    columns = [desc[0] for desc in cursor.description]
    routes = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    return routes


def delete_route(route_id):
    """Delete a route and all associated data."""
    conn = get_connection()
    _ensure_tables(conn)
    conn.execute("DELETE FROM route_points WHERE route_id = ?", (route_id,))
    conn.execute("DELETE FROM ride_plans WHERE route_id = ?", (route_id,))
    conn.execute("DELETE FROM activity_routes WHERE route_id = ?", (route_id,))
    conn.execute("DELETE FROM routes WHERE id = ?", (route_id,))
    conn.commit()
    conn.close()


def _get_route_points(route_id, conn):
    """Get downsampled points for a route as numpy array [[lat, lon], ...]."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT lat, lon FROM route_points WHERE route_id = ? ORDER BY point_order",
        (route_id,)
    )
    points = np.array(cursor.fetchall())
    return points


def frechet_distance(track_a, track_b):
    """Compute discrete Frechet distance between two tracks in meters.

    Uses Rust extension (~158x faster) when available, falls back to Python.

    Args:
        track_a: numpy array of shape (n, 2) with [lat, lon] in degrees
        track_b: numpy array of shape (m, 2) with [lat, lon] in degrees

    Returns: Frechet distance in meters
    """
    if _USE_RUST:
        flat_a = np.asarray(track_a).flatten().tolist()
        flat_b = np.asarray(track_b).flatten().tolist()
        return _rust.frechet_distance(flat_a, flat_b)

    n = len(track_a)
    m = len(track_b)

    if n == 0 or m == 0:
        return float("inf")

    # Compute pairwise distances
    dist = np.zeros((n, m))
    for i in range(n):
        for j in range(m):
            dist[i, j] = _haversine(track_a[i, 0], track_a[i, 1],
                                     track_b[j, 0], track_b[j, 1])

    # Dynamic programming for discrete Frechet distance
    dp = np.full((n, m), -1.0)
    dp[0, 0] = dist[0, 0]

    for i in range(1, n):
        dp[i, 0] = max(dp[i - 1, 0], dist[i, 0])

    for j in range(1, m):
        dp[0, j] = max(dp[0, j - 1], dist[0, j])

    for i in range(1, n):
        for j in range(1, m):
            dp[i, j] = max(
                min(dp[i - 1, j], dp[i, j - 1], dp[i - 1, j - 1]),
                dist[i, j]
            )

    return float(dp[n - 1, m - 1])


def _get_activity_track(activity_id, conn, target_spacing_m=1000):
    """Get downsampled GPS track from an activity's records.

    Converts Garmin semicircles to degrees and downsamples.
    Returns numpy array of shape (n, 2) with [lat, lon] or None if no GPS data.
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT latitude, longitude FROM records
        WHERE activity_id = ? AND latitude IS NOT NULL AND latitude != 0
        ORDER BY rowid
    """, (activity_id,))
    rows = cursor.fetchall()

    if len(rows) < 10:
        return None

    raw_lats = np.array([r[0] for r in rows])
    raw_lons = np.array([r[1] for r in rows])

    # Detect format: semicircles (large integers like 451061695) vs degrees (small floats like 37.8)
    # Semicircles have absolute values > 1000; degrees are -180 to 180
    if np.abs(raw_lats[0]) > 1000:
        lats = raw_lats * SEMICIRCLE_TO_DEG
        lons = raw_lons * SEMICIRCLE_TO_DEG
    else:
        lats = raw_lats
        lons = raw_lons

    # Downsample
    ds = downsample_track(lats, lons, target_spacing_m=target_spacing_m)
    return np.array([(lat, lon) for lat, lon, _ in ds])


def find_similar_routes(gpx_path, threshold_m=2000):
    """Find stored routes similar to a GPX file.

    Uses bounding box pre-filter then Frechet distance.

    Returns: list of {route_id, name, frechet_distance_m, total_distance_m} sorted by distance.
    """
    lats, lons, _, _ = _parse_gpx_points(gpx_path)
    ds = downsample_track(lats, lons, target_spacing_m=1000)
    query_track = np.array([(lat, lon) for lat, lon, _ in ds])

    query_bbox = (lats.min(), lats.max(), lons.min(), lons.max())
    bbox_margin = 0.05  # ~5km in degrees

    conn = get_connection()
    _ensure_tables(conn)
    cursor = conn.cursor()

    # Bounding box pre-filter
    cursor.execute("""
        SELECT id, name, total_distance_m, bbox_lat_min, bbox_lat_max, bbox_lon_min, bbox_lon_max
        FROM routes
        WHERE bbox_lat_max >= ? AND bbox_lat_min <= ?
        AND bbox_lon_max >= ? AND bbox_lon_min <= ?
    """, (
        query_bbox[0] - bbox_margin, query_bbox[1] + bbox_margin,
        query_bbox[2] - bbox_margin, query_bbox[3] + bbox_margin,
    ))

    candidates = cursor.fetchall()
    matches = []

    for route_id, name, dist_m, *_ in candidates:
        route_track = _get_route_points(route_id, conn)
        if len(route_track) < 2:
            continue

        fd = frechet_distance(query_track, route_track)
        if fd <= threshold_m:
            matches.append({
                "route_id": route_id,
                "name": name,
                "frechet_distance_m": round(fd, 0),
                "total_distance_m": dist_m,
            })

    conn.close()
    return sorted(matches, key=lambda x: x["frechet_distance_m"])


def link_activities_to_routes(threshold_m=2000):
    """Batch: for each stored route, find matching activities and link them.

    Uses Rust extension (frechet_rs.find_matching_activities) when available
    for ~100x speedup — reads SQLite, downsamples, and computes Frechet all in Rust.

    Returns number of links created.
    """
    conn = get_connection()
    _ensure_tables(conn)
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, bbox_lat_min, bbox_lat_max, bbox_lon_min, bbox_lon_max FROM routes")
    routes = cursor.fetchall()

    total_links = 0
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cycling_power.db")

    for route_id, route_name, bbox_lat_min, bbox_lat_max, bbox_lon_min, bbox_lon_max in routes:
        route_track = _get_route_points(route_id, conn)
        if len(route_track) < 2:
            continue

        ref_flat = route_track.flatten().tolist()
        ref_bbox = (bbox_lat_min, bbox_lat_max, bbox_lon_min, bbox_lon_max)

        if _USE_RUST:
            # Rust: reads DB, downsamples, computes Frechet — all in one call (~2s for 1400 activities)
            matches = _rust.find_matching_activities(
                db_path, ref_flat, ref_bbox,
                threshold_m=threshold_m, spacing_m=1000.0,
            )
            for act_id, fd in matches:
                cursor.execute(
                    "SELECT 1 FROM activity_routes WHERE activity_id = ? AND route_id = ?",
                    (act_id, route_id)
                )
                if cursor.fetchone():
                    continue
                confidence = max(0, 1.0 - fd / threshold_m)
                conn.execute("""
                    INSERT OR REPLACE INTO activity_routes (activity_id, route_id, frechet_distance_m, match_confidence)
                    VALUES (?, ?, ?, ?)
                """, (act_id, route_id, round(fd, 0), round(confidence, 3)))
                total_links += 1
                logger.info(f"Linked activity {act_id} to route '{route_name}' (Frechet={fd:.0f}m)")
        else:
            # Python fallback: slower but works without Rust
            cursor.execute("""
                SELECT DISTINCT a.id FROM activities a
                JOIN records r ON r.activity_id = a.id
                WHERE r.latitude IS NOT NULL AND r.latitude != 0
            """)
            activity_ids = [row[0] for row in cursor.fetchall()]

            for act_id in activity_ids:
                cursor.execute(
                    "SELECT 1 FROM activity_routes WHERE activity_id = ? AND route_id = ?",
                    (act_id, route_id)
                )
                if cursor.fetchone():
                    continue

                act_track = _get_activity_track(act_id, conn)
                if act_track is None or len(act_track) < 5:
                    continue

                act_lat_min, act_lat_max = act_track[:, 0].min(), act_track[:, 0].max()
                act_lon_min, act_lon_max = act_track[:, 1].min(), act_track[:, 1].max()

                margin = 0.05
                if (act_lat_max < bbox_lat_min - margin or act_lat_min > bbox_lat_max + margin or
                        act_lon_max < bbox_lon_min - margin or act_lon_min > bbox_lon_max + margin):
                    continue

                fd = frechet_distance(route_track, act_track)
                if fd <= threshold_m:
                    confidence = max(0, 1.0 - fd / threshold_m)
                    conn.execute("""
                        INSERT OR REPLACE INTO activity_routes (activity_id, route_id, frechet_distance_m, match_confidence)
                        VALUES (?, ?, ?, ?)
                    """, (act_id, route_id, round(fd, 0), round(confidence, 3)))
                    total_links += 1
                    logger.info(f"Linked activity {act_id} to route '{route_name}' (Frechet={fd:.0f}m)")

    conn.commit()
    conn.close()
    logger.info(f"Created {total_links} activity-route links")
    return total_links


def get_route_history(route_id):
    """Get all activities linked to a route with their stats.

    Returns list of dicts with activity data + TP enrichment if available.
    """
    conn = get_connection()
    _ensure_tables(conn)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            ar.activity_id, ar.frechet_distance_m, ar.match_confidence,
            a.start_time, a.total_timer_time, a.total_distance, a.avg_power,
            a.normalized_power, a.intensity_factor, a.training_stress_score,
            a.total_ascent, a.sub_sport
        FROM activity_routes ar
        JOIN activities a ON ar.activity_id = a.id
        WHERE ar.route_id = ?
        ORDER BY a.start_time DESC
    """, (route_id,))

    columns = [desc[0] for desc in cursor.description]
    history = [dict(zip(columns, row)) for row in cursor.fetchall()]

    # Enrich with TP data if available
    try:
        for ride in history:
            date = str(ride.get("start_time", ""))[:10]
            cursor.execute("""
                SELECT title, workout_description, coach_comments, athlete_comments, rpe, feeling
                FROM tp_workouts WHERE workout_day = ? LIMIT 1
            """, (date,))
            tp_row = cursor.fetchone()
            if tp_row:
                ride["tp_title"] = tp_row[0]
                ride["tp_description"] = tp_row[1]
                ride["coach_comments"] = tp_row[2]
                ride["athlete_comments"] = tp_row[3]
                ride["rpe"] = tp_row[4]
                ride["feeling"] = tp_row[5]
    except Exception:
        pass  # TP table may not exist

    conn.close()
    return history


def save_ride_plan(route_id, name, target_riding_hours, rest_hours=0,
                   cda=None, drafting_pct=0, drafting_savings=0.30,
                   baseline_intake_g_hr=None, starting_glycogen_g=None,
                   result_json=None):
    """Save a ride plan against a route.

    Returns: plan_id
    """
    conn = get_connection()
    _ensure_tables(conn)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO ride_plans (route_id, name, target_riding_hours, rest_hours,
                               cda, drafting_pct, drafting_savings,
                               baseline_intake_g_hr, starting_glycogen_g, result_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        route_id, name, target_riding_hours, rest_hours,
        cda, drafting_pct, drafting_savings,
        baseline_intake_g_hr, starting_glycogen_g,
        json.dumps(result_json) if result_json else None,
    ))
    plan_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return plan_id


def get_ride_plans(route_id):
    """Get all ride plans for a route."""
    conn = get_connection()
    _ensure_tables(conn)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ride_plans WHERE route_id = ? ORDER BY created_at DESC", (route_id,))
    columns = [desc[0] for desc in cursor.description]
    plans = [dict(zip(columns, row)) for row in cursor.fetchall()]
    for plan in plans:
        if plan.get("result_json") and isinstance(plan["result_json"], str):
            try:
                plan["result_json"] = json.loads(plan["result_json"])
            except (json.JSONDecodeError, TypeError):
                pass
    conn.close()
    return plans
