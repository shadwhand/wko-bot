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


def _estimate_initial_params(mmp, ftp_prior=None):
    """Estimate PD model parameters from MMP curve shape.

    Derives Pmax, FRC, tau from MMP data to break the FRC/TTE degeneracy
    that plagues unconstrained fitting. Works for any athlete.

    Strategy:
        1. Pmax from 1s MMP (+ 10% for extrapolation headroom)
        2. mFTP from FTP test, or estimated from long-duration MMP
        3. FRC from area between MMP and mFTP for durations < 300s
        4. tau = FRC*1000 / Pmax (phosphocreatine time constant)
        5. tau2 from the aerobic crossover point (~50% aerobic at 60-90s)
    """
    # Pmax: extrapolate slightly above 1s MMP
    pmax_est = float(mmp[0]) * 1.10

    # mFTP: from prior or long-duration MMP
    if ftp_prior and ftp_prior > 100:
        mftp_est = ftp_prior
    elif len(mmp) >= 3600:
        mftp_est = float(mmp[3599]) * 1.05
    elif len(mmp) >= 1200:
        mftp_est = float(mmp[1199]) * 0.95
    else:
        mftp_est = float(mmp[min(len(mmp) - 1, 299)]) * 0.80

    # FRC: anaerobic work capacity above mFTP.
    # In the PT model: FRC = integral of (anaerobic_term) over all time
    # Approximate from MMP: area between MMP curve and mFTP for t=1..120s
    # (beyond 120s, anaerobic contribution is negligible)
    max_t = min(120, len(mmp))
    excess_power = np.maximum(mmp[:max_t] - mftp_est, 0)
    frc_est = float(np.sum(excess_power)) / 1000  # joules → kJ
    # The integral overestimates because it includes aerobic ramp-up energy.
    # In the PT model, the anaerobic term at time t is FRC*1000/t*(1-exp(-t/tau)).
    # The area integral includes both anaerobic and the rising aerobic component.
    # Empirically, the raw area is ~3-4x the true FRC. Scale by 0.3.
    frc_est *= 0.30
    frc_est = np.clip(frc_est, 3, 30)

    # tau from Pmax and FRC
    tau_est = frc_est * 1000 / pmax_est if pmax_est > 0 else 10.0
    tau_est = np.clip(tau_est, 3, 30)

    # tau2: aerobic crossover. At t=tau2*ln(2), aerobic term is 50% of mFTP.
    # Typically 60-90s for the 50% point → tau2 ≈ 25-40s
    tau2_est = 30.0

    # TTE: rough estimate from where MMP drops below mFTP + 10W
    tte_est = 2400.0
    for t in range(300, min(len(mmp), 5400)):
        if mmp[t - 1] < mftp_est + 10:
            tte_est = float(t)
            break

    return pmax_est, frc_est, mftp_est, tau_est, tau2_est, tte_est


def fit_pd_model(mmp, ftp_prior=None, tte_prior=None):
    """Fit the Peronnet-Thibault / WKO4 PD model to an MMP array.

    Two-stage fitting:
        1. Estimate Pmax, FRC, tau from MMP shape (breaks FRC/TTE degeneracy)
        2. Fix Pmax, fit remaining params with anchor-weighted optimization

    Coach test protocol (recommended for accurate decomposition):
        - Sprint test → constrains Pmax (automatic from 1s MMP)
        - 1min max → constrains FRC decay shape (automatic from MMP)
        - 3-5min max → constrains FVO2max (automatic from MMP)
        - FTP test to exhaustion → provides ftp_prior AND tte_prior

    Args:
        mmp: numpy array where mmp[d-1] = best average power over d seconds
        ftp_prior: FTP test value in watts to anchor mFTP
        tte_prior: time to exhaustion in minutes from FTP test (breaks FRC/TTE degeneracy)

    Returns dict with {Pmax, FRC, mFTP, TTE, mVO2max, tau, tau2, a} or None on failure.
    """
    if len(mmp) < 60:
        logger.warning("MMP too short for model fitting (need >= 60s)")
        return None

    cfg = get_config()
    if ftp_prior is None:
        ftp_prior = cfg.get("ftp_manual")
    if tte_prior is None:
        tte_prior = cfg.get("tte_minutes")  # from baseline test, if available

    # Stage 1: estimate initial parameters from MMP shape
    pmax_est, frc_est, mftp_est, tau_est, tau2_est, tte_est = (
        _estimate_initial_params(mmp, ftp_prior)
    )
    logger.info(
        f"PD initial estimates: Pmax={pmax_est:.0f} FRC={frc_est:.1f}kJ "
        f"mFTP={mftp_est:.0f} tau={tau_est:.1f} TTE={tte_est:.0f}s"
    )

    # Stage 2: fit with Pmax fixed and FRC+mFTP priors
    # Uses differential evolution (global optimizer) to avoid local minima
    # that plague the FRC/TTE degeneracy.
    from scipy.optimize import differential_evolution

    max_dur = min(len(mmp), 28800)
    all_durations = np.arange(5, max_dur + 1, dtype=float)
    all_powers = mmp[4:max_dur].astype(float)
    if len(all_durations) > len(all_powers):
        all_durations = all_durations[:len(all_powers)]

    # Log-spaced sample points
    log_idx = np.unique(np.geomspace(1, len(all_durations) - 1, 200).astype(int))
    log_idx = log_idx[log_idx < len(all_durations)]
    fit_d = all_durations[log_idx]
    fit_p = all_powers[log_idx]

    def objective(params):
        frc_kj, mftp, tau2, tte_s, a = params
        tau = frc_kj * 1000 / pmax_est
        pred = _pd_model(fit_d, frc_kj, mftp, tau, tau2, tte_s, a)
        sse = np.sum((fit_p - pred) ** 2)
        # Priors to break FRC/TTE degeneracy
        frc_prior_cost = (frc_kj - frc_est) ** 2 * 20
        mftp_prior_cost = (mftp - mftp_est) ** 2 * 30
        # TTE prior from baseline test (strongest degeneracy breaker)
        tte_prior_cost = 0
        if tte_prior:
            tte_prior_cost = (tte_s - tte_prior * 60) ** 2 * 0.1
        return sse + frc_prior_cost + mftp_prior_cost + tte_prior_cost

    frc_lo = max(3, frc_est * 0.4)
    frc_hi = min(40, frc_est * 2.5)
    mftp_lo = max(100, mftp_est * 0.85)
    mftp_hi = min(500, mftp_est * 1.15)

    bounds = [
        (frc_lo, frc_hi),
        (mftp_lo, mftp_hi),
        (15, 80),       # tau2
        (900, 5400),    # tte
        (5, 80),        # a
    ]

    try:
        result = differential_evolution(
            objective, bounds, maxiter=5000, seed=42, tol=1e-12, popsize=40,
        )
        frc_kj, mftp, tau2, tte, a = result.x
    except Exception as e:
        logger.warning(f"PD model stage-2 fit failed: {e}, falling back to unconstrained")
        return _fit_pd_model_unconstrained(mmp, cfg)

    tau = frc_kj * 1000 / pmax_est
    pmax = pmax_est

    # mVO2max estimation
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
    }


def _fit_pd_model_unconstrained(mmp, cfg):
    """Fallback: unconstrained 6-parameter fit (original approach)."""
    max_dur = min(len(mmp), 28800)
    durations = np.arange(5, max_dur + 1, dtype=float)
    powers = mmp[4:max_dur].astype(float)
    if len(durations) != len(powers):
        durations = durations[:len(powers)]

    p0 = [20, 280, 15, 20, 2400, 20]
    bounds_low = [cfg["pd_frc_low"], cfg["pd_mftp_low"], cfg["pd_tau_low"], 5, 600, 1]
    bounds_high = [cfg["pd_frc_high"], cfg["pd_mftp_high"], cfg["pd_tau_high"], 120, 5400, 100]

    try:
        popt, _ = curve_fit(
            _pd_model, durations, powers,
            p0=p0, bounds=(bounds_low, bounds_high),
            maxfev=20000,
        )
    except (RuntimeError, ValueError) as e:
        logger.warning(f"PD model unconstrained fit failed: {e}")
        return None

    frc_kj, mftp, tau, tau2, tte, a = popt
    pmax = frc_kj * 1000 / tau

    weight_kg = cfg["weight_kg"]
    p_vo2max = float(mmp[299]) if len(mmp) >= 300 else mftp * 1.15
    gross_efficiency = 0.23
    vo2max_ml_min = p_vo2max * 60 * 1000 / (gross_efficiency * 20900)

    return {
        "Pmax": round(float(pmax), 1),
        "FRC": round(float(frc_kj), 2),
        "mFTP": round(float(mftp), 1),
        "TTE": round(float(tte) / 60, 1),
        "mVO2max_L_min": round(vo2max_ml_min / 1000, 2),
        "mVO2max_ml_min_kg": round(vo2max_ml_min / weight_kg, 1),
        "tau": round(float(tau), 1),
        "tau2": round(float(tau2), 1),
        "a": round(float(a), 1),
        "model": "peronnet_thibault",
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
