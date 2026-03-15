# wko5/ride.py
"""Single ride analysis — summary, interval detection, laps, HR decoupling."""

import logging
import numpy as np
import pandas as pd

from wko5.db import get_connection, get_records, FTP_DEFAULT
from wko5.training_load import compute_np, compute_tss
from wko5.pdcurve import compute_mmp

logger = logging.getLogger(__name__)


def ride_summary(activity_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM activities WHERE id = ?", (activity_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return {}
    columns = [desc[0] for desc in cursor.description]
    act = dict(zip(columns, row))
    conn.close()

    records = get_records(activity_id)
    if records.empty:
        return {}

    power = records["power"].fillna(0)
    np_watts = compute_np(power)
    ftp = act.get("threshold_power") or FTP_DEFAULT
    if not ftp or ftp <= 0:
        ftp = FTP_DEFAULT
    intensity_factor = np_watts / ftp
    duration_s = float(act.get("total_timer_time") or len(records))
    tss = compute_tss(np_watts, duration_s, ftp)
    kj = float(power.sum()) / 1000

    return {
        "activity_id": activity_id,
        "date": act.get("start_time", "")[:10],
        "sub_sport": act.get("sub_sport", ""),
        "duration_s": round(duration_s),
        "duration_min": round(duration_s / 60, 1),
        "distance_km": round(float(act.get("total_distance") or 0) / 1000, 1),
        "avg_power": round(float(power.mean()), 1),
        "np": round(np_watts, 1),
        "max_power": int(power.max()),
        "IF": round(intensity_factor, 2),
        "TSS": round(tss, 1),
        "kJ": round(kj, 1),
        "avg_hr": round(float(records["heart_rate"].dropna().mean()), 1) if records["heart_rate"].notna().any() else None,
        "max_hr": int(records["heart_rate"].max()) if records["heart_rate"].notna().any() else None,
        "avg_cadence": round(float(records["cadence"].dropna().mean()), 1) if records["cadence"].notna().any() else None,
        "elevation_gain": float(act.get("total_ascent") or 0),
        "ftp_used": ftp,
    }


def detect_intervals(activity_id, min_power_pct=0.9, min_duration=30, ftp=None):
    if ftp is None:
        ftp = FTP_DEFAULT
    threshold = ftp * min_power_pct

    records = get_records(activity_id)
    if records.empty:
        return []

    power = records["power"].fillna(0)
    smoothed = power.rolling(window=10, min_periods=1).mean()

    intervals = []
    in_interval = False
    start_idx = 0

    for i, p in enumerate(smoothed):
        if p >= threshold and not in_interval:
            in_interval = True
            start_idx = i
        elif p < threshold and in_interval:
            duration = i - start_idx
            if duration >= min_duration:
                segment = power.iloc[start_idx:i]
                hr_segment = records["heart_rate"].iloc[start_idx:i].dropna()
                cad_segment = records["cadence"].iloc[start_idx:i].dropna()
                intervals.append({
                    "start_idx": start_idx,
                    "end_idx": i,
                    "duration_s": duration,
                    "avg_power": round(float(segment.mean()), 1),
                    "max_power": int(segment.max()),
                    "avg_hr": round(float(hr_segment.mean()), 1) if len(hr_segment) > 0 else None,
                    "avg_cadence": round(float(cad_segment.mean()), 1) if len(cad_segment) > 0 else None,
                })
            in_interval = False

    if in_interval:
        duration = len(smoothed) - start_idx
        if duration >= min_duration:
            segment = power.iloc[start_idx:]
            hr_segment = records["heart_rate"].iloc[start_idx:].dropna()
            cad_segment = records["cadence"].iloc[start_idx:].dropna()
            intervals.append({
                "start_idx": start_idx,
                "end_idx": len(smoothed),
                "duration_s": duration,
                "avg_power": round(float(segment.mean()), 1),
                "max_power": int(segment.max()),
                "avg_hr": round(float(hr_segment.mean()), 1) if len(hr_segment) > 0 else None,
                "avg_cadence": round(float(cad_segment.mean()), 1) if len(cad_segment) > 0 else None,
            })

    return intervals


def lap_analysis(activity_id):
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM laps WHERE activity_id = ? ORDER BY lap_number",
        conn, params=(activity_id,),
    )
    conn.close()
    return df


def hr_decoupling(activity_id):
    records = get_records(activity_id)
    if records.empty:
        return float("nan")

    power = records["power"].fillna(0)
    hr = records["heart_rate"]

    valid = (hr > 0) & hr.notna() & (power > 0)
    if valid.sum() < 60:
        return float("nan")

    power_valid = power[valid].values
    hr_valid = hr[valid].values

    mid = len(power_valid) // 2
    first_half_ratio = power_valid[:mid].mean() / hr_valid[:mid].mean()
    second_half_ratio = power_valid[mid:].mean() / hr_valid[mid:].mean()

    if first_half_ratio == 0:
        return float("nan")

    decoupling = (first_half_ratio - second_half_ratio) / first_half_ratio * 100
    return round(float(decoupling), 2)


def best_efforts(activity_id, durations=None):
    if durations is None:
        durations = [60, 300, 1200]
    records = get_records(activity_id)
    if records.empty:
        return {}
    mmp = compute_mmp(records["power"])
    result = {}
    for d in durations:
        if d <= len(mmp):
            result[d] = round(float(mmp[d - 1]), 1)
        else:
            result[d] = float("nan")
    return result


def power_histogram(activity_id, bin_width=10):
    records = get_records(activity_id)
    if records.empty:
        return pd.DataFrame()
    power = records["power"].fillna(0).values
    max_power = int(power.max())
    bins = range(0, max_power + bin_width, bin_width)
    counts, edges = np.histogram(power, bins=bins)
    return pd.DataFrame({
        "bin_start": edges[:-1].astype(int),
        "bin_end": edges[1:].astype(int),
        "seconds": counts,
    })
