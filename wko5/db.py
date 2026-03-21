"""Core data layer — DB connection, common queries, athlete constants."""

import logging
import os
import sqlite3

import pandas as pd

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cycling_power.db")

# DEPRECATED — use get_config() instead. Kept for backward test compatibility.
WEIGHT_KG = 78.0
FTP_RANGE = (285, 299)
FTP_DEFAULT = 292


def get_connection():
    """Return a SQLite connection to the cycling power database."""
    return sqlite3.connect(DB_PATH)


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

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def get_records(activity_id):
    """Get per-second records for an activity as a DataFrame."""
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM records WHERE activity_id = ? ORDER BY timestamp",
        conn,
        params=(activity_id,),
    )
    conn.close()

    if df.empty:
        logger.warning(f"No records found for activity_id={activity_id}")
        return df

    # Clean via clean module (imported here to avoid circular import at module level)
    from wko5.clean import clean_records
    return clean_records(df)
