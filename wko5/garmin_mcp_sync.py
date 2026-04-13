#!/usr/bin/env python3
"""
Sync Garmin Connect activities into cycling_power.db via Playwright browser.

Routes API calls through a headless Chrome to bypass Cloudflare TLS fingerprinting.
Reads session cookies from ~/.garmin-connect-mcp/session.json (created by MCP login).

Usage:
    python3 wko5/garmin_mcp_sync.py              # sync new since last DB entry
    python3 wko5/garmin_mcp_sync.py --days 30     # sync last 30 days
    python3 wko5/garmin_mcp_sync.py --dry-run     # show what would sync
"""

import argparse
import base64
import io
import json
import os
import duckdb
import sys
import zipfile
from datetime import datetime, timedelta, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "cycling_power.duckdb")
SESSION_PATH = os.path.expanduser("~/.garmin-connect-mcp/session.json")

import fitdecode

sys.path.insert(0, SCRIPT_DIR)
from garmin_sync import get_latest_activity_date, safe_get


def load_session():
    if not os.path.exists(SESSION_PATH):
        print(f"No session at {SESSION_PATH}. Run garmin-login via MCP first.", file=sys.stderr)
        sys.exit(1)
    with open(SESSION_PATH) as f:
        return json.load(f)


class GarminBrowserClient:
    """API client that fetches through headless Chrome, same approach as garmin-connect-mcp."""

    def __init__(self, session):
        self.csrf_token = session["csrf_token"]
        self.cookies = session["cookies"]
        self.page = None
        self.browser = None

    def start(self):
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start()
        self.browser = self._pw.chromium.launch(headless=True)
        context = self.browser.new_context()
        context.add_cookies([
            {"name": c["name"], "value": c["value"], "domain": c["domain"], "path": "/"}
            for c in self.cookies
        ])
        self.page = context.new_page()
        self.page.goto(
            "https://connect.garmin.com/site-status/garmin-connect-status.json",
            wait_until="domcontentloaded", timeout=30000
        )

    def stop(self):
        if self.browser:
            self.browser.close()
        if self._pw:
            self._pw.stop()

    def get_json(self, path, params=None):
        url = f"/gc-api/{path}"
        if params:
            qs = "&".join(f"{k}={v}" for k, v in params.items())
            url += f"?{qs}"
        csrf = self.csrf_token
        result = self.page.evaluate("""
            async ({url, csrf}) => {
                const resp = await fetch(url, {
                    headers: { "connect-csrf-token": csrf, "Accept": "*/*" }
                });
                return { status: resp.status, body: await resp.text() };
            }
        """, {"url": url, "csrf": csrf})
        if result["status"] == 401:
            raise RuntimeError("Session expired. Re-login via MCP Playwright.")
        if result["status"] != 200:
            raise RuntimeError(f"Garmin API {result['status']}: {path}")
        return json.loads(result["body"])

    def get_bytes(self, path):
        url = f"/gc-api/{path}"
        csrf = self.csrf_token
        result = self.page.evaluate("""
            async ({url, csrf}) => {
                const resp = await fetch(url, {
                    headers: { "connect-csrf-token": csrf, "Accept": "*/*" }
                });
                if (!resp.ok) return { status: resp.status, data: null };
                const buf = await resp.arrayBuffer();
                const bytes = new Uint8Array(buf);
                let binary = "";
                for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i]);
                return { status: resp.status, data: btoa(binary) };
            }
        """, {"url": url, "csrf": csrf})
        if result["status"] != 200 or not result["data"]:
            raise RuntimeError(f"Garmin API {result['status']}: {path}")
        return base64.b64decode(result["data"])


def ingest_fit_parquet(fit_io, filename, conn):
    """Parse FIT, insert activity+laps+records into DuckDB."""
    session_data = {}
    records = []
    laps = []

    with fitdecode.FitReader(fit_io) as fit:
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
    has_power = any(r.get("power") is not None and r["power"] > 0 for r in records)
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
            "INSERT INTO records (activity_id, timestamp, power, heart_rate, "
            "cadence, speed, altitude, temperature, latitude, longitude, distance) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (activity_id, r["timestamp"], r["power"], r["heart_rate"],
             r["cadence"], r["speed"], r["altitude"], r["temperature"],
             r["latitude"], r["longitude"], r["distance"]),
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


def list_activities(client, start_date):
    activities = []
    offset = 0
    limit = 100
    while True:
        batch = client.get_json(
            "activitylist-service/activities/search/activities",
            {"start": offset, "limit": limit}
        )
        if not batch:
            break
        for act in batch:
            date_str = act.get("startTimeLocal", "")[:10]
            if date_str and date_str < str(start_date):
                return activities
            activities.append(act)
        if len(batch) < limit:
            break
        offset += limit
    return activities


def main():
    ap = argparse.ArgumentParser(description="Sync Garmin → cycling_power.db via browser")
    ap.add_argument("--days", type=int, help="Sync last N days")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    session = load_session()
    conn = duckdb.connect(DB_PATH)

    if args.days:
        start_date = (datetime.now(timezone.utc) - timedelta(days=args.days)).date()
    else:
        start_date = get_latest_activity_date(conn) - timedelta(days=1)

    print(f"Starting browser...")
    client = GarminBrowserClient(session)
    client.start()

    print(f"Fetching activities since {start_date}...")
    activities = list_activities(client, start_date)
    print(f"Found {len(activities)} activities on Garmin")

    # Filter to new only
    existing = {row[0] for row in conn.execute("SELECT filename FROM activities").fetchall()}

    new_acts = [a for a in activities if f"{a['activityId']}.fit" not in existing]
    print(f"{len(new_acts)} new (not in DB)")

    if args.dry_run:
        for a in new_acts:
            print(f"  {a['activityId']}  {a.get('startTimeLocal','?')[:10]}  {a.get('activityName','?')}")
        client.stop()
        conn.close()
        return

    synced = 0
    for i, act in enumerate(new_acts, 1):
        aid = act["activityId"]
        name = act.get("activityName", "?")
        date = act.get("startTimeLocal", "?")[:10]
        print(f"  [{i}/{len(new_acts)}] {date} {name}...", end=" ", flush=True)
        try:
            raw_bytes = client.get_bytes(f"download-service/files/activity/{aid}")
            # Garmin wraps FIT in ZIP
            if raw_bytes[:2] == b'PK':
                with zipfile.ZipFile(io.BytesIO(raw_bytes)) as zf:
                    fit_name = [n for n in zf.namelist() if n.endswith('.fit')][0]
                    fit_bytes = zf.read(fit_name)
            else:
                fit_bytes = raw_bytes
            ok = ingest_fit_parquet(io.BytesIO(fit_bytes), f"{aid}.fit", conn)
            if ok:
                print("ok")
                synced += 1
            else:
                print("skip (not cycling/no power)")
        except Exception as e:
            print(f"err: {e}")

    client.stop()
    conn.close()
    print(f"\nDone. Synced {synced}/{len(new_acts)}.")


if __name__ == "__main__":
    main()
