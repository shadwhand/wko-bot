# Durability & Fatigue Modeling

Knowledge wiki page for the cycling analytics platform. Compiled from Empirical Cycling podcast episodes, academic literature, TrainingPeaks coaching articles, and platform source code.

Evidence levels: **[R]** = Research-backed, **[E]** = Experience-based, **[O]** = Opinion/speculation.

---

## 1. Definition and Terminology

### What Is Durability?

Durability is the ability to maintain power output after accumulated work. It is not a new concept -- coaches have measured post-kJ power since power meters existed in the late 1990s. WKO4/5 users were plotting mean-max power after X kilojoules long before academic literature formalized the term. [E] (WD-60)

The formal definition from **Maunder et al. (August 2021)** -- the first paper to use the word "durability" in this context:

> "The time of onset and magnitude of deterioration in physiological characteristics over time during prolonged exercise." [R]

**Kolie Moore's critique of this definition:** It is deterioration of *performance* that reveals deterioration of measurements, not physiology deteriorating. Your heart's capacity to pump blood is not impaired because your legs fatigue. What is lost is the *ability to express performance*. [E] (WD-60)

### Four Overlapping Sub-Terms

A definitions paper proposed four distinct concepts:

| Term | Definition | Scope |
|------|-----------|-------|
| **Durability** | Decline of CP, VO2max, etc. during *steady* power output | Sustained fatigue |
| **Fatigability** | Acute impairment of max power output post-kJ/kg (Enoka's definition) | Peak power loss |
| **Repeatability** | Capacity to recover and reproduce high-intensity across bouts/stages/heats | Intermittent recovery |
| **Resilience** | Ability to resist fatigue and maintain performance; includes mental aspects | Holistic fatigue resistance |

**Coaching consensus:** These are highly correlated and likely not separately trainable. Coaches settled on kJ/kg as the unified catch-all metric. [E] (WD-60)

> **Platform note (`durability.py`):** The model does NOT decompose these four sub-types. They are treated as a single degradation process.

### What Coaches Have Always Called It

The concept pre-dates the academic literature by decades. Coaches variously called it "endurance," "fatigue resistance," "stamina," or simply "the ability to go hard at the end of a long ride." Tim Cusick at WKO/TrainingPeaks has used the term "fatigue resistance" since WKO4, comparing fresh PD curves to post-kJ PD curves to visualize it. [E]

---

## 2. The Controversy: Is Durability Overrated?

### The Evidence Base Is Thin

Kolie Moore read every published paper on durability. His assessment: the evidence base is surprisingly thin, and media interpretations are "much more strongly advised than the evidence would suggest." The field is still in a definitional squabbling phase. [E] (WD-60)

### The Core Argument: Sufficient Power First

From the van Erp (2021) World Tour data:

| Category | Starting Power | Drop at 50 kJ/kg |
|----------|---------------|-------------------|
| Successful sprinters | 18.25 W/kg (10s) | ~8% |
| Less successful sprinters | 17.7 W/kg (10s) | ~18% |
| Successful climbers | 6.28 W/kg (20min) | ~4% |
| Less successful climbers | 5.99 W/kg (20min) | ~9% |

The better group starts with more power AND loses less. This is correlation only -- there is no established causality. [R] (WD-60)

**The implication:** Over-indexing on durability without sufficient absolute power is a strategic error. You cannot "durability" your way to a result you lack the engine for. [E] (WD-60)

### Goodhart's Law Warning

Over-indexing on kJ/kg as a metric could lead to: [E] (WD-60)

1. Spending less energy in races (bad strategy) to "protect" durability numbers
2. Only doing long easy rides (missing power development)
3. Weight manipulation to improve kJ/kg ratios
4. Low-carb training for durability -- explicitly dismissed: "I checked my list... there is nothing here." [E]

> **Platform note (`durability.py`, `gap_analysis.py`):** Always display durability metrics alongside absolute power. Check absolute thresholds before raising durability flags.

---

## 3. Measurement: kJ/kg as the Standard Unit

### Why kJ/kg and Not Raw kJ

**van Erp et al. (September 2021)** -- the first paper to use kilojoules per kilogram for durability measurement. [R]

Raw kJ is misleading across body weights: 2000 kJ is a massive workload for a 55 kg woman but "just getting warmed up" for a 75 kg professional male. kJ/kg normalizes for body weight. [E] (WD-60)

**Standard binning:** 10 kJ/kg intervals (10, 20, 30, 40, 50 kJ/kg). [R] (van Erp 2021)

### Benchmarks

| Benchmark | Power Drop at 50 kJ/kg | Source |
|-----------|----------------------|--------|
| Elite pro | < 2% | WD-60 [E] |
| Strong amateur | 2-10% | WD-60 [E] |
| Good amateur | 10-20% | WD-60 [E] |
| Average amateur | 20-40% | WD-60 [E] |

> **Platform note (`durability.py :: durability_benchmark()`):** Classifies athletes against these tiers.

### Practical Field Test (from TrainingPeaks / ProCyclingCoaching)

Perform a max effort at a target duration after burning a set kJ amount:

1. Ride 2-2.5 hours at endurance pace to accumulate ~1500 kJ
2. Perform a 1-minute all-out effort (ideally same segment each time)
3. Compare to your fresh all-time best at that duration

| Drop | Rating |
|------|--------|
| < 1% | Elite/pro |
| < 5% | Very good |
| 5-10% | Good |
| 10-15%+ | Average |

Source: Jakub Novak (ProCyclingCoaching), TrainingPeaks article

### WKO5 Visualization

WKO5 plots the Power Duration Curve after a specific energy expenditure. The standard view compares:
- **Red line:** Fresh PD curve
- **Green line:** PD curve after X kJ of work

Tim Cusick's example (Amber Neben, world TT champion, 50 kg):
- Fresh 20-min power: 272W; After 2000 kJ: 268W (-4W, ~1.5% drop)
- Compared to "Joe Rider" (Cat 3, 65 kg): Fresh 274W; After 2000 kJ: 242W (-32W, ~11.7% drop)

"Fatigue resistance is the elite pro difference." -- Tim Cusick [E]

---

## 4. Measurement Caveats (Critical for Implementation)

Testing durability is harder than most people think. Six major confounds: [E] (WD-60)

### 4.1 Missing Fresh Baseline

If your only 1-minute max effort happened after 20 kJ/kg, that becomes your "0% loss" baseline -- completely misleading. You need a genuine fresh effort within the recent past to anchor the comparison.

> **Platform note (`durability.py :: check_fresh_baseline()`):** Checks for efforts in first 2 hours of ride AND cumulative kJ < 500. Flags stale baselines with staleness_days metric. Returns per-duration status for 60s, 300s, and 1200s.

### 4.2 Pre-Effort Intensity Context

2000 kJ at endurance pace then testing is very different from 2000 kJ of racing then testing. The *how* of energy expenditure matters enormously, not just the *how much*.

> **Platform note (`durability.py :: compute_windowed_mmp()`):** Computes `pre_effort_avg_if` and classifies into `endurance_preload` (IF < 0.65), `tempo_preload` (IF 0.65-0.80), or `race_preload` (IF > 0.80) for each window after the first.

### 4.3 Body Weight Scaling

Already addressed by kJ/kg normalization, but important: always use kJ/kg, never raw kJ, for cross-athlete comparisons.

### 4.4 Anaerobic Capacity Confound

Lab protocols at 105-108% threshold mean large W' athletes coast while small W' athletes are near max. Track sprinters (largest W') have the WORST real-world durability despite lab results suggesting otherwise. [E] (WD-60)

### 4.5 Nutrition as Dangling Confounder

Cannot be controlled in field data. Has a massive effect on durability measurements. An athlete who bonks at 3 hours due to under-fueling will show catastrophic durability numbers that reflect nutrition failure, not fitness limitation. [E] (WD-60)

> **Platform note (`durability.py :: fit_durability_model()`):** When the kJ decay rate `b > 0.003`, raises a `fueling_confound_warning`: "High degradation rate -- poor durability may reflect fueling habits, not fitness."

### 4.6 Environmental Factors

Heat, cold, altitude, and wind all affect measurements. No standardization is possible in field data.

---

## 5. The Degradation Factor Model

### Mathematical Form

The platform models durability as a dual exponential decay:

```
df = a * exp(-b * kJ/1000) + (1-a) * exp(-c * hours)
```

Where:
- `df` = degradation factor (1 = fresh, 0 = fully degraded)
- `a` = weight between kJ-based and time-based components
- `b` = kJ decay rate (how fast power drops per unit of work)
- `c` = time decay rate (how fast power drops per hour elapsed)

> **Platform note (`durability.py :: degradation_factor()`):** Returns float between 0 and 1. If `weight_kg` is provided, normalizes kJ to kJ/kg (recommended per van Erp 2021).

### Why Dual Components: kJ-Based vs Time-Based Fatigue

Two distinct fatigue mechanisms are at play:

**kJ-based fatigue (the `b` term):**
- Glycogen depletion and metabolic byproduct accumulation
- Directly proportional to work done
- Dominant mechanism in high-intensity efforts
- What most durability literature measures

**Time-based fatigue (the `c` term):**
- Central fatigue (neural drive reduction)
- Thermoregulatory stress
- Postural/mechanical fatigue
- Psychological fatigue
- Dominant in ultra-endurance events even at low power

The parameter `a` controls the relative weight. A value near 1.0 means kJ dominates; near 0.0 means time dominates.

### Fitting the Model

> **Platform note (`durability.py :: fit_durability_model()`):**

1. Selects rides longer than `min_ride_hours` (default 2h)
2. Computes windowed MMP at 4 durations (60s, 300s, 2400s, 3600s) in non-overlapping 2-hour windows
3. Uses the first window's 5-min power as the "fresh" baseline
4. Fits the decay model to all subsequent windows via scipy `curve_fit`
5. Bounds: `a` in [0.01, 0.99], `b` in [0.0001, 0.01], `c` in [0.001, 0.5]
6. Returns fitted params, RMSE, rides used, and fueling confound warning

Requirements: minimum 5 long rides, minimum 10 data points after filtering.

### Effective Capacity (Fatigued PD Curve)

```
effective_capacity = fresh_mmp * degradation_factor
```

This is the workhorse calculation. At any point in a ride, your available power at any duration is your fresh power multiplied by your current degradation factor.

> **Platform note (`durability.py :: effective_capacity()`):** Used by `pacing.py` and `gap_analysis.py` to project fatigued power onto route segments.

---

## 6. FRC Budget Model

Separate from the gradual degradation model, the FRC (Functional Reserve Capacity) budget tracks the acute depletion and recovery of anaerobic work capacity within a ride.

### Mechanics

- Power above mFTP depletes FRC at a rate of `(power - mFTP) * duration / 1000` kJ
- Power below mFTP recharges FRC at a recovery rate (default 50%) up to a ceiling
- Deep depletions (> 50% of total FRC in one effort) increment a depletion counter
- Recovery ceiling degrades with successive deep depletions: `ceiling = max(0.5, 1.0 - depletion_count * 0.1)`

This models the "match-burning" phenomenon: each deep anaerobic effort reduces your ability to fully recover for the next one.

> **Platform note (`durability.py :: frc_budget_simulate()`):** Simulates FRC budget across sequential segments. Returns per-segment FRC remaining, percentage, depletion count, and recovery ceiling.

---

## 7. Repeatability Index

A complementary metric to overall durability: the ratio of the 3rd-best to the 1st-best effort at a given duration within a single ride.

- High repeatability (> 0.95): Can reproduce efforts consistently across a race
- Low repeatability (< 0.80): Significant drop-off after initial efforts

This corresponds to the "repeatability" sub-concept from the definitions paper and maps to real-world scenarios like repeated climbs, multiple sprint contests, or criterium racing.

> **Platform note (`durability.py :: repeatability_index()`):** Computes from non-overlapping peak efforts at a configurable duration (default 300s).

---

## 8. Durability-Aware Pacing

### The Pacing Problem

The pacing solver answers: "What base power should I hold so that, accounting for fatigue over the entire ride, I finish in my target time?"

### How It Works

Base power is your fresh, flat-road power. Actual per-segment power accounts for:
1. **Degradation factor** -- power available decreases as kJ and time accumulate
2. **Terrain** -- grade affects speed-to-power relationship
3. **Aerodynamics** -- CdA, drafting percentage
4. **Physics** -- wind resistance is exponential (key pacing insight)

> **Platform note (`pacing.py :: solve_pacing()`):** Uses Brent's method to find the base power where total riding time equals the target. Each segment's target power = `base_power * degradation_factor(cumulative_kJ, elapsed_hours)`.

### Pacing Principles from the Literature

**Even pacing wins in long events.** Consistent evidence across cycling and triathlon that negative or even splits outperform positive splits. Banking time early is always a losing strategy due to exponential fatigue cost. [R] (multiple TrainingPeaks sources)

**Wind resistance is exponential.** The faster you go, the more resistance you get. Optimal pacing means higher power on climbs (lower speed, less aero drag, higher speed gain per watt) and slightly lower power on descents. This is the fundamental insight behind tools like Best Bike Split. [R]

**Variability Index matters.** How steadily paced a ride was ridden directly predicts performance outcomes. Lower VI (more even pacing) correlates with better race results, especially in long-course triathlon and time trials. [E] (Andrew Yoder / TrainingPeaks)

---

## 9. Training Durability

### What the Research Shows

Training evidence for specifically improving durability is underwhelming. [R] (WD-60)

- Cross-sectional study (Pro U23): correlation between low-intensity riding (under VT1) and fatigue resistance. **R = 0.4, R-squared ~ 0.2** -- only 20% of variability explained. [R]
- One PhD thesis with volume confound, 6W vs 12W improvement, tiny sample. [R]
- Maintaining fatigue resistance later in season correlated with higher training load at lower intensities (weak R values). [R]

### What Works in Practice

**Total time riding is the best predictor of durability** -- not specific "durability workouts." [E] (WD-60, strong)

Specific training approaches, ordered by evidence strength:

| Method | Description | Evidence |
|--------|-------------|----------|
| **Long rides** | Monthly 4-6+ hour rides | [E] strong -- WD-60, Cusick |
| **Late-ride intervals** | FTP/SS efforts after 2+ hours of endurance riding | [E] strong -- WD-60, Cusick, Novak |
| **Tempo home** | 30-60 min of tempo as the last part of a long ride | [E] -- Cusick |
| **Fatigue-prime intervals** | 1-min max sprint after 1000-1500 kJ, then 2-4 reps at 90-95% of that fatigued sprint | [E] -- Novak (ProCyclingCoaching) |
| **Progressive threshold** | 4x15min FTP spread across 4-hour ride | [E] -- WD-60 |
| **Low-cadence tempo** | Zone 3/4 at 50-70 RPM -- recruits more muscle fibers, improves fatigue resistance without high cardiovascular cost | [E] -- Landry Bobo, Andrew Yoder |
| **Gravel/varied terrain** | Long sessions on unpredictable surfaces (Marquardt's approach) | [E] -- Andrew Yoder |
| **Sweet spot extension** | Build to 60-80 min SST sessions; stretch tempo past 2 hours | [E] -- Cusick (WKO4 case study) |

**Key coaching insight:** Efforts throughout the ride are better than efforts clustered at the end (compliance issue). [E] (WD-60)

### What Doesn't Work

| Approach | Why It Fails | Source |
|----------|-------------|--------|
| Low-carb training for durability | No evidence; explicitly dismissed | WD-60 [E] |
| Reducing race energy expenditure | Goodhart's Law -- worse race results | WD-60 [E] |
| Only doing long easy rides | Misses power development | WD-60 [E] |
| Lab-style "durability protocols" | Anaerobic capacity confounds results | WD-60 [E] |

### Aerobic and Anaerobic Are Not Zero-Sum

Heavy lifting does NOT hurt durability long-term. Kolie Moore trains sprinters from 1500W/400W FTP to 1900W/430W FTP -- both improve. [E] (WD-60)

> **Platform note (`gap_analysis.py`):** No trade-off modeling between aerobic and anaerobic improvements.

---

## 10. Maunder et al. and the Academic Literature

### Key Papers

**Maunder et al. (August 2021)** -- First "durability" paper [R]
- Defines durability formally
- Introduces W' accumulation as a durability metric
- Discusses heart rate decoupling as "internal workload" indicator
- Kolie implemented the W' accumulation metric in WKO5 immediately after publication

**van Erp et al. (September 2021)** -- First kJ/kg paper [R]
- Cross-sectional: pro-conti vs World Tour teams
- Analysis binned at 10 kJ/kg intervals
- 75% training files, 22% racing, 3% TTs
- Key finding: decline is lower for better-performing cyclists regardless of category
- Critical caveat: how data was generated matters enormously -- sprinter 20-min power after X kJ/kg is meaningless since sprinters never do max 20-min efforts in races

**Definitions paper** -- durability/fatigability/repeatability/resilience [R]
- Four overlapping terms proposed (see Section 1)
- Kolie's assessment: highly correlated, different sides of same coin, likely not separately trainable

### Related WKO5 Metrics

| Metric | Definition | Relationship to Durability |
|--------|-----------|---------------------------|
| **TTE (Time to Exhaustion)** | Maximum duration at mFTP | Indicates threshold stamina -- how long before the kink in the PD curve |
| **Stamina** | Resistance to fatigue during prolonged sub-threshold exercise | Sub-threshold endurance -- complementary to above-threshold durability |
| **FRC** | Total work above mFTP before exhaustion | Sets the "match" budget; depletes faster with poor durability |
| **mFTP** | Model-derived functional threshold power | The baseline against which degradation is measured |

TTE and durability are related but distinct. TTE measures how long you can sustain threshold power in a fresh state. Durability measures how much of your power you retain after accumulated work. An athlete with excellent TTE but poor durability would hold threshold for 55 minutes fresh but lose 30% of their 5-min power after 40 kJ/kg.

---

## 11. Nutrition and Durability

Fueling is the single largest confounding variable in field durability measurement and the single most actionable lever for improving it. [E] (WD-60, TMT-73)

### Key Principles

- **On-bike carbs: 60-90 g/hr standard, up to 120 g/hr for elite with trained guts** [R] (Persp-41, TMT-73)
- **On-bike fueling does NOT spare muscle glycogen, only liver glycogen** -- confirmed by Podlogar [R] (Persp-41)
- **Delayed post-exercise carbs impair next-day performance by ~30%** even when 24hr glycogen levels equalize (ES=2.03) [R] (WD-59)
- **TTE extension is tied to better fueling** -- cannot extend TTE without adequate carbs [E] (TMT-73)
- **"Feel the same as when you left"** = properly fueled ride [E] (TMT-73)
- **Glycogen stores last ~90 minutes of aerobic exercise** -- beyond this, exogenous carbs determine performance [R] (multiple sources)

### How Under-Fueling Mimics Poor Durability

An athlete who takes in 30 g/hr instead of 80 g/hr will show dramatic power fade after 2-3 hours that looks identical to poor physiological durability. The platform's fueling confound warning (triggered when kJ decay rate `b > 0.003`) helps flag this, but cannot definitively distinguish fitness from fueling.

> **Platform note (`durability.py`):** The `fueling_confound_warning` flag exists specifically because this confound is so pervasive. Always consider fueling history before concluding poor durability.

---

## 12. Mechanical Durability

A distinct concept from metabolic durability: the musculoskeletal system's ability to handle prolonged load without breakdown.

Andrew Yoder (coach of pro triathlete Matthew Marquardt) distinguishes metabolic efficiency from mechanical durability: an athlete can be "metabolically efficient, but mechanically fails at first." [E] (TrainingPeaks)

Training approaches for mechanical durability:
- Long loaded rides (gravel with tight power window)
- Low-cadence torque work (50 RPM at LT2 intensity)
- Inclined treadmill running for consistent mechanical load
- Progressive week-over-week adaptation

This is especially relevant for athletes who train primarily indoors on ERG mode and lack exposure to variable terrain and sustained mechanical loading.

---

## 13. Heart Rate Decoupling as a Fatigue Marker

Heart rate decoupling -- the progressive rise of HR at constant power over the course of a ride -- is a well-established indirect marker of fatigue and durability. [R]

### How It Works

- Early in a ride: HR and power are coupled (stable relationship)
- As fatigue accumulates: HR drifts upward at the same power output
- Decoupling > 5% over a ride suggests the effort was above sustainable intensity for that duration
- Decoupling > 10% at moderate intensity is a clinical amber flag for insufficient aerobic fitness or excessive fatigue

### Limitations

HR decoupling is confounded by:
- Cardiac drift from dehydration and thermoregulation
- Ambient temperature changes
- Caffeine and stimulant intake
- It is an "internal workload" indicator, not a direct measure of performance capacity

Maunder et al. (2021) included HR decoupling as a durability metric, but it is best used as a supplementary signal rather than a primary durability measure.

---

## 14. Platform Implementation Summary

### Module: `durability.py`

| Function | Purpose |
|----------|---------|
| `degradation_factor()` | Core model: dual exponential decay with kJ and time terms |
| `effective_capacity()` | Fatigued PD curve = fresh MMP x degradation factor |
| `compute_windowed_mmp()` | Rolling MMP at 4 durations in 2-hour non-overlapping windows; classifies pre-effort intensity |
| `fit_durability_model()` | Fits a/b/c params from historical long rides via curve_fit |
| `frc_budget_simulate()` | FRC depletion/recovery across sequential segments with degrading recovery ceiling |
| `repeatability_index()` | Ratio of 3rd-best to 1st-best effort at a duration |
| `check_fresh_baseline()` | Validates fresh baseline exists for key durations within recent rides |
| `durability_benchmark()` | Classifies drop percentage against EC podcast tiers |

### Module: `pacing.py`

| Function | Purpose |
|----------|---------|
| `solve_pacing()` | Brent's method solver: finds base power for target riding time accounting for degradation |
| `_segment_time()` | Per-segment time/power calculation with degradation, drafting, terrain |
| `_effective_cda()` | CdA adjustment for drafting on flat/rolling segments |

### Module: `gap_analysis.py`

| Function | Purpose |
|----------|---------|
| `_perturb_durability()` | Monte Carlo perturbation of durability params for feasibility simulation |
| Uses `degradation_factor()` | Projects fatigued capacity onto route demand segments |

---

## 15. Conflicts with Conventional Wisdom

| Conventional Claim | EC / Platform Position | Evidence Level |
|-------------------|----------------------|----------------|
| "Durability is the missing piece for performance" | Need sufficient absolute power first; durability is one factor among many | [E] WD-60 |
| "Low-carb training improves durability" | No evidence; explicitly dismissed by Kolie Moore | [E] WD-60 |
| "Strength training hurts durability" | No long-term negative impact; both can improve simultaneously | [E] WD-60 |
| "Aerobic and anaerobic are zero-sum" | False; sprinters can gain power while maintaining or improving FTP | [E] WD-60 |
| "You need special durability workouts" | Total ride time is the best predictor; specific protocols add marginal value | [E] WD-60 |
| "kJ is the right metric for durability" | Must use kJ/kg to normalize for body weight | [R] van Erp 2021 |
| "Durability testing is straightforward" | Fresh baseline, pre-effort intensity, nutrition, environment, and W' all confound results | [E] WD-60 |
| "Zone 2 specifically builds durability" | Total volume at any sub-threshold intensity matters more than zone specificity | [E] TMT-69 |
| "Heart rate decoupling proves poor durability" | HR decoupling is confounded by dehydration, heat, cardiac drift; supplementary signal only | [R] Maunder 2021 |

---

## 16. Practical Decision Framework

### For the Athlete

1. **Do you have enough power?** Check absolute FTP and PD curve against event demands before worrying about durability.
2. **Are you fueling properly?** 60-90 g/hr carbs on the bike. Fix nutrition before diagnosing durability problems.
3. **Do you have a fresh baseline?** If not, establish one with a max effort early in a ride (< 500 kJ cumulative).
4. **How much are you riding?** Total hours per week is the strongest durability predictor. One longer ride per month makes a noticeable difference.
5. **Where do you place your hard efforts?** Moving intervals to later in the ride builds fatigue resistance without requiring extra training time.

### For the Platform

1. Always show durability alongside absolute power -- never in isolation.
2. Flag stale/missing fresh baselines before computing durability metrics.
3. Track pre-effort intensity class for every window (endurance/tempo/race preload).
4. Raise fueling confound warning when kJ decay rate is steep.
5. Use kJ/kg bins of 10 as the standard analysis unit.
6. Model degradation with dual kJ + time exponential decay.
7. Integrate durability into pacing solver and gap analysis -- these are the primary consumers.

---

## Cross-References

- [Power-Duration Modeling](power-duration-modeling.md) — the fatigued PD curve (fresh MMP x degradation factor) is the core durability model; FRC budget uses mFTP as the threshold reference
- [FTP & Threshold Testing](ftp-threshold-testing.md) — FTP stagnation does not mean fitness stagnation; race results can improve through durability gains even with flat FTP
- [Endurance Base Training](endurance-base-training.md) — total time riding is the best predictor of durability; long Zone 2 rides build fatigue resistance through accumulated kJ
- [Pacing Strategy](pacing-strategy.md) — durability-aware pacing solver adjusts target power per segment based on accumulated kJ and elapsed time
- [Fueling Fundamentals](../nutrition/fueling-fundamentals.md) — nutrition is the single largest confounding variable in durability measurement; under-fueling mimics poor physiological durability
- [Ultra-Endurance](ultra-endurance.md) — time-based fatigue (central fatigue, thermoregulation) dominates in events beyond 4-6 hours; the dual-decay model captures both kJ and time components
- [Training Load & Recovery](training-load-recovery.md) — CTL rising while performance declines is a classic overreaching signal, not a durability problem to train through
- [Heat, Altitude & Environment](heat-altitude-environment.md) — heat, cold, and altitude confound field durability measurements; no standardization is possible in field data
- [Pro Race Analyses](../entities/pro-race-analyses.md) — van Erp World Tour data (kJ/kg bins) and Amber Neben case study establish professional durability benchmarks
- [Race-Day Nutrition](../nutrition/race-day-nutrition.md) — 60-90 g/hr carbs on bike; TTE extension is tied to adequate fueling, not just fitness

---

## Sources

### Empirical Cycling Podcast
- **WD-60:** Durability's Limitations (primary source for this page)
- **WD-55:** VO2max Training / 30-15s reanalysis (W' confound)
- **WD-59:** Glycogen Paradox (post-exercise carb timing)
- **TMT-60:** FTP Decision Tree (durability as opportunity cost consideration)
- **TMT-69:** Riding Easier (endurance intensity, zone specificity)
- **TMT-70:** Fitness Beyond FTP (durability in race context)
- **TMT-73:** Things We Wish We Knew (fueling and TTE)
- **Persp-41:** Macros and Timing (carb absorption, liver glycogen)

### Academic Literature
- Maunder et al. (August 2021) -- First formal "durability" definition
- van Erp et al. (September 2021) -- First kJ/kg durability measurement, World Tour data
- Definitions paper -- durability/fatigability/repeatability/resilience taxonomy

### TrainingPeaks Articles
- Tim Cusick: "The Role of Fatigue Resistance at the Tour de France" -- WKO4 fatigue resistance visualization, Amber Neben case study
- Jakub Novak: "Race Stronger, Longer: How to Build Fatigue Resistance" -- Practical testing protocol, WKO5 visualization, training methods
- Tim Cusick: "Time to Exhaustion in WKO5" -- TTE metric definition, relationship to FTP and durability
- Tim Cusick: "WKO for Mountain Bikers: A Case Study" -- Fatigue resistance limiter diagnosis, SST prescription
- Zack Allison: "The Art and Science Behind Time Trial Pacing" -- Pacing principles, wind resistance, lactate buffering
- Pau Salva Martinez: "3 Workouts to Raise Your FTP" -- Threshold durability training, fatigue resistance intervals
- Landry Bobo: "Low-Cadence Intervals in Cycling Training" -- Muscle fiber recruitment, fatigue resistance via cadence
- Matthew Marquardt / Andrew Yoder: "Training for Ironman Worlds" -- Mechanical durability, torque work, VI for pacing
- Maria Simone: "How to Pace a Long Course Triathlon" -- Even pacing principles, fatigue management
- Mike Schultz: "Follow Your Heart: Using HR to Gauge Fatigue" -- HR decoupling as fatigue detection

### Platform Source Code
- `wko5/durability.py` -- Degradation model, windowed MMP, FRC budget, repeatability index
- `wko5/pacing.py` -- Durability-aware pacing solver with CdA and drafting support
- `wko5/gap_analysis.py` -- Monte Carlo demand simulation with durability perturbation
