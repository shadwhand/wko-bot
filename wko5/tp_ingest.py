# wko5/tp_ingest.py
"""TrainingPeaks CSV ingestion and activity matching."""

import logging
import os
import re

import pandas as pd

from wko5.db import get_connection, get_activities

logger = logging.getLogger(__name__)

TP_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS tp_workouts (
    id INTEGER PRIMARY KEY,
    workout_day TEXT NOT NULL,
    title TEXT,
    workout_type TEXT,
    workout_description TEXT,
    planned_duration_hr REAL,
    coach_comments TEXT,
    athlete_comments TEXT,
    actual_duration_hr REAL,
    distance_m REAL,
    power_avg REAL,
    power_max REAL,
    energy_kj REAL,
    intensity_factor REAL,
    tss REAL,
    rpe INTEGER,
    feeling INTEGER,
    hr_zone1_min REAL, hr_zone2_min REAL, hr_zone3_min REAL,
    hr_zone4_min REAL, hr_zone5_min REAL,
    pwr_zone1_min REAL, pwr_zone2_min REAL, pwr_zone3_min REAL,
    pwr_zone4_min REAL, pwr_zone5_min REAL, pwr_zone6_min REAL,
    pwr_zone7_min REAL,
    category TEXT,
    activity_id INTEGER,
    FOREIGN KEY (activity_id) REFERENCES activities(id)
);
"""

# Workout title → category mapping
CATEGORY_PATTERNS = [
    (r"(?i)(easy|recovery|rest)", "recovery"),
    (r"(?i)(endurance|long ride|base)", "endurance"),
    (r"(?i)(sweet\s*spot|tempo|ss\s)", "threshold"),
    (r"(?i)(vo2|anaerobic|interval|tabata)", "high_intensity"),
    (r"(?i)(ftp\s*test|ramp\s*test|tt|time\s*trial|test)", "test"),
    (r"(?i)(sprint|neuromuscular|snap)", "sprint"),
    (r"(?i)(strength|gym|weight|core|yoga|stretch)", "strength"),
]


def categorize_workout(title):
    """Categorize a workout by its title."""
    if not title:
        return "unknown"
    for pattern, category in CATEGORY_PATTERNS:
        if re.search(pattern, title):
            return category
    return "endurance"  # default for unlabeled bike rides


def _safe_float(val):
    """Convert to float, handling empty strings and None."""
    if val is None or val == "" or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _safe_int(val):
    """Convert to int, handling empty strings and None."""
    f = _safe_float(val)
    return int(f) if f is not None else None


def ingest_tp_csv(csv_path):
    """Ingest one or more TrainingPeaks workout CSVs into the database.

    Args:
        csv_path: single path string or list of paths

    Returns number of rows ingested.
    """
    if isinstance(csv_path, (list, tuple)):
        dfs = [pd.read_csv(p) for p in csv_path]
        df = pd.concat(dfs, ignore_index=True)
        # Deduplicate by date + title
        df = df.drop_duplicates(subset=["WorkoutDay", "Title"], keep="last")
    else:
        df = pd.read_csv(csv_path)
    conn = get_connection()
    conn.execute(TP_TABLE_DDL)

    # Clear existing data (re-ingest is idempotent)
    conn.execute("DELETE FROM tp_workouts")

    count = 0
    for _, row in df.iterrows():
        title = row.get("Title", "")
        category = categorize_workout(title)

        conn.execute("""
            INSERT INTO tp_workouts (
                workout_day, title, workout_type, workout_description,
                planned_duration_hr, coach_comments, athlete_comments,
                actual_duration_hr, distance_m, power_avg, power_max, energy_kj,
                intensity_factor, tss, rpe, feeling,
                hr_zone1_min, hr_zone2_min, hr_zone3_min, hr_zone4_min, hr_zone5_min,
                pwr_zone1_min, pwr_zone2_min, pwr_zone3_min, pwr_zone4_min,
                pwr_zone5_min, pwr_zone6_min, pwr_zone7_min,
                category
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            row.get("WorkoutDay"),
            title,
            row.get("WorkoutType"),
            row.get("WorkoutDescription"),
            _safe_float(row.get("PlannedDuration")),
            row.get("CoachComments"),
            row.get("AthleteComments"),
            _safe_float(row.get("TimeTotalInHours")),
            _safe_float(row.get("DistanceInMeters")),
            _safe_float(row.get("PowerAverage")),
            _safe_float(row.get("PowerMax")),
            _safe_float(row.get("Energy")),
            _safe_float(row.get("IF")),
            _safe_float(row.get("TSS")),
            _safe_int(row.get("Rpe")),
            _safe_int(row.get("Feeling")),
            _safe_float(row.get("HRZone1Minutes")),
            _safe_float(row.get("HRZone2Minutes")),
            _safe_float(row.get("HRZone3Minutes")),
            _safe_float(row.get("HRZone4Minutes")),
            _safe_float(row.get("HRZone5Minutes")),
            _safe_float(row.get("PWRZone1Minutes")),
            _safe_float(row.get("PWRZone2Minutes")),
            _safe_float(row.get("PWRZone3Minutes")),
            _safe_float(row.get("PWRZone4Minutes")),
            _safe_float(row.get("PWRZone5Minutes")),
            _safe_float(row.get("PWRZone6Minutes")),
            _safe_float(row.get("PWRZone7Minutes")),
            category,
        ))
        count += 1

    conn.commit()

    # Match to activities by date
    _match_activities(conn)

    conn.close()
    logger.info(f"Ingested {count} TrainingPeaks workouts")
    return count


def _match_activities(conn):
    """Match tp_workouts to activities by date and workout type (Bike)."""
    conn.execute("""
        UPDATE tp_workouts SET activity_id = (
            SELECT a.id FROM activities a
            WHERE date(a.start_time) = tp_workouts.workout_day
            AND tp_workouts.workout_type = 'Bike'
            ORDER BY a.total_timer_time DESC
            LIMIT 1
        )
        WHERE workout_type = 'Bike'
    """)
    conn.commit()

    # Count matches
    matched = conn.execute("SELECT COUNT(*) FROM tp_workouts WHERE activity_id IS NOT NULL").fetchone()[0]
    total_bike = conn.execute("SELECT COUNT(*) FROM tp_workouts WHERE workout_type = 'Bike'").fetchone()[0]
    logger.info(f"Matched {matched}/{total_bike} bike workouts to activities")


def get_tp_workouts(start=None, end=None):
    """Get TrainingPeaks workouts as DataFrame, optionally filtered by date."""
    conn = get_connection()

    # Ensure table exists
    conn.execute(TP_TABLE_DDL)

    query = "SELECT * FROM tp_workouts WHERE 1=1"
    params = []
    if start:
        query += " AND workout_day >= ?"
        params.append(start)
    if end:
        query += " AND workout_day <= ?"
        params.append(end)
    query += " ORDER BY workout_day"

    df = conn.execute(query, params).df()
    conn.close()
    return df


def match_tp_to_activities(start=None, end=None):
    """Get joined view of TP workouts matched to activities."""
    conn = get_connection()
    conn.execute(TP_TABLE_DDL)

    query = """
        SELECT
            tp.workout_day,
            tp.title AS tp_title,
            tp.workout_description AS tp_description,
            tp.planned_duration_hr AS tp_planned_hr,
            tp.coach_comments,
            tp.athlete_comments,
            tp.category AS tp_category,
            tp.rpe,
            tp.feeling,
            tp.activity_id,
            a.start_time,
            a.total_timer_time,
            a.total_distance,
            a.avg_power,
            a.normalized_power,
            a.intensity_factor AS garmin_if,
            a.training_stress_score AS garmin_tss,
            a.total_ascent,
            a.sub_sport
        FROM tp_workouts tp
        LEFT JOIN activities a ON tp.activity_id = a.id
        WHERE 1=1
    """
    params = []
    if start:
        query += " AND tp.workout_day >= ?"
        params.append(start)
    if end:
        query += " AND tp.workout_day <= ?"
        params.append(end)
    query += " ORDER BY tp.workout_day"

    df = conn.execute(query, params).df()
    conn.close()
    return df
