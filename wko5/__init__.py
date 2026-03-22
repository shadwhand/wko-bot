"""WKO5-style cycling power analysis library."""

from wko5.db import get_connection, get_activities, get_records, WEIGHT_KG, FTP_DEFAULT
from wko5.config import get_config, set_config, init_config_table
from wko5.pdcurve import compute_envelope_mmp, fit_pd_model, rolling_ftp
from wko5.training_load import build_pmc, current_fitness, compute_np
from wko5.zones import coggan_zones, ilevels, time_in_zones
from wko5.ride import ride_summary, detect_intervals
from wko5.profile import power_profile, strengths_limiters, phenotype
from wko5.physics import power_required, speed_from_power
from wko5.segments import analyze_ride_segments, analyze_gpx
from wko5.durability import fit_durability_model, effective_capacity, frc_budget_simulate
from wko5.demand_profile import build_demand_profile
from wko5.gap_analysis import gap_analysis, run_monte_carlo
from wko5.clinical import get_clinical_flags, check_ctl_ramp_rate, check_tsb_floor
from wko5.pacing import solve_pacing, RidePlan
from wko5.nutrition import evaluate_nutrition_plan, NutritionPlan, FeedEvent, time_to_bonk, cho_burn_rate
from wko5.ride_planner import plan_ride
