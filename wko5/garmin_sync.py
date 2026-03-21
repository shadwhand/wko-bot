#!/usr/bin/env python3
"""
Sync new cycling+power activities from Garmin Connect into cycling_power.db.

Usage:
    python garmin_sync.py                    # Sync new activities since last DB entry
    python garmin_sync.py --days 30          # Sync last 30 days
    python garmin_sync.py --from 2024-01-01  # Sync from specific date

First run will prompt for Garmin credentials and MFA, then save a session token
for future runs. Token is stored at ~/.garmin_tokens/
"""

import argparse
import os
import sys
import sqlite3
import tempfile
from datetime import datetime, timedelta
from getpass import getpass

import fitdecode
from garminconnect import Garmin

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "cycling_power.db")
FIT_DIR = os.path.join(SCRIPT_DIR, "..", "fit-files")
TOKEN_DIR = os.path.expanduser("~/.garmin_tokens")


def safe_get(msg, field, default=None):
    try:
        val = msg.get_value(field)
        return val if val is not None else default
    except (KeyError, TypeError):
        return default


def get_garmin_client():
    """Login to Garmin Connect, using saved tokens if available."""
    os.makedirs(TOKEN_DIR, exist_ok=True)

    client = Garmin()
    try:
        client.login(tokenstore=TOKEN_DIR)
        print("Logged in with saved session.")
    except Exception:
        email = input("Garmin email: ")
        password = getpass("Garmin password: ")
        client = Garmin(email=email, password=password, prompt_mfa=lambda: input("MFA code: "))
        client.login(tokenstore=TOKEN_DIR)
        print("Logged in and saved session token.")

    return client


def get_latest_activity_date(conn):
    """Get the most recent activity date in the DB."""
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(start_time) FROM activities")
    row = cursor.fetchone()
    if row and row[0]:
        # Parse the datetime string - format varies but typically "YYYY-MM-DD HH:MM:SS"
        try:
            return datetime.fromisoformat(str(row[0]).replace("Z", "+00:00")).date()
        except ValueError:
            return datetime.strptime(str(row[0])[:10], "%Y-%m-%d").date()
    return datetime(2015, 1, 1).date()


def ingest_fit_bytes(fit_bytes, filename, conn):
    """Parse FIT bytes and ingest into DB. Returns True if successful."""
    session_data = {}
    records = []
    laps = []

    with fitdecode.FitReader(fit_bytes) as fit:
        for frame in fit:
            if not isinstance(frame, fitdecode.FitDataMessage):
                continue

            if frame.name == "session":
                sport = str(safe_get(frame, "sport", "")).lower()
                if sport not in ("cycling", "6"):
                    return False  # Not cycling

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
                power = safe_get(frame, "power")
                records.append({
                    "timestamp": str(safe_get(frame, "timestamp", "")),
                    "elapsed_seconds": safe_get(frame, "elapsed_time"),
                    "power": power,
                    "heart_rate": safe_get(frame, "heart_rate"),
                    "cadence": safe_get(frame, "cadence"),
                    "speed": safe_get(frame, "enhanced_speed") or safe_get(frame, "speed"),
                    "altitude": safe_get(frame, "enhanced_altitude") or safe_get(frame, "altitude"),
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

    # Check if any records have power data
    has_power = any(r["power"] is not None and r["power"] > 0 for r in records)
    if not has_power:
        return False

    cursor = conn.cursor()
    cols = list(session_data.keys())
    cursor.execute(
        f"INSERT INTO activities ({','.join(cols)}) VALUES ({','.join('?' for _ in cols)})",
        [session_data[c] for c in cols],
    )
    activity_id = cursor.lastrowid

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
    parser = argparse.ArgumentParser(description="Sync Garmin cycling activities to local DB")
    parser.add_argument("--days", type=int, help="Sync last N days")
    parser.add_argument("--from", dest="from_date", help="Sync from date (YYYY-MM-DD)")
    parser.add_argument("--save-fit", action="store_true", help="Also save FIT files to fit-files/")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)

    # Determine start date
    if args.from_date:
        start_date = datetime.strptime(args.from_date, "%Y-%m-%d").date()
    elif args.days:
        start_date = (datetime.now() - timedelta(days=args.days)).date()
    else:
        start_date = get_latest_activity_date(conn)
        print(f"Last activity in DB: {start_date}")

    end_date = datetime.now().date()
    print(f"Syncing activities from {start_date} to {end_date}")

    # Get existing filenames to avoid duplicates
    cursor = conn.cursor()
    cursor.execute("SELECT filename FROM activities")
    existing_filenames = {row[0] for row in cursor.fetchall()}

    # Login and fetch activities
    client = get_garmin_client()
    activities = client.get_activities_by_date(
        startdate=start_date.isoformat(),
        enddate=end_date.isoformat(),
        activitytype="cycling",
    )
    print(f"Found {len(activities)} cycling activities on Garmin Connect")

    synced = 0
    skipped = 0
    no_power = 0

    for act in activities:
        activity_id = act["activityId"]
        activity_name = act.get("activityName", "unknown")
        filename = f"garmin_{activity_id}.fit"

        if filename in existing_filenames:
            skipped += 1
            continue

        try:
            fit_data = client.download_activity(
                activity_id,
                dl_fmt=Garmin.ActivityDownloadFormat.ORIGINAL,
            )

            # fitdecode needs a file-like object
            import io
            fit_io = io.BytesIO(fit_data)

            if ingest_fit_bytes(fit_io, filename, conn):
                synced += 1
                print(f"  + {activity_name} ({act.get('startTimeLocal', '')[:10]})")

                if args.save_fit:
                    os.makedirs(FIT_DIR, exist_ok=True)
                    fit_path = os.path.join(FIT_DIR, filename)
                    with open(fit_path, "wb") as f:
                        f.write(fit_data)
            else:
                no_power += 1

        except Exception as e:
            print(f"  ! Error syncing {activity_name}: {e}")

    print(f"\nDone: {synced} synced, {skipped} already in DB, {no_power} skipped (no power)")

    cursor.execute("SELECT COUNT(*) FROM activities")
    total = cursor.fetchone()[0]
    print(f"Total activities in DB: {total}")

    conn.close()


if __name__ == "__main__":
    main()
