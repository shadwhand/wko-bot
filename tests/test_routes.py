# tests/test_routes.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from wko5.routes import (
    save_route, get_route, get_all_routes, delete_route,
    downsample_track, semicircles_to_degrees,
    frechet_distance, find_similar_routes, link_activities_to_routes,
    get_route_history, save_ride_plan, get_ride_plans,
)
from wko5.db import get_connection


GPX_PATH = "/Users/jshin/Downloads/SCR_San_Gregorio-Greenfield_400k__3090.gpx"


def test_semicircles_to_degrees():
    """Garmin semicircles should convert to decimal degrees."""
    # 450983947 semicircles ≈ 37.78° N (San Francisco area)
    lat = semicircles_to_degrees(450983947)
    assert 37 < lat < 38


def test_downsample_track():
    """Downsampling should reduce points to ~1km spacing."""
    # 100 points over 10km
    lats = np.linspace(37.0, 37.09, 100)  # ~10km north
    lons = np.full(100, -122.0)
    ds = downsample_track(lats, lons, target_spacing_m=1000)
    assert len(ds) < 20  # should be ~10 points for 10km
    assert len(ds) > 5


def test_save_and_get_route():
    """Should save a GPX route and retrieve it."""
    if not os.path.exists(GPX_PATH):
        return

    route_id = save_route(GPX_PATH)
    assert route_id > 0

    route = get_route(route_id)
    assert route is not None
    assert route["name"] == "SCR San Gregorio-Greenfield 400k"
    assert route["total_distance_m"] > 400000
    assert route["total_elevation_m"] > 1000
    assert route["point_count"] > 300  # downsampled ~1km


def test_save_route_custom_name():
    """Should accept a custom name."""
    if not os.path.exists(GPX_PATH):
        return

    route_id = save_route(GPX_PATH, name="My Custom Route")
    route = get_route(route_id)
    assert route["name"] == "My Custom Route"


def test_get_all_routes():
    """Should list all stored routes."""
    routes = get_all_routes()
    assert isinstance(routes, list)


def test_frechet_distance_identical():
    """Frechet distance between identical tracks should be ~0."""
    track = np.array([[37.0, -122.0], [37.01, -122.0], [37.02, -122.0]])
    d = frechet_distance(track, track)
    assert d < 100  # <100m


def test_frechet_distance_different():
    """Frechet distance between different tracks should be large."""
    track_a = np.array([[37.0, -122.0], [37.01, -122.0], [37.02, -122.0]])
    track_b = np.array([[38.0, -121.0], [38.01, -121.0], [38.02, -121.0]])  # ~150km away
    d = frechet_distance(track_a, track_b)
    assert d > 100000  # >100km


def test_frechet_distance_similar():
    """Slightly different tracks should have small Frechet distance."""
    track_a = np.array([[37.0, -122.0], [37.01, -122.0], [37.02, -122.0]])
    # Same route but GPS drift of ~0.001 degrees (~100m)
    track_b = np.array([[37.001, -122.001], [37.011, -122.001], [37.021, -122.001]])
    d = frechet_distance(track_a, track_b)
    assert d < 2000  # <2km — within match threshold


def test_find_similar_routes():
    """Should find similar routes from stored routes."""
    if not os.path.exists(GPX_PATH):
        return

    # Save the route first
    save_route(GPX_PATH, name="Test Route for Matching")

    # Find similar — should match itself
    matches = find_similar_routes(GPX_PATH)
    assert len(matches) > 0
    assert matches[0]["frechet_distance_m"] < 100  # essentially identical


def test_link_activities_to_routes():
    """Batch linking should find matching activities."""
    if not os.path.exists(GPX_PATH):
        return

    save_route(GPX_PATH, name="Route for Linking")
    count = link_activities_to_routes()
    # May or may not find matches depending on whether the athlete
    # has ridden this exact route — just check it doesn't crash
    assert isinstance(count, int)


def test_save_and_get_ride_plan():
    """Should persist a ride plan against a route."""
    if not os.path.exists(GPX_PATH):
        return

    route_id = save_route(GPX_PATH, name="Route for Plan")
    plan_id = save_ride_plan(
        route_id=route_id,
        name="Fast solo attempt",
        target_riding_hours=13.5,
        rest_hours=0.5,
        cda=0.28,
        drafting_pct=0.0,
        result_json={"base_power": 185, "probability": 1.0},
    )
    assert plan_id > 0

    plans = get_ride_plans(route_id)
    assert len(plans) > 0
    assert plans[0]["name"] == "Fast solo attempt"
