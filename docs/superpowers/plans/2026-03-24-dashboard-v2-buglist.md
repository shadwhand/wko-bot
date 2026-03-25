# Dashboard v2 — Phase 1 Bug List

From initial user testing session 2026-03-24.

## CSS / Visual

- [ ] **Clinical flags tooltip z-index** — hover tooltip gets blocked by adjacent panel. Need `z-index` on tooltip higher than panel chrome.

## Data Wiring

- [ ] **IF Floor / RED-S "not available"** — panels show empty. The clinical flags API returns these as `{name, status, value, detail}` but panels may be filtering by wrong name. Check flag name matching in `IFFloor.tsx` and `RedsScreen.tsx` against actual API response (`"IF Floor"` vs `"if_floor"`).

- [ ] **MMP recency toggle does nothing** — the 30d/60d/90d/1yr/All buttons don't re-fetch with different `days` param. The store has `model` fetched once at startup with `days=90`. The toggle needs to call `getModel({ days })` and update the chart, not read from store.

- [ ] **Rolling FTP calculation unclear** — user doesn't know how FTP is calculated. Need hover tooltip explaining "mFTP from 90-day rolling PD model fit".

- [ ] **TTE shows no data** — RollingPd chart TTE toggle may have no data because `TTE_min` is `120.0` (capped) for all snapshots. Check if the field name matches (`TTE` vs `TTE_min`).

- [ ] **Power Profile empty** — panel reads from `store.profile` but may expect different field structure. API returns `{profile: {watts: {5: 1104, 60: 427, ...}, wkg: {...}}, ranking: {...}}`. Check PowerProfile.tsx field access.

- [ ] **Event Prep routes empty** — RouteSelector reads from `store.routes` but `fetchSecondary()` may not fetch routes. Check if `getRoutes()` is called in the store's `fetchSecondary` or `fetchCore`.

- [ ] **Rides table click does nothing** — RidesTable should call `setSelectedRide(id)` on row click which triggers RideDetail view. Check if click handler is wired.

- [ ] **Phenotype empty** — reads from `store.profile?.strengths_limiters` but API returns `{strength: {duration, label, category}, limiter: {...}}`. Check field mapping.

## To Fix

Priority order:
1. Routes not loading (blocks Event Prep entirely)
2. Rides table click (blocks Ride Detail testing)
3. Power Profile + Phenotype (core profile data)
4. MMP toggle (important UX)
5. Clinical flag panels (Health tab completeness)
6. Tooltip z-index (CSS fix)
7. Rolling FTP tooltip (polish)
