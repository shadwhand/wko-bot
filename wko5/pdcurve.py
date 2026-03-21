"""Power Duration Model — MMP curve, PD model fitting, physiological parameter estimation."""

import logging

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

from wko5.db import get_connection, get_activities, get_records
from wko5.config import get_config

logger = logging.getLogger(__name__)


def compute_mmp(power_series):
    """Compute Mean Max Power array using cumulative sum approach.
    Returns np.ndarray where mmp[d-1] = best average power over d seconds.
    """
    power = power_series.fillna(0).values.astype(float)
    n = len(power)
    if n == 0:
        return np.array([])

    cumsum = np.concatenate([[0], np.cumsum(power)])
    mmp = np.zeros(n)

    for d in range(1, n + 1):
        avgs = (cumsum[d:] - cumsum[:n - d + 1]) / d
        mmp[d - 1] = avgs.max()

    # Enforce non-increasing: MMP[d] should be >= MMP[d+1]
    # (best avg over d seconds >= best avg over d+1 seconds is not always
    # true mathematically, so we enforce it by taking running minimum)
    mmp = np.minimum.accumulate(mmp)

    return mmp


def _ensure_mmp_cache_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS mmp_cache (
            activity_id INTEGER,
            duration_s INTEGER,
            max_avg_power REAL,
            PRIMARY KEY (activity_id, duration_s),
            FOREIGN KEY (activity_id) REFERENCES activities(id)
        )
    """)
    conn.commit()


def get_cached_mmp(activity_id):
    """Get MMP for an activity, using cache if available."""
    conn = get_connection()
    _ensure_mmp_cache_table(conn)

    cursor = conn.cursor()
    cursor.execute(
        "SELECT duration_s, max_avg_power FROM mmp_cache WHERE activity_id = ? ORDER BY duration_s",
        (activity_id,),
    )
    rows = cursor.fetchall()

    if rows:
        conn.close()
        cached = np.array([r[1] for r in rows])
        return np.minimum.accumulate(cached)

    records = get_records(activity_id)
    if records.empty or "power" not in records.columns:
        conn.close()
        return np.array([])

    mmp = compute_mmp(records["power"])

    data = [(activity_id, d + 1, float(mmp[d])) for d in range(len(mmp))]
    conn.executemany(
        "INSERT OR REPLACE INTO mmp_cache (activity_id, duration_s, max_avg_power) VALUES (?, ?, ?)",
        data,
    )
    conn.commit()
    conn.close()
    return mmp


def compute_envelope_mmp(start=None, end=None, days=90, sub_sport=None):
    """Compute envelope MMP across rides in date range."""
    if days and not start:
        end_date = pd.Timestamp.now()
        start = (end_date - pd.Timedelta(days=days)).strftime("%Y-%m-%d")
        end = end_date.strftime("%Y-%m-%d 23:59:59")

    activities = get_activities(start=start, end=end, sub_sport=sub_sport)
    if activities.empty:
        logger.warning("No activities found in date range")
        return np.array([])

    max_len = 0
    mmps = []
    for _, act in activities.iterrows():
        mmp = get_cached_mmp(act["id"])
        if len(mmp) > 0:
            mmps.append(mmp)
            max_len = max(max_len, len(mmp))

    if not mmps:
        return np.array([])

    envelope = np.zeros(max_len)
    for mmp in mmps:
        envelope[:len(mmp)] = np.maximum(envelope[:len(mmp)], mmp)
    return envelope


def rebuild_mmp_cache():
    """Recompute and store MMP for all activities. Returns count processed."""
    conn = get_connection()
    _ensure_mmp_cache_table(conn)
    conn.execute("DELETE FROM mmp_cache")
    conn.commit()
    conn.close()

    activities = get_activities()
    count = 0
    for _, act in activities.iterrows():
        mmp = get_cached_mmp(act["id"])
        if len(mmp) > 0:
            count += 1
        if count % 100 == 0 and count > 0:
            logger.info(f"Cached MMP for {count} activities...")
    logger.info(f"MMP cache rebuilt for {count} activities")
    return count


def _pd_model(t, pmax, tau, frc_kj, t0, mftp):
    """3-component power-duration model.
    P(t) = Pmax * e^(-t/tau) + FRC*1000/(t+t0) + mFTP
    """
    return pmax * np.exp(-t / tau) + frc_kj * 1000 / (t + t0) + mftp


def fit_pd_model(mmp):
    """Fit the 3-component PD model to an MMP array.
    Returns dict with {Pmax, FRC, mFTP, TTE, mVO2max, tau, t0} or None on failure.
    """
    if len(mmp) < 60:
        logger.warning("MMP too short for model fitting (need >= 60s)")
        return None

    max_dur = min(len(mmp), 7200)
    durations = np.arange(5, max_dur + 1, dtype=float)
    powers = mmp[4:max_dur].astype(float)

    if len(durations) != len(powers):
        durations = durations[:len(powers)]

    cfg = get_config()
    p0 = [1200, 15, 20, 5, 280]
    bounds_low = [cfg["pd_pmax_low"], cfg["pd_tau_low"], cfg["pd_frc_low"], cfg["pd_t0_low"], cfg["pd_mftp_low"]]
    bounds_high = [cfg["pd_pmax_high"], cfg["pd_tau_high"], cfg["pd_frc_high"], cfg["pd_t0_high"], cfg["pd_mftp_high"]]

    try:
        popt, _ = curve_fit(
            _pd_model, durations, powers,
            p0=p0, bounds=(bounds_low, bounds_high),
            maxfev=10000,
        )
    except (RuntimeError, ValueError) as e:
        logger.warning(f"PD model fitting failed: {e}")
        return None

    pmax, tau, frc_kj, t0, mftp = popt

    # TTE
    t_range = np.arange(1, max_dur + 1, dtype=float)
    modeled = _pd_model(t_range, *popt)
    above_ftp = np.where(modeled > mftp + 1)[0]
    tte = float(above_ftp[-1] + 1) if len(above_ftp) > 0 else float("nan")

    # mVO2max for trained cyclists
    # Use power at ~5min (300s) from MMP as proxy for VO2max power
    # Convert via gross efficiency (23% for trained cyclists, range 22-25%)
    # Caloric equivalent: 1 L O2 ≈ 20.9 kJ (at RER ~0.9)
    # VO2 (mL/min) = Power(W) * 60 * 1000 / (efficiency * 20900)
    cfg = get_config()
    weight_kg = cfg["weight_kg"]
    if len(mmp) >= 300:
        p_vo2max = float(mmp[299])  # power at 5 min — proxy for VO2max power
    else:
        p_vo2max = mftp * 1.15  # rough estimate: VO2max power ~115% of FTP

    gross_efficiency = 0.23
    vo2max_ml_min = p_vo2max * 60 * 1000 / (gross_efficiency * 20900)
    vo2max_ml_min_kg = vo2max_ml_min / weight_kg

    return {
        "Pmax": round(float(pmax), 1),
        "FRC": round(float(frc_kj), 2),
        "mFTP": round(float(mftp), 1),
        "TTE": round(tte / 60, 1),
        "mVO2max_L_min": round(vo2max_ml_min / 1000, 2),
        "mVO2max_ml_min_kg": round(vo2max_ml_min_kg, 1),
        "tau": round(float(tau), 1),
        "t0": round(float(t0), 1),
    }


def power_at_durations(mmp, durations=None):
    """Extract power at specific durations from MMP array."""
    if durations is None:
        durations = [5, 60, 300, 1200, 3600]
    result = {}
    for d in durations:
        if d <= len(mmp):
            result[d] = float(mmp[d - 1])
        else:
            result[d] = float("nan")
    return result


def rolling_ftp(window_days=90, step_days=7):
    """Compute rolling modeled FTP over training history."""
    activities = get_activities()
    if activities.empty:
        return pd.DataFrame()

    activities["start_time"] = pd.to_datetime(activities["start_time"], format="ISO8601", utc=True)
    min_date = activities["start_time"].min()
    max_date = activities["start_time"].max()

    results = []
    current = min_date + pd.Timedelta(days=window_days)
    while current <= max_date:
        start = (current - pd.Timedelta(days=window_days)).strftime("%Y-%m-%d")
        end = current.strftime("%Y-%m-%d 23:59:59")
        mmp = compute_envelope_mmp(start=start, end=end)
        if len(mmp) >= 60:
            model = fit_pd_model(mmp)
            if model:
                results.append({
                    "date": current.strftime("%Y-%m-%d"),
                    "mFTP": model["mFTP"],
                    "Pmax": model["Pmax"],
                    "FRC": model["FRC"],
                    "TTE_min": model["TTE"],
                })
        current += pd.Timedelta(days=step_days)
    return pd.DataFrame(results)


def compare_periods(period1, period2):
    """Compare PD curves between two periods."""
    mmp1 = compute_envelope_mmp(start=period1[0], end=period1[1])
    mmp2 = compute_envelope_mmp(start=period2[0], end=period2[1])
    model1 = fit_pd_model(mmp1) if len(mmp1) >= 60 else None
    model2 = fit_pd_model(mmp2) if len(mmp2) >= 60 else None
    return {
        "period1": {"mmp": mmp1, "model": model1, "range": period1},
        "period2": {"mmp": mmp2, "model": model2, "range": period2},
    }
