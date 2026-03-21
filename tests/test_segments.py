# tests/test_segments.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
from wko5.segments import compute_grade, classify_segments, analyze_ride_segments, analyze_gpx


def test_compute_grade_flat():
    """Flat terrain should have ~0% grade."""
    altitude = pd.Series([100.0] * 100)
    distance = pd.Series(np.arange(0, 1000, 10, dtype=float))
    grade = compute_grade(altitude, distance)
    assert abs(grade.mean()) < 0.01


def test_compute_grade_climbing():
    """10m rise over 100m distance = 10% grade."""
    altitude = pd.Series(np.linspace(100, 110, 20))
    distance = pd.Series(np.linspace(0, 100, 20))
    grade = compute_grade(altitude, distance)
    assert 0.05 < grade.mean() < 0.15


def test_classify_segments_basic():
    """Should detect climb, flat, and descent segments."""
    n = 400
    alt = np.concatenate([
        np.full(100, 100),
        np.linspace(100, 200, 100),
        np.full(100, 200),
        np.linspace(200, 100, 100),
    ])
    dist = np.linspace(0, 4000, n)

    altitude = pd.Series(alt)
    distance = pd.Series(dist)

    segments = classify_segments(altitude, distance)
    assert isinstance(segments, list)
    assert len(segments) >= 3

    types = [s["type"] for s in segments]
    assert "climb" in types
    assert "descent" in types


def test_classify_segments_min_length():
    """Very short segments should be merged into neighbors."""
    alt = np.concatenate([
        np.full(50, 100),
        np.array([100, 105]),
        np.full(50, 100),
    ])
    dist = np.linspace(0, 1020, len(alt))

    segments = classify_segments(pd.Series(alt), pd.Series(dist))
    assert len(segments) <= 2


def test_classify_segments_has_cumulative_kj():
    """Segments should include cumulative_kj_at_start field."""
    n = 200
    alt = np.concatenate([np.full(100, 100), np.linspace(100, 200, 100)])
    dist = np.linspace(0, 2000, n)
    segments = classify_segments(pd.Series(alt), pd.Series(dist))
    for seg in segments:
        assert "cumulative_kj_at_start" in seg


def test_classify_segments_power_required_all_types():
    """All segment types should have power_required."""
    n = 400
    alt = np.concatenate([
        np.full(100, 100),
        np.linspace(100, 200, 100),
        np.full(100, 200),
        np.linspace(200, 100, 100),
    ])
    dist = np.linspace(0, 4000, n)
    segments = classify_segments(pd.Series(alt), pd.Series(dist))
    for seg in segments:
        assert "power_required" in seg


def test_analyze_ride_segments():
    """Analyze a real ride's segments."""
    from wko5.db import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.id FROM activities a
        JOIN records r ON r.activity_id = a.id
        WHERE a.sub_sport = 'road' AND a.total_ascent > 500
        AND r.altitude IS NOT NULL
        GROUP BY a.id
        ORDER BY a.start_time DESC LIMIT 1
    """)
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return

    result = analyze_ride_segments(row[0])
    assert isinstance(result, dict)
    assert "segments" in result
    assert "summary" in result
    assert len(result["segments"]) > 0

    seg = result["segments"][0]
    assert "type" in seg
    assert "distance_m" in seg
    assert "duration_s" in seg
    assert "avg_grade" in seg
    assert "cumulative_kj_at_start" in seg


def test_segment_demand_classification():
    """Segments should be classified by physiological system."""
    from wko5.db import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.id FROM activities a
        JOIN records r ON r.activity_id = a.id
        WHERE a.sub_sport = 'road' AND a.total_ascent > 1000
        AND r.altitude IS NOT NULL
        GROUP BY a.id
        ORDER BY a.start_time DESC LIMIT 1
    """)
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return

    result = analyze_ride_segments(row[0])
    for seg in result["segments"]:
        if seg["type"] == "climb":
            assert "system_taxed" in seg
            assert seg["system_taxed"] in ["neuromuscular", "anaerobic", "vo2max", "threshold", "endurance"]
