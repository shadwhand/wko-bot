# wko5/demand_profile.py
"""Demand profile — compose segments with durability model and PD curve."""

import numpy as np

from wko5.durability import degradation_factor


def _capacity_at_duration(pd_model, duration_s):
    """Estimate power capacity at a given duration from PD model parameters.

    Uses the 3-component model: P(t) = Pmax * e^(-t/tau) + FRC*1000/(t+t0) + mFTP
    For simplicity, approximate from mFTP and FRC for durations > 60s.
    """
    mftp = pd_model.get("mFTP", 0)
    frc_kj = pd_model.get("FRC", 0)

    if duration_s <= 0:
        return mftp

    # Above-threshold capacity from FRC: P_above = FRC * 1000 / duration_s
    frc_contribution = (frc_kj * 1000) / duration_s if duration_s > 0 else 0

    return mftp + frc_contribution


def build_demand_profile(segments, pd_model, durability_params):
    """Build demand profile by composing segments with durability and PD curve.

    For each segment:
    1. Look up cumulative_kj_at_start and elapsed time
    2. Compute degradation_factor at that point
    3. Compute effective capacity = fresh_capacity * degradation
    4. Compute demand_ratio = power_required / effective_capacity

    Args:
        segments: list of segment dicts (from classify_segments or analyze_ride_segments)
        pd_model: dict with at least {mFTP, FRC} from fit_pd_model
        durability_params: dict with {a, b, c} from fit_durability_model

    Returns: list of enriched segment dicts with demand_ratio, effective_capacity, degradation
    """
    result = []
    elapsed_s = 0.0

    for seg in segments:
        cum_kj = seg.get("cumulative_kj_at_start", 0)
        duration_s = seg.get("duration_s", seg.get("estimated_duration_s", 0))
        elapsed_h = elapsed_s / 3600

        # Compute degradation at this point in the ride
        deg = degradation_factor(cum_kj, elapsed_h, durability_params)

        # Fresh capacity at this segment's duration
        fresh_capacity = _capacity_at_duration(pd_model, duration_s)

        # Effective (fatigued) capacity
        eff_capacity = fresh_capacity * deg

        # Demand ratio
        p_required = seg.get("power_required", 0)
        demand_ratio = p_required / eff_capacity if eff_capacity > 0 else float("inf")

        enriched = dict(seg)
        enriched.update({
            "degradation": round(deg, 4),
            "fresh_capacity": round(fresh_capacity, 1),
            "effective_capacity": round(eff_capacity, 1),
            "demand_ratio": round(demand_ratio, 4),
        })

        result.append(enriched)
        elapsed_s += duration_s

    return result
