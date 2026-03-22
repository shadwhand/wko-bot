# tests/test_ride_planner.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from wko5.ride_planner import plan_ride
from wko5.pacing import RidePlan
from wko5.nutrition import NutritionPlan, FeedEvent


def test_plan_ride_basic():
    """plan_ride should return pacing, nutrition, and feasibility."""
    segments = [
        {"type": "flat", "distance_m": 50000, "avg_grade": 0.0, "cumulative_kj_at_start": 0},
        {"type": "climb", "distance_m": 5000, "avg_grade": 0.05, "cumulative_kj_at_start": 500},
        {"type": "flat", "distance_m": 50000, "avg_grade": 0.0, "cumulative_kj_at_start": 800},
    ]
    ride_plan = RidePlan(target_riding_hours=4, cda=0.35, weight_rider=78, weight_bike=9)
    nutrition_plan = NutritionPlan(baseline_intake_g_hr=60)
    dur_params = {"a": 0.5, "b": 0.001, "c": 0.05}
    pd_model = {"Pmax": 1100, "FRC": 20, "mFTP": 290, "TTE": 3600}

    result = plan_ride(segments, ride_plan, nutrition_plan, pd_model, dur_params, temp_c=20)
    assert "pacing" in result
    assert "nutrition" in result
    assert "feasibility" in result
    assert "base_power" in result["pacing"]
    assert "glycogen_timeline" in result["nutrition"]
    assert "overall" in result["feasibility"]


def test_plan_ride_with_feed_events():
    """Feed events should be reflected in the nutrition output."""
    segments = [
        {"type": "flat", "distance_m": 100000, "avg_grade": 0.0, "cumulative_kj_at_start": 0},
    ]
    ride_plan = RidePlan(target_riding_hours=4)
    nutrition_plan = NutritionPlan(
        baseline_intake_g_hr=60,
        feed_events=[FeedEvent(km=50, carbs_g=100, fluid_ml=750, description="control stop")],
    )
    dur_params = {"a": 0.5, "b": 0.001, "c": 0.05}
    pd_model = {"Pmax": 1100, "FRC": 20, "mFTP": 290, "TTE": 3600}

    result = plan_ride(segments, ride_plan, nutrition_plan, pd_model, dur_params)
    assert result["nutrition"]["total_carbs_planned_g"] > 240  # 60*4 baseline + 100 from stop


def test_plan_ride_with_real_ride():
    """End-to-end with real 300km ride."""
    from wko5.segments import analyze_ride_segments
    from wko5.pdcurve import compute_envelope_mmp, fit_pd_model
    from wko5.durability import fit_durability_model

    ride = analyze_ride_segments(1628)
    if not ride["segments"]:
        return

    pd_model = fit_pd_model(compute_envelope_mmp(days=90))
    dur_params = fit_durability_model()
    if pd_model is None or dur_params is None:
        return

    # Use manual FTP if model underestimates
    if pd_model["mFTP"] < 280:
        pd_model["mFTP"] = 292

    ride_plan = RidePlan(target_riding_hours=11, cda=0.28)
    nutrition_plan = NutritionPlan(
        baseline_intake_g_hr=60,
        feed_events=[
            FeedEvent(km=85, carbs_g=80, fluid_ml=750, description="control 1"),
            FeedEvent(km=170, carbs_g=120, fluid_ml=500, description="store"),
            FeedEvent(km=250, carbs_g=100, fluid_ml=400, description="burrito"),
        ],
    )

    result = plan_ride(ride["segments"], ride_plan, nutrition_plan, pd_model, dur_params, temp_c=25)
    assert result["pacing"]["base_power"] > 100
    assert result["nutrition"]["duration_hours"] > 10
    assert "warnings" in result["nutrition"]
