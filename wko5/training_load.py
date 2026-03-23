"""Training load — NP, TSS, IF, CTL/ATL/TSB (PMC), efficiency factor."""

import logging

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

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


def if_distribution(days_back=90, ftp=None):
    """Analyze IF distribution across recent rides.

    Returns dict with histogram, floor (10th percentile), ceiling (90th percentile),
    spread, compressed flag (floor > 0.70), and ride count.

    Source: TMT-68, TMT-69 — IF distribution is the #1 coaching diagnostic.
    """
    from wko5.db import FTP_DEFAULT

    if ftp is None:
        ftp = get_config().get("ftp") or FTP_DEFAULT

    activities = get_activities()
    cutoff = (pd.Timestamp.now() - pd.Timedelta(days=days_back)).strftime("%Y-%m-%d")
    recent = activities[activities["start_time"] >= cutoff]

    if_values = []
    for _, act in recent.iterrows():
        np_val = act.get("normalized_power")
        if np_val and np_val > 0 and ftp > 0:
            if_values.append(round(np_val / ftp, 3))

    if len(if_values) < 5:
        return None

    arr = np.array(if_values)
    floor = float(np.percentile(arr, 10))
    ceiling = float(np.percentile(arr, 90))

    bins = np.arange(0, 1.5, 0.05)
    counts, edges = np.histogram(arr, bins=bins)
    histogram = {f"{edges[i]:.2f}-{edges[i+1]:.2f}": int(counts[i])
                 for i in range(len(counts)) if counts[i] > 0}

    return {
        "histogram": histogram,
        "floor": round(floor, 3),
        "ceiling": round(ceiling, 3),
        "spread": round(ceiling - floor, 3),
        "compressed": floor > 0.70,
        "rides_analyzed": len(if_values),
    }


def ftp_growth_curve(window_days=90, step_days=30):
    """Fit a logarithmic model (FTP = a*ln(weeks+1) + b) to rolling FTP history.

    Uses rolling_ftp() from wko5.pdcurve to get the FTP history, then fits
    a logarithmic curve to characterise the athlete's adaptation trajectory.

    Returns dict with keys:
      slope, intercept, r_squared,
      improvement_rate_w_per_year (watts per year at current training age),
      plateau_detected (True if rate < 2 W/yr),
      growth_phase ("early"|"intermediate"|"mature"|"plateau"),
      training_age_weeks, data_points.
    Returns None if insufficient data (fewer than 3 points).
    """
    from wko5.pdcurve import rolling_ftp

    history = rolling_ftp(window_days=window_days, step_days=step_days)
    if history.empty or len(history) < 3:
        logger.warning("ftp_growth_curve: insufficient data points (need >= 3)")
        return None

    history = history.dropna(subset=["mFTP"]).reset_index(drop=True)
    if len(history) < 3:
        return None

    # Convert date index to weeks from first data point
    history["date"] = pd.to_datetime(history["date"])
    t0 = history["date"].iloc[0]
    history["weeks"] = (history["date"] - t0).dt.days / 7.0

    weeks = history["weeks"].values
    ftp_vals = history["mFTP"].values

    def _log_model(w, a, b):
        return a * np.log(w + 1) + b

    try:
        popt, _ = curve_fit(_log_model, weeks, ftp_vals, p0=[10.0, float(ftp_vals[0])], maxfev=5000)
    except (RuntimeError, ValueError) as e:
        logger.warning(f"ftp_growth_curve: curve_fit failed: {e}")
        return None

    a, b = popt
    fitted = _log_model(weeks, a, b)

    ss_res = np.sum((ftp_vals - fitted) ** 2)
    ss_tot = np.sum((ftp_vals - ftp_vals.mean()) ** 2)
    r_squared = float(1.0 - ss_res / ss_tot) if ss_tot > 0 else 0.0

    # Instantaneous rate at the current (last) training age
    training_age_weeks = float(weeks[-1])
    # d/dw [a*ln(w+1) + b] = a / (w+1)
    # Multiply by 52 to convert from W/week to W/year
    rate_w_per_week = a / (training_age_weeks + 1)
    improvement_rate_w_per_year = float(rate_w_per_week * 52)

    plateau_detected = improvement_rate_w_per_year < 2.0

    if plateau_detected:
        growth_phase = "plateau"
    elif training_age_weeks < 26:
        growth_phase = "early"
    elif training_age_weeks < 78:
        growth_phase = "intermediate"
    else:
        growth_phase = "mature"

    return {
        "slope": round(float(a), 4),
        "intercept": round(float(b), 4),
        "r_squared": round(r_squared, 4),
        "improvement_rate_w_per_year": round(improvement_rate_w_per_year, 2),
        "plateau_detected": plateau_detected,
        "growth_phase": growth_phase,
        "training_age_weeks": round(training_age_weeks, 1),
        "data_points": len(history),
    }


def performance_trend(durations=None, days_back=30):
    """Track best effort at key durations per ride over recent days.

    For each activity in the last *days_back* days, find the best average power
    at each requested duration using the ride's power records.

    Parameters
    ----------
    durations : list of int, optional
        Durations in seconds to analyse. Defaults to [300, 1200].
    days_back : int
        How many days back to search for activities.

    Returns
    -------
    pd.DataFrame with columns: date, activity_id, best_<N>s for each duration.
    Empty DataFrame if no activities found or no power data.
    """
    if durations is None:
        durations = [300, 1200]

    cutoff = (pd.Timestamp.now() - pd.Timedelta(days=days_back)).strftime("%Y-%m-%d")
    activities = get_activities(start=cutoff)

    if activities.empty:
        cols = ["date", "activity_id"] + [f"best_{d}s" for d in durations]
        return pd.DataFrame(columns=cols)

    rows = []
    for _, act in activities.iterrows():
        records = get_records(act["id"])
        if records.empty or "power" not in records.columns:
            continue

        power = records["power"].fillna(0).values.astype(float)
        n = len(power)
        if n == 0:
            continue

        cumsum = np.concatenate([[0.0], np.cumsum(power)])
        row = {
            "date": str(act["start_time"])[:10],
            "activity_id": act["id"],
        }
        for d in durations:
            col = f"best_{d}s"
            if d <= n:
                avgs = (cumsum[d:] - cumsum[:n - d + 1]) / d
                row[col] = float(avgs.max())
            else:
                row[col] = float("nan")
        rows.append(row)

    if not rows:
        cols = ["date", "activity_id"] + [f"best_{d}s" for d in durations]
        return pd.DataFrame(columns=cols)

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    return df
