"""FTP test detection and extraction — Kolie Moore protocol.

Identifies FTP test rides from TrainingPeaks data or power patterns,
extracts the actual FTP (average power of sustained effort) and TTE
(time to exhaustion). These become strong priors for the Bayesian PD model.
"""

import logging
from datetime import datetime

import numpy as np
import pandas as pd

from wko5.db import get_connection, get_records
from wko5.config import get_config

logger = logging.getLogger(__name__)

FTP_TESTS_DDL = """
CREATE TABLE IF NOT EXISTS ftp_tests (
    id INTEGER PRIMARY KEY,
    activity_id INTEGER,
    test_date TEXT NOT NULL,
    ftp_watts REAL NOT NULL,
    tte_minutes REAL,
    avg_hr REAL,
    max_hr REAL,
    source TEXT DEFAULT 'auto',
    notes TEXT,
    FOREIGN KEY (activity_id) REFERENCES activities(id)
);
"""


def _ensure_table(conn):
    conn.execute(FTP_TESTS_DDL)


def extract_ftp_test(activity_id):
    """Extract FTP and TTE from an FTP test ride.

    Uses the Kolie Moore protocol logic: FTP = average power of the
    sustained effort (longest continuous block above ~90% of peak 30-min power).
    TTE = duration of that effort.

    Returns dict with {ftp_watts, tte_minutes, avg_hr, max_hr} or None.
    """
    records = get_records(activity_id)
    if records.empty or "power" not in records.columns:
        return None

    power = records["power"].fillna(0).values.astype(float)
    hr = records["heart_rate"].fillna(0).values.astype(float) if "heart_rate" in records.columns else None
    n = len(power)

    if n < 1200:  # need at least 20 minutes
        return None

    # Find the sustained effort block
    # Strategy: use rolling 30-second average to smooth brief power dips,
    # then find the longest block above 85% of peak rolling power.
    # The Kolie Moore protocol has ramp phases and brief dips — raw
    # per-second power is too noisy for contiguous block detection.

    # Smooth power with 30-second rolling average
    smooth = pd.Series(power).rolling(30, min_periods=10, center=True).mean().values

    window = min(1800, n // 2)  # 30 min or half the ride
    rolling = pd.Series(smooth).rolling(window, min_periods=window // 2).mean().values

    peak_rolling = np.nanmax(rolling)
    if peak_rolling < 100:
        return None

    threshold = peak_rolling * 0.80  # 80% of peak rolling — allow ramp-in

    # Find the longest block above threshold, allowing gaps of up to 30 seconds
    above = smooth > threshold
    best_start = 0
    best_end = 0
    current_start = 0
    gap = 0
    max_gap = 30  # allow 30s gaps (shifting, brief recovery)

    i = 0
    while i < n:
        if above[i]:
            if current_start == 0:
                current_start = i
            gap = 0
            if i - current_start > best_end - best_start:
                best_start = current_start
                best_end = i
        else:
            gap += 1
            if gap > max_gap:
                current_start = 0
        i += 1

    best_len = best_end - best_start
    if best_len < 1200:  # need at least 20 min of sustained effort
        return None

    # FTP = average power of the sustained block
    effort_power = power[best_start:best_end]
    ftp = float(np.mean(effort_power))
    tte = best_len / 60  # minutes

    result = {
        "ftp_watts": round(ftp, 1),
        "tte_minutes": round(tte, 1),
    }

    if hr is not None:
        effort_hr = hr[best_start:best_end]
        valid_hr = effort_hr[effort_hr > 0]
        if len(valid_hr) > 0:
            result["avg_hr"] = round(float(np.mean(valid_hr)), 0)
            result["max_hr"] = round(float(np.max(valid_hr)), 0)

    return result


def detect_ftp_tests_from_tp():
    """Find FTP test rides from TrainingPeaks data.

    Looks for workouts with 'FTP' in the title, matches to activities,
    and extracts FTP/TTE from the power data.

    Returns list of test results.
    """
    conn = get_connection()
    _ensure_table(conn)

    # Find TP workouts with FTP in title that have matched activities
    try:
        tp_result = conn.execute("""
            SELECT tp.workout_day, tp.title, tp.activity_id, tp.athlete_comments
            FROM tp_workouts tp
            WHERE tp.title LIKE '%FTP%' AND tp.activity_id IS NOT NULL
            ORDER BY tp.workout_day
        """)
        tp_tests = tp_result.fetchall()
    except Exception:
        conn.close()
        return []

    results = []
    for workout_day, title, activity_id, comments in tp_tests:
        # Skip if already extracted
        check = conn.execute(
            "SELECT 1 FROM ftp_tests WHERE activity_id = ?", [activity_id]
        )
        if check.fetchone():
            continue

        test_result = extract_ftp_test(activity_id)
        if test_result is None:
            continue

        # Store in DB
        conn.execute("""
            INSERT INTO ftp_tests (activity_id, test_date, ftp_watts, tte_minutes,
                                   avg_hr, max_hr, source, notes)
            VALUES (?, ?, ?, ?, ?, ?, 'tp_auto', ?)
        """, (
            activity_id, workout_day, test_result["ftp_watts"],
            test_result.get("tte_minutes"),
            test_result.get("avg_hr"),
            test_result.get("max_hr"),
            title,
        ))

        test_result["test_date"] = workout_day
        test_result["activity_id"] = activity_id
        test_result["title"] = title
        results.append(test_result)

    conn.commit()
    conn.close()
    return results


def get_ftp_history():
    """Get all stored FTP test results, ordered by date."""
    conn = get_connection()
    _ensure_table(conn)
    result = conn.execute("SELECT * FROM ftp_tests ORDER BY test_date")
    columns = [desc[0] for desc in result.description]
    rows = [dict(zip(columns, row)) for row in result.fetchall()]
    conn.close()
    return rows


def get_latest_ftp_test():
    """Get the most recent FTP test result."""
    conn = get_connection()
    _ensure_table(conn)
    result = conn.execute("SELECT * FROM ftp_tests ORDER BY test_date DESC LIMIT 1")
    row = result.fetchone()
    if row is None:
        conn.close()
        return None
    columns = [desc[0] for desc in result.description]
    out = dict(zip(columns, row))
    conn.close()
    return out


def ftp_prior_strength(test_date_str=None):
    """Compute the prior SD for the Bayesian PD model based on time since last FTP test.

    Fresh test (<3 months): SD = 10W (very strong prior)
    Aging test (3-6 months): SD = 15-25W (weakening)
    Stale test (>6 months): SD = 30W+ (weak prior, let data speak)
    No test: SD = 40W (uninformative)
    """
    if test_date_str is None:
        latest = get_latest_ftp_test()
        if latest is None:
            return {"sd": 40, "months_since_test": None, "ftp": None}
        test_date_str = latest["test_date"]
        ftp = latest["ftp_watts"]
    else:
        ftp = None

    try:
        test_date = datetime.strptime(test_date_str, "%Y-%m-%d")
    except (ValueError, TypeError):
        return {"sd": 40, "months_since_test": None, "ftp": ftp}

    months = (datetime.now() - test_date).days / 30

    if months < 3:
        sd = 10
    elif months < 6:
        sd = 10 + (months - 3) * 5  # 10 → 25 over 3 months
    else:
        sd = min(40, 25 + (months - 6) * 2.5)  # caps at 40

    return {
        "sd": round(sd, 1),
        "months_since_test": round(months, 1),
        "ftp": ftp,
    }
