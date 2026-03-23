# Review: P3 Code Changes + Configurable Dashboard Design Spec

**Date:** 2026-03-23
**Document:** docs/superpowers/specs/2026-03-23-p3-dashboard-design.md
**Reviewers:** Principal Engineer, Product Designer, Security Engineer
**Synthesizer:** opus
**Scope:** 16 P3 backend functions, 10 new API endpoints, per-user layout system, edit mode, 6 new chart panels

---

## 1. Cross-Review Consensus

Eight issues were flagged independently by two or more reviewers. These are the highest-confidence findings.

### C1. User identity does not exist (Principal 1, Designer 1, Security HIGH-2)

The spec builds per-user layout storage on `user_token`, but the codebase has a single shared bearer token with no user concept. `auth.py` has one global `_token`; there is no login, no user switcher, no way to distinguish JinUk from Fabiano. The layout table uses raw token as primary key, which the Security reviewer escalates to CRITICAL (credential at rest). All three reviewers agree: the identity model is load-bearing and unresolved.

### C2. `dashboard.js` is a 1,250-line monolith with hardcoded panel wiring (Principal 3, 10, Designer 3)

The current `dashboard.js` has a `loadTab()` switch statement dispatching to `loadToday()`, `loadFitness()`, `loadEventPrep()`, `loadHistory()`, `loadProfile()` -- each function hardcodes which panels exist and which DOM selectors to use. Converting to dynamic panel instantiation from a registry is effectively a rewrite. The spec lists `layout-manager.js` and `panel-registry.js` as new files but does not acknowledge the `dashboard.js` refactor as a work item.

### C3. `allostatic_load_estimate` has weak data contract (Principal 6, Designer 7)

RPE is not in FIT files. "Comment sentiment" requires TP data that may not exist. "Missed sessions" has no ground truth (how do you know a session was missed vs. a rest day?). The function will be mostly stubbed. Designer adds: there is no UI surface to explain the inputs or their provenance.

### C4. `opportunity_cost_analysis` has undefined inputs (Principal 7, Designer 6)

The function signature requires `race_demands` and `durability_params` but the spec does not define where these come from. The endpoint is `GET /opportunity-cost/{route_id}` but no route selection UI exists. The data contract is incomplete on both sides.

### C5. Auth bypass when `_token is None` (Principal implicit, Security CRITICAL-2)

`auth.py` line 16-17: `if _token is None: return` -- this is fail-open. When no token is configured, all endpoints are unprotected. Flagged in Phase 2 review and still unfixed.

### C6. Missing panels in registry (Designer 3)

The default Health tab layout includes `if-floor` and `panic-training` panels, but these do not appear in the panel registry definition or the new chart files list. The spec has a hole -- these panels will fail to render.

### C7. No error/empty states for chart panels (Principal implicit, Designer 8, 12)

No error state is defined when a panel endpoint fails. For clinical panels, a silent empty panel is dangerous -- the coach could misread "no flags rendered" as "health is fine." Empty tab state is also undefined.

### C8. Raw bearer token stored as DB primary key (Security CRITICAL-1, Principal 1)

Storing the literal token in `dashboard_layouts.user_token` puts credentials at rest in SQLite. Anyone with file access can extract valid tokens.

---

## 2. Conflicts & Disagreements

### D1. Backend layout storage vs. localStorage

The Principal recommends replacing the backend layout system entirely with localStorage presets, eliminating the identity problem. The Designer implicitly assumes server-side storage (asks for "view as other user" feature). The Security reviewer accepts server-side storage but demands hashing and isolation.

**Resolution:** The Principal is correct for the current 2-user reality. localStorage presets eliminate the identity, credential-at-rest, and layout isolation problems simultaneously. If cross-device sync is needed later, add server-side storage with a proper user model at that time.

### D2. Severity of `auto_error=False`

Security rates it LOW (weakens defense-in-depth). Principal does not flag it. In the current architecture, `verify_token` manually handles the None-credentials case, so `auto_error=False` is functionally neutral -- but it makes the fail-open bug in C5 possible. Fixing C5 makes this moot.

### D3. `glycogen_budget` panel type

The Principal says this should be an interactive form (requires manual input: ride_kj, duration, carbs, weight, etc.). The Designer praises it as "strongest visualization." Both are right: the visualization is strong, but a passive panel cannot drive a function that needs manual parameters. It needs an input form that drives the chart.

---

## 3. Prioritized Action List

All findings from all three reviews, deduplicated and ranked. P0 = must fix before implementation begins, P1 = must fix during implementation, P2 = should fix, P3 = nice to have.

| # | Pri | Finding | Source | Action |
|---|-----|---------|--------|--------|
| 1 | P0 | User identity does not exist; layout system built on nonexistent concept | C1 | Switch to localStorage presets with `athlete`/`coach` keys. No backend layout table. |
| 2 | P0 | `dashboard.js` refactor is invisible in spec | C2 | Add explicit "Dashboard Refactor" section scoping the rewrite of `loadTab()` dispatch, panel instantiation, and DOM wiring. |
| 3 | P0 | Auth bypass: `_token is None` is fail-open | C5 | Change `auth.py` line 16-17 to `raise HTTPException(403)`. |
| 4 | P0 | `if-floor` and `panic-training` missing from registry and chart files | C6 | Either add them to registry + file list or remove from default layout. |
| 5 | P1 | Raw token as DB PK (if backend layout kept) | C8 | Moot if localStorage adopted (item 1). Otherwise use `SHA-256(token)`. |
| 6 | P1 | No input validation/size limit on layout JSON | Security HIGH-1 | If localStorage: browser-enforced. If backend: add schema validation + 64KB limit. |
| 7 | P1 | `opportunity_cost_analysis` has undefined data contract | C4 | Define `race_demands` schema, source, and UI for route selection -- or defer the panel. |
| 8 | P1 | `glycogen_budget` needs interactive form, not passive panel | D3 | Design input form (ride kJ, carbs, weight, timing) that drives the chart. |
| 9 | P1 | No error states for panels | C7 | Define error card (red border, retry button) and empty-state card. Clinical panels must show "unable to check" rather than blank. |
| 10 | P1 | Cache TTL missing for expensive new endpoints | Principal 5 | Add `rolling_pd_profile` and `ftp_growth` to `warmup_cache()` with appropriate TTLs. |
| 11 | P1 | `route_id` path param needs type constraint | Security MEDIUM-1 | Add `route_id: int` type annotation on FastAPI endpoint. |
| 12 | P1 | Panel endpoint resolution must be registry-only | Security MEDIUM-2 | Frontend must resolve endpoints from `WKO5.panels`, never from stored layout JSON. |
| 13 | P2 | `allostatic_load_estimate` is mostly stubbed | C3 | Defer to a later phase when RPE/TP data pipeline exists. |
| 14 | P2 | HTML5 DnD is fragile | Principal 2 | Use SortableJS (~8KB) instead of native DnD. Handles touch, animation, edge cases. |
| 15 | P2 | Edit mode has no undo/cancel | Designer 4 | Add "Cancel" button alongside "Done". Store pre-edit snapshot. |
| 16 | P2 | No "Layout saved" confirmation | Designer 9 | Toast notification on successful save; error toast on failure. |
| 17 | P2 | `check_reds_flags` gap-to-illness heuristic undefined | Principal 11 | Define threshold: e.g., gap >= 3 days within 8 weeks of high CTL = illness flag. |
| 18 | P2 | No DELETE endpoint for layout | Principal 12 | Add `DELETE /layout` to reset to defaults (or "Reset" button in localStorage approach). |
| 19 | P2 | No CSRF protection on PUT /layout | Security MEDIUM-3 | SameSite cookie or custom header check. Lower priority if localStorage approach adopted. |
| 20 | P2 | Add-panel modal has no descriptions | Designer 5 | Add `description` field to panel registry; show in modal. |
| 21 | P2 | Panel removal UX unclear | Designer 13 | Show tooltip "Removed from tab. Available in catalog." |
| 22 | P2 | No tab name validation | Designer 11 | Enforce: non-empty, <= 20 chars, no duplicates. |
| 23 | P3 | No "view as other user" for coach | Designer 10 | Defer. Only relevant if backend layout system is built. |
| 24 | P3 | Race condition: layout save during panel data fetch | Principal 4 | Guard: disable save while fetches in-flight, or snapshot layout at save-click time. |
| 25 | P3 | Health tab panel hierarchy undefined | Designer 2 | Make `clinical-flags` full-width at top of Health tab. |
| 26 | P3 | `energy_expenditure` uncertainty parameter | Spec | Low risk, backward-compatible. Implement as specified. |

---

## 4. Open Questions

The spec author should resolve these before implementation begins.

**Q1. Identity model decision.** Will you adopt localStorage presets (eliminating backend layout storage) or build a proper user model? This is a blocking architectural decision that cascades into 6+ items above.

**Q2. Which panels exist today?** The spec references `if-floor` and `panic-training` in the default layout but they are not in the panel registry or new chart file list. Are these existing panels being promoted, new panels that were accidentally omitted, or placeholders to remove?

**Q3. Where do `race_demands` come from?** The `opportunity_cost_analysis` function requires race demands as input. Is this a hardcoded profile, a route-derived calculation, or manual coach input? The endpoint `GET /opportunity-cost/{route_id}` implies route-derived, but the derivation is not specified.

**Q4. What defines "missed session" in allostatic load?** Without a training plan to compare against, there is no ground truth for missed sessions. Is this derived from weekly volume drop? Explicit plan integration? This determines whether the function is implementable or must be deferred.

**Q5. Is `glycogen_budget` always pre-ride planning, post-ride review, or both?** The parameter list (`ride_kj`, `ride_duration_h`, `on_bike_carbs_g`) implies known ride data, but the panel seems oriented toward planning. If pre-ride, the inputs are estimates; if post-ride, they can be pulled from FIT data. This changes the UI.

**Q6. How many tests are expected per new function?** The spec targets ~205 tests (up from 189), which is +16 -- exactly one test per function. Several of these functions (e.g., `check_reds_flags`, `ftp_growth_curve`) have multiple branches that need coverage. Is 1:1 the real target, or is it an undercount?

**Q7. Should `check_reds_flags` produce actionable flags today?** The gap-to-illness heuristic needs a concrete definition. Is there a reference threshold from the Stellingwerff/Carson sources, or should this be a configurable parameter?

---

## 5. Scope Reduction Opportunities

Items that can be safely deferred without compromising the core deliverable.

| Item | Rationale | Savings |
|------|-----------|---------|
| **`allostatic_load_estimate`** | RPE not in FIT files, "missed sessions" undefined, "comment sentiment" requires TP pipeline. Would ship as a mostly-stubbed function. | 1 backend function, 1 test, 1 panel |
| **`opportunity_cost_analysis`** | Undefined `race_demands` data contract, no route selection UI. Cannot be fully implemented without design work outside this spec. | 1 backend function, 1 endpoint, 1 chart file, 1 panel |
| **Backend layout storage** | Replace with localStorage presets. Eliminates `layout.py`, layout table, `GET/PUT /layout` endpoints, `test_layout.py`, and all identity/security issues. | 1 module, 1 table, 2 endpoints, 1 test file, 5 security issues |
| **Tab drag reorder** | Panel reorder within a tab covers the primary use case. Tab order is set once and rarely changed. | Reduces DnD scope by ~40% |
| **`energy_expenditure` uncertainty param** | Backward-compatible addition, low user impact, can ship any time. | 1 small function change |

**Net effect of full deferral:** removes ~8 items from scope, eliminates the two weakest data contracts, and sidesteps the identity problem entirely. Core deliverable (14 backend functions, 8 endpoints, dashboard refactor, 6 chart panels, edit mode) remains intact.

---

## 6. Implementation Cost Estimate

### Files Touched

| Category | New | Modified | Notes |
|----------|-----|----------|-------|
| Backend modules | 0-1 (`layout.py` only if keeping backend layouts) | 7 (`clinical.py`, `training_load.py`, `gap_analysis.py`, `nutrition.py`, `pdcurve.py`, `zones.py`, `durability.py`) | |
| API | 0 | 1 (`routes.py`) | 8-10 new endpoints added to existing file |
| Auth | 0 | 1 (`auth.py`) | Fix fail-open bug |
| Frontend JS | 2-3 (`layout-manager.js`, `panel-registry.js`, possibly SortableJS vendor) | 1 (`dashboard.js` -- major refactor) | dashboard.js refactor is the critical path |
| Frontend charts | 6 new chart files | 0 | `health-status.js`, `if-distribution.js`, `ftp-growth.js`, `opportunity-cost.js`, `glycogen-budget.js`, `rolling-pd.js` |
| Frontend HTML/CSS | 0 | 2 (`index.html`, `styles.css`) | Edit mode UI, new panel containers |
| Tests | 0-1 (`test_layout.py` only if backend layouts) | 7 test files | ~16-25 new test cases across files |
| **Total** | **8-11 new** | **19 modified** | |

### Integration Surfaces (where things break)

1. **`dashboard.js` refactor** -- Highest risk. 1,250 lines of tightly coupled wiring must be converted to dynamic panel instantiation. Every existing panel (`pmc`, `mmp`, `clinical`, `segment-profile`) must continue working through the transition. Regression risk is high.

2. **`warmup_cache()` expansion** -- New expensive endpoints (`rolling_pd_profile`, `ftp_growth`) need cache entries. The existing `_cached()` mechanism works, but startup time will increase.

3. **Panel registry <-> endpoint mapping** -- Each panel in `WKO5.panels` must map to a valid backend endpoint. Mismatches silently fail. The `if-floor`/`panic-training` gap (C6) is an example.

4. **`clinical.py` integration** -- `check_reds_flags` and `check_within_day_deficit` must integrate into existing `get_clinical_flags()`. The existing clinical dashboard (frontend) already renders flags, so the backend change must match the existing response schema.

### Suggested Agent Dispatch Order

Sequenced to minimize blocked dependencies:

| Phase | Work | Blocks |
|-------|------|--------|
| **0. Prep** | Fix `auth.py` fail-open (P0). Resolve Q1 (localStorage vs backend). Resolve Q2 (missing panels). | Everything |
| **1. Backend functions** | Implement 14 P3 functions in 7 modules. Unit tests. Can be parallelized across modules -- no cross-module dependencies. | Phase 2 |
| **2. API endpoints** | Add 8 endpoints to `routes.py`. Wire to backend functions. Add cache entries for expensive endpoints. | Phase 3 |
| **3. Dashboard refactor** | Refactor `dashboard.js` into dynamic panel system. Create `panel-registry.js`. Ensure all existing panels still work. | Phase 4 |
| **4. New charts** | Implement 6 new chart files. Register in panel registry. | Phase 5 |
| **5. Edit mode** | Create `layout-manager.js`. Implement add/remove/reorder. localStorage save/load. SortableJS integration. | -- |

Phases 1 and 3 are the critical path. Phase 1 is embarrassingly parallel (7 independent modules). Phase 3 is serial and high-risk -- allocate extra review time.

### Risk Summary

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| dashboard.js refactor breaks existing panels | High | High | Write snapshot tests for current panel rendering before refactoring |
| `allostatic_load` ships as mostly-stubbed function | Near-certain | Medium | Defer (see Scope Reduction) |
| `opportunity_cost` endpoint called with no route selection UI | High | Medium | Defer or add hardcoded default route |
| Edit mode DnD flaky on Safari/mobile | Medium | Low | Use SortableJS |
| New endpoints slow without cache warmup | Medium | Medium | Add to `warmup_cache()` in Phase 2 |

---

<details>
<summary>Appendix A: Principal Engineer Review (full text)</summary>

1. Layout user_token has no identity infrastructure -- existing auth is single shared bearer token with no user concept.
2. HTML5 Drag and Drop is fragile -- native DnD has notorious problems. Suggests SortableJS (8KB).
3. Dynamic panel rendering conflicts with static HTML wiring -- dashboard.js is tightly coupled, every panel assumed in DOM at load. Converting to dynamic panels is "effectively a rewrite of dashboard.js" -- the spec does not mention this.
4. Race condition: layout save during panel data fetch -- removing panels while fetches in-flight.
5. Cache TTL missing for expensive endpoints (rolling_pd_profile, ftp_growth).
6. allostatic_load_estimate is speculative -- RPE not in FIT files, will be mostly stubbed. DEFER.
7. opportunity_cost_analysis has undefined "race demands" data contract.
8. Full per-user layout system is over-engineered for 2 users -- suggests localStorage presets instead.
9. glycogen_budget_daily needs manual input, should be interactive form not passive panel.
10. dashboard.js refactor is the biggest risk and is invisible in the spec. Needs explicit section.
11. check_reds_flags gap-to-illness heuristic is undefined.
12. No DELETE /layout endpoint.

**Top Recommendations:**
- R1: Replace backend layout storage with localStorage presets (eliminates identity problem).
- R2: Explicitly scope the dashboard.js refactor as a major section.
- R3: Defer allostatic_load and opportunity_cost (weak data contracts).
- R4: Make glycogen_budget an interactive form, not passive panel.
- R5: Add expensive endpoints to warmup_cache().
- R6: Use SortableJS instead of native DnD.
- R7: Define gap-to-illness heuristic.

</details>

<details>
<summary>Appendix B: Product Designer Review (full text)</summary>

**Strengths:** Preset defaults for 2 users, Health tab dedicated surface, edit mode gear-to-Done pattern, panel registry as catalog, glycogen budget chart is strongest visualization.

**Concerns:**
1. User identity is unresolved and load-bearing -- no login, no user switcher.
2. Health tab has 5 panels but no reading order/hierarchy -- clinical-flags should be full-width at top.
3. if-floor and panic-training panels are in default layout but NOT in panel registry or new chart files -- spec has a hole.
4. Edit mode has no undo/cancel -- only "Done" saves, no way to discard changes.
5. Add-panel modal has no descriptions -- users can't preview what a panel shows.
6. opportunity-cost panel requires route_id but has no route selection UI.
7. allostatic_load has no UI surface to explain its inputs.
8. No error state for chart panels -- silent empty panel is dangerous for clinical panels.
9. No "Layout saved" confirmation -- PUT could fail silently.
10. No way for coach to "view as athlete" or vice versa.
11. No validation on tab names (empty, duplicate, long).
12. Empty tab state undefined.
13. Panel removal doesn't communicate "still in catalog" -- users think it's deleted.

</details>

<details>
<summary>Appendix C: Security Engineer Review (full text)</summary>

- **CRITICAL-1:** Raw bearer token stored as DB primary key -- credential at rest. Fix: use SHA-256(token) or UUID.
- **CRITICAL-2:** Auth bypass when _token is None -- fail-open bug. Fix: reject if no token configured.
- **HIGH-1:** No validation/size limit on layout JSON -- DoS, schema poisoning, stored XSS.
- **HIGH-2:** No user isolation -- any token reads/writes any layout.
- **MEDIUM-1:** route_id path param needs type constraint (int) to prevent SQL injection.
- **MEDIUM-2:** Panel endpoint resolution must be registry-only, never from stored layout.
- **MEDIUM-3:** No CSRF protection on PUT /layout.
- **LOW-1:** auto_error=False weakens defense-in-depth.

</details>
