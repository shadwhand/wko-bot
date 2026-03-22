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
