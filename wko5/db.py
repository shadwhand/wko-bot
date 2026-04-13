"""Core data layer — DB connection, common queries, athlete constants."""

import logging
import os
import duckdb

import pandas as pd

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cycling_power.duckdb")

# DEPRECATED — use get_config() instead. Kept for backward test compatibility.
WEIGHT_KG = 78.0
FTP_RANGE = (285, 299)
FTP_DEFAULT = 292


def get_connection():
    """Return a DuckDB connection to the cycling power database."""
    return duckdb.connect(DB_PATH)


def get_activities(start=None, end=None, sub_sport=None):
    """Get activities as a DataFrame, optionally filtered by date range and sub_sport."""
    conn = get_connection()
    query = "SELECT * FROM activities WHERE 1=1"
    params = []

    if start:
        query += " AND start_time >= ?"
        params.append(start)
    if end:
        query += " AND start_time <= ?"
        params.append(end)
    if sub_sport:
        query += " AND sub_sport = ?"
        params.append(sub_sport)

    query += " ORDER BY start_time"

    df = conn.execute(query, params).df()
    conn.close()
    return df


def get_records(activity_id):
    """Get per-second records for an activity as a DataFrame."""
    conn = get_connection()
    df = conn.execute(
        "SELECT * FROM records WHERE activity_id = ?",
        [activity_id],
    ).df()
    conn.close()

    if df.empty:
        logger.warning(f"No records found for activity_id={activity_id}")
        return df

    from wko5.clean import clean_records
    return clean_records(df)
