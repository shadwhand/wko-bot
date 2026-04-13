# Tools & Platforms

Software, hardware, and ecosystems used in power-based cycling analytics. How each fits into the platform.

Evidence levels: **[R]** = Research-backed, **[E]** = Experience-based, **[O]** = Opinion.

---

## 1. WKO5 (Formerly WKO4)

### Overview

WKO5 is the most advanced power analysis software for cycling, built on Dr. Andrew Coggan's Power-Duration Model. It is the primary analytical engine behind this platform's methodology.

### Core Capabilities

| Feature | Description | Platform Relevance |
|---------|-------------|-------------------|
| **Power-Duration Model** | Mathematical model of the entire power-duration relationship; validated against ~200 seasoned athletes | Foundation for `pdcurve.py`; rolling FTP, CP, W' decomposition |
| **iLevels** | 9 individualized training levels derived from PD curve shape | Prescription engine; replaces percentage-based zones above threshold |
| **Auto-Phenotyping** | Automatic athlete classification (sprinter, TTer, all-rounder, climber) from PD curve | `gap_analysis.py`; strengths/limiters identification |
| **Optimized Intervals** | Interval prescription based on individual PD curve | Dose-response precision for interval design |
| **Power Duration Metrics History** | Track micro-changes in fitness through PD curve evolution over time | Continuous monitoring instead of isolated tests |
| **Fatigue Resistance Charts** | PD curve plotted after specific kJ expenditure (e.g., 1,500 kJ) | `durability.py`; ultra-endurance analysis |
| **Elevation-Corrected Power** | Adjusts power data for altitude effects | Environmental analysis for mountain events |
| **Performance Manager Chart (PMC)** | CTL/ATL/TSB tracking | `training_load.py`; but EC warns against treating CTL as "fitness" |
| **Stamina metric** | Measures power sustainability over extended durations | Ultra-distance profiling |
| **Time to Exhaustion (TTE)** | Duration at FTP before failure | Key metric for TT and ultra performance |
| **Cadence Analysis** | Cadence distribution and optimization charts | Pacing and efficiency analysis |
| **Matches Burnt by Pmax/FRC** | Anaerobic effort tracking per hour | Race demand analysis |
| **mFTP vs CTL Peaks** | Historical fitness peaks correlated with training load | Season review and optimal CTL targeting |
| **Weekly Ramp Rate** | CTL progression analysis; sustainable ramp rates | Overtraining prevention; `clinical.py` |

### Key WKO5 Metrics

| Metric | Definition | Source |
|--------|-----------|--------|
| mFTP (modeled FTP) | FTP derived from PD model, not isolated test | Coggan PD model [R] |
| FRC (Functional Reserve Capacity) | Anaerobic work capacity above FTP | Coggan PD model [R] |
| Pmax | Maximum instantaneous power | PD model extrapolation [R] |
| TTE | Time to exhaustion at FTP | PD model [R] |
| Stamina | Ratio of sustained power at long durations vs FTP | WKO4+ [E] |
| dFRC | Dynamic FRC tracking within a ride | Real-time match burning [E] |

### Pricing & Access

- Desktop application (Mac/Windows); requires license
- WKO5 is the current version (evolution of WKO4)
- Part of the Peaksware ecosystem alongside TrainingPeaks

### EC Caveats About WKO Metrics

- **Rolling PD curves from training data are more reliable than isolated test days** -- single tests have ~2% power meter error (WD-62) [R]
- **PD model updates with each file uploaded** -- captures changes formal testing would miss (Cusick) [E]
- **CTL is NOT fitness** -- specifically objected to by Kolie Moore (TMT-68) [E]
- **TSB/Form is widely misinterpreted** -- positive TSB does not mean peaked (TMT-68) [E]

---

## 2. TrainingPeaks

### Overview

The dominant cloud-based training platform for endurance athletes and coaches. Provides workout planning, execution tracking, and performance analysis. Sister product to WKO5 under the Peaksware umbrella.

### Core Capabilities

| Feature | Description | Platform Relevance |
|---------|-------------|-------------------|
| **Workout Library & Builder** | Create, store, and share structured workouts | Training prescription delivery |
| **Annual Training Plan (ATP)** | Season planning tool with CTL targets by week | `blocks.py`; periodization framework |
| **Performance Management Chart (PMC)** | CTL/ATL/TSB visualization | `training_load.py` |
| **TSS / IF / NP** | Per-ride metrics (Coggan's framework) | Core metrics for all ride analysis |
| **Calendar View** | Visual training log with planned vs completed workouts | Compliance tracking |
| **Ramp Rate Monitoring** | CTL progression tracking with alerts | `clinical.py`; overtraining detection |
| **Threshold Improvement Notifications** | Automatic detection of new peak powers | FTP and zone update triggers |
| **Coach-Athlete Platform** | Coaches can prescribe, athletes execute, both analyze | Coaching workflow backbone |
| **Device Sync** | Garmin, Wahoo, Zwift, and dozens of other integrations | Data pipeline source |
| **TrainingPeaks Virtual** | Structured workouts executed on indoor trainers | ERG mode integration |
| **TrainingPeaks Strength** | Strength workout logging with video library | Off-bike training tracking |

### Key Metrics Available

| Metric | Notes |
|--------|-------|
| TSS (Training Stress Score) | Per-ride training load relative to FTP |
| CTL (Chronic Training Load) | 42-day rolling average of TSS ("fitness") |
| ATL (Acute Training Load) | 7-day rolling average of TSS ("fatigue") |
| TSB (Training Stress Balance) | CTL - ATL ("form") |
| IF (Intensity Factor) | NP / FTP |
| NP (Normalized Power) | Physiologically-weighted average power |
| EF (Efficiency Factor) | NP / avg HR; aerobic fitness indicator |
| Pa:Hr (Power-to-HR decoupling) | Drift metric for aerobic endurance |

### Pricing

- Free basic account (limited analytics)
- Premium account (full PMC, TSS, structured workouts)
- Coach Edition (multi-athlete management)

### Platform Integration

- TrainingPeaks is the primary data source for this analytics platform
- API access available for automated data ingestion
- Ride files (.FIT) synced from Garmin/Wahoo flow through TrainingPeaks to local SQLite DB

---

## 3. Best Bike Split (BBS)

### Overview

Advanced mathematical modeling software for predicting and optimizing cycling performance on specific courses. Acquired by TrainingPeaks. Particularly relevant for ultra-endurance pacing.

### Core Capabilities

| Feature | Description | Platform Relevance |
|---------|-------------|-------------------|
| **Performance Prediction** | Predict finish time given FTP, weight, equipment, course, weather | Pre-race planning for target events |
| **Pacing Optimization** | Optimal power targets per course segment | `route_analysis.py`; segment-by-segment power plans |
| **Equipment Modeling** | Compare wheel, frame, helmet, position changes | Aero optimization |
| **Weather Integration** | Wind speed/direction, temperature, humidity in predictions | Environmental race planning |
| **Race Plan Export** | Pacing cheat sheet or Garmin data field | Race-day execution |
| **Race Plan Comparison** | Compare multiple strategies side-by-side | Scenario analysis |
| **Course Simulation** | Export to indoor trainer for course-specific training | Event-specific preparation |

### Prediction Accuracy

| Event | Prediction Accuracy | Source |
|-------|-------------------|--------|
| Tour de France Stage 11 TT (Contador) | Within 3 seconds | BBS / Ryan Cooper [E] |
| TdF Stage 11 TT (Froome) | Within 9 seconds | BBS / Ryan Cooper [E] |
| TdF Stage 11 TT (Tony Martin) | Within 11 seconds | BBS / Ryan Cooper [E] |
| IRONMAN Mont Tremblant (TJ Tollakson) | Within 1:20 of actual over 112 miles | [E] |
| Left Hand Canyon climb (Dirk Friel) | Within 6 seconds over 16 miles | [E] |

### Ultra-Endurance Application

- **Leadville 100 modeling** -- 5% weight reduction = 15+ minutes faster, primarily on climbs [E]
- Segment-by-segment power targets critical for ultra events where terrain varies over 8+ hours
- Course simulation on indoor trainer enables terrain-specific preparation

---

## 4. Power Meters

### Types & Accuracy

| Type | Location | Pros | Cons | Accuracy |
|------|----------|------|------|----------|
| **Crank-based (dual)** | Both crank arms | L/R balance, total power | Expensive; battery per side | +/- 1-1.5% |
| **Crank-based (single)** | Left crank only | Affordable, easy install | Doubles left leg; no true L/R | +/- 2% |
| **Spider-based** | Chainring spider | Measures total power directly | Chainring-specific; expensive | +/- 1-1.5% |
| **Pedal-based** | Pedals | Easy swap between bikes; L/R | Cleat system dependent; fragile | +/- 1-2% |
| **Hub-based** | Rear hub | Measures all power at wheel | Heavy; wheel-specific; rear only | +/- 1-1.5% |
| **Trainer-based** | Smart trainer | No bike-mounted hardware needed | Indoor only; varies by trainer | +/- 2-5% |

### Key Brands

| Brand | Notable Products | Type |
|-------|-----------------|------|
| **Stages** | Stages LR, Stages L | Crank (single & dual) |
| **Quarq** | DZero, DFour | Spider-based |
| **Garmin (Rally)** | Rally RS/RK/XC | Pedal-based |
| **SRM** | SRM Origin, PM9 | Spider-based (gold standard) |
| **Favero** | Assioma Duo/Uno | Pedal-based |
| **4iiii** | Precision, Podium | Crank (single & dual) |
| **Power2Max** | NG/NGeco | Spider-based |
| **Wahoo** | POWRLINK Zero | Pedal-based |

### EC Guidelines on Power Meters

- **Power meter error is approximately 2%** -- at 300W, this means 294-306W range (WD-62) [R]
- **Meaningful FTP change must exceed 2% (~6W at 300W)** to distinguish from measurement noise (WD-62) [R]
- **Switching power meters breaks continuity** -- single to dual-sided can show zero FTP gain even with massive improvement (TMT-70) [E]
- **Consistency > absolute accuracy** -- use the same power meter for all training/testing [E]
- **ERG mode on trainers can hide true readiness** -- free-ride mode reveals daily capacity; wean off ERG for key sessions (TMT-73) [E]

---

## 5. Garmin Ecosystem

### Overview

Garmin is the dominant cycling computer and wearable ecosystem, providing GPS tracking, power display, navigation, and physiological metrics.

### Key Devices for Cycling

| Device | Category | Key Features |
|--------|----------|-------------|
| **Edge 1050/840/540** | Bike computer | GPS, power display, navigation, training load, ClimbPro |
| **Forerunner 965/265** | Multisport watch | Wrist HR, training readiness, VO2max estimate, HRV |
| **Fenix 8 / Enduro 3** | Ultra watch | Multi-day battery, solar, maps, ultra-specific features |
| **Varia Radar/Light** | Safety | Rear radar + tail light; approaching vehicle alerts |
| **Rally Power Pedals** | Power meter | Dual-sided, multiple cleat systems |
| **HRM-Pro Plus** | Chest strap | HR, running dynamics, HRV |

### Garmin Connect Integration

- **Activity sync** to TrainingPeaks, WKO5, and other platforms via API
- **Training Status / Load** -- Garmin's own training load algorithm (distinct from TSS/CTL)
- **Body Battery** -- recovery readiness metric based on HRV, stress, sleep
- **Sleep tracking** -- sleep stages, HRV during sleep, sleep score
- **Weather data** -- auto-attached to activities; useful for environmental analysis
- **.FIT file export** -- standard format for ride data; feeds into platform SQLite DB

### Platform Integration

- Garmin .FIT files are the primary data source for the analytics platform
- `garmin_mcp_sync.py` handles automated data retrieval
- Weather, HR, power, GPS all extracted from .FIT files
- HRV data used for recovery monitoring and clinical flags

### Limitations

- **VO2max estimates are directionally useful but not precise** -- use PD model instead [E]
- **Training Load/Status algorithms are proprietary** -- cannot be validated or customized [E]
- **Wrist HR unreliable during high-intensity intervals** -- chest strap recommended for key sessions [E]

---

## 6. Indoor Trainers

### Types

| Type | How It Works | Pros | Cons |
|------|-------------|------|------|
| **Direct-drive smart** | Bike mounts to trainer cassette | Most accurate power; quiet; realistic feel | Expensive; heavy |
| **Wheel-on smart** | Rear tire on roller | Cheaper; easy setup | Tire wear; less accurate; slippage |
| **Rollers** | Both wheels on cylinders | Balance training; natural feel | No resistance control; skill required |
| **Non-smart** | Manual resistance | Cheap | No power data; no ERG mode |

### Key Brands & Models

| Brand | Model | Type | Power Accuracy |
|-------|-------|------|---------------|
| **Wahoo** | KICKR / KICKR Core | Direct-drive | +/- 1-2% |
| **Tacx (Garmin)** | NEO 3 / Flux S | Direct-drive | +/- 1-2% |
| **Saris** | H3 / H4 | Direct-drive | +/- 2% |
| **Elite** | Direto / Suito | Direct-drive | +/- 1.5-2.5% |

### Indoor Training Considerations from EC

- **Indoor training recovery multiplier: 1.1-1.2x outdoor TSS** -- indoor rides are harder than equivalent outdoor rides (TMT-51) [E]
- **The problem with only training indoors** -- environmental skill development, bike handling, and mental variety are lost [E]
- **ERG mode hiding true readiness** -- free-ride mode reveals daily capacity better than locked-in ERG (TMT-73) [E]
- **Indoor heat without fan simulates humid conditions** -- useful for heat acclimatization [E]
- **Transition from indoor to outdoor** -- adjust tire pressure, pacing, handling; performance may differ [E]

### Virtual Training Platforms

| Platform | Key Feature | Integration |
|----------|-------------|-------------|
| **Zwift** | Virtual worlds, group rides, races | Syncs to TrainingPeaks/Garmin |
| **TrainerRoad** | Structured workout library, adaptive training | Syncs to TrainingPeaks |
| **Rouvy** | Real video courses, AR | Syncs to TrainingPeaks |
| **TrainingPeaks Virtual** | Execute TP structured workouts on trainer | Native TP integration |
| **Wahoo SYSTM (formerly Sufferfest)** | Structured workouts + 4DP testing | Wahoo ecosystem |

---

## 7. Other Relevant Tools

### Nutrition & Hydration

| Tool | Purpose | Notes |
|------|---------|-------|
| **SweatID** | Personalized sweat analysis | Electrolyte profiling; but EC notes sweat tests are nearly useless for prescription (Persp-41) |
| **Supersapiens / CGM** | Continuous glucose monitoring | Real-time fueling feedback; experimental for athletes |
| **MyFitnessPal** | Calorie/macro tracking | Useful for off-bike nutrition; ~20% label error acknowledged |

### Data Analysis & APIs

| Tool | Purpose | Notes |
|------|---------|-------|
| **Golden Cheetah** | Open-source power analysis | Free alternative to WKO; less individualized |
| **Strava** | Social, segment tracking | Complementary; segment analysis; fitness/freshness basic |
| **intervals.icu** | Free analytics platform | Strong PMC implementation; growing feature set |
| **Python / Pandas** | Custom analysis | This platform's analytics pipeline is Python-based |

### Bike Fit

| Tool | Purpose | Notes |
|------|---------|-------|
| **Retul / Guru** | 3D motion capture bike fit | Professional fitting systems |
| **Saddle pressure mapping** | Contact point optimization | Critical for ultra-endurance (8+ hour saddle time) |

---

## 8. How Each Tool Fits Into the Analytics Platform

### Data Flow Architecture

```
Garmin Device (.FIT files)
    |
    v
Garmin Connect (cloud sync)
    |
    v
TrainingPeaks (data hub, workout planning)
    |
    v
Local SQLite DB (1,653 activities, 11M records)
    |
    v
Python Analytics Pipeline
    |-- pdcurve.py (PD model, rolling FTP -- WKO5 concepts)
    |-- training_load.py (TSS, CTL, ATL, TSB -- Coggan/TP metrics)
    |-- durability.py (kJ/kg bins -- EC methodology)
    |-- nutrition.py (on-bike fueling models)
    |-- zones.py (iLevels + classic zones)
    |-- route_analysis.py (BBS-style pacing, elevation correction)
    |-- clinical.py (red/amber flags -- EC clinical framework)
    |-- gap_analysis.py (strengths/limiters -- WKO5 concepts)
    |-- blocks.py (periodization -- Friel/Moore hybrid)
    |
    v
Dashboard / API (React frontend, 35 endpoints)
```

### Tool-to-Module Mapping

| Tool/Platform | Primary Platform Module(s) | Role |
|--------------|---------------------------|------|
| WKO5 | `pdcurve.py`, `zones.py`, `gap_analysis.py` | PD model, iLevels, phenotyping |
| TrainingPeaks | `training_load.py`, `blocks.py` | TSS/CTL/PMC, season planning |
| BestBikeSplit | `route_analysis.py` | Course-specific pacing optimization |
| Garmin | Data pipeline (`.FIT` files) | Primary data source |
| Power meter | All modules | Power data quality determines all downstream accuracy |
| Indoor trainer | `training_load.py` (1.1-1.2x multiplier) | Indoor TSS correction |
| EC methodology | `clinical.py`, `durability.py`, `nutrition.py` | Evidence-based coaching logic layer |

---

## 9. Common Mistakes with Tools

1. **Treating power meter number as absolute truth** -- 2% error means 5W changes are noise (WD-62) [R]
2. **Switching power meters mid-season** -- breaks FTP tracking continuity (TMT-70) [E]
3. **Chasing CTL number in TrainingPeaks** -- CTL going up while performance goes down is a classic overreaching signal (TMT-72) [E]
4. **Over-relying on indoor training** -- environmental skills, bike handling, and mental variety are lost; recovery cost is higher (TMT-51) [E]
5. **Using Garmin VO2max as a training metric** -- it is an estimate, not a measurement; use PD model instead [E]
6. **Not calibrating tools** -- power meters, trainers, and scales all need regular calibration [E]
7. **Ignoring BestBikeSplit for ultra events** -- segment-by-segment pacing is critical when events span 8+ hours over variable terrain [E]
8. **Buying tools before movement competence** -- a $3,000 power meter on a rider who cannot squat properly prioritizes data over the body producing it [O]

---

## 10. Platform Integration Hints

### Priority Integrations

1. **Garmin MCP sync** -- automated .FIT file retrieval (already implemented: `garmin_mcp_sync.py`)
2. **TrainingPeaks API** -- structured workout sync, planned vs completed comparison
3. **WKO5 concepts** -- PD model, iLevels, phenotyping implemented in Python
4. **BestBikeSplit concepts** -- route analysis with environmental modeling
5. **Power meter validation** -- consistency checks across devices, drift detection

### Cross-References

- [Notable Coaches & Methods](notable-coaches-methods.md) — Coggan (WKO/TSS), Cusick (iLevels), Moore (durability) built these tools
- [FTP & Threshold Testing](../concepts/ftp-threshold-testing.md) — Rolling PD model in WKO5 vs formal tests; power meter accuracy implications
- [Power-Duration Modeling](../concepts/power-duration-modeling.md) — WKO5's PD model is the core analytical engine; phenotyping and iLevels derive from it
- [Training Load & Recovery](../concepts/training-load-recovery.md) — TrainingPeaks PMC (CTL/ATL/TSB) and WKO5 ramp rate monitoring
- [Ultra-Endurance](../concepts/ultra-endurance.md) — WKO5 fatigue resistance charts and BBS segment pacing for 8+ hr events
- [Heat, Altitude & Environment](../concepts/heat-altitude-environment.md) — BBS weather modeling and Garmin weather data for environmental race planning
- [Pacing Strategy](../concepts/pacing-strategy.md) — Best Bike Split course modeling and race plan optimization

---

## Sources

| Source | Type | Key Contribution |
|--------|------|-----------------|
| EC WD-62 | Podcast | Power meter error quantification |
| EC TMT-70 | Podcast | Power meter switching problems |
| EC TMT-68 | Podcast | CTL is not fitness; TSB misinterpretation |
| EC TMT-73 | Podcast | ERG mode limitations |
| EC TMT-51 | Podcast | Indoor training recovery multiplier; HRV utility |
| TrainingPeaks: iLevels (Coggan/Cusick) | Article | WKO individualization capabilities |
| TrainingPeaks: WKO4 Training Plans (Rollinson) | Article | WKO coaching workflow |
| TrainingPeaks: BBS Acquisition (Gear Fisher) | Article | BBS capabilities and vision |
| TrainingPeaks: Predicting Performance with BBS (Vance) | Article | BBS practical application |
| TrainingPeaks: Fatigue Resistance (Novak) | Article | WKO5 fatigue resistance visualization |
| TrainingPeaks: Tour de France vs Tour Divide (Howes) | Article | Cross-tool comparison at ultra scale |
