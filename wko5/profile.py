"""Power profile, Coggan ranking, strengths/limiters, phenotype, fatigue resistance."""

import logging
import numpy as np
import pandas as pd

from wko5.db import get_activities, get_records, WEIGHT_KG
from wko5.pdcurve import compute_envelope_mmp, compute_mmp, power_at_durations

logger = logging.getLogger(__name__)

COGGAN_TABLE = {
    "World Class":  {5: 24.04, 60: 11.50, 300: 7.60, 1200: 6.40, 3600: 6.10},
    "Exceptional":  {5: 22.22, 60: 10.44, 300: 6.95, 1200: 5.69, 3600: 5.36},
    "Very Good":    {5: 19.31, 60: 8.87,  300: 5.97, 1200: 4.92, 3600: 4.62},
    "Good":         {5: 16.85, 60: 7.42,  300: 5.05, 1200: 4.23, 3600: 3.90},
    "Moderate":     {5: 14.18, 60: 5.97,  300: 4.19, 1200: 3.52, 3600: 3.23},
    "Fair":         {5: 11.51, 60: 4.63,  300: 3.34, 1200: 2.78, 3600: 2.53},
    "Untrained":    {5: 0,     60: 0,     300: 0,    1200: 0,    3600: 0},
}

CATEGORY_ORDER = ["Untrained", "Fair", "Moderate", "Good", "Very Good", "Exceptional", "World Class"]
KEY_DURATIONS = [5, 60, 300, 1200, 3600]


def power_profile(days=90, sub_sport=None):
    mmp = compute_envelope_mmp(days=days, sub_sport=sub_sport)
    if len(mmp) == 0:
        return {}
    watts = power_at_durations(mmp, KEY_DURATIONS)
    wkg = {d: round(w / WEIGHT_KG, 2) if not np.isnan(w) else float("nan") for d, w in watts.items()}
    return {"watts": watts, "wkg": wkg}


def coggan_ranking(profile):
    if not profile or "wkg" not in profile:
        return {}
    result = {}
    for d in KEY_DURATIONS:
        wkg = profile["wkg"].get(d, float("nan"))
        if np.isnan(wkg):
            result[d] = "Unknown"
            continue
        category = "Untrained"
        for cat in CATEGORY_ORDER[1:]:
            threshold = COGGAN_TABLE[cat].get(d, 9999)
            if wkg >= threshold:
                category = cat
        result[d] = category
    return result


def strengths_limiters(profile):
    ranking = coggan_ranking(profile)
    if not ranking:
        return {}
    cat_score = {cat: i for i, cat in enumerate(CATEGORY_ORDER)}
    scored = {}
    for d, cat in ranking.items():
        if cat != "Unknown":
            scored[d] = cat_score.get(cat, 0)
    if not scored:
        return {}
    best_d = max(scored, key=scored.get)
    worst_d = min(scored, key=scored.get)
    duration_labels = {5: "5s (neuromuscular)", 60: "1min (anaerobic)", 300: "5min (VO2max)", 1200: "20min (threshold)", 3600: "60min (endurance)"}
    return {
        "strength": {"duration": best_d, "label": duration_labels.get(best_d, f"{best_d}s"), "category": ranking[best_d]},
        "limiter": {"duration": worst_d, "label": duration_labels.get(worst_d, f"{worst_d}s"), "category": ranking[worst_d]},
        "all_rankings": {duration_labels.get(d, f"{d}s"): cat for d, cat in ranking.items()},
    }


def phenotype(pd_model):
    if not pd_model:
        return "Unknown"
    pmax = pd_model.get("Pmax", 0)
    mftp = pd_model.get("mFTP", 1)
    frc = pd_model.get("FRC", 0)
    tte = pd_model.get("TTE", 0)
    pmax_ratio = pmax / mftp
    frc_ratio = frc / mftp
    if pmax_ratio > 6.0 and frc_ratio > 0.08:
        return f"Sprinter (Pmax/FTP={pmax_ratio:.1f}, FRC/FTP={frc_ratio:.3f})"
    elif 4.5 <= pmax_ratio <= 6.0 and frc_ratio > 0.06:
        return f"Pursuiter (Pmax/FTP={pmax_ratio:.1f}, FRC/FTP={frc_ratio:.3f})"
    elif pmax_ratio < 4.5 and tte > 50:
        return f"TTer (Pmax/FTP={pmax_ratio:.1f}, TTE={tte:.0f}min)"
    else:
        return f"All-rounder (Pmax/FTP={pmax_ratio:.1f}, FRC/FTP={frc_ratio:.3f}, TTE={tte:.0f}min)"


def profile_trend(duration_s, window_days=90, step_days=7):
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
        if len(mmp) >= duration_s:
            watts = float(mmp[duration_s - 1])
            results.append({"date": current.strftime("%Y-%m-%d"), "watts": round(watts, 1), "wkg": round(watts / WEIGHT_KG, 2)})
        current += pd.Timedelta(days=step_days)
    return pd.DataFrame(results)


def compare_profiles(period1, period2):
    p1 = _profile_for_range(period1[0], period1[1])
    p2 = _profile_for_range(period2[0], period2[1])
    return {"period1": p1, "period2": p2}


def _profile_for_range(start, end):
    mmp = compute_envelope_mmp(start=start, end=end)
    if len(mmp) == 0:
        return {}
    watts = power_at_durations(mmp, KEY_DURATIONS)
    wkg = {d: round(w / WEIGHT_KG, 2) if not np.isnan(w) else float("nan") for d, w in watts.items()}
    return {"watts": watts, "wkg": wkg}


def fatigue_resistance(days=90, fresh_minutes=30, fatigue_kj=1500):
    activities = get_activities(start=(pd.Timestamp.now() - pd.Timedelta(days=days)).strftime("%Y-%m-%d"))
    fresh_mmps = []
    fatigued_mmps = []
    for _, act in activities.iterrows():
        records = get_records(act["id"])
        if records.empty or "power" not in records.columns:
            continue
        power = records["power"].fillna(0)
        fresh_end = min(fresh_minutes * 60, len(power))
        if fresh_end >= 60:
            fresh_mmp = compute_mmp(power.iloc[:fresh_end])
            fresh_mmps.append(fresh_mmp)
        cumwork_kj = power.cumsum() / 1000
        fatigue_start = cumwork_kj.searchsorted(fatigue_kj)
        if fatigue_start < len(power) - 60:
            fatigued_mmp = compute_mmp(power.iloc[fatigue_start:])
            fatigued_mmps.append(fatigued_mmp)
    if not fresh_mmps or not fatigued_mmps:
        return {}
    def envelope(mmps):
        max_len = max(len(m) for m in mmps)
        env = np.zeros(max_len)
        for m in mmps:
            env[:len(m)] = np.maximum(env[:len(m)], m)
        return env
    fresh_env = envelope(fresh_mmps)
    fatigued_env = envelope(fatigued_mmps)
    compare_durations = [60, 300, 1200]
    ratios = {}
    for d in compare_durations:
        if d <= len(fresh_env) and d <= len(fatigued_env) and fresh_env[d - 1] > 0:
            ratio = fatigued_env[d - 1] / fresh_env[d - 1]
            ratios[d] = round(float(ratio), 3)
        else:
            ratios[d] = float("nan")
    return {"stamina_ratios": ratios, "fresh_rides": len(fresh_mmps), "fatigued_rides": len(fatigued_mmps)}
