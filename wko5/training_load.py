"""Training load — NP, TSS, IF, CTL/ATL/TSB (PMC), efficiency factor."""

import logging

import numpy as np
import pandas as pd

from wko5.db import get_connection, get_activities, get_records
from wko5.config import get_config

logger = logging.getLogger(__name__)


def compute_np(power_series):
    """Compute Normalized Power. 30s rolling avg -> 4th power -> mean -> 4th root."""
    power = power_series.fillna(0).values.astype(float)
    n = len(power)
    if n == 0:
        return float("nan")
    window = min(30, n)
    rolling_avg = pd.Series(power).rolling(window=window, min_periods=1).mean().values
    np_val = (np.mean(rolling_avg ** 4)) ** 0.25
    return float(np_val)


def compute_tss(np_watts, duration_s, ftp):
    """TSS = (duration_s * NP^2) / (FTP^2 * 3600) * 100"""
    if ftp <= 0 or duration_s <= 0 or np.isnan(np_watts):
        return float("nan")
    return (duration_s * np_watts ** 2) / (ftp ** 2 * 3600) * 100


def _get_activity_tss(activity_row, ftp=None):
    """Get TSS for an activity, using device value or computing from records."""
    device_tss = activity_row.get("training_stress_score")
    if device_tss and not pd.isna(device_tss) and device_tss > 0:
        return float(device_tss)

    if ftp is None:
        device_ftp = activity_row.get("threshold_power")
        if device_ftp and not pd.isna(device_ftp) and device_ftp > 0:
            ftp = float(device_ftp)
        else:
            ftp = get_config()["ftp_manual"]

    records = get_records(activity_row["id"])
    if records.empty or "power" not in records.columns:
        return 0.0

    np_watts = compute_np(records["power"])
    duration_s = float(activity_row.get("total_timer_time") or len(records))
    return compute_tss(np_watts, duration_s, ftp)


def _ensure_tss_cache_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tss_cache (
            activity_id INTEGER PRIMARY KEY,
            np_watts REAL,
            tss REAL,
            ftp_used REAL,
            FOREIGN KEY (activity_id) REFERENCES activities(id)
        )
    """)
    conn.commit()


def _get_cached_tss(activity_id, activity_row, ftp=None):
    """Get TSS from cache, or compute and cache it."""
    conn = get_connection()
    _ensure_tss_cache_table(conn)

    cursor = conn.cursor()
    cursor.execute("SELECT tss FROM tss_cache WHERE activity_id = ?", (activity_id,))
    row = cursor.fetchone()
    if row:
        conn.close()
        return float(row[0])

    tss = _get_activity_tss(activity_row, ftp=ftp)

    ftp_used = ftp or get_config()["ftp_manual"]
    conn.execute(
        "INSERT OR REPLACE INTO tss_cache (activity_id, np_watts, tss, ftp_used) VALUES (?, ?, ?, ?)",
        (activity_id, float("nan"), tss, ftp_used),
    )
    conn.commit()
    conn.close()
    return tss


def build_pmc(start=None, end=None, ftp=None):
    """Build Performance Management Chart (CTL/ATL/TSB). Uses TSS cache."""
    activities = get_activities(start=start, end=end)
    if activities.empty:
        return pd.DataFrame()

    activities["date"] = pd.to_datetime(activities["start_time"], format="ISO8601", utc=True).dt.date

    tss_list = []
    for _, act in activities.iterrows():
        tss = _get_cached_tss(act["id"], act, ftp=ftp)
        tss_list.append({"date": act["date"], "tss": tss})

    tss_df = pd.DataFrame(tss_list)
    daily_tss = tss_df.groupby("date")["tss"].sum().reset_index()
    daily_tss.columns = ["date", "TSS"]
    daily_tss["date"] = pd.to_datetime(daily_tss["date"])

    full_range = pd.date_range(daily_tss["date"].min(), daily_tss["date"].max())
    daily = pd.DataFrame({"date": full_range})
    daily = daily.merge(daily_tss, on="date", how="left").fillna(0)

    cfg = get_config()
    ctl_decay = 1 - np.exp(-1 / cfg["ctl_time_constant"])
    atl_decay = 1 - np.exp(-1 / cfg["atl_time_constant"])

    daily["CTL"] = daily["TSS"].ewm(alpha=ctl_decay, adjust=False).mean()
    daily["ATL"] = daily["TSS"].ewm(alpha=atl_decay, adjust=False).mean()
    daily["TSB"] = daily["CTL"] - daily["ATL"]

    return daily


def current_fitness(ftp=None):
    """Get latest CTL, ATL, TSB snapshot."""
    pmc = build_pmc(ftp=ftp)
    if pmc.empty:
        return {"CTL": 0, "ATL": 0, "TSB": 0}
    last = pmc.iloc[-1]
    return {
        "CTL": round(float(last["CTL"]), 1),
        "ATL": round(float(last["ATL"]), 1),
        "TSB": round(float(last["TSB"]), 1),
        "date": str(last["date"].date()),
    }


def fitness_trend(days=365, ftp=None):
    """Get CTL trajectory over recent days."""
    start = (pd.Timestamp.now() - pd.Timedelta(days=days)).strftime("%Y-%m-%d")
    return build_pmc(start=start, ftp=ftp)


def efficiency_factor(activity_id):
    """Compute Efficiency Factor (NP / avg HR) for an activity."""
    records = get_records(activity_id)
    if records.empty:
        return float("nan")
    np_watts = compute_np(records["power"])
    hr = records["heart_rate"].dropna()
    hr = hr[hr > 0]
    if hr.empty:
        return float("nan")
    avg_hr = hr.mean()
    return round(float(np_watts / avg_hr), 3)


def ef_trend(days=365):
    """Track Efficiency Factor over time."""
    start = (pd.Timestamp.now() - pd.Timedelta(days=days)).strftime("%Y-%m-%d")
    activities = get_activities(start=start)
    results = []
    for _, act in activities.iterrows():
        ef = efficiency_factor(act["id"])
        if not np.isnan(ef):
            results.append({
                "date": act["start_time"][:10],
                "EF": ef,
                "activity_id": act["id"],
            })
    return pd.DataFrame(results)
