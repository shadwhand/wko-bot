# WKO5 Desktop Dashboard & Optimization Engine — Design Spec

## Overview

An Electron desktop app for cycling power analysis with an embedded Claude Code terminal. The core is a deterministic computational engine that provides segment analysis, demand profiling, gap computation, pacing optimization, and training block analysis — backed by the existing `wko5/` Python library and 8 years of cycling data in SQLite.

## Multi-Athlete Model

Every athlete has a profile. Nothing is hardcoded. The system is built for N athletes; the current deployment has one.

### Athlete Profile Schema

```sql
CREATE TABLE athlete_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    sex TEXT DEFAULT 'male',            -- for Coggan ranking table selection

    -- Physical
    weight_kg REAL NOT NULL,
    max_hr INTEGER,
    lthr INTEGER,                       -- lactate threshold HR
    ftp_manual REAL,                    -- manually set FTP (optional, model-derived preferred)

    -- Equipment / aerodynamics
    bike_weight_kg REAL DEFAULT 9.0,
    cda REAL DEFAULT 0.35,
    crr REAL DEFAULT 0.005,

    -- PD model bounds (scale to athlete — defaults are for ~70-90kg male)
    pd_pmax_low REAL DEFAULT 800,
    pd_pmax_high REAL DEFAULT 2500,
    pd_mftp_low REAL DEFAULT 150,
    pd_mftp_high REAL DEFAULT 400,
    pd_frc_low REAL DEFAULT 5,
    pd_frc_high REAL DEFAULT 30,
    pd_tau_low REAL DEFAULT 5,
    pd_tau_high REAL DEFAULT 30,
    pd_t0_low REAL DEFAULT 1,
    pd_t0_high REAL DEFAULT 15,

    -- Data cleaning
    spike_threshold_watts REAL DEFAULT 2000,  -- power readings above this are sensor glitches
                                               -- should be > athlete's Pmax; track sprinters need higher

    -- Clinical guardrails
    resting_hr_baseline REAL,           -- auto-computed from data or manually set
    hrv_baseline REAL,                  -- auto-computed from data or manually set
    resting_hr_alert_delta REAL DEFAULT 5,  -- bpm above baseline to trigger alert
    ctl_ramp_rate_yellow REAL DEFAULT 7,    -- TSS/day/week
    ctl_ramp_rate_red REAL DEFAULT 10,
    tsb_floor_alert REAL DEFAULT -30,
    collapse_kj_threshold REAL,         -- empirically fitted from historical data

    -- Ultra / pacing
    intensity_ceiling_if REAL DEFAULT 0.70,  -- max IF for events >12h
    fueling_rate_g_hr REAL DEFAULT 75,       -- CHO intake rate for energy balance
    energy_deficit_alert_kcal REAL DEFAULT 3000,

    -- PMC constants (industry standard but tunable)
    ctl_time_constant REAL DEFAULT 42,
    atl_time_constant REAL DEFAULT 7,

    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

**Nothing is hardcoded in the engine.** All athlete-specific values, model bounds, thresholds, and constants are read from the athlete profile. The library loads the active athlete's profile at startup and passes parameters through every function call.

All existing tables (`activities`, `records`, `laps`, `mmp_cache`, `tss_cache`) gain an `athlete_id` foreign key. All library functions accept `athlete_id` parameter — defaults to the active athlete.

### Coggan Ranking Tables

Stored in a reference table, not hardcoded. Separate values for male and female. The athlete's `sex` field selects the correct table.

```sql
CREATE TABLE coggan_rankings (
    sex TEXT NOT NULL,          -- 'male' or 'female'
    duration_s INTEGER NOT NULL,
    category TEXT NOT NULL,     -- 'World Class', 'Exceptional', etc.
    wkg_threshold REAL NOT NULL,
    PRIMARY KEY (sex, duration_s, category)
);
```

### Durability Model Parameters (per athlete)

```sql
CREATE TABLE durability_models (
    athlete_id INTEGER,
    fitted_at TEXT,
    param_a REAL,       -- weight between kJ-based and time-based decay
    param_b REAL,       -- kJ decay rate
    param_c REAL,       -- time decay rate
    circadian_amplitude REAL,  -- 2-5 AM power reduction %
    recovery_ceiling REAL,     -- max FRC recharge fraction after deep depletion
    collapse_threshold_kj REAL,
    rides_used INTEGER,        -- how many rides went into the fit
    rmse REAL,                 -- model fit quality
    PRIMARY KEY (athlete_id, fitted_at),
    FOREIGN KEY (athlete_id) REFERENCES athlete_profiles(id)
);
```

### Context Flags (per athlete)

```sql
CREATE TABLE context_flags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    athlete_id INTEGER,
    start_date TEXT NOT NULL,
    end_date TEXT,
    flag_type TEXT NOT NULL,  -- illness, stress, sleep, travel, diet, fasted, heat
    severity INTEGER DEFAULT 1,  -- 1=mild, 2=moderate, 3=severe
    notes TEXT,
    FOREIGN KEY (athlete_id) REFERENCES athlete_profiles(id)
);
```

### Current Athlete (first deployment)

| Field | Value | Notes |
|---|---|---|
| name | jshin | |
| sex | male | |
| weight_kg | 78.0 | |
| max_hr | 186 | from data |
| ftp_manual | 292 | midpoint of 285-299 range |
| bike_weight_kg | 9.0 | estimate |
| cda | 0.35 | estimated from 2023 ride data |
| crr | 0.005 | typical road tire |
| spike_threshold_watts | 2000 | Pmax ~1050, safe margin |
| pd_pmax_low / high | 800 / 2500 | defaults OK for this athlete |
| pd_mftp_low / high | 150 / 400 | defaults OK |
| intensity_ceiling_if | 0.70 | fitted from successful ultras |
| fueling_rate_g_hr | 75 | |
| ctl_time_constant | 42 | standard |
| atl_time_constant | 7 | standard |
| Data | 1,653 activities (2018-2026), 11M+ records | |
| Primary events | ultra-endurance (600-1200km brevets) | |

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                Electron Desktop App              │
│  ┌──────────────────────┬─────────────────────┐  │
│  │   D3 Dashboard       │  Claude Code        │  │
│  │   (tabbed panels)    │  Terminal           │  │
│  │                      │  (node-pty+xterm.js)│  │
│  └──────────┬───────────┴─────────────────────┘  │
│             │ HTTP                                │
│  ┌──────────▼──────────────────────────────────┐  │
│  │          FastAPI Backend                     │  │
│  │  ┌────────────────────────────────────────┐  │  │
│  │  │     Optimization Engine (new)          │  │  │
│  │  │  • Segment analyzer                    │  │  │
│  │  │  • Durability model                    │  │  │
│  │  │  • Demand profiler (fatigued PD curve) │  │  │
│  │  │  • Gap analysis                        │  │  │
│  │  │  • Pacing optimizer (ultra-aware)       │  │  │
│  │  │  • FRC budget model                    │  │  │
│  │  │  • Training block stats                │  │  │
│  │  │  • Clinical guardrails                 │  │  │
│  │  └────────────────────────────────────────┘  │  │
│  │  ┌────────────────────────────────────────┐  │  │
│  │  │     wko5/ Analysis Library (existing)  │  │  │
│  │  └────────────────────────────────────────┘  │  │
│  │  ┌────────────────────────────────────────┐  │  │
│  │  │     cycling_power.db (SQLite)          │  │  │
│  │  └────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

## The Three-Layer Model

### Layer 1: Deterministic Engine (Python)

Same inputs → same outputs. No opinions. All computations are traceable — if a number changes, it's because an input changed.

"Same inputs" includes the athlete's current fitness state (PD curve window), not just the route. A ride analyzed today and in 6 months will produce different demand ratios because the PD curve changed. This is correct behavior.

### Layer 2: Context Layer (Structured Data)

Athlete-reported flags tagged to time periods in the DB: illness, stress, sleep quality, travel, diet changes, fasted sessions, heat. The engine annotates outputs with these flags but does not interpret them.

Note: the selection of what to annotate shapes the narrative Layer 3 works with. Layer 2 is not purely neutral — it's honest annotation that creates implicit associations.

### Layer 3: Coaching Layer (Claude + WKO5 Skills) — Bayesian Interpretation Framework

Claude's coaching interpretations follow a structured Bayesian reasoning process, not free-form advice. Every interpretation is grounded in the training methodology literature (priors), evaluated against the engine's data (likelihood), and synthesized into actionable conclusions (posteriors).

**The reasoning structure for every coaching interpretation:**

**1. State the prior (from methodology/literature):**
What does the training science say should happen in this situation?
- Source: `/wko5-training` skill reference documents (Cusick's 4-phase build, Kolie Moore's FRC/Pmax protocols, Coggan's trainability table, annual planning methodology)
- Source: `/wko5-science` skill (research papers, physiological models)
- Example: "Cusick's Phase 2 framework predicts 3-5% mFTP gain over 4 weeks of intensive aerobic work at 95-105% PDC, with TIZ target of ≥150% TTE per session."

**2. State the likelihood (from engine output):**
What does the athlete's data actually show?
- Source: Layer 1 deterministic engine output
- Source: Layer 2 context flags
- Example: "Engine shows mFTP +2% over 4 weeks. TIZ averaged 60% of target. Context: athlete flagged high stress weeks 2-3."

**3. Compute the posterior (updated belief):**
Given the prior expectation and the observed evidence, what's the most likely explanation? Rank competing hypotheses by their posterior probability.
- Example: "Response below expected. Ranked explanations:
  1. Insufficient stimulus (high posterior — TIZ was 60% of target, directly explains reduced response)
  2. Recovery limitation (moderate posterior — stress flag supports this, but stress was only 2 of 4 weeks)
  3. Approaching ceiling (low posterior — mFTP:VO2max at 83%, still below 85% threshold)
  Recommendation: Repeat Phase 2 block with full TIZ compliance before advancing to Phase 3."

**4. State confidence and what would change the conclusion:**
- "Confidence: moderate. Would increase to high if next block with full TIZ compliance produces expected 3-5% gain."
- "Would revise if: mFTP:VO2max reaches 85% with no further response → shift to Phase 3 VO2max work."

**This framework applies to all coaching interactions:**

| Question type | Prior source | Likelihood source |
|---|---|---|
| "How's my fitness?" | Expected CTL trajectory for current phase | Engine: current CTL/ATL/TSB + trend |
| "Am I improving?" | Trainability table: expected gains for training type | Engine: rolling power at key durations |
| "What should I work on?" | Phase-appropriate limiters (annual planning framework) | Engine: strengths/limiters + demand profile for target event |
| "Was this a good training block?" | Expected outcomes from methodology for block type | Engine: training block stats + context flags |
| "Am I ready for this event?" | Demand profile requirements | Engine: gap analysis + success probabilities |
| "Why did my power drop?" | Differential diagnosis from methodology | Engine: "what changed" differential + context flags |
| "What should I do next?" | Phase transition criteria from annual planning | Engine: mFTP:VO2max ratio, power plateau detection, phase auto-detection |

**Why this matters:**
- Reproducible: same data + same methodology = same interpretation
- Auditable: athlete can see the prior, the evidence, and the reasoning
- Self-correcting: wrong priors get updated by evidence over time
- Grounded: every recommendation traces back to either published methodology or measured data — never "I think you should..."
- Handles uncertainty honestly: "I don't know" is a valid posterior when evidence is insufficient

---

## Engine Sub-Projects

### Sub-project 1: Segment Analyzer

Decompose rides and routes into physiological demands.

**Segment detection from altitude + distance data:**
- Compute grade: altitude change / distance change per second, smoothed (10s rolling average to remove GPS noise)
- Classify: climb (>3%), rolling (1-3%), flat (-1% to 1%), descending (<-1%)
- Merge consecutive same-type samples into segments with minimum length thresholds
- Climb detection: sustained positive grade >3% for >500m distance

**Per-segment metrics:**
- Duration, distance, average grade, elevation gain/loss
- Power required (from physics model — see below)
- Physiological system taxed: map (duration, power_required) to PD curve region
  - <15s → neuromuscular/Pmax
  - 15s-2min → FRC/anaerobic
  - 2-8min → VO2max
  - 8-20min → threshold/FTP
  - 20min+ → endurance/stamina

**Demand profile output:**
- Ordered list of segments with (duration, power_required, system_taxed, cumulative_kJ_at_start)
- Aggregate demand summary: "This route requires X at 5min, Y at 20min, Z FRC matches"

**Physics model for power_required:**
```
P = (CdA * 0.5 * rho * v^3) + (Crr * m * g * v) + (m * g * v * grade) + P_accel
```

All parameters from athlete profile: `cda`, `crr`, `weight_kg + bike_weight_kg`. Air density `rho` adjusted for temperature/altitude if available. Route-level overrides supported (e.g., different CdA for TT bike, different Crr for gravel).

**Data sources:**
- Historical rides: altitude + distance from records table (2019-2023 have altitude; 2024+ needs re-ingestion)
- Future routes: GPX file import
- GPS coordinates stored as Garmin semicircles, convert: `degrees = semicircles * (180 / 2^31)`

---

### Sub-project 2: Durability Model

**The single most important and novel component.** (Dr. Vasquez: "This is the highest-value component. Nobody else has your 8-year ultra dataset.")

The PD curve represents fresh-state capacity. After hours of riding, effective capacity degrades nonlinearly based on:
- Cumulative work (kJ)
- Elapsed time (central fatigue, independent of work)
- Intensity distribution (time above FTP produces disproportionate peripheral fatigue)

**Approach: empirical degradation function fitted from historical data.**

For each ride >2 hours:
1. Compute best power at key durations (60s, 300s, 1200s) in rolling windows (e.g., hours 0-2, 2-4, 4-6, etc.)
2. Normalize each window's power against the ride's first-window power
3. Fit a decay curve across all long rides

**Model form:**
```
effective_capacity(duration, cumulative_kJ, elapsed_hours) =
    PD(duration) * degradation_factor(cumulative_kJ, elapsed_hours)
```

Start with a two-parameter exponential decay:
```
degradation_factor = a * exp(-b * cumulative_kJ / 1000) + (1-a) * exp(-c * elapsed_hours)
```

Fit `a`, `b`, `c` from historical data. Add complexity only if residuals demand it.

**Circadian adjustment for ultra events:**
- Apply a 5-15% power reduction during the 2:00-5:00 AM window (well-documented in chronobiology literature)
- Detect from timestamps in historical night rides
- Parameter: `circadian_factor(hour_of_day)` — fitted from the athlete's own data if sufficient night riding exists, else use literature defaults

**Collapse zone detection:**
- Identify the duration/cumulative-work threshold beyond which performance degrades catastrophically rather than linearly
- With 8 years of ultra data including 1200km events, this should be identifiable
- Alert when a demand profile pushes into this zone

**Repeatability index:**
- Ratio of 3rd-best effort to 1st-best effort at a duration within a ride, averaged across rides
- Measures ability to produce repeated efforts vs. one-off peaks
- Critical for ultra events where you need to climb 50 hills, not just 1

---

### Sub-project 3: Gap Analysis & Pacing Optimizer

**Race readiness snapshot:**
- Compare demand profile (from Sub-project 1) against the **fatigued** PD curve (from Sub-project 2), not fresh
- For each segment: compute demand ratio = power_required / effective_capacity at that point in the route
- Demand ratio interpretation:
  - < 0.85 → comfortable
  - 0.85-0.95 → hard but achievable
  - 0.95-1.0 → at your limit
  - \> 1.0 → exceeds current capability
- Output: per-segment demand ratios + overall route feasibility assessment
- This snapshot does not need context — you either have the watts or you don't

**Pacing optimizer:**
- Given the demand profile and fatigued PD curve, compute optimal power per segment to minimize total time
- Subject to constraints:
  - **Intensity ceiling:** ~0.68-0.72 IF for events >12 hours (adjustable, fitted from athlete's successful ultras)
  - **FRC budget:** track depletion/recharge across segments. FRC depletes above mFTP, recharges below. Further below = faster recharge. Never fully recharges after 2-3 deep deplections.
  - **Energy balance:** estimated expenditure per segment vs. realistic intake rate (60-90g CHO/hour). Alert when cumulative deficit exceeds ~2,000-3,000 kcal.
  - **Non-riding time budget:** realistic for event format (control stops, navigation, mechanicals, rest)
- Output: per-segment target power, expected split times, FRC state, energy balance

**FRC budget model across segments:**
```
For each segment in sequence:
  if target_power > mFTP_effective:
    frc_cost = (target_power - mFTP_effective) * duration_s / 1000  # kJ
    frc_remaining -= frc_cost
  else:
    frc_recovery = recovery_rate * (mFTP_effective - target_power) * duration_s / 1000
    frc_remaining = min(frc_remaining + frc_recovery, frc_max * recovery_ceiling)
```

Where `recovery_ceiling` < 1.0 (FRC never fully recharges after deep depletion, empirically fitted).

---

### Sub-project 4: Training Block Analysis

**Deterministic statistical summaries:**
- Per training block: volume (hours, km, kJ, elevation), intensity distribution (Seiler 3-zone, iLevel breakdown), time in zones, ride count, long ride count
- Power changes at key durations: rolling bests at 1min, 5min, 20min, 60min with trend lines
- Before/after comparisons around phase transitions
- Correlation matrices between training inputs (weekly TSS, time above FTP, sweet spot time, volume) and performance outputs (power at key durations)
- "What changed" differential: when PD curve shifts, automatically identify concurrent changes in volume, intensity distribution, and TIZ

**Periodization phase auto-detection:**
- Classify time periods as base/build/peak/recovery from intensity distribution and volume trends
- Base: high volume, low Zone 3 %, rising CTL
- Build: moderate volume, rising Zone 2-3 %, intensity increasing
- Peak: reduced volume, high Zone 3 %, CTL flattening or dropping
- Recovery: low volume, low intensity, CTL dropping
- Output: annotated timeline that Layer 3 can use for coaching context

**Intensity distribution analysis:**
- Seiler 3-zone split per week/month: % below LT1, % LT1-LT2, % above LT2
- Identify moderate-intensity wasteland: are easy days actually easy? Compute % of ride time below 0.65 IF on designated easy days
- Specificity check: does training distribution match event demands?

**Statistical rigor (per Dr. Vasquez):**
- Use effect sizes, not p-values (with 1,653 activities, everything is statistically significant)
- Time series awareness: data is autocorrelated. Use differencing or appropriate methods.
- Report practical significance: "this block was associated with a 12W FTP increase" not "p < 0.05"
- n=1 caveat: models are specific to this athlete and generalize to no one

**Feasibility projection:**
- Given current CTL, historical ramp rate, and event demands from Sub-project 1: is the timeline feasible?
- Constraint satisfaction: "You need CTL 85 by event day. Current CTL is 65. Historical sustainable ramp rate is 5 TSS/day/week. You have 12 weeks. Result: feasible with X margin."

---

### Sub-project 5: Clinical Guardrails

Deterministic flags in Layer 1. Claude interprets in Layer 3.

| Flag | Trigger | Severity |
|---|---|---|
| Cardiac drift anomaly | HR decoupling >10% in first 2-3 hours at moderate intensity | Red |
| Power-HR inversion | HR rising while power falling beyond normal fatigue pattern | Red |
| Resting HR elevation | Sustained +5 bpm above baseline for >3-4 days + declining power | Yellow |
| CTL ramp rate excessive | >7 TSS/day/week sustained | Yellow; >10 = Red |
| TSB floor breach | TSB below -30 for >2 weeks | Yellow |
| HRV suppression | Sustained HRV below rolling baseline + performance decline | Yellow |
| Collapse zone approach | Demand profile projects cumulative work beyond historical collapse threshold | Red |
| Energy deficit critical | Projected cumulative caloric deficit >3,000 kcal during event | Yellow |

---

### Sub-project 6: Bayesian Statistical Framework

Every model in the engine benefits from expressing uncertainty, handling sparse data, and updating beliefs as new evidence arrives. The Bayesian framework sits underneath the other sub-projects — it's how the models are fitted and how outputs are expressed.

#### Core Principle

Instead of point estimates ("your mFTP is 289W"), the engine produces **posterior distributions** ("your mFTP is 289W, 90% credible interval [278, 301]"). This propagates through to demand ratios, gap analysis, and pacing — giving the athlete probabilities, not just pass/fail.

#### Where Bayesian Inference Applies

**1. PD Model Parameter Estimation**

Replace `scipy.curve_fit` (maximum likelihood) with Bayesian parameter estimation:

- **Priors:** Physiologically reasonable ranges from the athlete profile bounds (pd_pmax_low/high, pd_mftp_low/high, etc.). New athletes get wider priors; experienced athletes with lots of data get tighter priors automatically.
- **Likelihood:** Each ride's MMP data updates the posterior on Pmax, FRC, mFTP, TTE, tau, t0.
- **Output:** Full posterior distributions on all PD parameters. Point estimates (MAP or median) for display; credible intervals for uncertainty-aware analysis.
- **Missing data handling:** If athlete never does max 1-min efforts, FRC credible interval stays wide but mFTP isn't contaminated. The model knows what it doesn't know.

**2. Durability Model**

- **Prior:** Population-level durability decay from literature (approximately 2-3% power loss per hour at endurance intensity). Used when athlete has few long rides.
- **Likelihood:** Each long ride (>2h) updates the posterior on decay parameters (a, b, c).
- **Posterior:** Personalized durability model that starts generic and narrows with data.
- **Cold-start solution:** A new athlete with zero long rides gets reasonable (wide) estimates from the prior. After 5-10 long rides, the posterior is dominated by their data. After 50+ rides (like the current athlete), the prior is irrelevant.

```
Prior:       P(a, b, c) ~ population defaults with wide variance
Likelihood:  P(observed_decay | a, b, c) per long ride
Posterior:   P(a, b, c | all rides) ∝ Prior × ∏ Likelihood_i
```

**3. Demand Ratio → Probability of Success**

Instead of hard thresholds (demand ratio > 1.0 = fail), compute the probability of completing each segment:

```
P(success | segment) = P(athlete_power_at_duration > power_required)
```

Where `athlete_power_at_duration` is drawn from the posterior distribution of the fatigued PD curve at that point in the route. This naturally accounts for:
- Uncertainty in the PD model (wider intervals = lower confidence)
- Uncertainty in the durability model (less data at extreme durations = wider intervals)
- The difference between "barely possible" and "comfortably possible"

**Output:** Per-segment success probability. Overall route probability = product of segment probabilities (assuming independence) or joint probability accounting for FRC correlation between segments.

Example: "Segment 7 (5-min climb at km 180): demand ratio 0.97, probability of holding target: 68%. If you reduce target by 10W: probability 89%."

**4. Clinical Guardrails**

Replace hard thresholds with anomaly probabilities:

- **Prior:** Athlete's historical distribution of resting HR, HRV, power-HR ratio (computed from their data, stored in athlete profile as baseline + variance).
- **Observation:** Today's values.
- **Posterior:** Probability that today's observation is outside the athlete's normal range.

Benefits:
- A single high resting HR reading → low posterior probability of a problem (no false alarm)
- Three consecutive high readings + declining power → high posterior probability → flag
- Naturally adapts to each athlete's individual variability
- Thresholds in athlete profile become prior parameters rather than hard cutoffs

**5. Training Response Model (Sub-project 4)**

The most natural Bayesian application — and the hardest to do well.

- **Prior:** Population-level dose-response from coaching literature (Coggan trainability table: "threshold training produces 30-45% short-term gains at low-moderate physiological cost")
- **Likelihood:** Each training block's measured input (volume, intensity distribution, TIZ) and output (power changes at key durations)
- **Posterior:** This athlete's personal dose-response relationship, which may differ significantly from population averages
- **Confounders handled correctly:** A training block where the athlete was sick contributes wider likelihood (more noise) rather than corrupting the posterior. The model down-weights uncertain observations automatically.

This is where n=1 becomes a strength: 8 years of data builds a rich posterior specific to one person. The model knows "when this athlete does 3 weeks of sweet spot at 3x/week, their 20-min power typically improves by X±Y watts."

**Output:** For any proposed training block, the model outputs a posterior predictive distribution: "Given your history, this block has a 70% probability of producing a 5-15W gain at 20 minutes, 20% probability of no change, 10% probability of regression."

#### Implementation Approach

| Application | Method | Rationale |
|---|---|---|
| Clinical guardrails | Conjugate priors / analytical updates | Simple distributions (normal for HR, log-normal for HRV). Fast — runs on every sync. |
| Durability model | Variational inference (PyMC or NumPyro) | Moderate complexity, needs speed for interactive use in demand analysis. Fit runs on data refresh, not per-query. |
| PD model parameters | Variational inference | Same rationale. Replaces current curve_fit. Outputs credible intervals. |
| Demand ratio → probability | Monte Carlo sampling from posteriors | Draw N samples from fatigued PD posterior, compute fraction exceeding demand. Fast with pre-fitted posteriors. |
| Training response | Full MCMC (PyMC / Stan) | Most complex model, highest dimensionality, most confounders. Runs offline (nightly or on-demand). Accuracy matters more than speed. |

#### Dependencies

- **PyMC** (preferred) or **NumPyro** — probabilistic programming framework
- **ArviZ** — posterior diagnostics, convergence checks, credible interval computation
- **JAX** (if using NumPyro) — for fast variational inference

These are added to the Python environment alongside numpy/pandas/scipy.

#### Determinism Constraint

Bayesian models are stochastic (MCMC sampling). To maintain the "same inputs → same outputs" constraint:
- Fix random seeds for all inference runs
- Store fitted posteriors (parameter samples) in the DB per athlete
- Queries draw from stored posteriors, not re-fitted models
- Model re-fitting is an explicit action (triggered by new data sync or manual refresh), not implicit

This means: between re-fits, the engine is fully deterministic. Re-fitting updates the stored posteriors, which changes downstream outputs — but traceably, because you can diff the before/after posteriors.

---

## Desktop App (Electron)

### App Shell
- Electron with resizable split layout: dashboard (top/left) + Claude Code terminal (bottom/right)
- Terminal: Claude Code via `node-pty` + `xterm.js`
- Split is resizable, terminal can be minimized/maximized
- macOS native theme detection for dark/light mode
- Layout state persisted to local JSON config

### Dashboard Framework
- Tab bar with default tabs (customizable — add/remove/rename/reorder):
  1. **Training** — PMC chart, CTL/ATL/TSB, weekly TSS, recent rides
  2. **Power Duration** — MMP curve, PD model overlay, rolling FTP, period comparison
  3. **Ride Analysis** — select ride, power/HR/cadence time series, intervals, zones, best efforts
  4. **Profile** — power profile, Coggan ranking, strengths/limiters, phenotype
  5. **Ultra** — mega ride comparisons, block-by-block analysis, fade tracking, durability model
  6. **Route Analysis** — upload GPX or select past ride, segment breakdown, demand profile, gap analysis
  7. **Race Prep** — race readiness snapshot, pacing plan per segment, FRC budget, energy balance
  8. **Training Blocks** — block summaries, before/after, phase detection, intensity distribution
- Within each tab: draggable/resizable panel grid (golden-layout or gridstack.js)
- Panel layout per tab persisted to config

### Chart Components (D3.js)

All charts follow existing WKO5-style visualization patterns. Dark/light theming via CSS variables.

| Chart | Type | Notes |
|---|---|---|
| PMC | Line/area | CTL/ATL/TSB, zoomable, hover for daily values |
| MMP Curve | Line (log x-axis) | PD model overlay + fatigued PD curve overlay |
| Rolling FTP | Line | Over full training history |
| Ride Time Series | Multi-line stacked | Power/HR/cadence, zoomable, interval markers |
| Zone Distribution | Stacked bar | Per ride or per period |
| Power Profile Radar | Spider/radar | W/kg at key durations vs. Coggan categories |
| Weekly TSS | Bar chart | Last 52 weeks |
| Recent Rides Table | Sortable table | Click to open in Ride Analysis tab |
| Ultra Comparison | Table + mini-charts | Block-by-block with fade tracking |
| EF Trend | Scatter + rolling avg | Aerobic efficiency over time |
| Segment Profile | Area chart | Altitude profile with colored segments + demand ratios |
| Demand Heatmap | Colored bar | Per-segment demand ratio (green/yellow/red) |
| FRC Budget | Line | FRC state across route, depletion/recharge |
| Energy Balance | Line | Cumulative expenditure vs. intake |
| Durability Curve | Line | Power decay vs. cumulative kJ, fitted vs. actual |
| Intensity Distribution | Stacked bar | Seiler 3-zone per week/month |
| Phase Timeline | Annotated bar | Auto-detected training phases |
| Clinical Dashboard | Indicators | Traffic-light flags from guardrails |

### Backend API (FastAPI)

Electron spawns FastAPI on app start, kills on quit. Maps to existing `wko5/` library + new engine modules.

**Existing library endpoints:**
- `GET /api/fitness` → `current_fitness()`
- `GET /api/pmc` → `build_pmc()`
- `GET /api/mmp` → `compute_envelope_mmp()`
- `GET /api/model` → `fit_pd_model()`
- `GET /api/ride/:id` → `ride_summary()` + `get_records()`
- `GET /api/ride/:id/intervals` → `detect_intervals()`
- `GET /api/activities` → `get_activities()`
- `GET /api/profile` → `power_profile()` + `coggan_ranking()`
- `GET /api/rolling-ftp` → `rolling_ftp()`
- `GET /api/ef-trend` → `ef_trend()`

**New engine endpoints:**
- `POST /api/segments/analyze` → segment analyzer (accepts ride ID or GPX upload)
- `GET /api/durability` → durability model parameters and curve
- `POST /api/demand` → demand profile for a route
- `POST /api/gap-analysis` → demand ratios against fatigued PD curve
- `POST /api/pacing` → optimal power per segment with constraints
- `GET /api/training-blocks` → block analysis with phase detection
- `GET /api/clinical-flags` → current clinical guardrail status

---

## Tech Stack

- **Electron** — desktop shell
- **node-pty + xterm.js** — embedded Claude Code terminal
- **D3.js** — chart rendering
- **golden-layout or gridstack.js** — panel tiling/resizing
- **FastAPI** — Python API layer
- **SQLite** — existing `cycling_power.db`
- **wko5/** — existing Python analysis library (unchanged)
- **scipy** — curve fitting for durability model
- **numpy/pandas** — all computation

## Phased Implementation

Each phase produces working, testable software. Each phase is scoped to fit within a single Claude Code session without context loss. Phases are sequential — each builds on the last.

### Phase 1: Foundation (Engine Core)
**Goal:** Athlete config, altitude fix, refactored library. Working API serving existing analysis.

- **1a. Athlete config table** — single-row `athlete_config` table, migrate all hardcoded constants from `db.py`. Update all library modules to read from config. Update tests.
- **1b. Altitude data fix** — re-ingest 2024+ FIT files to recover altitude field (check field name mapping). Verify GPS semicircle conversion.
- **1c. VO2max equation fix** — replace ACSM general-population formula with trained-cyclist-specific equation (Hawley-Noakes or efficiency-adjusted).
- **1d. FastAPI skeleton** — `app.py` + `routes.py`, serving existing `wko5/` library over HTTP. Bearer token auth, strict CORS to localhost, ephemeral port. GPX upload with `defusedxml`, size limits, numeric bounds.
- **1e. Garmin tokens** — move from plaintext to macOS Keychain via `keyring`.

**Ships:** API at `localhost` serving all existing analysis (fitness, PMC, PD model, ride analysis, zones, profile) with proper auth. Config-driven, no hardcoded athlete values.

---

### Phase 2: Segment Analyzer + Durability Model
**Goal:** The novel analytical core — segment decomposition, empirical durability, fatigued PD curves.

- **2a. Segment analyzer** — `segments.py` + `physics.py`. Altitude/distance → grade → segment classification → (duration, power_required) demand tuples. Physics model using athlete config (CdA, Crr, weight). GPX import support.
- **2b. Durability model** — `durability.py`. Empirical degradation function fitted from historical long rides (>2h). Start with `scipy.optimize`, intensity-weighted kJ (TSS-based, not raw kJ). Circadian adjustment. Collapse zone detection.
- **2c. Fatigued PD curve** — compose PD model with durability model at any cumulative-work point. This is the "effective capacity at km 180" computation.
- **2d. FRC budget model** — stateful `recovery_ceiling` tracking depletion count. Sequential FRC depletion/recharge across segments.

**Ships:** `POST /api/segments/analyze`, `GET /api/durability`. Can answer "what does this route demand?" and "what's my capacity at each point?"

---

### Phase 3: Gap Analysis + Clinical Guardrails
**Goal:** Race readiness and health monitoring — the two most actionable outputs.

- **3a. Demand ratios** — `demand.py`. Joint sequential simulation (not product of marginals). For each Monte Carlo draw: sample PD params, simulate entire route with FRC budget and durability decay, record per-segment completion. Report success probabilities.
- **3b. Gap analysis API** — `POST /api/gap-analysis`. Per-segment demand ratios, bottleneck identification, overall route feasibility.
- **3c. Clinical guardrails** — `clinical.py`. Threshold-based first (not Bayesian yet). HR decoupling, power-HR inversion, resting HR elevation, CTL ramp rate, TSB floor. All thresholds from athlete config. Mandatory medical disclaimers on all Red flags.
- **3d. HRV distribution fix** — log-normal for HRV, AR(1) for resting HR (per Data Scientist review).
- **3e. Clinical API** — `GET /api/clinical-flags`. Persistent notification data for future UI.

**Ships:** "Am I ready for this event?" and "Is anything medically concerning?" are both answerable. Claude can use these via `/wko5-analyzer`.

---

### Phase 4: Training Block Analysis + Pacing
**Goal:** Historical training analysis and prospective race planning.

- **4a. Training block stats** — `blocks.py`. Deterministic summaries: volume, intensity distribution (Seiler 3-zone), TIZ, ride count, power changes at key durations. "What changed" differential when PD curve shifts.
- **4b. Periodization phase auto-detection** — classify periods as base/build/peak/recovery from intensity distribution and volume trends.
- **4c. Intensity distribution analysis** — are easy days easy? Compute IF on designated recovery days. Seiler zone split per week/month.
- **4d. Pacing optimizer** — `pacing.py`. Constrained optimization: intensity ceiling, FRC budget, energy balance, non-riding time budget. Per-segment target power output.
- **4e. Training block + pacing APIs** — `GET /api/training-blocks`, `POST /api/pacing`.

**Ships:** Full deterministic engine. All sub-projects 1-5 complete with point estimates.

---

### Phase 5: Frontend v1 (Browser)
**Goal:** D3 dashboard served by FastAPI. No Electron yet — validate the visual layer first.

- **5a. Static HTML shell** — `index.html` + `app.js` served by FastAPI static files. Tab bar, fixed CSS Grid layout, dark/light theme via CSS variables + `prefers-color-scheme`.
- **5b. 6 core D3 charts** — PMC (line/area), MMP/PD curve (log x-axis + model overlay), Ride Time Series (multi-line stacked), Zone Distribution (stacked bar), Segment Profile (altitude + demand ratio heatmap), Clinical Dashboard (traffic lights).
- **5c. Tab structure** — decision-context-oriented: Today (TSB + recent + flags), Fitness (PMC + rolling FTP + power profile), Event Prep (segments + demand + pacing), History (ride list + block analysis), Profile (rankings + phenotype + config).
- **5d. Post-ride landing state** — "New Activity" card on sync showing ride summary, guardrail checks, TSB impact.
- **5e. MMP recency toggle** — 30/60/90/365/all-time window selector on Fitness tab.

**Ships:** Fully functional browser dashboard at `localhost`. Open after a ride, check fitness, prep for events.

---

### Phase 6: Bayesian Layer
**Goal:** Upgrade point estimates to posterior distributions with credible intervals.

- **6a. Bayesian PD model** — replace `curve_fit` with NUTS (PyMC). Full-rank covariance. Store 4000 posterior samples in `posteriors.db`. Shuffled for draw ordering.
- **6b. Bayesian durability model** — population-level cold-start priors, narrows with data. Investigate sigmoid vs. exponential functional form.
- **6c. Demand ratio upgrade** — Monte Carlo from stored posteriors. Per-segment success probabilities with joint sequential simulation.
- **6d. Clinical guardrail upgrade** — conjugate priors (normal-inverse-gamma for HR, log-normal for HRV). Exponentially weighted moving baseline for non-stationarity.
- **6e. Progressive disclosure UI** — point estimate default, CI on hover, full posterior on click.
- **6f. Model validation framework** — expanding-window CV, calibration curves (PIT), CRPS, posterior predictive checks. WAIC/LOO-CV for model comparison.
- **6g. Measurement error model** — device-level bias (2-5%) as explicit parameter in PD likelihood.

**Ships:** All models produce posterior distributions. Demand ratios are probabilistic. Clinical flags are Bayesian anomaly detection.

---

### Phase 7: Electron Desktop App
**Goal:** Wrap the browser dashboard in Electron with embedded Claude Code terminal.

- **7a. Electron shell** — `main.js`, `preload.js`. Spawn FastAPI on launch, kill on quit. Health check endpoint + watchdog restart. Dynamic port selection via IPC.
- **7b. Security hardening** — `contextIsolation: true`, `nodeIntegration: false`, `sandbox: true`. CSP headers. Explicit `contextBridge` IPC allowlist. ANSI escape stripping on all rendered data.
- **7c. Terminal integration** — `node-pty` + `xterm.js` running Claude Code. Resizable split layout.
- **7d. Chart-to-terminal context passing** — clicking a segment/ride/flag sends structured context to the terminal session.
- **7e. Layout persistence** — tab order, split position saved to JSON config. Strict schema validation on config load.
- **7f. Confirmation dialogs** — weight/CdA/FTP changes show impact preview before applying.

**Ships:** Full desktop app with embedded Claude Code.

---

### Phase 8: Advanced Features
**Goal:** Everything else from the spec.

- **8a. Pacing scenario comparison** — side-by-side "what if +10W on climbs?" overlay.
- **8b. Draggable panel grid** — golden-layout or gridstack.js, with named layout presets + keyboard shortcuts.
- **8c. Training response model** — Bayesian associational (not causal), max 3-4 coefficients, MCMC offline. Gaussian process priors for non-stationarity. Explicit "associational, not causal" labeling on all outputs.
- **8d. Phase auto-detection review/override UI** — timeline with edit mode, drag boundaries, manual override stored in DB.
- **8e. Fueling interaction model** — CHO absorption degradation with duration as durability input. Requires nutrition data entry or log import.
- **8f. SQLCipher encryption at rest** — for distribution beyond personal use.
- **8g. Posterior integrity checksums** — SHA-256 hash per sample set, verified on load.
- **8h. Remaining 12 chart components** — Power Profile Radar, Ultra Comparison, EF Trend, Weekly TSS, Rides Table, Demand Heatmap, FRC Budget, Energy Balance, Durability Curve, Intensity Distribution, Phase Timeline, Recent Rides.

---

### Review Findings Incorporated Per Phase

| Review Finding | Addressed In |
|---|---|
| FastAPI auth + CORS + ephemeral port (Security C1) | Phase 1d |
| Electron sandboxing (Security C2, H4) | Phase 7b |
| Altitude data gap (Principal) | Phase 1b |
| Posterior storage schema (Principal) | Phase 6a |
| Joint demand ratio simulation (Principal, Data Scientist) | Phase 3a |
| VO2max equation (Exercise Physiologist) | Phase 1c |
| FRC recovery_ceiling stateful (Principal) | Phase 2d |
| Clinical disclaimers (Security, Exercise Physiologist) | Phase 3c |
| Garmin tokens to Keychain (Security H2) | Phase 1e |
| GPX protections (Security H1) | Phase 1d |
| Intensity-weighted durability (Exercise Physiologist) | Phase 2b |
| NUTS over VI (Data Scientist) | Phase 6a |
| Measurement error model (Data Scientist) | Phase 6g |
| Model validation (Data Scientist, Exercise Physiologist) | Phase 6f |
| Post-ride workflow (Product Designer) | Phase 5d |
| Landing state (Product Designer) | Phase 5d |
| Decision-context tabs (Product Designer) | Phase 5c |
| Progressive disclosure CIs (Product Designer) | Phase 6e |
| Chart-terminal context passing (Product Designer) | Phase 7d |
| HRV log-normal, HR AR(1) (Data Scientist) | Phase 3d |
| Multi-athlete defer (Principal) | Phase 1a (single-row config) |
| Training response associational (Data Scientist) | Phase 8c |
| Sigmoid durability investigation (Exercise Physiologist) | Phase 6b |

## Key Constraints

1. **Deterministic.** Same inputs → same outputs. Every number is traceable to input data. The engine computes, annotates, and flags. It never interprets, excuses, or recommends. That's Claude's job in Layer 3.

2. **Nothing hardcoded.** Every athlete-specific value, model bound, threshold, and tunable constant lives in the athlete profile. The engine has no knowledge of any specific athlete. Adding a new athlete = inserting a row in `athlete_profiles` and ingesting their FIT files.

3. **Physiological constants are fine.** ACSM VO2max formula coefficients (12.35, 3.5), Coggan zone percentage definitions (55%, 75%, etc.), and similar published scientific constants remain in code — they're universal, not athlete-specific. But even PMC time constants (42-day CTL, 7-day ATL) are in the athlete profile because some coaches use different values.
