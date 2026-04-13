# wko5/gap_analysis.py
"""Monte Carlo demand simulation, bottleneck analysis, and route feasibility."""

import logging

import numpy as np

from wko5.demand_profile import build_demand_profile
from wko5.durability import degradation_factor
from wko5.db import get_activities, get_records

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
    1. Draw PD + durability params from Bayesian posteriors (or perturb if unavailable)
    2. Build demand profile with drawn params
    3. Record per-segment completion (demand_ratio <= 1.0)

    Returns: list of segment dicts with success_probability added.
    """
    from wko5.bayesian import load_posterior_samples

    rng = np.random.default_rng(seed)
    n_segments = len(segments)

    if n_segments == 0:
        return []

    # Try to use real posteriors
    pd_posterior = load_posterior_samples("pd_model")
    dur_posterior = load_posterior_samples("durability")

    # Track completions per segment across draws
    completions = np.zeros(n_segments)
    demand_ratios_all = np.zeros((n_draws, n_segments))

    for draw in range(n_draws):
        if pd_posterior and dur_posterior:
            # Draw from real posteriors
            pd_idx = rng.integers(0, len(pd_posterior["mFTP"]))
            pd_draw = dict(pd_model)  # keep non-sampled keys (e.g. TTE)
            for k in pd_posterior:
                pd_draw[k] = float(pd_posterior[k][pd_idx])

            dur_idx = rng.integers(0, len(dur_posterior["a"]))
            dur_draw = {k: float(dur_posterior[k][dur_idx])
                        for k in dur_posterior if k != "sigma"}
        else:
            # Fallback to Gaussian perturbation
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

    # Absolute power check (WD-60: need sufficient power first)
    max_demand = max((s.get("power_required", 0) for s in segments), default=0)
    fresh_capacity = pd_model.get("mFTP", 0)
    absolute_power_check = {
        "fresh_mftp_w": round(fresh_capacity, 1),
        "max_segment_demand_w": round(max_demand, 1),
        "fresh_power_sufficient": fresh_capacity >= max_demand * 0.95,
        "message": ("Absolute power is sufficient for this route."
                    if fresh_capacity >= max_demand * 0.95
                    else f"Fresh power ({fresh_capacity:.0f}W) may be insufficient for "
                         f"hardest segment ({max_demand:.0f}W). Durability is secondary."),
    }

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
        "absolute_power_check": absolute_power_check,
    }


def opportunity_cost_analysis(route_id):
    """Derive race demands from route segments and compare against current power profile.

    Uses linked activities from route_links/activity_routes to identify real efforts on
    this route, then builds a demand profile and quantifies how much time would be saved
    by improving each physiological dimension.

    Args:
        route_id: integer route ID from the routes table

    Returns:
        Sorted list of dicts: [{dimension: str, impact: float (minutes saved),
        level: "high"|"medium"|"low"}, ...] sorted by impact descending.
        Returns None if route not found or insufficient data.
    """
    from wko5.routes import get_route
    from wko5.segments import analyze_ride_segments
    from wko5.pdcurve import compute_envelope_mmp, fit_pd_model
    from wko5.durability import fit_durability_model
    from wko5.db import get_connection

    # Verify route exists
    route = get_route(route_id)
    if route is None:
        logger.warning(f"Route {route_id} not found")
        return None

    # Find activities linked to this route via activity_routes table
    conn = get_connection()

    # Check for route_links table first, fall back to activity_routes
    tbl_result = conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_name IN ('route_links', 'activity_routes')"
    )
    link_tables = {row[0] for row in tbl_result.fetchall()}

    linked_activity_ids = []
    if "route_links" in link_tables:
        result = conn.execute(
            "SELECT activity_id FROM route_links WHERE route_id = ?", [route_id]
        )
        linked_activity_ids = [row[0] for row in result.fetchall()]
    elif "activity_routes" in link_tables:
        result = conn.execute(
            "SELECT activity_id FROM activity_routes WHERE route_id = ?", [route_id]
        )
        linked_activity_ids = [row[0] for row in result.fetchall()]
    conn.close()

    if not linked_activity_ids:
        logger.warning(f"No activities linked to route {route_id}")
        return None

    # Analyze segments from the most recent linked activity
    segments = []
    for act_id in linked_activity_ids:
        ride = analyze_ride_segments(act_id)
        if ride["segments"]:
            segments = ride["segments"]
            break

    if not segments:
        logger.warning(f"No usable segments found for route {route_id}")
        return None

    # Fit current PD model and durability
    pd_model = fit_pd_model(compute_envelope_mmp(days=365))
    dur_params = fit_durability_model()

    if pd_model is None:
        logger.warning("Cannot fit PD model — insufficient power data")
        return None

    # Use default durability params if fitting failed
    if dur_params is None:
        dur_params = {"a": 0.5, "b": 0.001, "c": 0.05}

    # Compute baseline total time (sum of segment durations)
    baseline_time_s = sum(s.get("duration_s", 0) for s in segments)
    if baseline_time_s <= 0:
        return None

    def _simulate_time(pd_override, dur_override):
        """Estimate total route time using the demand profile with given models."""
        from wko5.demand_profile import build_demand_profile
        profile = build_demand_profile(segments, pd_override, dur_override)
        total_time = 0.0
        for i, seg in enumerate(profile):
            dur = segments[i].get("duration_s", 0)
            demand_ratio = seg.get("demand_ratio", 1.0)
            # If demand > capacity, rider must slow down — scale time proportionally
            if demand_ratio > 1.0:
                total_time += dur * demand_ratio
            else:
                total_time += dur
        return total_time

    baseline_time = _simulate_time(pd_model, dur_params)

    results = []

    # 1. FTP +10W
    pd_ftp_plus = dict(pd_model)
    pd_ftp_plus["mFTP"] = pd_model["mFTP"] + 10
    time_ftp = _simulate_time(pd_ftp_plus, dur_params)
    impact_ftp = (baseline_time - time_ftp) / 60.0

    # 2. Durability -2% fade (reduce c parameter for slower time-based decay)
    dur_better = dict(dur_params)
    dur_better["c"] = max(0.001, dur_params.get("c", 0.05) * 0.98)
    time_dur = _simulate_time(pd_model, dur_better)
    impact_dur = (baseline_time - time_dur) / 60.0

    # 3. VO2max +5W (modeled as an increase in peak power at 5-min / mFTP headroom)
    pd_vo2_plus = dict(pd_model)
    pd_vo2_plus["mFTP"] = pd_model["mFTP"] + 5
    pd_vo2_plus["Pmax"] = pd_model["Pmax"] + 5
    time_vo2 = _simulate_time(pd_vo2_plus, dur_params)
    impact_vo2 = (baseline_time - time_vo2) / 60.0

    # 4. Sprint +50W (Pmax improvement — affects short high-power segments)
    pd_sprint_plus = dict(pd_model)
    pd_sprint_plus["Pmax"] = pd_model["Pmax"] + 50
    time_sprint = _simulate_time(pd_sprint_plus, dur_params)
    impact_sprint = (baseline_time - time_sprint) / 60.0

    # 5. Nutrition optimization — reduces effective fatigue (b param, work-based decay)
    dur_nutrition = dict(dur_params)
    dur_nutrition["b"] = max(0.00001, dur_params.get("b", 0.001) * 0.9)
    time_nutrition = _simulate_time(pd_model, dur_nutrition)
    impact_nutrition = (baseline_time - time_nutrition) / 60.0

    raw = [
        ("FTP (+10W)", impact_ftp),
        ("Durability (-2% fade)", impact_dur),
        ("VO2max (+5W)", impact_vo2),
        ("Sprint (+50W)", impact_sprint),
        ("Nutrition optimization", impact_nutrition),
    ]

    def _level(impact):
        if impact >= 1.0:
            return "high"
        elif impact >= 0.25:
            return "medium"
        else:
            return "low"

    output = [
        {
            "dimension": name,
            "impact": round(max(0.0, imp), 3),
            "level": _level(max(0.0, imp)),
        }
        for name, imp in raw
    ]

    return sorted(output, key=lambda x: x["impact"], reverse=True)


def short_power_consistency(duration_s=60, days_back=365):
    """Compute peak vs median best effort at a given duration across all rides.

    Loads all activities in the lookback window, extracts the best (mean max) power
    at `duration_s` from each ride, then reports peak, typical (median), and ratio.

    A high ratio (> 1.3) indicates a consistency problem — the rider can occasionally
    produce very high power at this duration but typically doesn't. A ratio close to 1
    suggests the ceiling IS the typical output (capacity limited, not consistency).

    Args:
        duration_s: target duration in seconds (default 60)
        days_back: number of days to look back (default 365)

    Returns:
        {
            peak: float (watts),
            typical: float (median watts),
            ratio: float,
            diagnosis: "consistency" if ratio > 1.3 else "capacity",
            efforts_analyzed: int,
            message: str,
        }
        Returns None if fewer than 5 efforts are found.
    """
    import pandas as pd

    end_date = pd.Timestamp.now()
    start_date = (end_date - pd.Timedelta(days=days_back)).strftime("%Y-%m-%d")

    activities = get_activities(start=start_date)
    if activities.empty:
        return None

    best_powers = []

    for _, act in activities.iterrows():
        records = get_records(act["id"])
        if records.empty or "power" not in records.columns:
            continue

        power = records["power"].fillna(0).values.astype(float)
        n = len(power)

        if n < duration_s:
            continue  # ride is shorter than target duration

        # Compute mean max power at duration_s via sliding window
        cumsum = np.concatenate([[0], np.cumsum(power)])
        avgs = (cumsum[duration_s:] - cumsum[:n - duration_s + 1]) / duration_s
        best = float(avgs.max())

        if best > 0:
            best_powers.append(best)

    if len(best_powers) < 5:
        logger.warning(
            f"Only {len(best_powers)} efforts found at {duration_s}s, need at least 5"
        )
        return None

    arr = np.array(best_powers)
    peak = float(np.max(arr))
    typical = float(np.median(arr))

    if typical <= 0:
        return None

    ratio = round(peak / typical, 3)
    diagnosis = "consistency" if ratio > 1.3 else "capacity"

    if diagnosis == "consistency":
        message = (
            f"Peak {duration_s}s power ({peak:.0f}W) is {ratio:.1f}x your typical "
            f"({typical:.0f}W). Training focus: repeatability and pacing."
        )
    else:
        message = (
            f"Peak {duration_s}s power ({peak:.0f}W) is close to typical "
            f"({typical:.0f}W, ratio {ratio:.2f}). Training focus: raising absolute ceiling."
        )

    return {
        "peak": round(peak, 1),
        "typical": round(typical, 1),
        "ratio": ratio,
        "diagnosis": diagnosis,
        "efforts_analyzed": len(best_powers),
        "message": message,
    }
