# wko5/nutrition.py
"""Nutrition engine — energy math, glycogen budget, hydration, feed schedule evaluation."""

import logging
from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np

logger = logging.getLogger(__name__)

# Constants
KCAL_PER_G_CHO = 4.0
KCAL_PER_G_FAT = 9.0
KJ_TO_KCAL = 1 / 4.184
NA_MOLECULAR_WEIGHT = 23  # g/mol


@dataclass
class FeedEvent:
    """A planned feeding event at a specific point on the route."""
    km: float
    carbs_g: float = 0
    fluid_ml: float = 0
    sodium_mg: float = 0
    description: str = ""


@dataclass
class NutritionPlan:
    """Rider's nutrition plan for a ride."""
    baseline_intake_g_hr: float = 75    # Updated: 60-90g/hr standard (EC podcast, Persp-41)
    feed_events: List[FeedEvent] = field(default_factory=list)
    starting_glycogen_g: float = 500    # normal diet; 650 if carb loaded
    bottles_capacity_ml: float = 1500
    sweat_na_mmol: float = 45           # individual sweat sodium concentration


def energy_expenditure(power_watts, efficiency=0.23, with_uncertainty=False):
    """Compute energy expenditure in kcal/hr from power output.

    EE = P * 3.6 / (GE * 4.184) kcal/hr

    Args:
        power_watts: average power output in watts
        efficiency: gross mechanical efficiency (default 0.23)
        with_uncertainty: if True, return (mid, low, high) tuple where low uses
            efficiency=0.25 (more efficient → less expenditure) and high uses
            efficiency=0.20 (less efficient → more expenditure)

    Returns:
        float kcal/hr when with_uncertainty=False (default)
        tuple (mid, low, high) kcal/hr when with_uncertainty=True
    """
    if power_watts <= 0:
        if with_uncertainty:
            return (80.0, 80.0, 80.0)
        return 80.0  # basal metabolic rate while coasting
    mid = power_watts * 3.6 / (efficiency * 4.184)
    if not with_uncertainty:
        return mid
    low = power_watts * 3.6 / (0.25 * 4.184)   # higher efficiency → lower expenditure
    high = power_watts * 3.6 / (0.20 * 4.184)  # lower efficiency → higher expenditure
    return (mid, low, high)


def check_absorption_ceiling(intake_g_hr, ceiling_g_hr=90):
    """Check whether carbohydrate intake exceeds the gut absorption ceiling.

    Args:
        intake_g_hr: planned carbohydrate intake in g/hr
        ceiling_g_hr: maximum absorbable CHO per hour (default 90 g/hr,
            achievable with multiple transporter sources)

    Returns:
        None if intake is within the ceiling.
        dict with warning, intake, ceiling, and excess if ceiling is exceeded.
    """
    if intake_g_hr <= ceiling_g_hr:
        return None
    excess = intake_g_hr - ceiling_g_hr
    return {
        "warning": (
            f"Intake {intake_g_hr:.0f} g/hr exceeds absorption ceiling "
            f"{ceiling_g_hr:.0f} g/hr by {excess:.0f} g/hr. "
            "Use multiple CHO sources (glucose + fructose) to raise ceiling."
        ),
        "intake": intake_g_hr,
        "ceiling": ceiling_g_hr,
        "excess": excess,
    }


def glycogen_budget_daily(ride_kj, ride_duration_h, on_bike_carbs_g,
                          post_ride_delay_h, daily_carb_target_g_kg, weight_kg):
    """Model daily glycogen budget after a ride.

    Args:
        ride_kj: total mechanical work done in the ride (kJ)
        ride_duration_h: ride duration in hours
        on_bike_carbs_g: total exogenous CHO consumed during the ride (g)
        post_ride_delay_h: hours between ride end and first post-ride meal
        daily_carb_target_g_kg: daily carbohydrate target in g/kg body mass
        weight_kg: rider body mass in kg

    Returns:
        dict with:
            cho_burned_g: estimated CHO oxidised during the ride
            on_bike_carbs_g: exogenous CHO taken on-bike (echo of input)
            net_glycogen_cost_g: net glycogen draw after on-bike fuelling
            recovery_carbs_available_g: CHO available from the rest of daily target
            recovery_hours_available: waking hours left for recovery eating
            achievable_repletion_g: glycogen that can realistically be replenished
            next_day_glycogen_pct: predicted starting glycogen as % of capacity
            warning: str or None
    """
    glycogen_capacity_g = weight_kg * 6.4

    # CHO burned: treat ride_kj as kcal (1 kJ ≈ 1 kcal for mechanical work context),
    # then 60% from CHO at 4 kcal/g
    ride_kcal = ride_kj * KJ_TO_KCAL
    cho_burned_g = ride_kcal * 0.60 / KCAL_PER_G_CHO

    net_glycogen_cost_g = max(0.0, cho_burned_g - on_bike_carbs_g)

    daily_carb_total_g = daily_carb_target_g_kg * weight_kg
    recovery_carbs_available_g = max(0.0, daily_carb_total_g - on_bike_carbs_g)

    # Waking day = 16 h; subtract ride time and post-ride delay
    recovery_hours_available = max(0.0, 16.0 - ride_duration_h - post_ride_delay_h)

    # Optimal repletion rate is 1.2 g/kg/hr
    optimal_rate_g_hr = 1.2 * weight_kg
    achievable_repletion_g = min(
        recovery_carbs_available_g,
        optimal_rate_g_hr * recovery_hours_available,
    )

    # Predicted glycogen at start of next day
    starting_glycogen_g = glycogen_capacity_g  # assume fully topped up at ride start
    next_day_glycogen_g = max(
        0.0, starting_glycogen_g - net_glycogen_cost_g + achievable_repletion_g
    )
    next_day_glycogen_pct = min(100.0, next_day_glycogen_g / glycogen_capacity_g * 100.0)

    warning = None
    msgs = []
    if post_ride_delay_h > 2:
        msgs.append(
            f"Post-ride delay of {post_ride_delay_h:.1f}h reduces glycogen repletion rate. "
            "Aim to eat within 30-60 min of finishing."
        )
    if next_day_glycogen_pct < 70:
        msgs.append(
            f"Predicted next-day glycogen {next_day_glycogen_pct:.0f}% of capacity. "
            "Consider increasing daily carbohydrate target."
        )
    if msgs:
        warning = " | ".join(msgs)

    return {
        "cho_burned_g": round(cho_burned_g, 1),
        "on_bike_carbs_g": on_bike_carbs_g,
        "net_glycogen_cost_g": round(net_glycogen_cost_g, 1),
        "recovery_carbs_available_g": round(recovery_carbs_available_g, 1),
        "recovery_hours_available": round(recovery_hours_available, 2),
        "achievable_repletion_g": round(achievable_repletion_g, 1),
        "next_day_glycogen_pct": round(next_day_glycogen_pct, 1),
        "warning": warning,
    }


def _cho_fraction(intensity_pct):
    """Fraction of energy from carbohydrate at a given intensity (% of FTP).

    Based on crossover concept. Trained cyclist crossover ~75-80% FTP.
    """
    # Sigmoid: ~0.20 at rest, ~0.35 at 60% FTP, ~0.74 at FTP
    x = max(0, min(intensity_pct, 1.5))
    return 0.20 + 0.65 / (1 + np.exp(-8 * (x - 0.80)))


def cho_burn_rate(power_watts, ftp, efficiency=0.23):
    """Carbohydrate burn rate in g/hr at a given power."""
    ee_kcal_hr = energy_expenditure(power_watts, efficiency)
    intensity = power_watts / ftp if ftp > 0 else 0
    cho_frac = _cho_fraction(intensity)
    return ee_kcal_hr * cho_frac / KCAL_PER_G_CHO


def fat_burn_rate(power_watts, ftp, efficiency=0.23):
    """Fat burn rate in g/hr at a given power."""
    ee_kcal_hr = energy_expenditure(power_watts, efficiency)
    intensity = power_watts / ftp if ftp > 0 else 0
    fat_frac = 1 - _cho_fraction(intensity)
    return ee_kcal_hr * fat_frac / KCAL_PER_G_FAT


def time_to_bonk(power_watts, ftp, intake_g_hr=0, starting_glycogen_g=500,
                 glycogen_critical_g=75, sparing_factor=0.35):
    """Estimate time to bonk (glycogen depletion) in hours.

    Args:
        power_watts: average power
        ftp: functional threshold power
        intake_g_hr: exogenous carb intake rate
        starting_glycogen_g: initial muscle + liver glycogen
        glycogen_critical_g: glycogen level where bonking occurs
        sparing_factor: fraction of exogenous CHO that spares endogenous

    Returns: hours until bonk, or float('inf') if intake matches burn
    """
    burn = cho_burn_rate(power_watts, ftp)
    effective_sparing = intake_g_hr * sparing_factor
    net_drain = burn - effective_sparing

    if net_drain <= 0:
        return float("inf")  # intake covers burn rate

    usable = (starting_glycogen_g - glycogen_critical_g) * 0.95  # ~95% usable
    return usable / net_drain


def glycogen_timeline(power_series, ftp, intake_g_hr=0, starting_glycogen_g=500,
                      glycogen_critical_g=75, sample_interval_s=300):
    """Compute glycogen remaining over time from a power series.

    Args:
        power_series: list/array of per-second power values
        ftp: functional threshold power
        intake_g_hr: baseline carb intake rate
        starting_glycogen_g: initial glycogen
        sample_interval_s: output sampling interval (default 5 min)

    Returns: list of dicts {time_s, time_h, glycogen_g, cho_burned_g, cho_ingested_g}
    """
    glycogen = starting_glycogen_g
    total_burned = 0
    total_ingested = 0
    timeline = [{"time_s": 0, "time_h": 0, "glycogen_g": glycogen,
                 "cho_burned_g": 0, "cho_ingested_g": 0}]

    n = len(power_series)
    for i in range(n):
        power = power_series[i] if power_series[i] is not None else 0

        # Per-second CHO burn
        intensity = power / ftp if ftp > 0 else 0
        ee_kcal_s = energy_expenditure(power) / 3600
        cho_frac = _cho_fraction(intensity)
        cho_burned_s = ee_kcal_s * cho_frac / KCAL_PER_G_CHO

        # Per-second intake (sparing)
        intake_s = intake_g_hr / 3600 * 0.35  # sparing factor

        glycogen = max(0, glycogen - cho_burned_s + intake_s)
        total_burned += cho_burned_s
        total_ingested += intake_g_hr / 3600

        if (i + 1) % sample_interval_s == 0:
            timeline.append({
                "time_s": i + 1,
                "time_h": round((i + 1) / 3600, 2),
                "glycogen_g": round(glycogen, 1),
                "cho_burned_g": round(total_burned, 1),
                "cho_ingested_g": round(total_ingested, 1),
            })

    return timeline


def sweat_rate(power_watts, temp_c=20, humidity_pct=50, weight_kg=78):
    """Estimate sweat rate in L/hr.

    Simplified model based on metabolic heat production and environment.
    """
    # Base sweat from metabolic heat
    heat_watts = power_watts * (1 / 0.23 - 1) if power_watts > 0 else 0
    base_sr = heat_watts / 2426000 * 3600  # latent heat of vaporization, convert to L/hr

    # Temperature modifier
    temp_factor = 0.5 + 0.5 * max(0, (temp_c - 10)) / 25
    temp_factor = min(temp_factor, 1.5)

    # Humidity modifier (less effective evaporation → more sweating)
    humidity_factor = 1.0 + 0.3 * max(0, (humidity_pct / 100 - 0.50)) / 0.50
    humidity_factor = min(humidity_factor, 1.3)

    # Weight modifier
    weight_factor = weight_kg / 75

    sr = base_sr * temp_factor * humidity_factor * weight_factor

    # Clamp to realistic range
    return max(0.3, min(sr, 3.0))


def sodium_loss(sweat_rate_l_hr, sweat_na_mmol=45):
    """Compute sodium loss in mg/hr from sweat rate and concentration."""
    return sweat_rate_l_hr * sweat_na_mmol * NA_MOLECULAR_WEIGHT


def evaluate_nutrition_plan(paced_segments, plan, ftp=None, temp_c=20, humidity_pct=50):
    """Evaluate a nutrition plan against paced segments.

    Takes paced segments (with target_power, estimated_duration_s, elapsed_hours)
    and a NutritionPlan, simulates glycogen and hydration state across the route.

    Returns: dict with glycogen_timeline, hydration_timeline, bonk_risk_km, warnings
    """
    from wko5.config import get_config
    cfg = get_config()
    if ftp is None:
        ftp = cfg["ftp_manual"]

    glycogen = plan.starting_glycogen_g
    fluid_deficit_ml = 0
    sodium_deficit_mg = 0
    cumulative_km = 0
    cumulative_cho_burned = 0
    cumulative_cho_ingested = 0
    bonk_risk_km = None
    glycogen_tl = []
    hydration_tl = []
    warnings = []

    # Index feed events by km
    feed_by_km = sorted(plan.feed_events, key=lambda f: f.km)
    feed_idx = 0

    for seg in paced_segments:
        power = seg.get("target_power", 0)
        duration_s = seg.get("estimated_duration_s", seg.get("duration_s", 0))
        distance_m = seg.get("distance_m", 0)
        duration_h = duration_s / 3600

        # CHO burn for this segment
        cho_burned = cho_burn_rate(power, ftp) * duration_h
        fat_burned = fat_burn_rate(power, ftp) * duration_h

        # Baseline intake for this segment
        cho_ingested = plan.baseline_intake_g_hr * duration_h

        # Check for feed events in this segment's km range
        seg_start_km = cumulative_km / 1000
        seg_end_km = (cumulative_km + distance_m) / 1000
        while feed_idx < len(feed_by_km) and feed_by_km[feed_idx].km <= seg_end_km:
            evt = feed_by_km[feed_idx]
            if evt.km >= seg_start_km:
                cho_ingested += evt.carbs_g
                fluid_deficit_ml -= evt.fluid_ml
                sodium_deficit_mg -= evt.sodium_mg
            feed_idx += 1

        # Glycogen update (sparing from exogenous intake)
        sparing = cho_ingested * 0.35
        glycogen = max(0, glycogen - cho_burned + sparing)
        cumulative_cho_burned += cho_burned
        cumulative_cho_ingested += cho_ingested

        # Hydration update
        sr = sweat_rate(power, temp_c, humidity_pct, cfg["weight_kg"])
        fluid_lost_ml = sr * duration_h * 1000
        fluid_deficit_ml += fluid_lost_ml

        na_lost = sodium_loss(sr, plan.sweat_na_mmol) * duration_h
        sodium_deficit_mg += na_lost

        cumulative_km += distance_m

        # Bonk risk check
        if glycogen <= 75 and bonk_risk_km is None:
            bonk_risk_km = cumulative_km / 1000

        glycogen_tl.append({
            "km": round(cumulative_km / 1000, 1),
            "glycogen_g": round(glycogen, 1),
            "cho_burned_cumulative_g": round(cumulative_cho_burned, 1),
            "cho_ingested_cumulative_g": round(cumulative_cho_ingested, 1),
        })

        hydration_tl.append({
            "km": round(cumulative_km / 1000, 1),
            "fluid_deficit_ml": round(fluid_deficit_ml, 0),
            "sodium_deficit_mg": round(sodium_deficit_mg, 0),
            "dehydration_pct": round(fluid_deficit_ml / (cfg["weight_kg"] * 10), 1),
        })

    # Generate warnings
    total_duration_h = sum(s.get("estimated_duration_s", s.get("duration_s", 0))
                          for s in paced_segments) / 3600

    if bonk_risk_km is not None:
        warnings.append(f"Glycogen critical at km {bonk_risk_km:.0f}. Increase intake or reduce intensity.")

    if hydration_tl and hydration_tl[-1]["dehydration_pct"] > 3.0:
        warnings.append(f"Dehydration reaches {hydration_tl[-1]['dehydration_pct']:.1f}% body mass. Increase fluid intake.")

    # Check for long gaps between feed events
    if len(feed_by_km) >= 2:
        for i in range(1, len(feed_by_km)):
            gap_km = feed_by_km[i].km - feed_by_km[i-1].km
            if gap_km > 60:
                warnings.append(f"Feed gap of {gap_km:.0f}km between km {feed_by_km[i-1].km:.0f} and {feed_by_km[i].km:.0f}. Consider adding a stop.")

    return {
        "glycogen_timeline": glycogen_tl,
        "hydration_timeline": hydration_tl,
        "bonk_risk_km": bonk_risk_km,
        "total_carbs_needed_g": round(cumulative_cho_burned, 0),
        "total_carbs_planned_g": round(cumulative_cho_ingested, 0),
        "total_fluid_needed_L": round(sum(
            sweat_rate(s.get("target_power", 0), temp_c, humidity_pct, cfg["weight_kg"])
            * s.get("estimated_duration_s", s.get("duration_s", 0)) / 3600
            for s in paced_segments
        ), 1),
        "total_sodium_needed_mg": round(sodium_deficit_mg, 0),
        "duration_hours": round(total_duration_h, 1),
        "warnings": warnings,
    }
