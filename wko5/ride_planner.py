"""Ride planner — chains pacing, nutrition, and gap analysis into one output."""

from wko5.pacing import solve_pacing, RidePlan
from wko5.nutrition import evaluate_nutrition_plan, NutritionPlan
from wko5.gap_analysis import gap_analysis


def plan_ride(segments, ride_plan, nutrition_plan, pd_model, dur_params,
              temp_c=20, humidity_pct=50, n_draws=100):
    """Plan a complete ride: pacing → nutrition → feasibility.

    Args:
        segments: list of segment dicts from analyze_ride_segments or analyze_gpx
        ride_plan: RidePlan with target time, equipment, drafting
        nutrition_plan: NutritionPlan with feed events and baseline intake
        pd_model: dict from fit_pd_model (with mFTP, FRC, etc)
        dur_params: dict from fit_durability_model
        temp_c: ambient temperature
        humidity_pct: ambient humidity
        n_draws: Monte Carlo draws for gap analysis

    Returns: dict with {pacing, nutrition, feasibility}
    """
    # Step 1: Solve pacing
    pacing = solve_pacing(segments, ride_plan, dur_params)

    # Step 2: Map pacing output fields for downstream consumers
    # build_demand_profile expects 'power_required' and 'duration_s'
    for seg in pacing["segments"]:
        seg["power_required"] = seg.get("target_power", seg.get("power_required", 0))
        seg["duration_s"] = seg.get("estimated_duration_s", seg.get("duration_s", 0))

    # Step 3: Evaluate nutrition against paced segments
    nutrition = evaluate_nutrition_plan(
        pacing["segments"], nutrition_plan,
        ftp=pd_model.get("mFTP", 290),
        temp_c=temp_c,
        humidity_pct=humidity_pct,
    )

    # Step 4: Gap analysis on paced segments
    feasibility = gap_analysis(
        pacing["segments"], pd_model, dur_params, n_draws=n_draws,
    )

    return {
        "pacing": pacing,
        "nutrition": nutrition,
        "feasibility": feasibility,
    }
