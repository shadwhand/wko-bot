"""API route definitions."""

import math
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
import json
import numpy as np
from wko5.api.auth import verify_token, get_token_value


class _NanSafeEncoder(json.JSONEncoder):
    """JSON encoder that converts NaN/Inf/numpy types to JSON-safe values."""
    def default(self, obj):
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            if np.isnan(obj) or np.isinf(obj):
                return None
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

    def encode(self, o):
        return super().encode(_sanitize_nans(o))


def convert_numpy(obj):
    """Recursively convert numpy types to Python natives for JSON serialization."""
    if isinstance(obj, dict):
        return {k: convert_numpy(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_numpy(item) for item in obj]
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return convert_numpy(obj.tolist())
    return obj


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
import time

router = APIRouter(prefix="/api")

# Simple in-memory cache — data only changes on Garmin sync or model update
_cache = {}
_CACHE_TTL = 300  # 5 minutes
_data_version = 1


def _cached(key, fn, ttl=_CACHE_TTL):
    """Return cached result if fresh, otherwise compute and cache."""
    now = time.time()
    if key in _cache and (now - _cache[key]["t"]) < ttl:
        return _cache[key]["v"]
    result = fn()
    _cache[key] = {"v": result, "t": now}
    return result


def _invalidate_cache():
    """Clear all cached data (call after sync or model update)."""
    global _data_version
    _cache.clear()
    _data_version += 1


# Warmup state — tracks precompute results
_warmup_status = {"running": False, "done": False, "results": {}, "errors": {}}


def warmup_cache():
    """Pre-compute all expensive endpoints at startup. Call from a background thread."""
    import threading
    _warmup_status["running"] = True
    _warmup_status["done"] = False
    _warmup_status["results"] = {}
    _warmup_status["errors"] = {}

    tasks = {
        "fitness": lambda: _cached("fitness", current_fitness, ttl=86400),
        "pmc": lambda: _cached("pmc:None:None", lambda: (
            lambda df: [] if df.empty else _sanitize_nans(
                df.assign(date=df["date"].astype(str))[["date", "TSS", "CTL", "ATL", "TSB"]].to_dict(orient="records")
            )
        )(build_pmc()), ttl=86400),
        "model_90": lambda: _cached("model:90", lambda: (
            lambda mmp: {"error": "Insufficient data"} if len(mmp) < 60 else (
                lambda r: r if r is None else dict(r, mmp=_smooth_mmp(mmp))
            )(fit_pd_model(mmp))
        )(compute_envelope_mmp(days=90)), ttl=86400),
        "profile_90": lambda: _cached("profile:90", lambda: (
            lambda p: {"error": "Insufficient data"} if not p else {
                "profile": p, "ranking": coggan_ranking(p), "strengths_limiters": strengths_limiters(p)
            }
        )(power_profile(days=90)), ttl=86400),
        "rolling_ftp": lambda: _cached("rolling_ftp:90:14", lambda: rolling_ftp(window_days=90, step_days=14).to_dict(orient="records"), ttl=86400),
        "clinical": lambda: (
            lambda r: _sanitize_nans(r)
        )(get_clinical_flags(days_back=30)),
        "ftp_growth": lambda: _cached("ftp_growth", lambda: __import__("wko5.training_load", fromlist=["ftp_growth_curve"]).ftp_growth_curve(), ttl=86400),
        "rolling_pd": lambda: _cached("rolling_pd_profile", lambda: (lambda r: {"data": []} if r is None else {"data": r.to_dict(orient="records")})(__import__("wko5.pdcurve", fromlist=["rolling_pd_profile"]).rolling_pd_profile()), ttl=86400),
    }

    for name, fn in tasks.items():
        t0 = time.time()
        try:
            fn()
            elapsed = round(time.time() - t0, 1)
            _warmup_status["results"][name] = f"ok ({elapsed}s)"
            import sys; sys.stderr.write(f"  [warmup] {name}: ok ({elapsed}s)\n"); sys.stderr.flush()
        except Exception as e:
            elapsed = round(time.time() - t0, 1)
            _warmup_status["errors"][name] = str(e)
            import sys; sys.stderr.write(f"  [warmup] {name}: FAILED ({elapsed}s) — {e}\n"); sys.stderr.flush()

    _warmup_status["running"] = False
    _warmup_status["done"] = True
    ok = len(_warmup_status["results"])
    fail = len(_warmup_status["errors"])
    import sys; sys.stderr.write(f"  [warmup] Complete: {ok} ok, {fail} failed\n"); sys.stderr.flush()


@router.get("/health")
def health():
    return {
        "status": "ok",
        "cache_warm": _warmup_status["done"],
        "warmup_errors": _warmup_status["errors"] if _warmup_status["errors"] else None,
        "data_version": _data_version,
    }


@router.get("/warmup-status")
def warmup_status():
    """Check precompute warmup status — no auth needed so dashboard can poll during startup."""
    return {
        "running": _warmup_status["running"],
        "done": _warmup_status["done"],
        "results": _warmup_status["results"],
        "errors": _warmup_status["errors"],
    }


@router.get("/runtime")
def runtime_config(request: Request):
    """Return runtime config for frontend bootstrap. Localhost only, no auth."""
    host = request.client.host if request.client else ""
    if host not in ("127.0.0.1", "localhost", "::1"):
        raise HTTPException(status_code=403, detail="Localhost only")
    return {"token": get_token_value()}


@router.get("/config", dependencies=[Depends(verify_token)])
def config():
    return get_config()


@router.get("/fitness", dependencies=[Depends(verify_token)])
def fitness():
    return _cached("fitness", current_fitness)


@router.get("/pmc", dependencies=[Depends(verify_token)])
def pmc(start: str = None, end: str = None):
    """Full PMC history for charting."""
    cache_key = f"pmc:{start}:{end}"
    def compute():
        df = build_pmc(start=start, end=end)
        if df.empty:
            return []
        df["date"] = df["date"].astype(str)
        return _sanitize_nans(df[["date", "TSS", "CTL", "ATL", "TSB"]].to_dict(orient="records"))
    return _cached(cache_key, compute)


@router.get("/activities", dependencies=[Depends(verify_token)])
def activities(start: str = None, end: str = None, sub_sport: str = None,
               limit: int = 50, offset: int = 0):
    df = get_activities(start=start, end=end, sub_sport=sub_sport)
    # Sort newest first
    df = df.sort_values("start_time", ascending=False).reset_index(drop=True)
    total = len(df)
    df = df.iloc[offset:offset + limit]
    records = _sanitize_nans(df.to_dict(orient="records"))
    return {"activities": records, "total": total, "limit": limit, "offset": offset}


def _smooth_mmp(mmp):
    """WKO5-style log-spaced MMP sampling with smoothing.

    Returns ~250 points: every second up to 30s, then log-spaced with
    rolling geometric mean smoothing at longer durations.
    """
    import numpy as np
    n = len(mmp)
    indices = set()
    # Every second up to 30s
    for i in range(min(30, n)):
        indices.add(i)
    # Every 2s from 30s to 2min
    for i in range(30, min(120, n), 2):
        indices.add(i)
    # Every 5s from 2min to 10min
    for i in range(120, min(600, n), 5):
        indices.add(i)
    # Every 15s from 10min to 30min
    for i in range(600, min(1800, n), 15):
        indices.add(i)
    # Every 30s from 30min to 60min
    for i in range(1800, min(3600, n), 30):
        indices.add(i)
    # Every 60s beyond 60min
    for i in range(3600, n, 60):
        indices.add(i)
    # Always include last point
    if n > 0:
        indices.add(n - 1)

    indices = sorted(indices)
    arr = np.array(mmp, dtype=float)
    result = []
    for i in indices:
        # Smooth: average a window around i (wider at longer durations)
        window = max(1, i // 20)  # ~5% of duration
        lo = max(0, i - window)
        hi = min(n, i + window + 1)
        smoothed = float(np.mean(arr[lo:hi]))
        result.append([i + 1, round(smoothed, 1)])
    return result


@router.get("/model", dependencies=[Depends(verify_token)])
def model(days: int = 90):
    def compute():
        mmp = compute_envelope_mmp(days=days)
        if len(mmp) < 60:
            return {"error": "Insufficient data"}
        result = fit_pd_model(mmp)
        if result is None:
            return {"error": "Model fitting failed"}
        result["mmp"] = _smooth_mmp(mmp)
        return result
    return _cached(f"model:{days}", compute)


@router.get("/profile", dependencies=[Depends(verify_token)])
def profile(days: int = 90):
    def compute():
        p = power_profile(days=days)
        if not p:
            return {"error": "Insufficient data"}
        ranking = coggan_ranking(p)
        sl = strengths_limiters(p)
        return {"profile": p, "ranking": ranking, "strengths_limiters": sl}
    return _cached(f"profile:{days}", compute)


@router.get("/ride/{activity_id}", dependencies=[Depends(verify_token)])
def ride(activity_id: int, include_records: bool = True):
    # Use raw DB row so field names match the frontend RideSummary type
    # (id, filename, sport, start_time, normalized_power, etc.)
    from wko5.db import get_connection, get_records
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM activities WHERE id = ?", (activity_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return {"error": "Activity not found"}
    columns = [desc[0] for desc in cursor.description]
    summary = _sanitize_nans(dict(zip(columns, row)))
    conn.close()

    result = {"summary": summary}
    if include_records:
        records_df = get_records(activity_id)
        if not records_df.empty:
            result["records"] = _sanitize_nans(
                records_df[["elapsed_seconds", "power", "heart_rate", "cadence", "speed", "altitude"]]
                .to_dict(orient="records")
            )
        else:
            result["records"] = []
        result["intervals"] = detect_intervals(activity_id)
    return result


@router.get("/ride/{activity_id}/intervals", dependencies=[Depends(verify_token)])
def intervals(activity_id: int):
    return detect_intervals(activity_id)


@router.get("/ride/{activity_id}/efforts", dependencies=[Depends(verify_token)])
def efforts(activity_id: int):
    return best_efforts(activity_id)


@router.get("/rolling-ftp", dependencies=[Depends(verify_token)])
def rolling_ftp_endpoint(window: int = 90, step: int = 14):
    def compute():
        df = rolling_ftp(window_days=window, step_days=step)
        return df.to_dict(orient="records")
    return _cached(f"rolling_ftp:{window}:{step}", compute)


def _get_segments(activity_id):
    """Cached segment analysis per route/activity."""
    return _cached(f"segments:{activity_id}", lambda: analyze_ride_segments(activity_id))


def _get_pd_model():
    """Cached PD model — reuses warmup cache if available."""
    def compute():
        mmp = compute_envelope_mmp(days=90)
        if len(mmp) < 60:
            return None
        return fit_pd_model(mmp)
    return _cached("pd_model_raw", compute)


def _get_durability():
    """Cached durability model."""
    return _cached("durability_raw", fit_durability_model)


@router.get("/segments/{activity_id}", dependencies=[Depends(verify_token)])
def segments(activity_id: int):
    return _sanitize_nans(_get_segments(activity_id))


@router.get("/durability", dependencies=[Depends(verify_token)])
def durability():
    result = _get_durability()
    if result is None:
        return {"error": "Insufficient data for durability model"}
    return result


@router.get("/demand/{activity_id}", dependencies=[Depends(verify_token)])
def demand(activity_id: int):
    def compute():
        ride_segments = _get_segments(activity_id)
        if not ride_segments["segments"]:
            return {"error": "No segments found"}
        pd_model = _get_pd_model()
        if pd_model is None:
            return {"error": "PD model fitting failed"}
        dur_params = _get_durability()
        if dur_params is None:
            return {"error": "Insufficient data for durability model"}
        profile = build_demand_profile(ride_segments["segments"], pd_model, dur_params)
        return {"segments": profile, "summary": ride_segments["summary"]}
    return _sanitize_nans(_cached(f"demand:{activity_id}", compute))


@router.get("/gap-analysis/{activity_id}", dependencies=[Depends(verify_token)])
def gap_analysis_endpoint(activity_id: int, n_draws: int = 200):
    def compute():
        ride_segments = _get_segments(activity_id)
        if not ride_segments["segments"]:
            return {"error": "No segments found"}
        pd_model = _get_pd_model()
        if pd_model is None:
            return {"error": "PD model fitting failed"}
        dur_params = _get_durability()
        if dur_params is None:
            return {"error": "Insufficient data for durability model"}
        return gap_analysis(ride_segments["segments"], pd_model, dur_params, n_draws=n_draws)
    return _sanitize_nans(_cached(f"gap:{activity_id}:{n_draws}", compute))


@router.get("/clinical-flags", dependencies=[Depends(verify_token)])
def clinical_flags(days_back: int = 30):
    try:
        result = get_clinical_flags(days_back=days_back)
        # Normalize to {flags: [...]} format for the ClinicalDashboard component
        flags = result.get("current_flags", [])
        normalized = []
        for f in flags:
            normalized.append({
                "name": f.get("flag", f.get("name", "Unknown")),
                "status": "danger" if f.get("severity") == "red" else "warning" if f.get("severity") == "yellow" else "ok",
                "value": f.get("value", f.get("detail", "--")),
                "threshold": f.get("threshold", ""),
                "detail": f.get("detail", f.get("recommendation", "")),
            })
        # Add "all clear" entries for checks that passed
        all_checks = ["CTL Ramp Rate", "TSB Floor", "HR Decoupling", "IF Floor", "Intensity Distribution", "Panic Training"]
        flagged_names = {n["name"] for n in normalized}
        for check in all_checks:
            if check not in flagged_names:
                normalized.append({"name": check, "status": "ok", "value": "Normal", "threshold": "", "detail": "No issues detected"})
        return _sanitize_nans({"flags": normalized, "alert_level": result.get("alert_level", "green")})
    except Exception as e:
        return {"flags": [], "alert_level": "unknown", "error": str(e)}


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
def route_detail(route_id: int, include_points: bool = True):
    route = get_route(route_id)
    if route is None:
        return {"error": "Route not found"}
    route["history"] = get_route_history(route_id)
    route["plans"] = get_ride_plans(route_id)
    if include_points:
        from wko5.db import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT lat, lon, elevation, cumulative_distance_m FROM route_points "
            "WHERE route_id = ? ORDER BY point_order", (route_id,)
        )
        route["points"] = [
            {"lat": r[0], "lon": r[1], "elevation": r[2], "km": round(r[3] / 1000, 2) if r[3] else 0}
            for r in cursor.fetchall()
        ]
        conn.close()
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
    _invalidate_cache()
    return {"status": "updated"}


# ── P3 Endpoints ─────────────────────────────────────────────────────────────

@router.get("/if-distribution", dependencies=[Depends(verify_token)])
def get_if_distribution():
    from wko5.training_load import if_distribution
    return _sanitize_nans(if_distribution() or {})


@router.get("/ftp-growth", dependencies=[Depends(verify_token)])
def get_ftp_growth():
    from wko5.training_load import ftp_growth_curve
    return _sanitize_nans(_cached("ftp_growth", ftp_growth_curve) or {})


@router.get("/performance-trend", dependencies=[Depends(verify_token)])
def get_performance_trend():
    from wko5.training_load import performance_trend
    result = performance_trend()
    if result is None:
        return {"data": []}
    return _sanitize_nans({"data": result.to_dict(orient="records")})


@router.get("/opportunity-cost/{route_id}", dependencies=[Depends(verify_token)])
def get_opportunity_cost(route_id: int):
    from wko5.gap_analysis import opportunity_cost_analysis
    return _sanitize_nans(opportunity_cost_analysis(route_id) or [])


@router.post("/glycogen-budget", dependencies=[Depends(verify_token)])
def post_glycogen_budget(body: dict):
    from wko5.nutrition import glycogen_budget_daily
    return _sanitize_nans(glycogen_budget_daily(
        ride_kj=float(body.get("ride_kj", 0)),
        ride_duration_h=float(body.get("ride_duration_h", 0)),
        on_bike_carbs_g=float(body.get("on_bike_carbs_g", 0)),
        post_ride_delay_h=float(body.get("post_ride_delay_h", 1)),
        daily_carb_target_g_kg=float(body.get("daily_carb_target_g_kg", 8)),
        weight_kg=float(body.get("weight_kg", 78)),
    ))


@router.get("/rolling-pd-profile", dependencies=[Depends(verify_token)])
def get_rolling_pd_profile():
    from wko5.pdcurve import rolling_pd_profile
    def compute():
        result = rolling_pd_profile()
        if result is None:
            return {"data": []}
        return {"data": result.to_dict(orient="records")}
    return _sanitize_nans(_cached("rolling_pd_profile", compute))


@router.get("/fresh-baseline", dependencies=[Depends(verify_token)])
def get_fresh_baseline():
    from wko5.durability import check_fresh_baseline
    return _sanitize_nans(check_fresh_baseline() or {})


@router.get("/short-power-consistency", dependencies=[Depends(verify_token)])
def get_short_power_consistency():
    from wko5.gap_analysis import short_power_consistency
    return _sanitize_nans(short_power_consistency() or {})
