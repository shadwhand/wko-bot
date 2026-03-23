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


def check_reds_flags(days_back=180):
    """Screen for RED-S (Relative Energy Deficiency in Sport) risk factors.

    Checks:
    - Performance decline while training load is maintained (last 30d NP vs prior 30-60d)
    - Illness pattern: 5+ consecutive days with no activity, excluding rest weeks
      (rest week = prior 7-day TSS > 200)

    Returns:
        dict with risk_level ("low"|"moderate"|"high"), flags list, and recommendation str.

    Source: RED-S clinical framework — energy availability below 30 kcal/kg FFM/day
    impairs recovery, immunity, and adaptation.
    """
    end = datetime.now()
    start = end - timedelta(days=days_back)

    activities = get_activities(
        start=start.strftime("%Y-%m-%d"),
        end=end.strftime("%Y-%m-%d"),
    )

    flags = []

    # --- Flag 1: Performance declining while load maintained ---
    # Compare last 30d normalized power avg vs prior 30-60d
    cutoff_30 = end - timedelta(days=30)
    cutoff_60 = end - timedelta(days=60)

    if not activities.empty and "normalized_power" in activities.columns:
        # Parse start_time to datetime for windowing
        acts = activities.copy()
        acts["_dt"] = pd.to_datetime(acts["start_time"], utc=True).dt.tz_convert(None)

        recent_np = acts[acts["_dt"] >= cutoff_30]["normalized_power"].dropna()
        prior_np = acts[
            (acts["_dt"] >= cutoff_60) & (acts["_dt"] < cutoff_30)
        ]["normalized_power"].dropna()

        if len(recent_np) >= 3 and len(prior_np) >= 3:
            recent_avg = float(recent_np.mean())
            prior_avg = float(prior_np.mean())
            # Load proxy: use TSS in same windows
            recent_tss = acts[acts["_dt"] >= cutoff_30]["training_stress_score"].dropna()
            prior_tss = acts[
                (acts["_dt"] >= cutoff_60) & (acts["_dt"] < cutoff_30)
            ]["training_stress_score"].dropna()

            # Only flag if load is maintained (recent TSS avg >= 80% of prior)
            if len(recent_tss) >= 3 and len(prior_tss) >= 3:
                load_ratio = float(recent_tss.mean()) / max(float(prior_tss.mean()), 1)
                np_ratio = recent_avg / max(prior_avg, 1)

                if load_ratio >= 0.80 and np_ratio < 0.92:
                    flags.append({
                        "type": "performance_decline_with_load",
                        "recent_np_avg": round(recent_avg, 1),
                        "prior_np_avg": round(prior_avg, 1),
                        "np_ratio": round(np_ratio, 3),
                        "load_ratio": round(load_ratio, 3),
                        "detail": (f"NP dropped {(1-np_ratio)*100:.0f}% over last 30d "
                                   f"while TSS load ratio is {load_ratio:.2f}"),
                    })

    # --- Flag 2: Illness detection — 5+ consecutive days with no activity ---
    # Build the PMC to get daily TSS, then check for no-activity gaps
    pmc = build_pmc()
    if not pmc.empty:
        pmc_window = pmc[pmc["date"] >= pd.Timestamp(start)].copy()

        if not pmc_window.empty:
            # Mark days with zero TSS as rest/illness candidates
            pmc_window = pmc_window.reset_index(drop=True)
            pmc_window["no_activity"] = pmc_window["TSS"] == 0

            # Find runs of consecutive zero-TSS days
            streak = 0
            streak_start_idx = None
            for idx, row in pmc_window.iterrows():
                if row["no_activity"]:
                    if streak == 0:
                        streak_start_idx = idx
                    streak += 1
                else:
                    # Evaluate completed streak of 5+
                    if streak >= 5 and streak_start_idx is not None:
                        # Check if it's a rest week: prior 7-day TSS > 200
                        pre_start = max(0, streak_start_idx - 7)
                        prior_week_tss = float(
                            pmc_window.loc[pre_start:streak_start_idx - 1, "TSS"].sum()
                        )
                        if prior_week_tss <= 200:
                            streak_date = str(pmc_window.loc[streak_start_idx, "date"])[:10]
                            flags.append({
                                "type": "illness_gap",
                                "consecutive_zero_days": streak,
                                "gap_start": streak_date,
                                "prior_week_tss": round(prior_week_tss, 1),
                                "detail": (f"{streak} consecutive days with no activity "
                                           f"starting {streak_date} (prior week TSS: "
                                           f"{prior_week_tss:.0f}, not a planned rest week)"),
                            })
                    streak = 0
                    streak_start_idx = None

            # Handle trailing streak
            if streak >= 5 and streak_start_idx is not None:
                pre_start = max(0, streak_start_idx - 7)
                prior_week_tss = float(
                    pmc_window.loc[pre_start:streak_start_idx - 1, "TSS"].sum()
                )
                if prior_week_tss <= 200:
                    streak_date = str(pmc_window.loc[streak_start_idx, "date"])[:10]
                    flags.append({
                        "type": "illness_gap",
                        "consecutive_zero_days": streak,
                        "gap_start": streak_date,
                        "prior_week_tss": round(prior_week_tss, 1),
                        "detail": (f"{streak} consecutive days with no activity "
                                   f"starting {streak_date} (prior week TSS: "
                                   f"{prior_week_tss:.0f}, not a planned rest week)"),
                    })

    # Determine risk level
    n_flags = len(flags)
    if n_flags == 0:
        risk_level = "low"
        recommendation = "No RED-S risk factors detected. Maintain adequate fueling around training."
    elif n_flags == 1:
        risk_level = "moderate"
        recommendation = ("One RED-S risk factor detected. Review energy availability and "
                          "ensure adequate carbohydrate intake around training sessions.")
    else:
        risk_level = "high"
        recommendation = ("Multiple RED-S risk factors detected. Consider consulting a sports "
                          "dietitian. Prioritise energy availability: aim for ≥45 kcal/kg FFM/day.")

    return {
        "risk_level": risk_level,
        "flags": flags,
        "recommendation": recommendation,
    }


def check_within_day_deficit(activity_id):
    """Estimate within-day energy deficit risk for a single activity.

    Checks:
    - High-kJ ride (>500 kJ) ending after 7 pm — delayed post-ride refueling window
    - Back-to-back rides: another activity within 4 hours before or after
    - High energy cost: total_work > 1500 kcal equivalent

    Returns:
        dict with deficit_risk, total_kj, deficit_kcal_estimate, risk_factors,
        end_hour, hours_to_next_activity — or None if activity not found.

    Source: Within-day energy deficiency impairs adaptation even when daily
    energy intake appears adequate (Fahrenholtz et al., 2018).
    """
    activities = get_activities()
    if activities.empty:
        return None

    row = activities[activities["id"] == activity_id]
    if row.empty:
        return None

    row = row.iloc[0]

    # Parse start time and compute end time
    start_dt = pd.to_datetime(row["start_time"], utc=True)
    duration_s = row.get("total_timer_time") or row.get("total_elapsed_time") or 0
    end_dt = start_dt + timedelta(seconds=float(duration_s))
    end_hour = end_dt.hour + end_dt.minute / 60.0

    # Energy in kJ (total_work is in Joules)
    total_work_j = row.get("total_work")
    if total_work_j is None or (isinstance(total_work_j, float) and np.isnan(total_work_j)):
        # Fallback: estimate from avg_power * duration
        avg_power = row.get("avg_power") or 0
        total_work_j = float(avg_power) * float(duration_s)
    total_kj = float(total_work_j) / 1000.0

    # Rough kcal estimate: mechanical efficiency ~25%, 1 kJ mechanical ≈ 4 kJ metabolic
    # plus 1 kJ ≈ 0.239 kcal, so total_kj * 4 / 4.184 ≈ total_kj * 0.956
    deficit_kcal_estimate = round(total_kj * 0.956, 0)

    # Find hours to next activity (positive = next, negative if none)
    other_acts = activities[activities["id"] != activity_id].copy()
    other_acts["_dt"] = pd.to_datetime(other_acts["start_time"], utc=True)
    future = other_acts[other_acts["_dt"] > end_dt].sort_values("_dt")
    if not future.empty:
        next_start = future.iloc[0]["_dt"]
        hours_to_next = (next_start - end_dt).total_seconds() / 3600.0
    else:
        hours_to_next = None

    risk_factors = []

    # Flag 1: high-kJ ride ending after 7 pm
    if total_kj > 500 and end_hour >= 19.0:
        risk_factors.append({
            "type": "late_high_kj_ride",
            "detail": (f"High-energy ride ({total_kj:.0f} kJ) ended at "
                       f"{int(end_dt.hour):02d}:{int(end_dt.minute):02d} — "
                       f"delayed refueling window (post-7 pm)."),
        })

    # Flag 2: back-to-back — next activity within 4 hours
    if hours_to_next is not None and hours_to_next < 4.0:
        risk_factors.append({
            "type": "back_to_back_ride",
            "detail": (f"Next activity starts {hours_to_next:.1f} h after this ride — "
                       f"insufficient recovery window (<4 h)."),
        })

    # Flag 3: high energy cost > 1500 kcal
    if deficit_kcal_estimate > 1500:
        risk_factors.append({
            "type": "high_energy_cost",
            "detail": (f"Estimated energy cost {deficit_kcal_estimate:.0f} kcal — "
                       f"exceeds 1500 kcal threshold."),
        })

    n = len(risk_factors)
    if n == 0:
        deficit_risk = "low"
    elif n == 1:
        deficit_risk = "moderate"
    else:
        deficit_risk = "high"

    return {
        "deficit_risk": deficit_risk,
        "total_kj": round(total_kj, 1),
        "deficit_kcal_estimate": deficit_kcal_estimate,
        "risk_factors": risk_factors,
        "end_hour": round(end_hour, 2),
        "hours_to_next_activity": round(hours_to_next, 2) if hours_to_next is not None else None,
    }


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

    # RED-S screening
    reds = check_reds_flags()
    if reds and reds["risk_level"] != "low":
        flags.append({
            "flag": "reds_risk",
            "severity": "red" if reds["risk_level"] == "high" else "yellow",
            "risk_level": reds["risk_level"],
            "reds_flags": reds["flags"],
            "message": reds["recommendation"],
        })

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
