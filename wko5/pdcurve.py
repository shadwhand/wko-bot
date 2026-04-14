"""Power Duration Model — MMP curve, PD model fitting, physiological parameter estimation."""

import logging
import os

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
            PRIMARY KEY (activity_id, duration_s)
        )
    """)
    conn.commit()


MMP_CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mmp_cache")


def get_cached_mmp(activity_id):
    """Get MMP for an activity, using Parquet cache if available, then SQLite, then compute."""
    import pandas as pd

    # Try Parquet cache first
    parquet_path = os.path.join(MMP_CACHE_DIR, f"{activity_id}.parquet")
    if os.path.exists(parquet_path):
        try:
            df = pd.read_parquet(parquet_path)
            if not df.empty:
                cached = np.array(df["max_avg_power"].values, dtype=float)
                return np.minimum.accumulate(cached)
        except Exception:
            pass

    # Try SQLite cache
    conn = get_connection()
    _ensure_mmp_cache_table(conn)
    result = conn.execute(
        "SELECT duration_s, max_avg_power FROM mmp_cache WHERE activity_id = ? ORDER BY duration_s",
        [activity_id],
    )
    rows = result.fetchall()

    if rows:
        conn.close()
        cached = np.array([r[1] for r in rows])
        return np.minimum.accumulate(cached)

    # Compute and cache to Parquet
    records = get_records(activity_id)
    if records.empty or "power" not in records.columns:
        conn.close()
        return np.array([])

    mmp = compute_mmp(records["power"])

    # Save to Parquet cache
    os.makedirs(MMP_CACHE_DIR, exist_ok=True)
    cache_df = pd.DataFrame({
        "duration_s": np.arange(1, len(mmp) + 1, dtype=np.int32),
        "max_avg_power": mmp.astype(np.float32),
    })
    cache_df.to_parquet(parquet_path, engine="pyarrow", compression="zstd", index=False)

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


def _pd_model(t, frc_kj, mftp, tau, tau2, tte, a):
    """Peronnet-Thibault / WKO4 power-duration model.

    Based on veloclinic.com analysis showing WKO4/5 uses a modified Peronnet &
    Thibault (1989) model, itself an extension of Ward-Smith → LLoyd → Hill.

    For t <= TTE:
        P(t) = FRC*1000/t * (1-exp(-t/tau)) + mFTP * (1-exp(-t/tau2))
    For t > TTE:
        P(t) = FRC*1000/t * (1-exp(-t/tau)) + mFTP * (1-exp(-t/tau2)) - a*ln(t/TTE)

    Parameters:
        frc_kj: Functional Reserve Capacity (kJ) — anaerobic work capacity above FTP
        mftp:   modeled Functional Threshold Power (W) — maximal aerobic power (MAP)
        tau:    time constant for anaerobic onset (s) — ≈ FRC*1000/Pmax
        tau2:   time constant for aerobic onset (s) — how fast aerobic system ramps up
        tte:    Time to Exhaustion at FTP (s) — longest duration mFTP can be sustained
        a:      slope of log-linear decline after TTE (W per ln(s))

    Derived:
        Pmax ≈ FRC*1000 / tau (instantaneous max power)
    """
    anaerobic = frc_kj * 1000 / t * (1 - np.exp(-t / tau))
    aerobic = mftp * (1 - np.exp(-t / tau2))

    # Post-TTE log-linear decline
    decline = np.where(t > tte, a * np.log(t / tte), 0.0)

    return anaerobic + aerobic - decline


def _pd_model_legacy(t, pmax, tau, frc_kj, t0, mftp):
    """Legacy 3-component additive model (pre-P&T update). Kept for reference.
    P(t) = Pmax * e^(-t/tau) + FRC*1000/(t+t0) + mFTP
    """
    return pmax * np.exp(-t / tau) + frc_kj * 1000 / (t + t0) + mftp


def fit_pd_model(mmp):
    """Fit the Peronnet-Thibault / WKO4 PD model to an MMP array.

    Returns dict with {Pmax, FRC, mFTP, TTE, mVO2max, tau, tau2, a} or None on failure.
    """
    if len(mmp) < 60:
        logger.warning("MMP too short for model fitting (need >= 60s)")
        return None

    max_dur = min(len(mmp), 28800)  # up to 8 hours — P&T model handles long durations
    durations = np.arange(5, max_dur + 1, dtype=float)
    powers = mmp[4:max_dur].astype(float)

    if len(durations) != len(powers):
        durations = durations[:len(powers)]

    cfg = get_config()

    # Parameters: frc_kj, mftp, tau, tau2, tte, a
    # Initial guesses
    p0 = [20, 280, 15, 20, 2400, 20]

    # Bounds
    bounds_low = [
        cfg["pd_frc_low"],     # frc_kj
        cfg["pd_mftp_low"],    # mftp
        cfg["pd_tau_low"],     # tau (anaerobic onset)
        5,                      # tau2 (aerobic onset) — at least 5s
        600,                    # tte — at least 10 min
        1,                      # a — decline slope, at least 1
    ]
    bounds_high = [
        cfg["pd_frc_high"],    # frc_kj
        cfg["pd_mftp_high"],   # mftp
        cfg["pd_tau_high"],    # tau
        120,                    # tau2 — up to 120s
        5400,                   # tte — up to 90 min
        100,                    # a — decline slope
    ]

    try:
        popt, _ = curve_fit(
            _pd_model, durations, powers,
            p0=p0, bounds=(bounds_low, bounds_high),
            maxfev=20000,
        )
    except (RuntimeError, ValueError) as e:
        logger.warning(f"PD model fitting failed: {e}")
        return None

    frc_kj, mftp, tau, tau2, tte, a = popt

    # Derived: Pmax ≈ FRC*1000 / tau
    pmax = frc_kj * 1000 / tau

    # mVO2max estimation
    cfg = get_config()
    weight_kg = cfg["weight_kg"]
    if len(mmp) >= 300:
        p_vo2max = float(mmp[299])
    else:
        p_vo2max = mftp * 1.15

    gross_efficiency = 0.23
    vo2max_ml_min = p_vo2max * 60 * 1000 / (gross_efficiency * 20900)
    vo2max_ml_min_kg = vo2max_ml_min / weight_kg

    return {
        "Pmax": round(float(pmax), 1),
        "FRC": round(float(frc_kj), 2),
        "mFTP": round(float(mftp), 1),
        "TTE": round(float(tte) / 60, 1),
        "mVO2max_L_min": round(vo2max_ml_min / 1000, 2),
        "mVO2max_ml_min_kg": round(vo2max_ml_min_kg, 1),
        "tau": round(float(tau), 1),
        "tau2": round(float(tau2), 1),
        "a": round(float(a), 1),
        "model": "peronnet_thibault",
        "note": "Based on Peronnet & Thibault (1989), modified per WKO4 implementation. "
                "Pmax is derived (FRC*1000/tau). Post-TTE decline modeled as -a*ln(t/TTE).",
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


def rolling_pd_profile(window_days=90, step_days=14):
    """Compute full PD model params at regular intervals over training history.

    Steps forward from earliest date + window_days to latest date. At each
    step, calls compute_envelope_mmp(start, end) and fit_pd_model(mmp).

    Returns DataFrame with columns: date, mFTP, Pmax, FRC, TTE.
    Returns None if insufficient data.
    """
    activities = get_activities()
    if activities.empty:
        return None

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
                    "TTE": model["TTE"],
                })
        current += pd.Timedelta(days=step_days)

    if not results:
        return None

    return pd.DataFrame(results)


def _pd_power(duration_s, model):
    """Compute predicted power at a duration from PD model parameters."""
    frc = model.get("FRC", 20)
    mftp = model.get("mFTP", 280)
    tau = model.get("tau", 15)
    tau2 = model.get("tau2", 20)
    tte = model.get("TTE", 40) * 60  # TTE stored in minutes, convert to seconds
    a = model.get("a", 20)

    t = np.float64(duration_s)
    anaerobic = frc * 1000 / t * (1 - np.exp(-t / tau))
    aerobic = mftp * (1 - np.exp(-t / tau2))
    decline = a * np.log(t / tte) if t > tte else 0.0

    return anaerobic + aerobic - decline


def decompose_pd_change(model_old, model_new):
    """Decompose PD curve change into CP vs W' vs Pmax contributions.

    Compares two PD models and attributes power changes at key durations
    to mFTP (aerobic), FRC (anaerobic), or Pmax (neuromuscular).

    Source: WD-55 — ramp test gains may reflect W', not VO2max.
    """
    mftp_delta = model_new.get("mFTP", 0) - model_old.get("mFTP", 0)
    frc_delta = model_new.get("FRC", 0) - model_old.get("FRC", 0)
    pmax_delta = model_new.get("Pmax", 0) - model_old.get("Pmax", 0)

    # Determine dominant change
    changes = {
        "aerobic": abs(mftp_delta) / max(model_old.get("mFTP", 280), 1) * 100,
        "anaerobic": abs(frc_delta) / max(model_old.get("FRC", 20), 1) * 100,
        "neuromuscular": abs(pmax_delta) / max(model_old.get("Pmax", 1100), 1) * 100,
    }
    dominant = max(changes, key=changes.get)

    # Compute power at key durations for both models
    durations = [10, 60, 300, 1200, 3600]
    at_durations = {}
    for d in durations:
        old_p = _pd_power(d, model_old)
        new_p = _pd_power(d, model_new)
        at_durations[d] = {
            "old": round(old_p, 1),
            "new": round(new_p, 1),
            "delta": round(new_p - old_p, 1),
        }

    return {
        "mFTP_change_w": round(mftp_delta, 1),
        "FRC_change_kj": round(frc_delta, 1),
        "Pmax_change_w": round(pmax_delta, 1),
        "dominant_change": dominant,
        "at_durations": at_durations,
    }


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
