# wko5/segments.py
"""Segment detection, classification, and demand profiling from ride data."""

import logging

import numpy as np
import pandas as pd

from wko5.config import get_config
from wko5.db import get_connection, get_records
from wko5.physics import power_required, speed_from_power

logger = logging.getLogger(__name__)

# Segment type thresholds (grade as decimal)
CLIMB_THRESHOLD = 0.03
ROLLING_THRESHOLD = 0.01
FLAT_THRESHOLD = 0.01  # -1% to +1%
MIN_SEGMENT_DISTANCE = 200  # meters — segments shorter than this are merged


def compute_grade(altitude, distance, smoothing_window=10):
    """Compute grade from altitude and distance series."""
    alt_diff = altitude.diff()
    dist_diff = distance.diff().replace(0, np.nan)

    grade = (alt_diff / dist_diff).fillna(0)

    if smoothing_window > 1:
        grade = grade.rolling(window=smoothing_window, min_periods=1, center=True).mean()

    grade = grade.clip(-0.5, 0.5)

    return grade


def _classify_point(grade):
    """Classify a single grade value into a segment type."""
    if grade > CLIMB_THRESHOLD:
        return "climb"
    elif grade > ROLLING_THRESHOLD:
        return "rolling"
    elif grade < -CLIMB_THRESHOLD:
        return "descent"
    elif grade < -ROLLING_THRESHOLD:
        return "rolling_descent"
    else:
        return "flat"


def _classify_demand(duration_s):
    """Classify physiological demand based on expected segment duration."""
    if duration_s < 15:
        return "neuromuscular"
    elif duration_s < 120:
        return "anaerobic"
    elif duration_s < 480:
        return "vo2max"
    elif duration_s < 1200:
        return "threshold"
    else:
        return "endurance"


def classify_segments(altitude, distance, power=None, speed=None, timestamps=None):
    """Detect and classify segments from altitude and distance data.

    Returns list of segment dicts with:
        type, start_idx, end_idx, distance_m, elevation_gain, avg_grade,
        cumulative_kj_at_start, power_required, duration_s, etc.
    """
    grade = compute_grade(altitude, distance)

    classifications = grade.apply(_classify_point)

    raw_segments = []
    current_type = classifications.iloc[0]
    start_idx = 0

    for i in range(1, len(classifications)):
        if classifications.iloc[i] != current_type:
            raw_segments.append({
                "type": current_type,
                "start_idx": start_idx,
                "end_idx": i,
            })
            current_type = classifications.iloc[i]
            start_idx = i

    raw_segments.append({
        "type": current_type,
        "start_idx": start_idx,
        "end_idx": len(classifications),
    })

    merged = []
    for seg in raw_segments:
        seg_dist = float(distance.iloc[min(seg["end_idx"]-1, len(distance)-1)] -
                        distance.iloc[seg["start_idx"]])

        if seg_dist < MIN_SEGMENT_DISTANCE and merged:
            merged[-1]["end_idx"] = seg["end_idx"]
        else:
            merged.append(seg)

    # Get config once outside loop (not per-segment)
    cfg = get_config()

    # Compute metrics for each segment, tracking cumulative kJ
    result = []
    cumulative_kj = 0.0

    for seg in merged:
        s, e = seg["start_idx"], min(seg["end_idx"], len(altitude) - 1)
        if s >= e:
            continue

        seg_alt = altitude.iloc[s:e+1]
        seg_dist_vals = distance.iloc[s:e+1]
        seg_grade = grade.iloc[s:e+1]

        dist_m = float(seg_dist_vals.iloc[-1] - seg_dist_vals.iloc[0])
        elev_gain = float(max(0, seg_alt.iloc[-1] - seg_alt.iloc[0]))
        elev_loss = float(max(0, seg_alt.iloc[0] - seg_alt.iloc[-1]))
        avg_grade = float(seg_grade.mean())

        entry = {
            "type": seg["type"],
            "start_idx": s,
            "end_idx": e,
            "distance_m": round(dist_m, 1),
            "elevation_gain": round(elev_gain, 1),
            "elevation_loss": round(elev_loss, 1),
            "avg_grade": round(avg_grade, 4),
            "cumulative_kj_at_start": round(cumulative_kj, 1),
        }

        if timestamps is not None and len(timestamps) > e:
            try:
                t_start = pd.to_datetime(timestamps.iloc[s])
                t_end = pd.to_datetime(timestamps.iloc[e])
                entry["duration_s"] = (t_end - t_start).total_seconds()
            except Exception:
                entry["duration_s"] = float(e - s)
        else:
            entry["duration_s"] = float(e - s)

        if power is not None:
            seg_power = power.iloc[s:e+1].dropna()
            if len(seg_power) > 0:
                entry["avg_power"] = round(float(seg_power.mean()), 1)
                entry["max_power"] = int(seg_power.max())
                cumulative_kj += float(seg_power.sum()) / 1000

        if speed is not None:
            seg_speed = speed.iloc[s:e+1].dropna()
            if len(seg_speed) > 0:
                entry["avg_speed_ms"] = round(float(seg_speed.mean()), 2)

        # Classify physiological demand for climbs
        if seg["type"] == "climb" and entry["duration_s"] > 0:
            entry["system_taxed"] = _classify_demand(entry["duration_s"])

        # Compute power required for ALL segment types (spec requirement)
        if dist_m > 0 and entry["duration_s"] > 0:
            avg_speed = dist_m / entry["duration_s"]
            p_req = power_required(
                speed=avg_speed,
                grade=avg_grade,
                weight_rider=cfg["weight_kg"],
                weight_bike=cfg["bike_weight_kg"],
                cda=cfg["cda"],
                crr=cfg["crr"],
            )
            entry["power_required"] = round(max(0, p_req), 1)

        result.append(entry)

    return result


def analyze_ride_segments(activity_id):
    """Full segment analysis for a recorded ride."""
    records = get_records(activity_id)
    if records.empty:
        return {"segments": [], "summary": {}}

    if "altitude" not in records.columns or records["altitude"].isna().all():
        logger.warning(f"Activity {activity_id} has no altitude data")
        return {"segments": [], "summary": {"error": "no altitude data"}}

    if "distance" not in records.columns or records["distance"].isna().all():
        logger.warning(f"Activity {activity_id} has no distance data")
        return {"segments": [], "summary": {"error": "no distance data"}}

    altitude = records["altitude"].interpolate()
    distance = records["distance"].interpolate()
    power = records.get("power")
    speed = records.get("speed")
    timestamps = records.get("timestamp")

    segments = classify_segments(altitude, distance, power=power, speed=speed, timestamps=timestamps)

    climbs = [s for s in segments if s["type"] == "climb"]
    total_climbing = sum(s["elevation_gain"] for s in climbs)
    total_distance = float(distance.iloc[-1] - distance.iloc[0]) if len(distance) > 0 else 0

    demand_summary = {}
    for seg in climbs:
        system = seg.get("system_taxed", "unknown")
        if system not in demand_summary:
            demand_summary[system] = {"count": 0, "total_time_s": 0, "total_elevation": 0}
        demand_summary[system]["count"] += 1
        demand_summary[system]["total_time_s"] += seg.get("duration_s", 0)
        demand_summary[system]["total_elevation"] += seg.get("elevation_gain", 0)

    summary = {
        "total_segments": len(segments),
        "total_climbs": len(climbs),
        "total_climbing_m": round(total_climbing, 1),
        "total_distance_m": round(total_distance, 1),
        "demand_by_system": demand_summary,
    }

    return {"segments": segments, "summary": summary}


def analyze_gpx(gpx_path):
    """Analyze segments from a GPX file (for prospective route analysis)."""
    import defusedxml.ElementTree as ET

    tree = ET.parse(gpx_path)
    root = tree.getroot()

    ns = {"gpx": "http://www.topografix.com/GPX/1/1"}

    points = []
    cum_dist = 0.0
    prev_lat = prev_lon = None

    for trkpt in root.iter("{http://www.topografix.com/GPX/1/1}trkpt"):
        lat = float(trkpt.get("lat"))
        lon = float(trkpt.get("lon"))
        ele_elem = trkpt.find("gpx:ele", ns) or trkpt.find("{http://www.topografix.com/GPX/1/1}ele")
        ele = float(ele_elem.text) if ele_elem is not None else 0

        if prev_lat is not None:
            R = 6371000
            dlat = np.radians(lat - prev_lat)
            dlon = np.radians(lon - prev_lon)
            a = np.sin(dlat/2)**2 + np.cos(np.radians(prev_lat)) * np.cos(np.radians(lat)) * np.sin(dlon/2)**2
            c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
            cum_dist += R * c

        points.append({"altitude": ele, "distance": cum_dist})
        prev_lat, prev_lon = lat, lon

    if not points:
        return {"segments": [], "summary": {"error": "no trackpoints in GPX"}}

    df = pd.DataFrame(points)
    segments = classify_segments(df["altitude"], df["distance"])

    cfg = get_config()
    from wko5.pdcurve import compute_envelope_mmp, fit_pd_model
    mmp = compute_envelope_mmp(days=90)
    model = fit_pd_model(mmp)
    target_power = model["mFTP"] * 0.85 if model else cfg["ftp_manual"] * 0.85

    for seg in segments:
        if seg["distance_m"] > 0:
            est_speed = speed_from_power(
                power=target_power,
                grade=seg["avg_grade"],
                weight_rider=cfg["weight_kg"],
                weight_bike=cfg["bike_weight_kg"],
                cda=cfg["cda"],
                crr=cfg["crr"],
            )
            seg["estimated_duration_s"] = round(seg["distance_m"] / max(est_speed, 0.5), 1)
            seg["estimated_speed_kmh"] = round(est_speed * 3.6, 1)
            # Recompute power_required for ALL types using estimated speed
            p_req = power_required(
                speed=est_speed,
                grade=seg["avg_grade"],
                weight_rider=cfg["weight_kg"],
                weight_bike=cfg["bike_weight_kg"],
                cda=cfg["cda"],
                crr=cfg["crr"],
            )
            seg["power_required"] = round(max(0, p_req), 1)
            if seg["type"] == "climb":
                seg["system_taxed"] = _classify_demand(seg["estimated_duration_s"])

    climbs = [s for s in segments if s["type"] == "climb"]
    summary = {
        "total_segments": len(segments),
        "total_climbs": len(climbs),
        "total_climbing_m": round(sum(s["elevation_gain"] for s in climbs), 1),
        "total_distance_m": round(df["distance"].iloc[-1], 1),
    }

    return {"segments": segments, "summary": summary}
