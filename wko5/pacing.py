# wko5/pacing.py
"""Durability-aware pacing solver with CdA and drafting support."""

from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import brentq

from wko5.config import get_config
from wko5.physics import power_required, speed_from_power
from wko5.durability import degradation_factor


@dataclass
class RidePlan:
    """Ride plan input — describes how the rider intends to ride."""
    target_riding_hours: float
    rest_hours: float = 0
    cda: float = None            # defaults to config
    crr: float = None            # defaults to config
    weight_rider: float = None   # defaults to config
    weight_bike: float = None    # defaults to config
    drafting_pct: float = 0.0    # fraction of flat/rolling time in draft (0-1)
    drafting_savings: float = 0.30  # aero reduction when drafting
    starting_glycogen_g: float = 500
    nutrition: dict = field(default_factory=dict)

    def __post_init__(self):
        cfg = get_config()
        if self.cda is None:
            self.cda = cfg["cda"]
        if self.crr is None:
            self.crr = cfg["crr"]
        if self.weight_rider is None:
            self.weight_rider = cfg["weight_kg"]
        if self.weight_bike is None:
            self.weight_bike = cfg["bike_weight_kg"]


def _effective_cda(cda, segment_type, drafting_pct, drafting_savings):
    """Compute effective CdA accounting for drafting on flat/rolling segments."""
    if segment_type in ("flat", "rolling", "rolling_descent", "descent") and drafting_pct > 0:
        return cda * (1 - drafting_pct * drafting_savings)
    return cda


def _segment_time(base_power, seg, plan, elapsed_hours, cumulative_kj, dur_params):
    """Compute time for one segment given base power and fatigue state."""
    # Apply durability decay to base power
    deg = degradation_factor(cumulative_kj, elapsed_hours, dur_params)
    target_power = base_power * deg

    # Effective CdA with drafting
    eff_cda = _effective_cda(plan.cda, seg.get("type", "flat"),
                             plan.drafting_pct, plan.drafting_savings)

    # Compute speed at this power on this grade
    v = speed_from_power(
        power=target_power,
        grade=seg.get("avg_grade", 0),
        weight_rider=plan.weight_rider,
        weight_bike=plan.weight_bike,
        cda=eff_cda,
        crr=plan.crr,
    )

    # Cap descent speed at 70 km/h (19.4 m/s) for safety/realism
    MAX_DESCENT_SPEED = 70 / 3.6
    if seg.get("type") in ("descent", "rolling_descent") and v > MAX_DESCENT_SPEED:
        v = MAX_DESCENT_SPEED

    distance_m = seg.get("distance_m", 0)
    if distance_m <= 0 or v <= 0:
        return 0.0, target_power, v

    duration_s = distance_m / v
    return duration_s, target_power, v


def _total_time(base_power, segments, plan, dur_params):
    """Compute total riding time at a given base power."""
    total_s = 0
    elapsed_s = 0
    cumulative_kj = 0

    for seg in segments:
        elapsed_hours = elapsed_s / 3600
        cum_kj = seg.get("cumulative_kj_at_start", cumulative_kj)

        dt, target_p, v = _segment_time(base_power, seg, plan, elapsed_hours, cum_kj, dur_params)

        total_s += dt
        elapsed_s += dt
        cumulative_kj = cum_kj + target_p * dt / 1000

    return total_s


def solve_pacing(segments, plan, dur_params):
    """Solve for the base power that produces the target riding time.

    Base power is the fresh, flat-road power. Actual per-segment power is:
    target_power = base_power * degradation_factor(cumulative_kj, elapsed_hours)

    Uses Brent's method to find the base power where total time = target.

    Args:
        segments: list of segment dicts from analyze_ride_segments or analyze_gpx
        plan: RidePlan with target time, equipment, drafting
        dur_params: dict with {a, b, c} from fit_durability_model

    Returns: dict with base_power and enriched segments
    """
    target_s = plan.target_riding_hours * 3600

    # Binary search on base power
    def residual(bp):
        return _total_time(bp, segments, plan, dur_params) - target_s

    try:
        base_power = brentq(residual, 20, 600, xtol=0.5)
    except ValueError:
        # If no solution in range, find closest
        t_low = _total_time(600, segments, plan, dur_params)
        t_high = _total_time(20, segments, plan, dur_params)
        if t_low > target_s:
            base_power = 600  # even 600W isn't fast enough
        else:
            base_power = 20

    # Build enriched segments with pacing details
    result_segments = []
    elapsed_s = 0
    cumulative_kj = 0

    for seg in segments:
        elapsed_hours = elapsed_s / 3600
        cum_kj = seg.get("cumulative_kj_at_start", cumulative_kj)

        dt, target_p, v = _segment_time(base_power, seg, plan, elapsed_hours, cum_kj, dur_params)

        enriched = dict(seg)
        enriched.update({
            "target_power": round(target_p, 1),
            "estimated_speed_kmh": round(v * 3.6, 1),
            "estimated_duration_s": round(dt, 1),
            "elapsed_hours": round(elapsed_s / 3600, 2),
            "degradation": round(degradation_factor(cum_kj, elapsed_hours, dur_params), 4),
        })
        result_segments.append(enriched)

        elapsed_s += dt
        cumulative_kj = cum_kj + target_p * dt / 1000

    return {
        "base_power": round(base_power, 1),
        "total_riding_time_h": round(elapsed_s / 3600, 2),
        "segments": result_segments,
    }
