# tests/test_nutrition.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from wko5.nutrition import (
    energy_expenditure, cho_burn_rate, fat_burn_rate,
    glycogen_timeline, time_to_bonk, sweat_rate, sodium_loss,
    evaluate_nutrition_plan, NutritionPlan, FeedEvent,
)


def test_energy_expenditure_200w():
    """200W at 23% efficiency should be ~715 kcal/hr."""
    ee = energy_expenditure(power_watts=200, efficiency=0.23)
    assert 680 < ee < 750


def test_energy_expenditure_scales_with_power():
    ee1 = energy_expenditure(150)
    ee2 = energy_expenditure(300)
    assert ee2 > ee1 * 1.9  # should roughly double


def test_cho_burn_rate_increases_with_intensity():
    """Higher intensity = more carb burning."""
    cho_low = cho_burn_rate(power_watts=150, ftp=290)
    cho_high = cho_burn_rate(power_watts=260, ftp=290)
    assert cho_high > cho_low * 1.5


def test_fat_burn_rate_peaks_at_moderate_intensity():
    """Fat burning should peak around 55-65% FTP."""
    fat_low = fat_burn_rate(power_watts=100, ftp=290)
    fat_mid = fat_burn_rate(power_watts=175, ftp=290)  # ~60% FTP
    fat_high = fat_burn_rate(power_watts=260, ftp=290)
    assert fat_mid > fat_low
    assert fat_mid > fat_high  # peaks at moderate, drops at high intensity


def test_time_to_bonk_without_fueling():
    """Without fueling at threshold, should bonk in 3-5 hours."""
    ttb = time_to_bonk(power_watts=290, ftp=290, intake_g_hr=0, starting_glycogen_g=500)
    assert 2 < ttb < 6


def test_time_to_bonk_with_fueling():
    """With fueling, bonk time should extend significantly."""
    ttb_none = time_to_bonk(power_watts=200, ftp=290, intake_g_hr=0, starting_glycogen_g=500)
    ttb_fed = time_to_bonk(power_watts=200, ftp=290, intake_g_hr=80, starting_glycogen_g=500)
    assert ttb_fed > ttb_none * 1.5


def test_glycogen_timeline():
    """Glycogen should decrease over time."""
    timeline = glycogen_timeline(
        power_series=[200] * 7200,  # 2 hours at 200W
        ftp=290,
        intake_g_hr=60,
        starting_glycogen_g=500,
    )
    assert len(timeline) > 0
    assert timeline[-1]["glycogen_g"] < 500
    assert timeline[0]["glycogen_g"] == 500


def test_sweat_rate_increases_with_heat():
    """Hotter = more sweat."""
    sr_cool = sweat_rate(power_watts=200, temp_c=15, humidity_pct=50, weight_kg=78)
    sr_hot = sweat_rate(power_watts=200, temp_c=35, humidity_pct=50, weight_kg=78)
    assert sr_hot > sr_cool


def test_sodium_loss():
    """Sodium loss should be proportional to sweat rate."""
    na = sodium_loss(sweat_rate_l_hr=1.0, sweat_na_mmol=45)
    assert 900 < na < 1200  # ~1035 mg at 45 mmol/L


def test_evaluate_nutrition_plan_basic():
    """Evaluate a simple nutrition plan."""
    paced_segments = [
        {"type": "flat", "distance_m": 50000, "target_power": 180,
         "estimated_duration_s": 3600, "elapsed_hours": 0},
        {"type": "climb", "distance_m": 5000, "target_power": 250,
         "estimated_duration_s": 1200, "elapsed_hours": 1},
        {"type": "flat", "distance_m": 50000, "target_power": 170,
         "estimated_duration_s": 3600, "elapsed_hours": 1.33},
    ]
    plan = NutritionPlan(
        baseline_intake_g_hr=60,
        feed_events=[
            FeedEvent(km=50, carbs_g=80, fluid_ml=750),
        ],
        starting_glycogen_g=500,
    )
    result = evaluate_nutrition_plan(paced_segments, plan, ftp=290, temp_c=25)
    assert "glycogen_timeline" in result
    assert "hydration_timeline" in result
    assert "bonk_risk_km" in result
    assert "total_carbs_needed_g" in result
    assert "total_fluid_needed_L" in result
    assert "warnings" in result


def test_evaluate_plan_detects_bonk_risk():
    """A long ride with low fueling should flag bonk risk."""
    # 6 hours at 250W with only 30g/hr
    paced_segments = [
        {"type": "flat", "distance_m": 30000, "target_power": 250,
         "estimated_duration_s": 3600, "elapsed_hours": i}
        for i in range(6)
    ]
    plan = NutritionPlan(baseline_intake_g_hr=30, starting_glycogen_g=500)
    result = evaluate_nutrition_plan(paced_segments, plan, ftp=290, temp_c=20)
    assert result["bonk_risk_km"] is not None
    assert result["bonk_risk_km"] < 180  # should bonk within 180km
