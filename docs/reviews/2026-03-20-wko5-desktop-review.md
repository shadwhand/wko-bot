# Review: WKO5 Desktop Dashboard & Optimization Engine

**Date:** 2026-03-20
**Document:** `docs/superpowers/specs/2026-03-20-wko5-desktop-design.md`
**Reviewers:** Principal Engineer (opus), Product Designer (sonnet), Security Engineer (sonnet), Exercise Physiologist (opus), Data Scientist (opus)
**Synthesizer:** opus

---

## Cross-Review Consensus

### Bayesian Framework Overscoped (Principal, Data Scientist, Exercise Physiologist)
- VI mean-field underestimates posterior correlations — use full-rank ADVI or NUTS
- Posterior storage undefined — determines query architecture
- Fatigued PD curve composition needs joint sampling, not independence
- Training response model not causally identified — reframe as associational
- Coggan trainability table is qualitative, cannot encode as prior

### Clinical Guardrails Need Stronger Safeguards (Security, Exercise Physiologist, Designer)
- Layer 3 must NOT make clinical recommendations — recommend professional evaluation
- Mandatory disclaimers on all Red flags
- Red flags need persistent notification, not buried in a tab

### Durability Model Has Known Gaps (Exercise Physiologist, Data Scientist)
- Missing intensity weighting (use TSS not raw kJ)
- Missing fueling interaction
- Exponential decay wrong shape for collapse — sigmoid more accurate
- FRC recovery_ceiling should be stateful

### Multi-Athlete Schema Premature (Principal)
- Single-row config table sufficient for now

### Altitude Data Gap Blocks Segment Analyzer (Principal)

### Model Validation Missing (Data Scientist, Exercise Physiologist)

---

## Prioritized Action List

### P0 — Blocking
1. FastAPI security (bearer token, CORS, ephemeral port)
2. Electron renderer sandboxing
3. Altitude data gap resolution
4. Posterior storage schema decision
5. Demand ratio: joint simulation not product of marginals

### P1 — Required for v1
6. Ship point estimates first, Bayesian incremental
7. 6 core charts initially
8. Clinical disclaimers
9. Garmin tokens to Keychain
10. GPX upload protections (defusedxml)
11. Post-ride review workflow
12. Landing state design
13. VO2max equation fix
14. FRC recovery_ceiling stateful
15. HRV log-normal, resting HR AR(1)
16. Single-row athlete config

### P2 — v1.1
17. Bayesian PD model with NUTS
18. Intensity-weighted durability model
19. Measurement error model
20. Model validation framework
21. Sigmoid vs exponential durability
22. Scenario comparison in pacing
23. MMP recency toggle
24. Cascading edit confirmations
25. Rate limiting
26. JSON config sanitization
27. Persistent clinical notification banner
28. Progressive disclosure for CIs

### P3 — Defer
29. Training response MCMC
30. SQLCipher encryption
31. Posterior integrity checksums
32. Fueling interaction model
33. Draggable panel layouts
34. Phase override UI
35. Electron crash recovery
36. PD model temporal non-stationarity
37. Distinguish computational vs qualitative Bayesian

---

## Open Questions
1. Minimum viable demo: math-first or UI-first?
2. Is multi-athlete a concrete requirement or speculative?
3. How to source altitude for 2024+ activities?
4. Tolerance for stochastic outputs between refits?
5. Nutrition data available?
6. Target event timeline?
7. Layer 3 Bayesian: computational or rhetorical?
8. Distribution target: personal or product?

## Scope Reduction (if needed)
- Drop multi-athlete FK: saves ~15 files + all test rewrites
- Defer Bayesian: removes PyMC/NumPyro/JAX, saves ~10 files
- Ship 6 charts: saves ~12 D3 components
- Fixed CSS Grid: saves 1 dependency + drag logic
- Drop pacing optimizer from v1: saves ~5 engine files
- Defer Electron, ship browser-only: eliminates all C1/C2/H4 security issues
