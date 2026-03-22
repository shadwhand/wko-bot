# tests/test_tp_ingest.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import sqlite3
import pandas as pd
from wko5.tp_ingest import ingest_tp_csv, get_tp_workouts, match_tp_to_activities
from wko5.db import get_connection


def test_ingest_tp_csv():
    """Should create tp_workouts table and populate it."""
    csv_path = "/Users/jshin/Downloads/workouts.csv"
    if not os.path.exists(csv_path):
        return

    count = ingest_tp_csv(csv_path)
    assert count > 200


def test_ingest_multiple_csvs():
    """Should handle multiple CSV files and deduplicate."""
    paths = [
        "/Users/jshin/Downloads/workouts-2.csv",
        "/Users/jshin/Downloads/workouts.csv",
    ]
    if not all(os.path.exists(p) for p in paths):
        return

    count = ingest_tp_csv(paths)
    assert count > 500  # ~620 combined minus overlap

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM tp_workouts")
    db_count = cursor.fetchone()[0]
    conn.close()
    assert db_count == count


def test_get_tp_workouts():
    """Should return workouts as DataFrame."""
    workouts = get_tp_workouts()
    if workouts.empty:
        return

    assert "title" in workouts.columns
    assert "workout_day" in workouts.columns
    assert "workout_description" in workouts.columns
    assert "coach_comments" in workouts.columns
    assert "athlete_comments" in workouts.columns
    assert "rpe" in workouts.columns


def test_get_tp_workouts_date_filter():
    """Should filter by date range."""
    all_workouts = get_tp_workouts()
    if all_workouts.empty:
        return

    filtered = get_tp_workouts(start="2025-06-01", end="2025-06-30")
    assert len(filtered) <= len(all_workouts)


def test_match_tp_to_activities():
    """Should match TP workouts to Garmin activities by date."""
    matched = match_tp_to_activities()
    if matched.empty:
        return

    assert "activity_id" in matched.columns
    assert "tp_title" in matched.columns
    assert "tp_description" in matched.columns
    # Most workouts should match (same athlete, same dates)
    total_tp = len(get_tp_workouts())
    match_rate = len(matched[matched["activity_id"].notna()]) / total_tp if total_tp > 0 else 0
    assert match_rate > 0.5, f"Only {match_rate:.0%} of TP workouts matched to activities"


def test_tp_workout_categories():
    """Workout titles should be categorizable."""
    from wko5.tp_ingest import categorize_workout
    assert categorize_workout("Easy") == "recovery"
    assert categorize_workout("Recovery") == "recovery"
    assert categorize_workout("Endurance") == "endurance"
    assert categorize_workout("Endurance + Sprints") == "endurance"
    assert categorize_workout("Indoor VO2s 7x3") == "high_intensity"
    assert categorize_workout("FTP Test") == "test"
    assert categorize_workout("Strength") == "strength"
    assert categorize_workout("Sweet Spot 3x15") == "threshold"
