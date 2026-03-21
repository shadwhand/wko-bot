#!/usr/bin/env python3
"""Backfill altitude and speed for rides where enhanced_altitude/enhanced_speed exists in FIT files."""

import os
import gzip
import sqlite3
import io
import fitdecode

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cycling_power.db")
FIT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fit-files")


def safe_get(msg, field, default=None):
    try:
        val = msg.get_value(field)
        return val if val is not None else default
    except (KeyError, TypeError):
        return default


def backfill():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Find activities with NULL altitude in records (non-Zwift, since Zwift has altitude)
    cursor.execute("""
        SELECT DISTINCT a.id, a.filename
        FROM activities a
        JOIN records r ON r.activity_id = a.id
        WHERE r.altitude IS NULL
        AND a.sub_sport != 'virtual_activity'
    """)
    candidates = cursor.fetchall()
    print(f"Found {len(candidates)} activities with missing altitude data")

    updated = 0
    for activity_id, filename in candidates:
        gz_path = os.path.join(FIT_DIR, filename + ".gz")
        fit_path = os.path.join(FIT_DIR, filename)

        if os.path.exists(gz_path):
            with gzip.open(gz_path, "rb") as f:
                data = f.read()
        elif os.path.exists(fit_path):
            with open(fit_path, "rb") as f:
                data = f.read()
        else:
            continue

        records_data = []
        try:
            with fitdecode.FitReader(io.BytesIO(data)) as fit:
                for frame in fit:
                    if not isinstance(frame, fitdecode.FitDataMessage) or frame.name != "record":
                        continue
                    ts = str(safe_get(frame, "timestamp", ""))
                    alt = safe_get(frame, "enhanced_altitude") or safe_get(frame, "altitude")
                    spd = safe_get(frame, "enhanced_speed") or safe_get(frame, "speed")
                    if ts:
                        records_data.append((alt, spd, activity_id, ts))
        except Exception as e:
            print(f"  Error reading {filename}: {e}")
            continue

        if not records_data:
            continue

        conn.executemany(
            "UPDATE records SET altitude = ?, speed = ? WHERE activity_id = ? AND timestamp = ?",
            records_data,
        )
        conn.commit()

        cursor.execute(
            "SELECT COUNT(*) FROM records WHERE activity_id = ? AND altitude IS NOT NULL",
            (activity_id,),
        )
        alt_count = cursor.fetchone()[0]
        if alt_count > 0:
            updated += 1

        if updated % 50 == 0 and updated > 0:
            print(f"  Updated {updated} activities...")

    print(f"\nDone: {updated} activities backfilled with altitude/speed data")
    conn.close()


if __name__ == "__main__":
    backfill()
