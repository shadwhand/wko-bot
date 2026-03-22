# wko5/clinical.py
"""Clinical guardrails — threshold-based health flags with medical disclaimers."""

import logging
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from wko5.config import get_config
from wko5.training_load import build_pmc, current_fitness
from wko5.db import get_activities, get_records

logger = logging.getLogger(__name__)


MEDICAL_DISCLAIMER = """MEDICAL DISCLAIMER: This analysis is based on training data and athlete \
profile parameters only. It is NOT a substitute for medical evaluation by a healthcare provider.

If you experience any of the following during training or racing, STOP IMMEDIATELY and seek \
medical attention: chest pain or pressure, severe shortness of breath, dizziness or loss of \
consciousness, palpitations or irregular heartbeat, severe muscle cramps or weakness.

Always consult with a physician before making significant changes to your training or \
competing when you have any health concerns."""


def check_ctl_ramp_rate(pmc=None):
    """Check if CTL ramp rate exceeds thresholds.

    Returns flag dict or None if no issue.
    """
    cfg = get_config()
    yellow_threshold = cfg.get("ctl_ramp_rate_yellow", 7)
    red_threshold = cfg.get("ctl_ramp_rate_red", 10)

    if pmc is None:
        pmc = build_pmc()

    if len(pmc) < 14:
        return None

    # Compute 7-day rolling CTL change rate
    pmc = pmc.copy()
    pmc["ctl_change_7d"] = pmc["CTL"].diff(7) / 7  # TSS/day/week

    recent = pmc.tail(14)
    max_rate = recent["ctl_change_7d"].max()

    if max_rate >= red_threshold:
        return {
            "flag_type": "ctl_ramp_excessive",
            "flag_name": "CTL ramp rate excessive",
            "severity": "red",
            "triggered_value": round(float(max_rate), 1),
            "threshold": red_threshold,
            "medical_disclaimer": MEDICAL_DISCLAIMER,
            "recommendation": f"CTL ramp rate of {max_rate:.1f} TSS/day/week exceeds safe limit ({red_threshold}). Reduce training load immediately.",
        }
    elif max_rate >= yellow_threshold:
        return {
            "flag_type": "ctl_ramp_excessive",
            "flag_name": "CTL ramp rate elevated",
            "severity": "yellow",
            "triggered_value": round(float(max_rate), 1),
            "threshold": yellow_threshold,
            "recommendation": f"CTL ramp rate of {max_rate:.1f} TSS/day/week approaching unsafe levels ({red_threshold}). Consider reducing load.",
        }

    return None


def check_tsb_floor(pmc=None):
    """Check if TSB has been below floor for >14 consecutive days.

    Returns flag dict or None.
    """
    cfg = get_config()
    floor = cfg.get("tsb_floor_alert", -30)

    if pmc is None:
        pmc = build_pmc()

    if len(pmc) < 14:
        return None

    # Count consecutive days with TSB <= floor (from end)
    consecutive = 0
    for _, row in pmc.iloc[::-1].iterrows():
        if row["TSB"] <= floor:
            consecutive += 1
        else:
            break

    if consecutive >= 14:
        current_tsb = float(pmc.iloc[-1]["TSB"])
        return {
            "flag_type": "tsb_floor_breach",
            "flag_name": "TSB floor breach",
            "severity": "yellow",
            "triggered_value": round(current_tsb, 1),
            "threshold": floor,
            "days_flagged": consecutive,
            "recommendation": f"TSB has been below {floor} for {consecutive} consecutive days. Schedule recovery days.",
        }

    return None


def check_hr_decoupling_anomaly(days_back=14):
    """Check recent rides for HR decoupling >10% at moderate intensity.

    Returns flag dict or None.
    """
    from wko5.ride import hr_decoupling

    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    activities = get_activities(start=start, end=end)

    if activities.empty:
        return None

    # Filter moderate intensity rides (2-3 hours)
    moderate = activities[
        (activities["total_timer_time"] > 5400) &  # >1.5h
        (activities["total_timer_time"] < 14400)    # <4h
    ]

    flagged_rides = []
    for _, ride in moderate.iterrows():
        dc = hr_decoupling(ride["id"])
        if dc is not None and not np.isnan(dc) and dc > 10:
            flagged_rides.append({
                "activity_id": ride["id"],
                "date": str(ride["start_time"])[:10],
                "decoupling": round(dc, 3),
            })

    if flagged_rides:
        return {
            "flag_type": "cardiac_drift_anomaly",
            "flag_name": "Cardiac drift anomaly",
            "severity": "red",
            "triggered_value": flagged_rides[0]["decoupling"],
            "threshold": 10,
            "context": {"flagged_rides": flagged_rides},
            "medical_disclaimer": MEDICAL_DISCLAIMER,
            "recommendation": f"HR decoupling >10% detected on {len(flagged_rides)} recent ride(s). May indicate cardiovascular stress or dehydration.",
        }

    return None


def check_power_hr_inversion(activity_id):
    """Check a single ride for power-HR inversion (HR rising while power drops).

    Returns flag dict or None.
    """
    records = get_records(activity_id)
    if records.empty:
        return None

    if "power" not in records.columns or "heart_rate" not in records.columns:
        return None

    power = records["power"].fillna(0).values.astype(float)
    hr = records["heart_rate"].fillna(0).values.astype(float)
    n = len(power)

    if n < 1200:  # need at least 20 minutes
        return None

    # Use 10-minute rolling averages
    window = 600
    if n < window * 2:
        return None

    power_rolling = pd.Series(power).rolling(window).mean().values
    hr_rolling = pd.Series(hr).rolling(window).mean().values

    # Check for inversion: power decreasing while HR increasing
    # Exclude final 30 minutes (expected fatigue pattern)
    check_end = max(window, n - 1800)
    inversions = 0

    for i in range(window + 600, check_end, 600):  # check every 10 min
        if i >= len(power_rolling) or i < 600:
            continue
        power_change = power_rolling[i] - power_rolling[i - 600]
        hr_change = hr_rolling[i] - hr_rolling[i - 600]

        if power_change < -10 and hr_change > 3:
            inversions += 1

    if inversions >= 2:
        return {
            "flag_type": "power_hr_inversion",
            "flag_name": "Power-HR inversion",
            "severity": "red",
            "triggered_value": inversions,
            "threshold": 2,
            "medical_disclaimer": MEDICAL_DISCLAIMER,
            "recommendation": f"Power decreased while HR increased at {inversions} points during the ride (outside final 30min). May indicate acute fatigue or illness.",
        }

    return None


def check_collapse_zone(total_kj, collapse_threshold=None):
    """Check if route cumulative kJ exceeds collapse threshold.

    Returns flag dict or None.
    """
    if collapse_threshold is None:
        cfg = get_config()
        collapse_threshold = cfg.get("collapse_kj_threshold")

    if collapse_threshold is None or collapse_threshold <= 0:
        return None

    if total_kj >= collapse_threshold:
        return {
            "flag_type": "collapse_zone",
            "flag_name": "Collapse zone approach",
            "severity": "red",
            "triggered_value": round(total_kj, 0),
            "threshold": collapse_threshold,
            "medical_disclaimer": MEDICAL_DISCLAIMER,
            "recommendation": f"Route demands {total_kj:.0f} kJ, exceeding your historical collapse threshold of {collapse_threshold:.0f} kJ. Risk of catastrophic performance failure.",
        }

    return None


def check_energy_deficit(total_duration_s, avg_power, weight_kg,
                         fueling_rate_g_hr=None, alert_threshold_kcal=None):
    """Check if projected energy deficit exceeds threshold.

    Returns flag dict or None.
    """
    cfg = get_config()
    if fueling_rate_g_hr is None:
        fueling_rate_g_hr = cfg.get("fueling_rate_g_hr", 75)
    if alert_threshold_kcal is None:
        alert_threshold_kcal = cfg.get("energy_deficit_alert_kcal", 3000)

    hours = total_duration_s / 3600

    # Energy expenditure: ~1 kcal per watt-hour (approximate)
    # More precisely: power_kj_hr = avg_power * 3.6, but mechanical efficiency ~25%
    # Total metabolic cost ≈ power * 3.6 / 0.25 kJ/hr = power * 14.4 kJ/hr
    # Plus basal: ~weight_kg * 1.036 kcal/hr
    expenditure_kcal = (avg_power * 14.4 / 4.184 + weight_kg * 1.036) * hours

    # Intake from fueling
    intake_kcal = fueling_rate_g_hr * hours * 4  # 4 kcal per gram carbohydrate

    deficit = expenditure_kcal - intake_kcal

    if deficit >= alert_threshold_kcal:
        return {
            "flag_type": "energy_deficit",
            "flag_name": "Energy deficit critical",
            "severity": "yellow",
            "triggered_value": round(deficit, 0),
            "threshold": alert_threshold_kcal,
            "context": {
                "expenditure_kcal": round(expenditure_kcal, 0),
                "intake_kcal": round(intake_kcal, 0),
                "duration_hours": round(hours, 1),
            },
            "recommendation": f"Projected caloric deficit of {deficit:.0f} kcal over {hours:.1f}h. Increase fueling rate from {fueling_rate_g_hr}g/hr.",
        }

    return None


def check_if_floor(days_back=90):
    """Check if endurance ride IF floor is too high.

    IF floor > 0.70 = yellow (riding endurance too hard)
    IF floor > 0.75 = red (significant easy gains available from riding easier)

    Source: TMT-69, TMT-68 — IF distribution is the #1 diagnostic coaches check.
    """
    from wko5.training_load import if_distribution

    dist = if_distribution(days_back=days_back)
    if dist is None:
        return None

    floor_if = dist["floor"]
    if floor_if > 0.75:
        severity = "red"
        message = (f"Endurance ride IF floor is {floor_if:.2f} — riding too hard. "
                   f"Easy gains available from riding easier (target IF 0.50-0.65).")
    elif floor_if > 0.70:
        severity = "yellow"
        message = (f"Endurance ride IF floor is {floor_if:.2f} — slightly high. "
                   f"Consider riding easier on recovery/endurance days.")
    else:
        severity = "green"
        message = f"Endurance ride IF floor is {floor_if:.2f} — good distribution."

    return {
        "flag": "if_floor",
        "floor_if": round(floor_if, 3),
        "severity": severity,
        "message": message,
        "rides_analyzed": dist["rides_analyzed"],
    }


def check_intensity_black_hole(days_back=90):
    """Detect intensity black hole — most rides in moderate zone.

    Flags when IF distribution is compressed (floor > 0.70, spread < 0.25),
    meaning the athlete never rides truly easy or truly hard.

    Source: TMT-58, TMT-69 — athletes who don't polarize settle into
    80-90% capacity, never truly hard or easy.
    """
    from wko5.training_load import if_distribution

    dist = if_distribution(days_back=days_back)
    if dist is None:
        return None

    floor = dist["floor"]
    ceiling = dist["ceiling"]
    spread = dist["spread"]

    if dist["compressed"] and spread < 0.25:
        return {
            "flag": "intensity_black_hole",
            "compressed": True,
            "floor": round(floor, 3),
            "ceiling": round(ceiling, 3),
            "spread": round(spread, 3),
            "severity": "yellow",
            "message": (f"Intensity black hole detected: IF range {floor:.2f}-{ceiling:.2f}. "
                        f"Most rides are moderate — add truly easy (IF<0.50) and truly hard "
                        f"(IF>0.90) sessions."),
        }

    return None


def check_panic_training(days_back=90):
    """Detect panic training pattern: sudden intensity spike after low-load period.

    Flags when 2+ weeks of low training load are followed by a sudden
    CTL ramp > 7 TSS/day.

    Source: TMT-71 — panic training almost always backfires.
    """
    pmc = build_pmc()
    if pmc.empty or len(pmc) < 28:
        return None

    recent = pmc.tail(days_back)
    if len(recent) < 28:
        return None

    # Look for pattern: 14+ days of low CTL followed by rapid ramp
    tss = recent["TSS"].values

    for i in range(14, len(tss) - 7):
        # Check if preceding 14 days had low average TSS
        pre_avg_tss = float(np.mean(tss[i-14:i]))
        # Check if following 7 days had high average TSS
        post_avg_tss = float(np.mean(tss[i:i+7]))

        if pre_avg_tss < 30 and post_avg_tss > 60:
            ramp_ratio = post_avg_tss / max(pre_avg_tss, 1)
            if ramp_ratio > 2.0:
                return {
                    "flag": "panic_training",
                    "severity": "yellow",
                    "pre_avg_tss": round(pre_avg_tss, 1),
                    "post_avg_tss": round(post_avg_tss, 1),
                    "ramp_ratio": round(ramp_ratio, 1),
                    "message": (f"Panic training pattern detected: avg TSS jumped from "
                                f"{pre_avg_tss:.0f} to {post_avg_tss:.0f} "
                                f"({ramp_ratio:.1f}x increase). Recommend building volume "
                                f"first, then adding intensity gradually."),
                }

    return None


def get_clinical_flags(days_back=30):
    """Get all current clinical flags.

    Returns structured dict with alert level, current flags, and health metrics.
    """
    pmc = build_pmc()
    flags = []

    # Check each guardrail
    ctl_flag = check_ctl_ramp_rate(pmc)
    if ctl_flag:
        flags.append(ctl_flag)

    tsb_flag = check_tsb_floor(pmc)
    if tsb_flag:
        flags.append(tsb_flag)

    hr_flag = check_hr_decoupling_anomaly(days_back=days_back)
    if hr_flag:
        flags.append(hr_flag)

    # EC podcast diagnostics
    if_floor = check_if_floor()
    if if_floor and if_floor["severity"] != "green":
        flags.append(if_floor)

    black_hole = check_intensity_black_hole()
    if black_hole:
        flags.append(black_hole)

    panic = check_panic_training()
    if panic:
        flags.append(panic)

    # Determine overall alert level
    severities = [f["severity"] for f in flags]
    if "red" in severities:
        alert_level = "red"
    elif "yellow" in severities:
        alert_level = "yellow"
    else:
        alert_level = "green"

    # Current health metrics
    fitness = current_fitness()

    return {
        "alert_level": alert_level,
        "current_flags": flags,
        "current_health_metrics": {
            "ctl": fitness.get("CTL"),
            "atl": fitness.get("ATL"),
            "tsb": fitness.get("TSB"),
        },
    }
