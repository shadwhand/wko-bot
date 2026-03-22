"""RideWithGPS API integration — import routes with track points."""

import logging
import os

import numpy as np
import requests

from wko5.db import get_connection
from wko5.routes import _ensure_tables, downsample_track

logger = logging.getLogger(__name__)

# Credentials from environment or keyring
RWGPS_API_KEY = os.environ.get("RWGPS_API_KEY", "c8da9c01")
RWGPS_AUTH_TOKEN = os.environ.get("RWGPS_AUTH_TOKEN", "1d3398ca6114c6cc559ca30aa9116129")

BASE_URL = "https://ridewithgps.com/api/v1"


def _headers():
    return {
        "x-rwgps-api-key": RWGPS_API_KEY,
        "x-rwgps-auth-token": RWGPS_AUTH_TOKEN,
        "Content-Type": "application/json",
    }


def list_rwgps_routes():
    """List all routes from the RWGPS account.

    Returns list of dicts with id, name, distance, elevation_gain.
    """
    all_routes = []
    page = 1
    while True:
        resp = requests.get(
            f"{BASE_URL}/routes.json?page={page}&page_size=200",
            headers=_headers(),
        )
        resp.raise_for_status()
        data = resp.json()
        routes = data.get("routes", [])
        if not routes:
            break
        all_routes.extend(routes)
        page += 1
    return all_routes


def import_rwgps_route(rwgps_route_id):
    """Import a single RWGPS route by ID.

    Fetches track points, downsamples, and stores in the routes table.
    Returns the local route_id.
    """
    resp = requests.get(
        f"{BASE_URL}/routes/{rwgps_route_id}.json",
        headers=_headers(),
    )
    resp.raise_for_status()
    detail = resp.json()

    route_data = detail.get("route", detail)
    name = route_data.get("name", f"RWGPS Route {rwgps_route_id}")
    distance = route_data.get("distance", 0)
    elevation = route_data.get("elevation_gain", 0)
    track_points = route_data.get("track_points", [])

    if not track_points:
        raise ValueError(f"No track points for route {rwgps_route_id}")

    lats = np.array([p["y"] for p in track_points])
    lons = np.array([p["x"] for p in track_points])

    ds = downsample_track(lats, lons, target_spacing_m=1000)

    conn = get_connection()
    _ensure_tables(conn)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO routes (name, source_file, total_distance_m, total_elevation_m,
                           point_count, bbox_lat_min, bbox_lat_max, bbox_lon_min, bbox_lon_max)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        name, f"rwgps_{rwgps_route_id}", distance, elevation,
        len(ds), float(lats.min()), float(lats.max()),
        float(lons.min()), float(lons.max()),
    ))
    route_id = cursor.lastrowid

    for i, (lat, lon, cum_dist) in enumerate(ds):
        cursor.execute("""
            INSERT INTO route_points (route_id, point_order, lat, lon, cumulative_distance_m)
            VALUES (?, ?, ?, ?, ?)
        """, (route_id, i, lat, lon, cum_dist))

    conn.commit()
    conn.close()
    logger.info(f"Imported RWGPS route '{name}' ({distance/1000:.0f}km) as route {route_id}")
    return route_id


def import_all_rwgps_routes():
    """Import all routes from the RWGPS account.

    Skips routes already imported (by source_file).
    Returns (imported_count, skipped_count).
    """
    all_routes = list_rwgps_routes()
    logger.info(f"Found {len(all_routes)} routes on RWGPS")

    conn = get_connection()
    _ensure_tables(conn)
    cursor = conn.cursor()
    cursor.execute("SELECT source_file FROM routes WHERE source_file LIKE 'rwgps_%'")
    existing = {row[0] for row in cursor.fetchall()}
    conn.close()

    imported = 0
    skipped = 0

    for r in all_routes:
        source_file = f"rwgps_{r['id']}"
        if source_file in existing:
            skipped += 1
            continue

        try:
            import_rwgps_route(r["id"])
            imported += 1
            if imported % 20 == 0:
                logger.info(f"Imported {imported} routes...")
        except Exception as e:
            logger.warning(f"Failed to import {r.get('name', r['id'])}: {e}")

    logger.info(f"Done: {imported} imported, {skipped} already existed")
    return imported, skipped
