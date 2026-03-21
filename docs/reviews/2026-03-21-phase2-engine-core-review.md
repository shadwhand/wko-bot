# Review: Phase 2 Engine Core Implementation Plan

**Date:** 2026-03-21
**Document:** docs/superpowers/plans/2026-03-21-phase2-engine-core.md
**Reviewers:** Principal Engineer (opus), Product Designer (sonnet), Security Engineer (opus)
**Synthesizer:** opus

---

## Cross-Review Consensus

1. **Missing `cumulative_kJ_at_start` on segments** (Principal 3d, Designer) — load-bearing for Phase 3 durability composition. Spec line 267 explicitly requires it.

2. **Durability model never persisted to DB** (Principal 3e, Designer C1) — spec defines `durability_models` table but plan never writes to it. Re-fits from scratch every call.

3. **GPX parsing has no input guards** (Security F1, Designer C6) — no file size limit, no trackpoint cap, no path validation.

4. **`rolling_descent` type not in spec** (Principal 2c, Designer C5) — no downstream consumer, inconsistent API shape.

5. **`power_required` missing for flat/descent segments** (Principal 3c, Designer) — spec says all segments get power_required.

6. **FRC constants hardcoded** (Designer C3/C7) — `recovery_rate=0.5` and depletion threshold `0.5` violate "nothing hardcoded" rule.

7. **MMP computation is O(n^2) per window** (Principal 1b) — estimated 30-60 min, not the plan's claimed 1-2 min.

8. **`tss_weighted_kj` is mathematically wrong** (Principal 2b) — conflates cumulative and windowed quantities.

---

## Conflicts & Disagreements

**1. Severity of `set_config()` SQL pattern**
Security rates f-string column name as HIGH. Principal doesn't flag it. Real risk: LOW today (allowlist effective), MEDIUM in multi-athlete future. Regex validation (`^[a-z_]+$`) is cheap insurance.

**2. `brentq` boundary return behavior**
Security treats as acceptable. Designer flags as workflow gap needing a warning. Designer is correct — silently returning 0.1 m/s or 30 m/s produces nonsensical estimates downstream.

**3. Auth bypass criticality**
Security flags `if _token is None: return` as HIGH combined with expensive endpoints. Phase 1 issue that Phase 2 makes more dangerous.

---

## Prioritized Action List

| Priority | Finding | Source | Recommendation |
|----------|---------|--------|----------------|
| P0 | MMP computation ~30-60 min, not 1-2 min | Principal | Compute only at 4 durations (60s, 300s, 2400s, 3600s) via vectorized rolling max. ~2,000x speedup |
| P0 | `build_demand_profile()` missing — core deliverable | Principal | Add `demand_profile.py` composing segments + durability into demand ratios |
| P0 | `cumulative_kJ_at_start` missing from segment output | Principal + Designer | Add running kJ accumulator to `classify_segments` |
| P1 | Durability params not persisted to DB | Principal + Designer | Write to `durability_models` table, check cache before re-fitting |
| P1 | `tss_weighted_kj` mathematically incoherent | Principal | Replace with cumulative TSS (sum of per-second power^2 / FTP / 3600) |
| P1 | GPX: no file size limit, trackpoint cap, path validation | Security + Designer | Check size (<50MB), cap points (500K), use UploadFile for API |
| P1 | `analyze_gpx` fits PD model on every call | Principal | Accept model params as argument or cache |
| P1 | `power_required` not computed for flat/descent | Principal | Compute for all segment types per spec |
| P2 | `rolling_descent` not in spec | Principal + Designer | Remove. Use spec's 4 types |
| P2 | FRC recovery_rate and depletion threshold hardcoded | Designer | Move to athlete config |
| P2 | Decay model non-identifiable (kJ/hours correlated) | Principal | Warn when input correlation > 0.9 |
| P2 | No end-to-end integration test | Designer | One test: GPX → segments → durability → FRC budget |
| P2 | `speed_from_power` silently returns boundary | Designer | Add warning log on fallback |
| P2 | Test coverage thin: `or` assertions, vacuous DB tests | Principal + Designer | Add synthetic tests, fix assertions |
| P3 | Circadian adjustment / collapse zone not mentioned | Principal | Document as explicitly deferred |
| P3 | CORS won't match Electron ephemeral port | Security | Use `allow_origin_regex` |
| P3 | Tests run against production DB | Security | Add `PRAGMA query_only = ON` |

---

## Open Questions

1. **Is `build_demand_profile()` in Phase 2 scope or Phase 3?** → Resolved: in scope, new `demand_profile.py` module.
2. **What should `tss_weighted_kj` actually be?** → Resolved: cumulative TSS.
3. **Is circadian adjustment deferred?** The `durability_models` table has a `circadian_amplitude` column that will be NULL.
4. **Should durability fitting be manual trigger or auto?** GET (cached) vs POST (triggers fit).

---

## Scope Reduction Opportunities

- **Defer `analyze_gpx` to Task 2b** — most security surface, ride segment analysis is sufficient for Phase 2 validation
- **Drop `rolling_descent`** — merge into `descent`
- **Defer `repeatability_index`** — no consumer in Phase 2, vacuous test
- **Defer skill update** — do it after modules are stable

---

## Implementation Cost Estimate

- **Files to create:** 4 (physics.py, segments.py, durability.py, demand_profile.py)
- **Test files to create:** 4 (test_physics.py, test_segments.py, test_durability.py, test_demand_profile.py)
- **Files to modify:** 3 (routes.py, __init__.py, test_api.py)
- **Total files:** 11
- **Integration surfaces:** 8
- **Estimated token budget:** ~120K tokens
- **Agent dispatches:** 6-8
- **Key risk areas:** MMP performance fix, durability model convergence, tss_weighted_kj redesign, demand profile composition

---

## Individual Reviews

<details>
<summary>Principal Engineer — Full Review</summary>

### 1. Architectural Risks

**1a. `get_config()` called inside hot loops (segments.py, line 564)**
In `classify_segments`, `get_config()` is called once per segment inside the loop at line 563-573 of the plan. While the config is cached after first fetch, the function still copies the dict every time. The bigger problem is coupling: `classify_segments` should be a pure data-processing function. Config should be a parameter.

**1b. `fit_durability_model` loads every long ride into memory (plan lines 965-1004)**
The function calls `get_records(ride["id"])` for each of potentially 337+ long rides. More critically, `compute_windowed_mmp` calls `compute_mmp` on each 2-hour window. `compute_mmp` is O(n^2). A 2-hour window = 7,200 seconds = ~52M iterations per window. ~700 windows x 52M = ~36 billion operations. Estimated 30-60 minutes, not 1-2 minutes.

**1c. SQLite connection management not safe for concurrent API use.** Multiple connections can produce `database is locked` errors. Phase 2 makes this more likely because `fit_durability_model` holds a connection pattern for minutes.

**1d. `_decay_model` fitting is non-identifiable under certain data distributions.** kJ and hours are strongly correlated. Optimizer cannot separate the two terms.

### 2. Over-Engineering Concerns

- `analyze_gpx` fits PD model on every call (wasteful)
- `tss_weighted_kj` is mathematically incoherent (multiplies cumulative kJ by current window's NP/FTP)
- Five segment types is more than needed (`rolling_descent` not in spec)

### 3. Missing Pieces

- No circadian adjustment (spec Phase 2b)
- No collapse zone detection (spec Sub-project 2)
- No `power_required` for flat/descent segments
- No `cumulative_kJ_at_start` field (spec requires it)
- No persistence of durability model parameters
- `repeatability_index` has no synthetic test
- GPX with no elevation data silently produces all-flat segments

### 4. Sequencing Issues

- Durability fitting independent of segments (could parallel)
- Task 4 underspecified — missing demand profile endpoint
- Phase 2 imports in `__init__.py` could break entire package

### 5. Feasibility

Buildable with one major exception: O(n^2) MMP performance. Highest-risk integration: missing segments + durability composition.

### 6. Recommendations (ranked)

1. Add `build_demand_profile()` — the missing glue
2. Fix MMP performance — compute at specific durations only (~2,000x speedup)
3. Persist durability params to DB
4. Fix `tss_weighted_kj`
5. Pass config as parameter to `classify_segments`
6. Add `cumulative_kJ_at_start` to segment output
7. Add synthetic test for `repeatability_index`
8. Document what is explicitly deferred

</details>

<details>
<summary>Product Designer — Full Review</summary>

### UX Strengths

- TDD structure with explicit pass/fail expectations
- Commit granularity is appropriate
- `_sanitize_nans()` is important for JSON serialization
- Error return pattern (structured dicts) is correct for library+API
- `min_rides=5` guard fails fast with clear message
- Skill update in Task 5 closes the loop for Layer 3

### UX Concerns

- C1: Durability model fit is blocking with no progress signal, not cached
- C2: `analyze_gpx()` makes two expensive DB calls inline
- C3: FRC deep depletion threshold (50%) is hardcoded and undocumented
- C4: Test coverage thin — `or` assertions, vacuous DB tests
- C5: `rolling_descent` created but never surfaced
- C6: GPX has no file size or waypoint count guard
- C7: `recovery_rate = 0.5` is unexplained

### API Contract Issues

- Inconsistent null handling across modules
- `duration_s` vs `estimated_duration_s` field name divergence
- `power_required` computed for climbs only in ride analysis, all segments in GPX
- `cumulative_kJ_at_start` missing — load-bearing for Phase 3

### Workflow Gaps

- No data validation on durability model input quality
- No incremental update path for durability model
- `brentq` failure returns boundary silently
- No end-to-end integration test
- Skill update underspecified

### Recommendations (ranked)

1. Add `cumulative_kJ_at_start` to every segment dict
2. Wire durability to `durability_models` cache table
3. Move FRC thresholds to athlete config
4. Add downsampling to `analyze_gpx` for large files
5. Fix `test_frc_budget_recovery_ceiling_degrades` assertion
6. Classify `rolling_descent` as `"recovery"` or remove
7. Unify null handling
8. Reconcile endpoint shape between plan and spec
9. Add end-to-end integration test

</details>

<details>
<summary>Security Engineer — Full Review</summary>

### FINDING 1 — HIGH: GPX `analyze_gpx()` has no file size limit, no trackpoint cap, no path validation

No file size check before parsing. No cap on trackpoint count. No path validation on `gpx_path`. Remediation: check size (<50MB), cap trackpoints (500K), use `UploadFile` + temp dir for API.

### FINDING 2 — HIGH: `set_config()` builds SQL with f-string column name

Currently safe due to allowlist check against `DEFAULTS` dict, but pattern is latent injection vector. Remediation: validate key matches `^[a-z_]+$` as second defense.

### FINDING 3 — MEDIUM: `fit_durability_model()` expensive and exposed via potentially unauthenticated GET

Multi-minute computation, no caching. Auth bypass: `if _token is None: return` means no token = all endpoints open. Remediation: cache results, add computation lock, fix auth to fail closed.

### FINDING 4 — MEDIUM: CORS origins won't match Electron ephemeral port

Origins don't include port numbers. Starlette does exact match. Remediation: use `allow_origin_regex`.

### FINDING 5 — MEDIUM: Tests run against production DB

Future write tests could corrupt 8 years of data. Remediation: `PRAGMA query_only = ON` or DB copy fixture.

### FINDING 6 — LOW: Bearer token in global variable, handoff unspecified

Token persists in process memory. Transmission channel not documented. Remediation: temp file with 0600 permissions.

### NON-FINDINGS (confirmed safe)

- defusedxml for GPX ✓
- Parameterized SQL in db.py ✓
- FastAPI type coercion ✓
- scipy curve_fit bounds ✓

</details>
