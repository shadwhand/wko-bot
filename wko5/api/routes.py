"""API route definitions."""

import math
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
import json
from wko5.api.auth import verify_token


class _NanSafeEncoder(json.JSONEncoder):
    """JSON encoder that converts NaN/Inf to None."""
    def default(self, obj):
        return super().default(obj)

    def encode(self, o):
        return super().encode(_sanitize_nans(o))


def _sanitize_nans(obj):
    """Recursively replace NaN/Inf with None for JSON serialization."""
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    if isinstance(obj, dict):
        return {k: _sanitize_nans(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_nans(v) for v in obj]
    return obj
from wko5.config import get_config
from wko5.segments import analyze_ride_segments
from wko5.durability import fit_durability_model
from wko5.demand_profile import build_demand_profile
from wko5.gap_analysis import gap_analysis
from wko5.clinical import get_clinical_flags
from wko5.pacing import solve_pacing, RidePlan
from wko5.nutrition import NutritionPlan, FeedEvent
from wko5.ride_planner import plan_ride
from wko5.blocks import block_stats, detect_phase, feasibility_projection
from wko5.routes import save_route as save_route_fn, get_route, get_all_routes, get_route_history, get_ride_plans
from wko5.training_load import current_fitness, build_pmc
from wko5.pdcurve import compute_envelope_mmp, fit_pd_model, rolling_ftp
from wko5.profile import power_profile, coggan_ranking, strengths_limiters, phenotype
from wko5.ride import ride_summary, detect_intervals, best_efforts, hr_decoupling
from wko5.zones import coggan_zones, ilevels, ride_distribution
from wko5.db import get_activities

router = APIRouter(prefix="/api")


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/config", dependencies=[Depends(verify_token)])
def config():
    return get_config()


@router.get("/fitness", dependencies=[Depends(verify_token)])
def fitness():
    return current_fitness()


@router.get("/activities", dependencies=[Depends(verify_token)])
def activities(start: str = None, end: str = None, sub_sport: str = None):
    df = get_activities(start=start, end=end, sub_sport=sub_sport)
    return _sanitize_nans(df.to_dict(orient="records"))


@router.get("/model", dependencies=[Depends(verify_token)])
def model(days: int = 90):
    mmp = compute_envelope_mmp(days=days)
    if len(mmp) < 60:
        return {"error": "Insufficient data"}
    result = fit_pd_model(mmp)
    if result is None:
        return {"error": "Model fitting failed"}
    return result


@router.get("/profile", dependencies=[Depends(verify_token)])
def profile(days: int = 90):
    p = power_profile(days=days)
    if not p:
        return {"error": "Insufficient data"}
    ranking = coggan_ranking(p)
    sl = strengths_limiters(p)
    return {"profile": p, "ranking": ranking, "strengths_limiters": sl}


@router.get("/ride/{activity_id}", dependencies=[Depends(verify_token)])
def ride(activity_id: int):
    summary = ride_summary(activity_id)
    if not summary:
        return {"error": "Activity not found"}
    return summary


@router.get("/ride/{activity_id}/intervals", dependencies=[Depends(verify_token)])
def intervals(activity_id: int):
    return detect_intervals(activity_id)


@router.get("/ride/{activity_id}/efforts", dependencies=[Depends(verify_token)])
def efforts(activity_id: int):
    return best_efforts(activity_id)


@router.get("/rolling-ftp", dependencies=[Depends(verify_token)])
def rolling_ftp_endpoint(window: int = 90, step: int = 14):
    df = rolling_ftp(window_days=window, step_days=step)
    return df.to_dict(orient="records")


@router.get("/segments/{activity_id}", dependencies=[Depends(verify_token)])
def segments(activity_id: int):
    result = analyze_ride_segments(activity_id)
    return _sanitize_nans(result)


@router.get("/durability", dependencies=[Depends(verify_token)])
def durability():
    result = fit_durability_model()
    if result is None:
        return {"error": "Insufficient data for durability model"}
    return result


@router.get("/demand/{activity_id}", dependencies=[Depends(verify_token)])
def demand(activity_id: int):
    ride_segments = analyze_ride_segments(activity_id)
    if not ride_segments["segments"]:
        return {"error": "No segments found"}
    pd_model = fit_pd_model(compute_envelope_mmp(days=90))
    if pd_model is None:
        return {"error": "PD model fitting failed"}
    dur_params = fit_durability_model()
    if dur_params is None:
        return {"error": "Insufficient data for durability model"}
    profile = build_demand_profile(ride_segments["segments"], pd_model, dur_params)
    return _sanitize_nans({"segments": profile, "summary": ride_segments["summary"]})


@router.get("/gap-analysis/{activity_id}", dependencies=[Depends(verify_token)])
def gap_analysis_endpoint(activity_id: int, n_draws: int = 200):
    ride_segments = analyze_ride_segments(activity_id)
    if not ride_segments["segments"]:
        return {"error": "No segments found"}
    pd_model = fit_pd_model(compute_envelope_mmp(days=90))
    if pd_model is None:
        return {"error": "PD model fitting failed"}
    dur_params = fit_durability_model()
    if dur_params is None:
        return {"error": "Insufficient data for durability model"}
    result = gap_analysis(ride_segments["segments"], pd_model, dur_params, n_draws=n_draws)
    return _sanitize_nans(result)


@router.get("/clinical-flags", dependencies=[Depends(verify_token)])
def clinical_flags(days_back: int = 30):
    result = get_clinical_flags(days_back=days_back)
    return _sanitize_nans(result)


@router.post("/plan-ride", dependencies=[Depends(verify_token)])
def plan_ride_endpoint(body: dict):
    """Plan a ride with pacing, nutrition, and feasibility analysis."""
    activity_id = body.get("activity_id")
    if not activity_id:
        return {"error": "activity_id required"}

    ride_segments = analyze_ride_segments(activity_id)
    if not ride_segments["segments"]:
        return {"error": "No segments found"}

    pd_model = fit_pd_model(compute_envelope_mmp(days=90))
    if pd_model is None:
        return {"error": "PD model fitting failed"}

    cfg = get_config()
    if pd_model["mFTP"] < cfg["ftp_manual"] * 0.85:
        pd_model["mFTP"] = cfg["ftp_manual"]

    dur_params = fit_durability_model()
    if dur_params is None:
        return {"error": "Insufficient data for durability model"}

    ride_plan = RidePlan(
        target_riding_hours=body.get("target_riding_hours", 4),
        rest_hours=body.get("rest_hours", 0),
        cda=body.get("cda", cfg["cda"]),
        drafting_pct=body.get("drafting_pct", 0),
        drafting_savings=body.get("drafting_savings", 0.30),
    )

    feed_events = [FeedEvent(**e) for e in body.get("feed_events", [])]
    nutrition_plan = NutritionPlan(
        baseline_intake_g_hr=body.get("baseline_intake_g_hr", cfg["fueling_rate_g_hr"]),
        feed_events=feed_events,
        starting_glycogen_g=body.get("starting_glycogen_g", 500),
    )

    result = plan_ride(
        ride_segments["segments"], ride_plan, nutrition_plan, pd_model, dur_params,
        temp_c=body.get("temp_c", 20),
        humidity_pct=body.get("humidity_pct", 50),
    )
    return _sanitize_nans(result)


@router.get("/training-blocks", dependencies=[Depends(verify_token)])
def training_blocks(start: str = "2025-01-01", end: str = None):
    from datetime import datetime
    if not end:
        end = datetime.now().strftime("%Y-%m-%d")
    result = block_stats(start, end)
    return _sanitize_nans(result)


@router.get("/weekly-summary", dependencies=[Depends(verify_token)])
def weekly_summary_endpoint(start: str = "2025-01-01", end: str = None):
    from datetime import datetime
    from wko5.blocks import weekly_summary
    if not end:
        end = datetime.now().strftime("%Y-%m-%d")
    df = weekly_summary(start, end)
    return _sanitize_nans(df.to_dict(orient="records"))


@router.get("/detect-phase", dependencies=[Depends(verify_token)])
def detect_phase_endpoint(start: str = "2025-01-01", end: str = None):
    from datetime import datetime
    if not end:
        end = datetime.now().strftime("%Y-%m-%d")
    return detect_phase(start, end)


@router.get("/feasibility", dependencies=[Depends(verify_token)])
def feasibility(target_ctl: int = 80, weeks: int = 12):
    return feasibility_projection(target_ctl, weeks)


@router.get("/routes", dependencies=[Depends(verify_token)])
def list_routes():
    return get_all_routes()


@router.get("/routes/{route_id}", dependencies=[Depends(verify_token)])
def route_detail(route_id: int):
    route = get_route(route_id)
    if route is None:
        return {"error": "Route not found"}
    route["history"] = get_route_history(route_id)
    route["plans"] = get_ride_plans(route_id)
    return _sanitize_nans(route)


@router.get("/posterior-summary", dependencies=[Depends(verify_token)])
def posterior_summary():
    from wko5.bayesian import get_posterior_summary
    pd_summary = get_posterior_summary("pd_model")
    dur_summary = get_posterior_summary("durability")
    return _sanitize_nans({"pd_model": pd_summary, "durability": dur_summary})


@router.post("/update-models", dependencies=[Depends(verify_token)])
def update_models():
    from wko5.bayesian import update_all_models
    update_all_models()
    return {"status": "updated"}
