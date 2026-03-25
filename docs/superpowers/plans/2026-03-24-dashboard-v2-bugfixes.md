# Dashboard v2 — Phase 1 Bug Fixes

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all remaining Phase 1 bugs so the dashboard is fully functional end-to-end: Event Prep shows route analysis, ride detail opens on click, backend doesn't crash on numpy types, and developer experience is smooth (one-command startup).

**Architecture:** Four independent fix tracks that can be implemented in any order. Backend fixes first (unblocks frontend testing), then frontend wiring, then DX.

**Tech Stack:** Python/FastAPI (backend), React/TypeScript (frontend), shell script (launcher)

**Spec:** `docs/superpowers/specs/2026-03-24-dashboard-v2-rewrite.md`

**Test commands:**
- Backend: `source /tmp/fitenv/bin/activate && cd /Users/jshin/Documents/wko5-experiments && python -m pytest tests/ -v`
- Frontend: `cd frontend-v2 && npx vitest run`

---

## File Structure

```
wko5/api/
  routes.py              — MODIFY: add numpy middleware, add /route-analysis composite endpoint
  app.py                 — MODIFY: register numpy serialization middleware

frontend-v2/
  src/
    api/
      client.ts          — MODIFY: add getRouteAnalysis(), read config from .runtime.json
      types.ts           — MODIFY: add RouteAnalysisResponse type
    store/
      data-store.ts      — MODIFY: replace fetchRouteDetail with fetchRouteAnalysis, fix ride detail
    panels/
      event-prep/
        GapAnalysis.tsx       — MODIFY: read from routeAnalysis instead of routeDetail
        OpportunityCost.tsx   — MODIFY: same
        SegmentProfile.tsx    — MODIFY: same
        GlycogenBudget.tsx    — MODIFY: wire route context
    ride/
      RideDetail.tsx     — VERIFY: check rendering, fix if needed
  index.html             — MODIFY: remove hardcoded token, read from .runtime.json
  vite.config.ts         — MODIFY: read port from .runtime.json or env

start.sh                 — CREATE: launcher script
.runtime.json            — GENERATED: written by backend at startup
tests/
  test_numpy_middleware.py — CREATE: test numpy type conversion
  test_route_analysis.py   — CREATE: test composite endpoint
```

---

## Task 1: Global numpy type conversion middleware

**Problem:** `GET /gap-analysis/{id}` crashes with `'numpy.bool' object is not iterable`. Other endpoints may have similar latent bugs with numpy float64, int64, etc.

**Files:**
- Modify: `wko5/api/app.py`
- Modify: `wko5/api/routes.py`
- Create: `tests/test_numpy_middleware.py`

- [ ] **Step 1: Read current serialization approach**

Read `wko5/api/routes.py` to find the existing `_NanSafeEncoder` and `_sanitize_nans` functions.

- [ ] **Step 2: Create a comprehensive numpy-to-python converter**

Add to `wko5/api/routes.py` (or a new `wko5/api/serialization.py`):

```python
import numpy as np

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
```

- [ ] **Step 3: Apply converter in the JSON response middleware**

Update the custom JSON encoder or add a FastAPI middleware that runs `convert_numpy` on all response bodies before serialization. The cleanest approach: update `_NanSafeEncoder.default()` to handle all numpy types.

```python
class _NanSafeEncoder(json.JSONEncoder):
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
```

- [ ] **Step 4: Write tests**

```python
# tests/test_numpy_middleware.py
import numpy as np
from wko5.api.routes import convert_numpy

def test_numpy_bool():
    assert convert_numpy(np.bool_(True)) is True
    assert convert_numpy(np.bool_(False)) is False

def test_numpy_int():
    assert convert_numpy(np.int64(42)) == 42
    assert isinstance(convert_numpy(np.int64(42)), int)

def test_numpy_float():
    assert convert_numpy(np.float64(3.14)) == 3.14
    assert convert_numpy(np.float64(float('nan'))) is None

def test_nested_dict():
    d = {"feasible": np.bool_(True), "values": [np.float64(1.0), np.int64(2)]}
    result = convert_numpy(d)
    assert result == {"feasible": True, "values": [1.0, 2]}

def test_ndarray():
    arr = np.array([1.0, 2.0, 3.0])
    assert convert_numpy(arr) == [1.0, 2.0, 3.0]
```

- [ ] **Step 5: Run tests**

```bash
source /tmp/fitenv/bin/activate && python -m pytest tests/test_numpy_middleware.py -v
```

- [ ] **Step 6: Verify gap-analysis endpoint works**

```bash
curl -s -H "Authorization: Bearer $TOKEN" http://127.0.0.1:$PORT/api/gap-analysis/196
```

Should return JSON instead of 500.

- [ ] **Step 7: Commit**

```bash
git add wko5/api/routes.py wko5/api/app.py tests/test_numpy_middleware.py
git commit -m "fix: global numpy type conversion — prevents serialization crashes on all endpoints"
```

---

## Task 2: Composite route analysis endpoint

**Problem:** Event Prep panels need 4 separate API calls when a route is selected. Some fail independently. A single composite endpoint simplifies the frontend and provides atomic success/failure.

**Files:**
- Modify: `wko5/api/routes.py`
- Create: `tests/test_route_analysis.py`

- [ ] **Step 1: Add composite endpoint**

Add to `wko5/api/routes.py`:

```python
@router.get("/route-analysis/{route_id}")
def route_analysis(route_id: int, n_draws: int = 200, token: str = Depends(verify_token)):
    """Composite endpoint: route detail + demand + gap analysis + opportunity cost."""
    result = {}

    # Route detail (required)
    try:
        route = get_route(route_id)
        if not route:
            raise HTTPException(status_code=404, detail="Route not found")
        result["route"] = route
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Route not found: {e}")

    # Demand profile (optional — may fail for routes without segments)
    try:
        segments = analyze_ride_segments(route_id)  # or build_demand_profile
        result["demand"] = _sanitize_nans(segments) if segments else {"segments": [], "summary": {}}
    except Exception as e:
        result["demand"] = {"error": str(e), "segments": []}

    # Gap analysis (optional — may fail if PD model can't fit)
    try:
        gap = gap_analysis(route_id, n_draws=n_draws)
        result["gap_analysis"] = convert_numpy(gap) if gap else None
    except Exception as e:
        result["gap_analysis"] = {"error": str(e)}

    # Opportunity cost (optional — may return empty)
    try:
        opp = opportunity_cost_analysis(route_id)
        result["opportunity_cost"] = convert_numpy(opp) if opp else []
    except Exception as e:
        result["opportunity_cost"] = {"error": str(e)}

    return _json(result)
```

Note: Use `convert_numpy()` from Task 1 on each sub-result. Each section is independently try/caught so one failure doesn't kill the whole response.

- [ ] **Step 2: Write tests**

```python
# tests/test_route_analysis.py
from fastapi.testclient import TestClient
from wko5.api.app import create_app

def _get_client():
    app = create_app(token="test-token")
    return TestClient(app), "test-token"

def test_route_analysis_returns_all_sections():
    client, token = _get_client()
    # Use a known route ID from the DB
    resp = client.get("/api/route-analysis/196", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "route" in data
    assert "demand" in data
    assert "gap_analysis" in data
    assert "opportunity_cost" in data

def test_route_analysis_404_unknown():
    client, token = _get_client()
    resp = client.get("/api/route-analysis/999999", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404
```

- [ ] **Step 3: Run tests**

```bash
source /tmp/fitenv/bin/activate && python -m pytest tests/test_route_analysis.py -v
```

- [ ] **Step 4: Commit**

```bash
git add wko5/api/routes.py tests/test_route_analysis.py
git commit -m "feat: composite /route-analysis endpoint — route + demand + gap + opportunity cost"
```

---

## Task 3: Frontend route analysis wiring

**Problem:** Event Prep panels fetch route detail only. Need to use the new composite endpoint and display all sections.

**Files:**
- Modify: `frontend-v2/src/api/client.ts`
- Modify: `frontend-v2/src/api/types.ts`
- Modify: `frontend-v2/src/store/data-store.ts`
- Modify: `frontend-v2/src/panels/event-prep/GapAnalysis.tsx`
- Modify: `frontend-v2/src/panels/event-prep/OpportunityCost.tsx`
- Modify: `frontend-v2/src/panels/event-prep/SegmentProfile.tsx`

- [ ] **Step 1: Add type + client function**

In `types.ts`:
```typescript
export interface RouteAnalysisResponse {
  route: RouteDetail
  demand: { segments: any[]; summary?: any; error?: string }
  gap_analysis: { feasible?: boolean; bottleneck?: string; error?: string } | null
  opportunity_cost: any[] | { error?: string }
}
```

In `client.ts`:
```typescript
export async function getRouteAnalysis(routeId: number): Promise<RouteAnalysisResponse> {
  return fetchApi<RouteAnalysisResponse>(`/route-analysis/${routeId}`)
}
```

- [ ] **Step 2: Update store**

Replace `fetchRouteDetail` with `fetchRouteAnalysis` in `data-store.ts`:
- Add `routeAnalysis: Record<number, RouteAnalysisResponse>` to store
- `fetchRouteAnalysis(routeId)` calls `getRouteAnalysis(routeId)`, stores result
- `setSelectedRoute(id)` triggers `fetchRouteAnalysis(id)`

- [ ] **Step 3: Update Event Prep panels**

Each panel reads from `store.routeAnalysis[selectedRouteId]` instead of `store.routeDetail`:
- `GapAnalysis` → reads `.gap_analysis`, shows error message if `.error` field present
- `OpportunityCost` → reads `.opportunity_cost`
- `SegmentProfile` → reads `.demand.segments` and `.route.points`

- [ ] **Step 4: Run frontend tests**

```bash
cd frontend-v2 && npx vitest run
```

- [ ] **Step 5: Commit**

```bash
git add frontend-v2/src/
git commit -m "feat: wire Event Prep panels to composite /route-analysis endpoint"
```

---

## Task 4: Verify + fix ride detail navigation

**Problem:** Clicking a ride in the table should open the ride detail view. May already work — needs verification with browser console.

**Files:**
- Possibly modify: `frontend-v2/src/App.tsx`
- Possibly modify: `frontend-v2/src/ride/RideDetail.tsx`
- Possibly modify: `frontend-v2/src/store/data-store.ts`

- [ ] **Step 1: Verify the data flow**

Read and trace the full chain:
1. `RidesTable.tsx` → `setSelectedRide(id)` on row click
2. `data-store.ts` → `selectedRideId` state + `setSelectedRide` action
3. `App.tsx` → reads `selectedRideId`, conditionally renders `RideDetail`
4. `RideDetail.tsx` → calls `fetchRide(id)` on mount, renders metrics + chart

Check each file and verify the wiring is correct.

- [ ] **Step 2: Test manually**

Start the dev server, open browser console, click a ride. Look for:
- Console errors
- Network request to `/api/ride/{id}`
- Whether the response contains data

- [ ] **Step 3: Fix any issues found**

Common issues:
- `selectedRideId` might be `string` from data attribute but `number` in the store
- `RideDetail` might have import errors from unbuilt dependencies
- The ride endpoint might need the activity ID format checked

- [ ] **Step 4: Verify back button works**

In ride detail, clicking "Back" should call `setSelectedRide(null)` and return to the main layout.

- [ ] **Step 5: Commit if changes needed**

```bash
git add frontend-v2/src/
git commit -m "fix: ride detail navigation — verify and fix click-to-detail flow"
```

---

## Task 5: Config file coordination (.runtime.json)

**Problem:** Backend uses random port, token changes each restart. Frontend has hardcoded values.

**Files:**
- Modify: `run_api.py`
- Modify: `frontend-v2/vite.config.ts`
- Modify: `frontend-v2/index.html`
- Modify: `frontend-v2/src/api/client.ts`
- Create: `start.sh`

- [ ] **Step 1: Backend writes .runtime.json on startup**

In `run_api.py`, after determining port and token:

```python
import json
runtime = {
    "port": port,
    "token": token,
    "api_url": f"http://127.0.0.1:{port}",
    "mcp_port": None  # filled in Phase 2
}
with open(".runtime.json", "w") as f:
    json.dump(runtime, f, indent=2)
```

- [ ] **Step 2: Vite config reads port from .runtime.json**

```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { readFileSync, existsSync } from 'fs'

function getBackendPort(): number {
  try {
    if (existsSync('../.runtime.json')) {
      const runtime = JSON.parse(readFileSync('../.runtime.json', 'utf-8'))
      return runtime.port || 8000
    }
  } catch {}
  return 8000
}

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: `http://127.0.0.1:${getBackendPort()}`,
        changeOrigin: true,
      },
    },
  },
  build: { outDir: 'dist', sourcemap: true },
})
```

- [ ] **Step 3: Frontend reads token from .runtime.json via API**

Add a new unauthenticated endpoint `GET /api/runtime` that returns the token (only accessible from localhost):

```python
@router.get("/runtime")
def runtime_config(request: Request):
    """Return runtime config for frontend bootstrap. Localhost only."""
    host = request.client.host if request.client else ""
    if host not in ("127.0.0.1", "localhost", "::1"):
        raise HTTPException(status_code=403, detail="Localhost only")
    return {"token": _token}
```

Frontend `resolveToken()` can call this as a fallback if no meta tag or localStorage token exists.

- [ ] **Step 4: Remove hardcoded token from index.html**

Remove the `<meta name="wko5-token">` tag.

- [ ] **Step 5: Create launcher script**

```bash
#!/bin/bash
# start.sh — Start backend + frontend dev server
set -e

echo "Starting WKO5 backend..."
source /tmp/fitenv/bin/activate
cd "$(dirname "$0")"
python run_api.py &
BACKEND_PID=$!
sleep 4

# Read runtime config
PORT=$(python3 -c "import json; print(json.load(open('.runtime.json'))['port'])")
TOKEN=$(python3 -c "import json; print(json.load(open('.runtime.json'))['token'])")
echo "Backend running on port $PORT"

echo "Starting frontend dev server..."
cd frontend-v2
npm run dev &
FRONTEND_PID=$!

echo ""
echo "  Dashboard: http://localhost:5173?token=$TOKEN"
echo "  API:       http://127.0.0.1:$PORT"
echo ""
echo "Press Ctrl+C to stop both servers"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
```

- [ ] **Step 6: Add .runtime.json to .gitignore**

- [ ] **Step 7: Commit**

```bash
git add run_api.py frontend-v2/vite.config.ts frontend-v2/index.html frontend-v2/src/api/client.ts start.sh .gitignore
git commit -m "feat: config file coordination — .runtime.json + launcher script"
```

---

## Task 6: Research — MMP/PD model smoothing (no code changes)

**Problem:** The MMP curve is jagged and the PD model fit may not match WKO5's approach.

**Files:** None (research only)

- [ ] **Step 1: Research WKO5 PD model**

Investigate:
- The 4-parameter model functional form (Pmax, FRC, mFTP, TTE)
- How WKO5 smooths the MMP envelope (monotonic decreasing constraint? rolling average?)
- What Intervals.icu does for their PD curve
- Published papers on the Morton/CP model variants
- Whether our `fit_pd_model` in `wko5/pdcurve.py` matches the standard approach

- [ ] **Step 2: Document findings**

Write findings to `docs/research/pd-model-smoothing.md` with:
- What WKO5 does
- What we currently do
- Recommended changes (if any)
- Code references

- [ ] **Step 3: Create follow-up task if changes needed**

If the research reveals our model is wrong or the smoothing approach needs work, create a separate implementation plan for those changes.
