# wko5/gap_analysis.py
"""Monte Carlo demand simulation, bottleneck analysis, and route feasibility."""

import logging

import numpy as np

from wko5.demand_profile import build_demand_profile
from wko5.durability import degradation_factor

logger = logging.getLogger(__name__)


def feasibility_flag(demand_ratio):
    """Classify demand ratio into feasibility category."""
    if demand_ratio < 0.85:
        return "comfortable"
    elif demand_ratio < 0.95:
        return "hard"
    elif demand_ratio <= 1.0:
        return "limit"
    else:
        return "impossible"


def _perturb_pd_model(pd_model, rng):
    """Create a perturbed PD model for one Monte Carlo draw.

    Uses Gaussian noise scaled to ~5% CV on each parameter.
    This is a placeholder for Phase 6 Bayesian posterior sampling.

    Note: Pmax perturbation has no effect on demand ratios because
    _capacity_at_duration only uses mFTP and FRC. Pmax is included for
    completeness — Phase 6 will use the full PD model.
    """
    perturbed = {}
    for key, val in pd_model.items():
        if isinstance(val, (int, float)) and key in ("Pmax", "FRC", "mFTP"):
            # 5% coefficient of variation
            noise = rng.normal(0, val * 0.05)
            perturbed[key] = max(val * 0.5, val + noise)  # floor at 50% of original
        else:
            perturbed[key] = val
    return perturbed


def _perturb_durability(dur_params, rng):
    """Create perturbed durability params for one Monte Carlo draw."""
    perturbed = {}
    for key, val in dur_params.items():
        if isinstance(val, (int, float)) and key in ("a", "b", "c"):
            noise = rng.normal(0, abs(val) * 0.10)
            perturbed[key] = max(0.001, val + noise)
            if key == "a":
                perturbed[key] = min(0.99, perturbed[key])  # a must be < 1
        else:
            perturbed[key] = val
    return perturbed


def run_monte_carlo(segments, pd_model, durability_params, n_draws=200, seed=42):
    """Run Monte Carlo simulation over demand profiles.

    For each draw:
    1. Perturb PD model and durability params
    2. Build demand profile with perturbed params
    3. Record per-segment completion (demand_ratio <= 1.0)

    Returns: list of segment dicts with success_probability added.
    """
    rng = np.random.default_rng(seed)
    n_segments = len(segments)

    if n_segments == 0:
        return []

    # Track completions per segment across draws
    completions = np.zeros(n_segments)
    demand_ratios_all = np.zeros((n_draws, n_segments))

    for draw in range(n_draws):
        pd_draw = _perturb_pd_model(pd_model, rng)
        dur_draw = _perturb_durability(durability_params, rng)

        profile = build_demand_profile(segments, pd_draw, dur_draw)

        for i, seg in enumerate(profile):
            dr = seg.get("demand_ratio", 0)
            demand_ratios_all[draw, i] = dr
            if dr <= 1.0:
                completions[i] += 1

    # Build result: original segments enriched with MC stats
    result = []
    for i, seg in enumerate(segments):
        enriched = dict(seg)
        prob = completions[i] / n_draws
        median_dr = float(np.median(demand_ratios_all[:, i]))
        p10_dr = float(np.percentile(demand_ratios_all[:, i], 10))
        p90_dr = float(np.percentile(demand_ratios_all[:, i], 90))

        enriched.update({
            "success_probability": round(prob, 3),
            "demand_ratio_median": round(median_dr, 4),
            "demand_ratio_p10": round(p10_dr, 4),
            "demand_ratio_p90": round(p90_dr, 4),
            "feasibility_flag": feasibility_flag(median_dr),
        })
        result.append(enriched)

    return result


def gap_analysis(segments, pd_model, durability_params, n_draws=200, seed=42):
    """Full gap analysis: Monte Carlo simulation + bottleneck identification + feasibility.

    Args:
        segments: list of segment dicts from analyze_ride_segments or analyze_gpx
        pd_model: dict from fit_pd_model
        durability_params: dict from fit_durability_model
        n_draws: number of Monte Carlo draws
        seed: random seed for reproducibility

    Returns: dict with {segments, bottleneck, overall}
    """
    mc_segments = run_monte_carlo(segments, pd_model, durability_params, n_draws, seed)

    if not mc_segments:
        return {
            "segments": [],
            "bottleneck": {},
            "overall": {
                "route_completable": False,
                "probability_of_completion": 0.0,
                "key_risk_factors": ["No segments to analyze"],
                "safety_margin_w": 0,
            },
        }

    # Also compute the deterministic demand profile for safety margin
    det_profile = build_demand_profile(segments, pd_model, durability_params)

    # Bottleneck: segment with highest median demand ratio
    hardest_idx = max(range(len(mc_segments)),
                      key=lambda i: mc_segments[i].get("demand_ratio_median", 0))
    hardest = mc_segments[hardest_idx]

    # Safety margin at bottleneck: effective_capacity - power_required
    det_hardest = det_profile[hardest_idx] if hardest_idx < len(det_profile) else {}
    safety_margin = (det_hardest.get("effective_capacity", 0) -
                     det_hardest.get("power_required", det_hardest.get("power_required", 0)))

    # Overall completion probability: probability all segments are completable
    # Use joint probability (product of independent segment probs as approximation)
    segment_probs = [s["success_probability"] for s in mc_segments]
    # Better: count draws where ALL segments were completed
    # We approximate with min(segment_probs) for conservative estimate
    overall_prob = min(segment_probs) if segment_probs else 0.0

    # Key risk factors
    risk_factors = []
    impossible_segs = [s for s in mc_segments if s["feasibility_flag"] == "impossible"]
    limit_segs = [s for s in mc_segments if s["feasibility_flag"] == "limit"]

    if impossible_segs:
        risk_factors.append(
            f"{len(impossible_segs)} segment(s) exceed current capability"
        )

    if limit_segs:
        risk_factors.append(
            f"{len(limit_segs)} segment(s) at the limit of current capability"
        )

    # Check cumulative kJ vs collapse threshold
    total_kj = sum(s.get("avg_power", 0) * s.get("duration_s", 0) / 1000
                   for s in segments if s.get("avg_power"))
    if total_kj > 0:
        last_seg = mc_segments[-1]
        if last_seg.get("demand_ratio_median", 0) > 0.95:
            risk_factors.append(
                f"Cumulative fatigue ({total_kj:.0f} kJ) degrades capacity significantly by route end"
            )

    if not risk_factors:
        risk_factors.append("No significant risks identified")

    return {
        "segments": mc_segments,
        "bottleneck": {
            "hardest_segment_idx": hardest_idx,
            "hardest_demand_ratio": hardest.get("demand_ratio_median", 0),
            "hardest_success_probability": hardest.get("success_probability", 0),
            "safety_margin_w": round(safety_margin, 1),
        },
        "overall": {
            "route_completable": overall_prob > 0.5,
            "probability_of_completion": round(overall_prob, 3),
            "key_risk_factors": risk_factors,
            "safety_margin_w": round(safety_margin, 1),
        },
    }
