#!/usr/bin/env python3
"""
Sync cycling+power activities from Strava into cycling_power.db.

Uses Strava API v3 with OAuth2. Tokens are saved to ~/.strava_tokens/.

First run:
    1. Create a Strava API app at https://www.strava.com/settings/api
    2. Set "Authorization Callback Domain" to "localhost"
    3. Run this script — it will prompt for client_id and client_secret,
       open a browser for authorization, and save tokens.

Usage:
    python strava_sync.py                    # Sync new since last DB entry
    python strava_sync.py --days 90          # Sync last 90 days
    python strava_sync.py --from 2024-01-01  # Sync from specific date
"""

import argparse
import json
import os
import sqlite3
import sys
import time
import webbrowser
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

import httpx

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "cycling_power.db")
TOKEN_DIR = os.path.expanduser("~/.strava_tokens")
TOKEN_FILE = os.path.join(TOKEN_DIR, "tokens.json")
CREDS_FILE = os.path.join(TOKEN_DIR, "credentials.json")

STRAVA_AUTH_URL = "https://www.strava.com/oauth/authorize"
STRAVA_TOKEN_URL = "https://www.strava.com/oauth/token"
STRAVA_API = "https://www.strava.com/api/v3"
REDIRECT_PORT = 8089
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}/callback"
SCOPES = "activity:read_all"


# ── OAuth2 Flow ─────────────────────────────────────────────

_auth_code = None


class _CallbackHandler(BaseHTTPRequestHandler):
    """Handles the OAuth2 callback from Strava."""
    def do_GET(self):
        global _auth_code
        params = parse_qs(urlparse(self.path).query)
        _auth_code = params.get("code", [None])[0]
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(b"<h2>Authorization complete. You can close this tab.</h2>")

    def log_message(self, *args):
        pass  # Suppress request logging


def _load_credentials():
    """Load or prompt for Strava API credentials."""
    os.makedirs(TOKEN_DIR, exist_ok=True)
    if os.path.exists(CREDS_FILE):
        with open(CREDS_FILE) as f:
            return json.load(f)

    print("Strava API credentials needed.")
    print("Create an app at https://www.strava.com/settings/api")
    print("Set 'Authorization Callback Domain' to: localhost")
    print()
    client_id = input("Client ID: ").strip()
    client_secret = input("Client Secret: ").strip()
    creds = {"client_id": client_id, "client_secret": client_secret}
    with open(CREDS_FILE, "w") as f:
        json.dump(creds, f)
    os.chmod(CREDS_FILE, 0o600)
    print("Credentials saved to ~/.strava_tokens/credentials.json")
    return creds


def _load_tokens():
    """Load saved tokens if they exist."""
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            return json.load(f)
    return None


def _save_tokens(tokens):
    """Save tokens to disk."""
    os.makedirs(TOKEN_DIR, exist_ok=True)
    with open(TOKEN_FILE, "w") as f:
        json.dump(tokens, f)
    os.chmod(TOKEN_FILE, 0o600)


def _authorize(creds):
    """Run the OAuth2 authorization flow with a local callback server."""
    global _auth_code
    _auth_code = None

    auth_url = (
        f"{STRAVA_AUTH_URL}?client_id={creds['client_id']}"
        f"&response_type=code&redirect_uri={REDIRECT_URI}"
        f"&approval_prompt=auto&scope={SCOPES}"
    )

    print("Opening browser for Strava authorization...")
    webbrowser.open(auth_url)

    server = HTTPServer(("localhost", REDIRECT_PORT), _CallbackHandler)
    server.timeout = 120
    print(f"Waiting for callback on localhost:{REDIRECT_PORT}...")
    while _auth_code is None:
        server.handle_request()

    server.server_close()

    resp = httpx.post(STRAVA_TOKEN_URL, data={
        "client_id": creds["client_id"],
        "client_secret": creds["client_secret"],
        "code": _auth_code,
        "grant_type": "authorization_code",
    })
    resp.raise_for_status()
    tokens = resp.json()
    _save_tokens(tokens)
    print("Authorization complete. Tokens saved.")
    return tokens


def _refresh_token(creds, tokens):
    """Refresh an expired access token."""
    resp = httpx.post(STRAVA_TOKEN_URL, data={
        "client_id": creds["client_id"],
        "client_secret": creds["client_secret"],
        "grant_type": "refresh_token",
        "refresh_token": tokens["refresh_token"],
    })
    resp.raise_for_status()
    new_tokens = resp.json()
    _save_tokens(new_tokens)
    return new_tokens


def login():
    """Authenticate with Strava. Returns a valid access token."""
    creds = _load_credentials()
    tokens = _load_tokens()

    if tokens is None:
        tokens = _authorize(creds)
    elif tokens.get("expires_at", 0) < time.time():
        print("Token expired, refreshing...")
        tokens = _refresh_token(creds, tokens)

    return tokens["access_token"]


# ── Strava API Calls ────────────────────────────────────────

def _api_get(path, token, params=None):
    """Make an authenticated GET request to the Strava API."""
    resp = httpx.get(
        f"{STRAVA_API}{path}",
        headers={"Authorization": f"Bearer {token}"},
        params=params or {},
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.json()


def fetch_cycling_activities(token, after_epoch, before_epoch):
    """Fetch all cycling activities in the date range."""
    activities = []
    page = 1
    per_page = 100

    while True:
        batch = _api_get("/athlete/activities", token, {
            "after": after_epoch,
            "before": before_epoch,
            "page": page,
            "per_page": per_page,
        })
        if not batch:
            break

        for act in batch:
            sport = act.get("sport_type", act.get("type", ""))
            if sport.lower() in ("ride", "virtualride", "ebikeride"):
                activities.append(act)

        if len(batch) < per_page:
            break
        page += 1

    return activities


def fetch_streams(token, activity_id):
    """Fetch per-second streams for an activity."""
    keys = "time,watts,heartrate,cadence,velocity_smooth,altitude,latlng,temp,distance"
    try:
        return _api_get(f"/activities/{activity_id}/streams", token, {
            "keys": keys,
            "key_type": "time",
        })
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return []
        raise


def fetch_laps(token, activity_id):
    """Fetch laps for an activity."""
    try:
        return _api_get(f"/activities/{activity_id}/laps", token)
    except httpx.HTTPStatusError:
        return []


# ── DB Ingestion ────────────────────────────────────────────

def _stream_by_type(streams, stream_type):
    """Extract a specific stream from the streams response."""
    for s in streams:
        if s.get("type") == stream_type:
            return s.get("data", [])
    return []


def ingest_activity(act, streams, laps, conn):
    """Ingest a Strava activity + streams into the DB."""
    time_stream = _stream_by_type(streams, "time")
    power_stream = _stream_by_type(streams, "watts")
    hr_stream = _stream_by_type(streams, "heartrate")
    cadence_stream = _stream_by_type(streams, "cadence")
    speed_stream = _stream_by_type(streams, "velocity_smooth")
    altitude_stream = _stream_by_type(streams, "altitude")
    latlng_stream = _stream_by_type(streams, "latlng")
    temp_stream = _stream_by_type(streams, "temp")
    distance_stream = _stream_by_type(streams, "distance")

    has_power = any(w is not None and w > 0 for w in power_stream)
    if not has_power:
        return False

    start_time = act.get("start_date", "")
    filename = f"strava_{act['id']}"

    session_data = {
        "filename": filename,
        "sport": "cycling",
        "sub_sport": act.get("sport_type", ""),
        "start_time": start_time,
        "total_elapsed_time": act.get("elapsed_time"),
        "total_timer_time": act.get("moving_time"),
        "total_distance": act.get("distance"),
        "avg_power": act.get("average_watts"),
        "max_power": act.get("max_watts"),
        "normalized_power": act.get("weighted_average_watts"),
        "avg_heart_rate": act.get("average_heartrate"),
        "max_heart_rate": act.get("max_heartrate"),
        "avg_cadence": act.get("average_cadence"),
        "max_cadence": None,
        "avg_speed": act.get("average_speed"),
        "max_speed": act.get("max_speed"),
        "total_ascent": act.get("total_elevation_gain"),
        "total_descent": None,
        "total_calories": act.get("calories"),
        "avg_temperature": act.get("average_temp"),
        "threshold_power": None,
        "intensity_factor": None,
        "training_stress_score": act.get("suffer_score"),
        "total_work": act.get("kilojoules"),
    }

    cursor = conn.cursor()
    cols = list(session_data.keys())
    cursor.execute(
        f"INSERT INTO activities ({','.join(cols)}) VALUES ({','.join('?' for _ in cols)})",
        [session_data[c] for c in cols],
    )
    activity_id = cursor.lastrowid

    n = len(time_stream)
    start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))

    for i in range(n):
        elapsed = time_stream[i] if i < len(time_stream) else None
        ts = (start_dt + timedelta(seconds=elapsed)).isoformat() if elapsed is not None else None
        latlng = latlng_stream[i] if i < len(latlng_stream) else None
        lat = latlng[0] if latlng else None
        lng = latlng[1] if latlng else None

        cursor.execute(
            "INSERT INTO records (activity_id, timestamp, elapsed_seconds, power, heart_rate, "
            "cadence, speed, altitude, temperature, latitude, longitude, distance) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                activity_id,
                ts,
                elapsed,
                power_stream[i] if i < len(power_stream) else None,
                hr_stream[i] if i < len(hr_stream) else None,
                cadence_stream[i] if i < len(cadence_stream) else None,
                speed_stream[i] if i < len(speed_stream) else None,
                altitude_stream[i] if i < len(altitude_stream) else None,
                temp_stream[i] if i < len(temp_stream) else None,
                lat,
                lng,
                distance_stream[i] if i < len(distance_stream) else None,
            ),
        )

    for j, lap in enumerate(laps):
        cursor.execute(
            "INSERT INTO laps (activity_id, lap_number, start_time, total_elapsed_time, "
            "total_timer_time, total_distance, avg_power, max_power, avg_heart_rate, "
            "max_heart_rate, avg_cadence, avg_speed, total_ascent, total_calories, intensity) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                activity_id,
                j + 1,
                lap.get("start_date", ""),
                lap.get("elapsed_time"),
                lap.get("moving_time"),
                lap.get("distance"),
                lap.get("average_watts"),
                lap.get("max_watts"),
                lap.get("average_heartrate"),
                lap.get("max_heartrate"),
                lap.get("average_cadence"),
                lap.get("average_speed"),
                lap.get("total_elevation_gain"),
                lap.get("calories"),
                "",
            ),
        )

    conn.commit()
    return True


# ── Main ────────────────────────────────────────────────────

def get_latest_activity_date(conn):
    """Get the most recent activity date in the DB."""
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(start_time) FROM activities")
    row = cursor.fetchone()
    if row and row[0]:
        try:
            return datetime.fromisoformat(str(row[0]).replace("Z", "+00:00")).date()
        except ValueError:
            return datetime.strptime(str(row[0])[:10], "%Y-%m-%d").date()
    return datetime(2015, 1, 1).date()


def main():
    parser = argparse.ArgumentParser(description="Sync Strava cycling activities to local DB")
    parser.add_argument("--days", type=int, help="Sync last N days")
    parser.add_argument("--from", dest="from_date", help="Sync from date (YYYY-MM-DD)")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)

    if args.from_date:
        start_date = datetime.strptime(args.from_date, "%Y-%m-%d").date()
    elif args.days:
        start_date = (datetime.now() - timedelta(days=args.days)).date()
    else:
        start_date = get_latest_activity_date(conn)
        print(f"Last activity in DB: {start_date}")

    end_date = datetime.now().date()
    print(f"Syncing activities from {start_date} to {end_date}")

    after_epoch = int(datetime.combine(start_date, datetime.min.time()).timestamp())
    before_epoch = int(datetime.combine(end_date, datetime.max.time()).timestamp())

    cursor = conn.cursor()
    cursor.execute("SELECT filename FROM activities")
    existing = {row[0] for row in cursor.fetchall()}

    token = login()
    activities = fetch_cycling_activities(token, after_epoch, before_epoch)
    print(f"Found {len(activities)} cycling activities on Strava in date range")

    synced = 0
    skipped = 0
    no_power = 0

    for act in activities:
        filename = f"strava_{act['id']}"
        if filename in existing:
            skipped += 1
            continue

        name = act.get("name", "unknown")
        date_str = act.get("start_date_local", "")[:10]

        try:
            streams = fetch_streams(token, act["id"])
            lap_data = fetch_laps(token, act["id"])

            if ingest_activity(act, streams, lap_data, conn):
                synced += 1
                print(f"  + {name} ({date_str})")
            else:
                no_power += 1
        except Exception as e:
            print(f"  ! Error syncing {name}: {e}")

    print(f"\nDone: {synced} synced, {skipped} already in DB, {no_power} skipped (no power)")

    cursor.execute("SELECT COUNT(*) FROM activities")
    total = cursor.fetchone()[0]
    print(f"Total activities in DB: {total}")
    conn.close()


if __name__ == "__main__":
    main()
