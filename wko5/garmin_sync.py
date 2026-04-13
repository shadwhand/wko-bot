#!/usr/bin/env python3
"""
Sync new cycling+power activities from Garmin Connect into cycling_power.db.

Uses garth for authentication (OAuth tokens with auto-refresh, saved to ~/.garth/).

Usage:
    python garmin_sync.py                    # Sync new activities since last DB entry
    python garmin_sync.py --days 30          # Sync last 30 days
    python garmin_sync.py --from 2024-01-01  # Sync from specific date
    python garmin_sync.py --save-fit         # Also save FIT files to fit-files/
"""

import argparse
import io
import os
import duckdb
from datetime import datetime, timedelta
from getpass import getpass

import fitdecode
import garth

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "cycling_power.duckdb")
FIT_DIR = os.path.join(SCRIPT_DIR, "..", "fit-files")
GARTH_DIR = os.path.expanduser("~/.garth")


def safe_get(msg, field, default=None):
    try:
        val = msg.get_value(field)
        return val if val is not None else default
    except (KeyError, TypeError):
        return default


def login():
    """Login to Garmin Connect via garth. Tokens auto-refresh and persist to ~/.garth/."""
    try:
        garth.resume(GARTH_DIR)
        print("Logged in with saved session.")
    except Exception:
        email = input("Garmin email: ")
        password = getpass("Garmin password: ")
        garth.login(email, password)
        garth.save(GARTH_DIR)
        print("Logged in and saved session.")


def get_latest_activity_date(conn):
    """Get the most recent activity date in the DB."""
    row = conn.execute("SELECT MAX(start_time) FROM activities").fetchone()
    if row and row[0]:
        try:
            return datetime.fromisoformat(str(row[0]).replace("Z", "+00:00")).date()
        except ValueError:
            return datetime.strptime(str(row[0])[:10], "%Y-%m-%d").date()
    return datetime(2015, 1, 1).date()


def fetch_cycling_activities(start_date, end_date):
    """Fetch cycling activities from Garmin Connect via garth."""
    activities = []
    start = 0
    limit = 100

    while True:
        batch = garth.Activity.list(limit=limit, start=start)
        if not batch:
            break

        for act in batch:
            # Filter by date
            act_date_str = act.start_time_local or act.start_time_gmt
            if act_date_str:
                try:
                    act_date = datetime.fromisoformat(str(act_date_str).replace("Z", "+00:00")).date()
                except (ValueError, TypeError):
                    continue
                if act_date < start_date:
                    # Activities are ordered newest first, so we can stop
                    return activities
                if act_date > end_date:
                    continue

            activities.append(act)

        if len(batch) < limit:
            break
        start += limit

    return activities


def download_fit(activity_id):
    """Download the original FIT file for an activity."""
    return garth.client.download(f"/download-service/files/activity/{activity_id}")


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
                    return False

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

    has_power = any(r["power"] is not None and r["power"] > 0 for r in records)
    if not has_power:
        return False

    conn.begin()
    cols = list(session_data.keys())
    activity_id = conn.execute(
        f"INSERT INTO activities ({','.join(cols)}) VALUES ({','.join('?' for _ in cols)}) RETURNING rowid",
        [session_data[c] for c in cols],
    ).fetchone()[0]

    for r in records:
        conn.execute(
            "INSERT INTO records (activity_id, timestamp, elapsed_seconds, power, heart_rate, "
            "cadence, speed, altitude, temperature, latitude, longitude, distance) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (activity_id, r["timestamp"], r["elapsed_seconds"], r["power"], r["heart_rate"],
             r["cadence"], r["speed"], r["altitude"], r["temperature"], r["latitude"],
             r["longitude"], r["distance"]),
        )

    for lap in laps:
        conn.execute(
            "INSERT INTO laps (activity_id, lap_number, start_time, total_elapsed_time, "
            "total_timer_time, total_distance, avg_power, max_power, avg_heart_rate, "
            "max_heart_rate, avg_cadence, avg_speed, total_ascent, total_calories, intensity) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (activity_id, lap["lap_number"], lap["start_time"], lap["total_elapsed_time"],
             lap["total_timer_time"], lap["total_distance"], lap["avg_power"], lap["max_power"],
             lap["avg_heart_rate"], lap["max_heart_rate"], lap["avg_cadence"], lap["avg_speed"],
             lap["total_ascent"], lap["total_calories"], lap["intensity"]),
        )

    conn.commit()
    return True


def main():
    parser = argparse.ArgumentParser(description="Sync Garmin cycling activities to local DB")
    parser.add_argument("--days", type=int, help="Sync last N days")
    parser.add_argument("--from", dest="from_date", help="Sync from date (YYYY-MM-DD)")
    parser.add_argument("--save-fit", action="store_true", help="Also save FIT files to fit-files/")
    args = parser.parse_args()

    conn = duckdb.connect(DB_PATH)

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
    existing_filenames = {row[0] for row in conn.execute("SELECT filename FROM activities").fetchall()}

    # Login and fetch activities
    login()
    activities = fetch_cycling_activities(start_date, end_date)
    print(f"Found {len(activities)} activities on Garmin Connect in date range")

    synced = 0
    skipped = 0
    no_power = 0

    for act in activities:
        # Get activity ID from the summary dict
        summary = act.summary or {}
        activity_id = summary.get("activityId")
        activity_name = summary.get("activityName", "unknown")

        if not activity_id:
            continue

        filename = f"garmin_{activity_id}.fit"

        if filename in existing_filenames:
            skipped += 1
            continue

        try:
            fit_data = download_fit(activity_id)
            fit_io = io.BytesIO(fit_data)

            if ingest_fit_bytes(fit_io, filename, conn):
                synced += 1
                date_str = str(act.start_time_local or "")[:10]
                print(f"  + {activity_name} ({date_str})")

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

    total = conn.execute("SELECT COUNT(*) FROM activities").fetchone()[0]
    print(f"Total activities in DB: {total}")

    conn.close()


if __name__ == "__main__":
    main()
