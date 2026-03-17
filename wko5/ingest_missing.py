#!/usr/bin/env python3
"""Ingest missing cycling+power FIT files into cycling_power.db, then clean up non-cycling files."""

import os
import sys
import sqlite3
import fitdecode

DB_PATH = os.path.join(os.path.dirname(__file__), "cycling_power.db")
FIT_DIR = os.path.join(os.path.dirname(__file__), "..", "fit-files")

def safe_get(msg, field, default=None):
    try:
        val = msg.get_value(field)
        return val if val is not None else default
    except (KeyError, TypeError):
        return default

def is_cycling_with_power(filepath):
    """Check if a FIT file is a cycling activity with power data."""
    try:
        with fitdecode.FitReader(filepath) as fit:
            is_cycling = False
            has_power = False
            for frame in fit:
                if not isinstance(frame, fitdecode.FitDataMessage):
                    continue
                if frame.name == "session":
                    sport = safe_get(frame, "sport", "")
                    if str(sport).lower() in ("cycling", "6"):
                        is_cycling = True
                if frame.name == "record" and not has_power:
                    p = safe_get(frame, "power")
                    if p is not None and p > 0:
                        has_power = True
                if is_cycling and has_power:
                    return True
        return is_cycling and has_power
    except Exception:
        return False

def ingest_file(filepath, conn):
    """Ingest a single FIT file into the database."""
    filename = os.path.basename(filepath)
    session_data = {}
    records = []
    laps = []

    with fitdecode.FitReader(filepath) as fit:
        for frame in fit:
            if not isinstance(frame, fitdecode.FitDataMessage):
                continue

            if frame.name == "session":
                session_data = {
                    "filename": filename,
                    "sport": str(safe_get(frame, "sport", "")),
                    "sub_sport": str(safe_get(frame, "sub_sport", "")),
                    "start_time": str(safe_get(frame, "start_time", "")),
                    "total_elapsed_time": safe_get(frame, "total_elapsed_time"),
                    "total_timer_time": safe_get(frame, "total_timer_time"),
                    "total_distance": safe_get(frame, "total_distance"),
                    "avg_power": safe_get(frame, "avg_power"),
                    "max_power": safe_get(frame, "max_power"),
                    "normalized_power": safe_get(frame, "normalized_power"),
                    "avg_heart_rate": safe_get(frame, "avg_heart_rate"),
                    "max_heart_rate": safe_get(frame, "max_heart_rate"),
                    "avg_cadence": safe_get(frame, "avg_cadence"),
                    "max_cadence": safe_get(frame, "max_cadence"),
                    "avg_speed": safe_get(frame, "avg_speed"),
                    "max_speed": safe_get(frame, "max_speed"),
                    "total_ascent": safe_get(frame, "total_ascent"),
                    "total_descent": safe_get(frame, "total_descent"),
                    "total_calories": safe_get(frame, "total_calories"),
                    "avg_temperature": safe_get(frame, "avg_temperature"),
                    "threshold_power": safe_get(frame, "threshold_power"),
                    "intensity_factor": safe_get(frame, "intensity_factor"),
                    "training_stress_score": safe_get(frame, "training_stress_score"),
                    "total_work": safe_get(frame, "total_work"),
                }

            elif frame.name == "record":
                records.append({
                    "timestamp": str(safe_get(frame, "timestamp", "")),
                    "elapsed_seconds": safe_get(frame, "elapsed_time"),
                    "power": safe_get(frame, "power"),
                    "heart_rate": safe_get(frame, "heart_rate"),
                    "cadence": safe_get(frame, "cadence"),
                    "speed": safe_get(frame, "speed"),
                    "altitude": safe_get(frame, "altitude"),
                    "temperature": safe_get(frame, "temperature"),
                    "latitude": safe_get(frame, "position_lat"),
                    "longitude": safe_get(frame, "position_long"),
                    "distance": safe_get(frame, "distance"),
                })

            elif frame.name == "lap":
                laps.append({
                    "lap_number": len(laps) + 1,
                    "start_time": str(safe_get(frame, "start_time", "")),
                    "total_elapsed_time": safe_get(frame, "total_elapsed_time"),
                    "total_timer_time": safe_get(frame, "total_timer_time"),
                    "total_distance": safe_get(frame, "total_distance"),
                    "avg_power": safe_get(frame, "avg_power"),
                    "max_power": safe_get(frame, "max_power"),
                    "avg_heart_rate": safe_get(frame, "avg_heart_rate"),
                    "max_heart_rate": safe_get(frame, "max_heart_rate"),
                    "avg_cadence": safe_get(frame, "avg_cadence"),
                    "avg_speed": safe_get(frame, "avg_speed"),
                    "total_ascent": safe_get(frame, "total_ascent"),
                    "total_calories": safe_get(frame, "total_calories"),
                    "intensity": str(safe_get(frame, "intensity", "")),
                })

    if not session_data:
        return False

    cursor = conn.cursor()
    cols = list(session_data.keys())
    cursor.execute(
        f"INSERT INTO activities ({','.join(cols)}) VALUES ({','.join('?' for _ in cols)})",
        [session_data[c] for c in cols],
    )
    activity_id = cursor.lastrowid

    if records:
        for r in records:
            cursor.execute(
                "INSERT INTO records (activity_id, timestamp, elapsed_seconds, power, heart_rate, cadence, speed, altitude, temperature, latitude, longitude, distance) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (activity_id, r["timestamp"], r["elapsed_seconds"], r["power"], r["heart_rate"], r["cadence"], r["speed"], r["altitude"], r["temperature"], r["latitude"], r["longitude"], r["distance"]),
            )

    for lap in laps:
        cursor.execute(
            "INSERT INTO laps (activity_id, lap_number, start_time, total_elapsed_time, total_timer_time, total_distance, avg_power, max_power, avg_heart_rate, max_heart_rate, avg_cadence, avg_speed, total_ascent, total_calories, intensity) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (activity_id, lap["lap_number"], lap["start_time"], lap["total_elapsed_time"], lap["total_timer_time"], lap["total_distance"], lap["avg_power"], lap["max_power"], lap["avg_heart_rate"], lap["max_heart_rate"], lap["avg_cadence"], lap["avg_speed"], lap["total_ascent"], lap["total_calories"], lap["intensity"]),
        )

    conn.commit()
    return True


def main():
    conn = sqlite3.connect(DB_PATH)

    # Get already-ingested filenames
    cursor = conn.cursor()
    cursor.execute("SELECT filename FROM activities")
    existing = {row[0] for row in cursor.fetchall()}
    print(f"Already in DB: {len(existing)} activities")

    # Scan all FIT files
    fit_files = [f for f in os.listdir(FIT_DIR) if f.lower().endswith(".fit")]
    print(f"Total FIT files: {len(fit_files)}")

    # Find candidates not yet in DB
    candidates = [f for f in fit_files if f not in existing]
    print(f"Not yet in DB: {len(candidates)}")

    # Phase 1: Ingest missing cycling+power files
    ingested = 0
    failed = 0
    not_cycling = []
    cycling_filenames = set()

    for i, filename in enumerate(candidates):
        filepath = os.path.join(FIT_DIR, filename)
        try:
            if is_cycling_with_power(filepath):
                if ingest_file(filepath, conn):
                    ingested += 1
                    cycling_filenames.add(filename)
                else:
                    failed += 1
            else:
                not_cycling.append(filename)
        except Exception as e:
            failed += 1
            print(f"  Error {filename}: {e}")

        if (i + 1) % 500 == 0:
            print(f"  Scanned {i+1}/{len(candidates)}...")

    # Also track existing DB files as cycling
    cycling_filenames.update(existing)

    print(f"\nIngestion complete: {ingested} new activities, {failed} failed")

    # Updated totals
    cursor.execute("SELECT COUNT(*) FROM activities")
    total_activities = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM records")
    total_records = cursor.fetchone()[0]
    print(f"DB now has: {total_activities} activities, {total_records} records")

    # Phase 2: Clean up non-cycling FIT files
    all_fit = set(fit_files)
    non_cycling = all_fit - cycling_filenames
    print(f"\nNon-cycling FIT files to remove: {len(non_cycling)}")

    removed = 0
    for filename in non_cycling:
        filepath = os.path.join(FIT_DIR, filename)
        try:
            os.remove(filepath)
            removed += 1
        except Exception as e:
            print(f"  Could not remove {filename}: {e}")

    print(f"Removed {removed} non-cycling files")

    remaining = len([f for f in os.listdir(FIT_DIR) if f.lower().endswith(".fit")])
    print(f"Remaining FIT files: {remaining}")

    conn.close()


if __name__ == "__main__":
    main()
