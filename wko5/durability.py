# wko5/durability.py
"""Empirical durability model — degradation fitting, fatigued PD curves, FRC budget."""

import logging

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

from wko5.config import get_config
from wko5.db import get_connection, get_activities, get_records
from wko5.pdcurve import compute_mmp
from wko5.training_load import compute_np, compute_tss

logger = logging.getLogger(__name__)


def degradation_factor(cumulative_kj, elapsed_hours, params):
    """Compute the degradation factor at a given point in a ride.

    Model: df = a * exp(-b * kJ/1000) + (1-a) * exp(-c * hours)

    Returns: float between 0 and 1 (1 = fresh, 0 = fully degraded)
    """
    a = params["a"]
    b = params["b"]
    c = params["c"]

    kj_term = a * np.exp(-b * cumulative_kj / 1000)
    time_term = (1 - a) * np.exp(-c * elapsed_hours)

    return float(max(0, kj_term + time_term))


def effective_capacity(fresh_mmp, cumulative_kj, elapsed_hours, params):
    """Compute the fatigued PD curve at a given point in a ride.

    effective_capacity = fresh_mmp * degradation_factor
    """
    df = degradation_factor(cumulative_kj, elapsed_hours, params)
    return fresh_mmp * df


def compute_windowed_mmp(power_series, window_hours=2):
    """Compute MMP at specific durations in rolling time windows across a ride.

    Uses vectorized rolling max at 4 target durations instead of full O(n^2) MMP.
    Returns list of dicts per window.
    """
    DURATIONS = [60, 300, 2400, 3600]  # 1min, 5min, 40min, 1hr

    window_s = int(window_hours * 3600)
    n = len(power_series)

    if n < window_s:
        return []

    power = power_series.fillna(0).values.astype(float)
    cumsum = np.concatenate([[0], np.cumsum(power)])

    # Pre-compute cumulative TSS: sum(power_i^2) / FTP / 3600
    cfg = get_config()
    ftp = cfg["ftp_manual"]
    cum_tss = np.cumsum(power ** 2) / (ftp * 3600) if ftp > 0 else np.cumsum(power) / 1000

    results = []

    # Non-overlapping windows
    for start in range(0, n - window_s + 1, window_s):
        end = start + window_s
        window_power = power[start:end]

        # Cumulative work and TSS from ride start to window midpoint
        midpoint = start + window_s // 2
        cum_kj = float(cumsum[midpoint]) / 1000
        elapsed_h = midpoint / 3600
        cum_tss_val = float(cum_tss[midpoint - 1]) if midpoint > 0 else 0.0

        entry = {
            "window_start_h": round(start / 3600, 2),
            "window_end_h": round(end / 3600, 2),
            "elapsed_hours": round(elapsed_h, 2),
            "cumulative_kj": round(cum_kj, 1),
            "cumulative_tss": round(cum_tss_val, 1),
        }

        # Compute MMP at specific durations via rolling mean max (vectorized)
        window_cumsum = np.concatenate([[0], np.cumsum(window_power)])
        for d in DURATIONS:
            label = f"mmp_{d}s"
            if d <= len(window_power):
                rolling_avg = (window_cumsum[d:] - window_cumsum[:len(window_power) - d + 1]) / d
                entry[label] = round(float(rolling_avg.max()), 1)
            else:
                entry[label] = float("nan")

        results.append(entry)

    return results


def _decay_model(x, a, b, c):
    """Decay function for curve fitting. x = (cumulative_tss, elapsed_hours)."""
    tss, hours = x
    return a * np.exp(-b * tss / 1000) + (1 - a) * np.exp(-c * hours)


def fit_durability_model(min_ride_hours=2, min_rides=5):
    """Fit the durability degradation model from historical long rides.

    Returns dict with fitted params {a, b, c, rides_used, rmse} or None if insufficient data.
    """
    activities = get_activities()
    long_rides = activities[activities["total_timer_time"] > min_ride_hours * 3600]

    if len(long_rides) < min_rides:
        logger.warning(f"Only {len(long_rides)} rides > {min_ride_hours}h, need {min_rides}")
        return None

    all_x_kj = []
    all_x_hours = []
    all_y_ratio = []
    rides_used = 0

    for _, ride in long_rides.iterrows():
        records = get_records(ride["id"])
        if records.empty or "power" not in records.columns:
            continue

        windows = compute_windowed_mmp(records["power"], window_hours=2)
        if len(windows) < 2:
            continue

        # Use 300s (5-min) power as the reference
        first_window_power = windows[0].get("mmp_300s")
        if first_window_power is None or first_window_power <= 0 or np.isnan(first_window_power):
            continue

        for w in windows[1:]:
            wp = w.get("mmp_300s")
            if wp is None or wp <= 0 or np.isnan(wp):
                continue

            ratio = wp / first_window_power
            if ratio > 1.2:
                continue

            all_x_kj.append(w["cumulative_tss"])
            all_x_hours.append(w["elapsed_hours"])
            all_y_ratio.append(ratio)

        rides_used += 1

        if rides_used % 20 == 0:
            logger.info(f"Processed {rides_used} rides...")

    if len(all_y_ratio) < 10:
        logger.warning(f"Only {len(all_y_ratio)} data points, need at least 10")
        return None

    x_data = np.array([all_x_kj, all_x_hours])
    y_data = np.array(all_y_ratio)

    try:
        popt, _ = curve_fit(
            _decay_model, x_data, y_data,
            p0=[0.5, 0.001, 0.05],
            bounds=([0.01, 0.0001, 0.001], [0.99, 0.01, 0.5]),
            maxfev=10000,
        )
    except (RuntimeError, ValueError) as e:
        logger.warning(f"Durability model fitting failed: {e}")
        return None

    a, b, c = popt
    y_pred = _decay_model(x_data, a, b, c)
    rmse = float(np.sqrt(np.mean((y_data - y_pred) ** 2)))

    return {
        "a": round(float(a), 4),
        "b": round(float(b), 6),
        "c": round(float(c), 4),
        "rides_used": rides_used,
        "data_points": len(all_y_ratio),
        "rmse": round(rmse, 4),
    }


def frc_budget_simulate(segments, mftp, frc_kj, initial_depletion_count=0):
    """Simulate FRC budget across sequential segments.

    FRC depletes above mFTP, recharges below. Recovery ceiling degrades
    with successive deep depletions.
    """
    frc_remaining = frc_kj
    depletion_count = initial_depletion_count
    results = []

    for seg in segments:
        power = seg.get("avg_power", 0) or 0
        duration_s = seg.get("duration_s", 0) or 0

        if power > mftp:
            cost_kj = (power - mftp) * duration_s / 1000
            frc_remaining = max(0, frc_remaining - cost_kj)

            if cost_kj > frc_kj * 0.5:
                depletion_count += 1
        else:
            recovery_rate = 0.5
            recovery_kj = recovery_rate * (mftp - power) * duration_s / 1000

            recovery_ceiling = max(0.5, 1.0 - depletion_count * 0.1)
            max_frc = frc_kj * recovery_ceiling

            frc_remaining = min(frc_remaining + recovery_kj, max_frc)

        results.append({
            "frc_remaining": round(frc_remaining, 2),
            "frc_pct": round(frc_remaining / frc_kj * 100, 1) if frc_kj > 0 else 0,
            "depletion_count": depletion_count,
            "recovery_ceiling": round(max(0.5, 1.0 - depletion_count * 0.1), 2),
        })

    return results


def repeatability_index(activity_id, duration_s=300):
    """Compute repeatability index: ratio of 3rd-best to 1st-best effort at a duration."""
    records = get_records(activity_id)
    if records.empty or "power" not in records.columns:
        return None

    power = records["power"].fillna(0).values.astype(float)
    n = len(power)

    if n < duration_s * 3:
        return None

    cumsum = np.concatenate([[0], np.cumsum(power)])
    rolling_avg = (cumsum[duration_s:] - cumsum[:n - duration_s + 1]) / duration_s

    efforts = []
    used_indices = set()

    sorted_indices = np.argsort(rolling_avg)[::-1]

    for idx in sorted_indices:
        overlap = False
        for used_start in used_indices:
            if abs(idx - used_start) < duration_s:
                overlap = True
                break

        if not overlap:
            efforts.append(float(rolling_avg[idx]))
            used_indices.add(idx)

        if len(efforts) >= 3:
            break

    if len(efforts) < 3 or efforts[0] <= 0:
        return None

    return round(efforts[2] / efforts[0], 3)
