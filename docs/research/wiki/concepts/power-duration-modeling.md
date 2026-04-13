# Power-Duration Modeling and Phenotyping

Synthesized from: Empirical Cycling Master Reference (53 episodes), TrainingPeaks/WKO literature (Coggan, Cusick, Allen), and platform codebase.

Evidence levels: **[R]** = Research-backed, **[E]** = Experience-based, **[O]** = Opinion.

---

## 1. The Power-Duration Relationship

### Core Concept

The power-duration (PD) relationship describes the maximum power a cyclist can sustain as a function of time. It is the single most informative construct in cycling analytics: every performance metric (FTP, Pmax, FRC, TTE, Stamina, VO2max power) is a read-off or derivative of this curve [R].

The WKO4/5 PD model was developed by Dr. Andrew Coggan in 2012, based on first-principles reasoning about metabolic energy systems. It was validated against a dataset of ~200 season-athletes ranging from weekend warriors to World Champions and Grand Tour winners [R] (Coggan, "Scientific Basis of the New Power Duration Model in WKO4").

### Why Model at All?

The primary purpose of the PD model is **not** to predict performance at a given duration -- raw MMP data can do that. The two real purposes are [R]:

1. **Quantitative insight into physiological determinants.** The model decomposes performance into distinct metabolic components (neuromuscular, anaerobic, aerobic), enabling phenotyping and strengths/limiters analysis.
2. **Robust mathematical description of MMP data.** Raw MMP fluctuates with testing recency, effort distribution, and data gaps. The model smooths these, providing stable foundations for iLevels, adaptation scores, and tracking.

### The Three-Component Model

The platform implements a 3-component model:

```
P(t) = Pmax * e^(-t/tau) + FRC*1000 / (t + t0) + mFTP
```

| Component | Physiological Basis | Duration Dominance |
|-----------|--------------------|--------------------|
| Pmax * e^(-t/tau) | Neuromuscular power (phosphagen system, motor unit recruitment) | 1-15 seconds |
| FRC * 1000 / (t + t0) | Anaerobic work capacity (glycolytic + aerobic above FTP) | 30 seconds - 5 minutes |
| mFTP (constant) | Aerobic steady-state (oxidative metabolism at MLSS) | 10+ minutes |

This is conceptually aligned with the principal metabolic limiters of exercise performance across durations [R]:

| Duration Range | Primary Limiter | Secondary Factors |
|---------------|-----------------|-------------------|
| 0-5 seconds | Excitation/contraction coupling, phosphocreatine | Motor unit recruitment, muscle mass |
| 5-30 seconds | H2PO4- accumulation, glycolytic flux | Neural fatigue, buffering capacity |
| 30 seconds - 5 minutes | VO2max kinetics, anaerobic capacity | Lactate buffering, pain tolerance |
| 5-60 minutes | Metabolic steady state (MLSS/FTP) | Substrate availability, thermoregulation |
| 60+ minutes | Glycogen depletion, thermoregulation | Fueling, durability, TTE |

Source: Coggan, "Scientific Basis of the New PD Model in WKO4", Figure 2.

### Model Validation Statistics

| Metric | Value | Source |
|--------|-------|--------|
| Mean absolute error | 3.2 +/- 2.8% | Coggan WKO4 validation [R] |
| Residual distribution | Normal, centered on zero | Coggan WKO4 validation [R] |
| Domain of validity | 1 second to ~100,000 seconds (~28 hours) | Coggan WKO4 validation [R] |
| Parameter intercorrelation | Limited (model not overparameterized) | Coggan WKO4 validation [R] |
| FTP CV (precision) | Tightest of all parameters | Coggan WKO4 validation [R] |
| Pmax/FRC CV | Somewhat higher (fewer data points exert leverage) | Coggan WKO4 validation [R] |

Platform module: `wko5/pdcurve.py` -- `_pd_model()`, `fit_pd_model()`, `compute_mmp()`, `compute_envelope_mmp()`

---

## 2. Key Metrics Derived from the PD Curve

### 2.1 Pmax (Maximal Neuromuscular Power)

**Definition:** The maximal power that can be generated over at least a full pedal revolution of both legs [R].

**Physiological basis:** Reflects peak rate of ATP turnover from phosphocreatine hydrolysis, motor unit recruitment, muscle fiber type (Type II proportion), and neural drive [R].

**Typical values:**

| Category | Pmax (W) | Pmax/FTP Ratio |
|----------|----------|----------------|
| Sprinter (World Class) | 1800-2200+ | > 6.0 |
| Pursuiter | 1200-1800 | 4.5-6.0 |
| All-rounder | 900-1400 | 3.5-5.0 |
| TTer/Steady-stater | 700-1100 | < 4.5 |

**Key findings:**
- Pmax is the parameter most responsive to freshness/taper -- "it is performance at very short durations that is impacted the most by freshness" [R] (Coggan, Champion Cyclist case study)
- Sprint training has low opportunity cost -- short sprints year-round costs almost nothing in fatigue (TMT-45, 64) [E]
- Sprint PRs after time off are common -- do not chase more sprint training if sprint is down late-season (TMT-72) [E]

### 2.2 FRC (Functional Reserve Capacity)

**Definition:** The total amount of work that can be done during continuous exercise above FTP before fatigue occurs. Units are kilojoules (kJ) or kJ/kg [R].

**Physiological basis:** Conceptually similar to W' (W-prime) in the critical power model. Includes both anaerobic glycolytic capacity and the aerobic contribution above FTP. Unlike MAOD (maximal accumulated O2 deficit), FRC includes an aerobic component [R].

**Practical interpretation:** If FRC = 15 kJ, then theoretically 1000W for 15 seconds or 500W for 30 seconds above FTP can be sustained [E] (Cusick, iLevels article).

**Key findings:**
- FRC can change dramatically with training focus -- in the Coggan champion case study, FRC more than doubled in one season with pursuit-specific training [R]
- Ramp test improvements may reflect W'/FRC, not VO2max -- decompose PD curve changes into CP vs W' contributions (WD-55) [R]
- FRC match burn rate in road races: ~100 matches/hour is typical for mass-start events [E] (Rollinson, WKO4 training plans)

### 2.3 mFTP (Modeled Functional Threshold Power)

**Definition:** The model-derived highest power a rider can maintain in a quasi-steady-state without fatiguing. An estimate of power at MLSS (Maximal Lactate Steady State) [R].

**Critical clarifications:**
- FTP is sustainable for **30-70 minutes** depending on the athlete -- NOT specifically "1-hour power" [R] (Coggan, EC Master Reference)
- Rolling PD curves from training data are more reliable than isolated test days -- single tests have ~2% power meter error making 5W changes meaningless (WD-62) [R]
- The model-derived mFTP auto-updates with each new file upload, tracking micro-changes in fitness [E] (Cusick, TTE article)

**Precision thresholds:**

| Metric | Value | Source |
|--------|-------|--------|
| Power meter error | ~2% (300W = 294-306W) | WD-62 [R] |
| Meaningful FTP change | > 6W (> 2%) | WD-62 [R] |
| FTP test frequency | Every 3-4 months max | TMT-66 [E] |
| mFTP as tightest parameter | Lowest CV of all PD model params | Coggan validation [R] |

Platform module: `wko5/pdcurve.py` -- `fit_pd_model()["mFTP"]`, `rolling_ftp()`

### 2.4 TTE (Time to Exhaustion)

**Definition:** The maximum duration for which a power equal to mFTP can be maintained. Appears as a downward "kink" in the tail of the PD curve [R].

**Physiological basis:** Represents the point where the quasi-steady-state at FTP can no longer be sustained. Related to substrate depletion (glycogen), thermoregulation, and neural fatigue. Extension is tied to better fueling (TMT-73) [E].

**Typical values:**

| Population | TTE Range | Source |
|-----------|-----------|--------|
| Untrained | 30-35 minutes | Coggan/Cusick [R] |
| Trained cyclists | 40-55 minutes | WKO5 [R] |
| Well-trained | 50-65 minutes | TMT-60 [E] |
| Maximum useful | 60-75 minutes | TMT-60 [E] |
| Beyond which | Opportunity cost too high; shift to raising FTP itself | TMT-60 [E] |

**Training implications:**
- FTP training decomposes into two goals: (1) increase FTP wattage, (2) extend TTE at that wattage [E] (Cusick, TTE article)
- TTE stagnation at FTP signals need for VO2max work, not more threshold training (TMT-60) [E]
- TTE extension is tied to better fueling -- cannot extend TTE without adequate carbs (TMT-73) [E]

Platform module: `wko5/pdcurve.py` -- `fit_pd_model()["TTE"]`

### 2.5 Stamina

**Definition:** A measure of resistance to fatigue during prolonged-duration, moderate-intensity (sub-FTP) exercise. Scored as percent of maximum (0-100%), with most individuals falling 75-85% [R].

**Physiological basis:** On the PD curve, stamina governs the rate of decline in the "flat tail" beyond about one hour. Higher stamina = flatter tail = less power degradation over time. Related to mitochondrial density, fiber type distribution (Type I proportion), habitual training volume, and fuel availability [R] (Cusick, Stamina article).

**Key findings:**
- FTP and stamina are closely related -- FTP describes the level at which the PD curve plateaus; stamina describes the rate of decline past that point [R]
- Even with the same FTP, subtle differences in stamina exist based on fiber type, training specificity, and habitual diet [R]
- Building stamina: progress training duration (10% weekly), extend individual ride length, and include 3-5 threshold/sweet-spot sessions per macrocycle [E] (Cusick, Stamina article)

### 2.6 mVO2max (Modeled VO2max Power)

Power at approximately 5 minutes from the MMP curve serves as a proxy for VO2max power. The platform converts via gross efficiency (23% for trained cyclists, range 22-25%) using: VO2 (mL/min) = Power(W) * 60 * 1000 / (efficiency * 20900) [R].

**Caveats:**
- "VO2max power" is not a fixed number -- achievable at a range of powers [R] (WD-55)
- 5-minute power correlates well with VO2max but is not identical (athletes can sustain 105-110% of VO2max for 5 minutes) [R] (Coggan, Power Profiling)

---

## 3. Phenotyping: The Four Rider Types

### Concept

A phenotype is the composite of a rider's observable physiological characteristics and power individualities, expressed by grouping like individuals of similar traits [R] (Allen/Cusick, "4 Key Uses for the PD Model"). Auto-phenotyping in WKO4/5 objectively classifies riders based on the shape of their PD curve.

### The Four Phenotypes

#### 3.1 Sprinter

**Characteristics:**
- Large proportion of fast-twitch (Type II) muscle fibers [R]
- Excellent force production in very short periods (< 30 seconds)
- High Pmax, high Pmax/FTP ratio (> 6.0) [E]
- PD curve is steeply left-skewed: very high short-duration power that drops off rapidly

**Sub-types:**
- **Explosive sprinter:** Incredible peak wattage in first 5 seconds [E]
- **Diesel sprinter:** Ability to maintain very high wattage for 20-30 seconds; may not show as sprinter in 5-second column but dominates at 15-20 seconds [E] (Allen, Individualizing Your Training)

**Classic PD curve shape:** Distinctly down-sloping plot, especially between 1 minute and 5 minutes [R] (Coggan, Power Profiling)

**Training considerations:**
- Since aerobic ability is quite trainable, a sprinter may become more of an all-rounder with focused endurance work [E]
- If heavily trained for years, may always be better at anaerobic vs. aerobic efforts -- focus on events that favor sprint abilities (track, criteriums) [E]

#### 3.2 Pursuiter

**Characteristics:**
- Large natural VO2max power; can produce high watts from roughly 3-8 minutes [R]
- Typically 120+% of FTP for 5 minutes (above upper limit for classic Coggan Level 5) [E]
- Pmax/FTP ratio of 4.5-6.0, with elevated FRC/FTP ratio (> 0.06) [E]
- Sharply inverted-V PD profile: both high anaerobic capacity and high aerobic ability [R]

**Key distinction from sprinter:** Power is sustained longer -- the "shelf" or plateau extends to ~20 seconds, indicating large FRC rather than just peak Pmax [R] (Coggan, Champion Cyclist case study, Figure 4).

**Training considerations:**
- May also represent a potential all-rounder who hasn't focused on raising FTP to its highest level [R] (Coggan, Power Profiling)
- Can be developed from TTer phenotype through focused pursuit-specific training -- the Coggan champion case study showed a shift from "TTer" to "Pursuiter" in one season through deliberate FRC/Pmax work [R]

#### 3.3 All-Arounder

**Characteristics:**
- Fairly even blend of fast-twitch and slow-twitch fibers [E]
- Generally horizontal power profile: all four standard durations fall at about the same ranking relative to population [R]
- Good sprint, good time trial, competitive across broad range of events but not dominant in any single one [E]

**Key properties:**
- Can "change" phenotypes depending on training focus -- can spend a year working on pursuit and become a pursuiter, then switch to climbing and become a TTer [E] (Allen, 4 Key Uses)
- This plasticity is the defining feature of the all-arounder phenotype [E]
- Very few non-elite athletes will show a truly horizontal profile AND fall at the upper end of each range -- only specialists excel at extreme durations [R] (Coggan, Power Profiling)

**Developmental note:** New cyclists almost always present as all-arounders because phenotypic differentiation takes years of training to emerge [E] (Allen, "From Beginning Junior to Category 1 Racer"). The junior case study showed the rider cycling between all-arounder and TTer phenotypes over a 7-year career.

#### 3.4 TTer / Steady-Stater

**Characteristics:**
- Large percentage of slow-twitch (Type I) fibers [R]
- High FTP relative to body mass, poor neuromuscular power
- Can sustain power output for extended durations (30+ minutes), excellent endurance for many hours [E]
- Pmax/FTP ratio < 4.5, TTE > 50 minutes [E]

**Classic PD curve shape:** Distinctly up-sloping profile when plotted as relative ranking (weak at short durations, strong at long durations) [R] (Coggan, Power Profiling). The PD curve has a slow, gradual progression through training levels, showing the ability to extend "time in zone" with little power degradation [E] (Cusick, iLevels article).

**Training considerations:**
- May improve performance by working on weaknesses, but this may not necessarily be true if it results in a decline in their strength (sustainable power) [R] (Coggan, Power Profiling)
- Excellent in stage races, long rides, time trialing, climbing, and any event requiring sustained effort [E]

### Phenotyping Summary Table

| Phenotype | Pmax/FTP | FRC/FTP | TTE | PD Curve Shape | Best Events |
|-----------|----------|---------|-----|----------------|-------------|
| Sprinter | > 6.0 | > 0.08 | Variable | Steep left descent | Track, criterium, field sprints |
| Pursuiter | 4.5-6.0 | > 0.06 | Variable | Inverted-V peak at 1-5 min | Pursuit, cyclocross, hilly road |
| All-arounder | 3.5-5.0 | Variable | Variable | Flat/horizontal profile | Versatile -- all events |
| TTer | < 4.5 | Variable | > 50 min | Rising right, flat tail | TT, climbing, stage races, ultra |

**Platform module:** `wko5/profile.py` -- `phenotype()`, `coggan_ranking()`, `strengths_limiters()`

### Phenotype != Performance (Critical Caveat)

The EC podcast explicitly warns against over-interpreting phenotype (WD-51) [R]:
- HIF knockout mice had a "trained" phenotype but untrained performance [R]
- The PD curve is an integrated output -- avoid over-decomposing into single mechanisms [R]
- Phenotype describes the shape of the curve, not the height -- a Cat 4 all-arounder and a World Tour all-arounder have the same phenotype but vastly different power [E]

---

## 4. Strengths and Limiters Analysis

### The Power Profile Approach (Original Coggan Method)

Compare power at four index durations against population standards [R]:

| Duration | Reflects | Physiological System |
|----------|----------|---------------------|
| 5 seconds | Neuromuscular power | Phosphagen system, motor unit recruitment |
| 1 minute | Anaerobic capacity | Glycolytic energy system |
| 5 minutes | VO2max | Maximal aerobic power |
| FTP (~60 min) | Lactate threshold | Metabolic steady state (MLSS) |

The rider's profile is constructed by ranking each duration against the Coggan table (Untrained through World Class). The pattern of rankings reveals strengths and limiters [R] (Coggan, "Creating Your Power Profile").

**Platform implementation:** The Coggan W/kg table is implemented in `wko5/profile.py` with seven categories (Untrained, Fair, Moderate, Good, Very Good, Exceptional, World Class) at five durations (5s, 60s, 300s, 1200s, 3600s).

### Evolution: From Profile to Full PD Curve

The original 4-point power profile was superseded by the full PD curve analysis in WKO4 [R]:
1. **Power Profile (4 points):** 5s, 1min, 5min, FTP
2. **Fatigue Profile (12 points):** Expanded to 12 durations to capture fatigue resistance patterns [E] (Allen, Individualizing)
3. **Full PD Model (continuous):** Compares power across ALL time periods, enabling highly specific identification of strengths and limiters [R]

### Practical Strengths/Limiters Guidelines

From the consolidated EC and TrainingPeaks sources:

**"Train your weakness, race your strengths"** with important caveats [E]:

1. **Focus weakness work early in the season** -- shift to strength maintenance as racing approaches [E] (Allen, 4 Key Uses)
2. **Limit weakness work volume** -- weaknesses are more fatiguing to train because they are inherently harder for the athlete [E]
3. **Monitor adaptation to weakness training** -- some athletes are non-adaptors at specific durations. If the PD curve does not respond after focused training, redirect that time elsewhere [E] (Allen, 4 Key Uses)
4. **Must consider trainability and opportunity cost** -- a sprinter who has trained for years may never develop strong aerobic fitness; accept and optimize around it (TMT-64) [E]

### The "Non-Adaptor" Insight

One of the most valuable applications of PD curve tracking over time is identifying areas where the curve simply does not move despite focused training [E]. The Allen case study showed an athlete whose PD curves all crossed at ~1:40 -- no amount of short-duration training moved his curve below that point, but focusing on longer durations yielded 80W improvement at 14 minutes in 6 months [E] (Allen, 4 Key Uses).

Platform module: `wko5/profile.py` -- `strengths_limiters()`, `profile_trend()`; `wko5/pdcurve.py` -- `decompose_pd_change()`

---

## 5. How PD Curves Change with Training

### Within-Season Changes

The Coggan champion case study (Angie Coggan, national pursuit champion) provides the most detailed documented example of within-season PD evolution [R]:

| Phase | Duration | Emphasis | Pmax | FRC | mFTP |
|-------|----------|----------|------|-----|------|
| 1. Build | ~6 months | mFTP development | Constant | Constant | 225 -> 260W |
| 2. Road racing | ~2 months | Race + L5 intervals | No change | No change | 260 -> 277W (peak) |
| 3. Pursuit-specific | 6 weeks | Track L4-L7 daily | Rising | Immediate increase | Drifting down |
| 4. Taper | 2 weeks | Reduced frequency | Significant increase | Continued rise | Continued decline |
| 5. Post-competition | 4 weeks | Reduced training | Sustained/amplified | Sustained/amplified | Lowest all season |

**Key takeaways:**
- mFTP and FRC often move in opposite directions when training emphasis shifts [R]
- Pmax is most responsive to taper/freshness [R]
- Despite declining mFTP during pursuit-specific training, pursuit-duration power (3:50) rose steadily all season because FRC and Pmax gains outpaced mFTP losses [R]
- Athletes may need to taper longer than they normally do to maximize very-high-intensity performance. They are frequently unwilling because they sense their "base" (mFTP) dissipating [R]
- The net phenotype shifted from "TTer" to "Pursuiter" in one season [R]

### Across-Season Development

From the DuCournau junior development case study (7 years of data, FTP from 2.8 to 5.6 W/kg) [E]:

| Year | Phenotype | Key Changes |
|------|-----------|-------------|
| Year 1 | All-arounder (low level) | Everything is a weakness; no differentiation |
| Year 2 | All-arounder (improving) | 1-min catch-up; still undifferentiated |
| Year 3 | Maintenance year | College time management |
| Year 4 | TTer emerging | 5-min and FTP columns rise above 1-min and 5-sec |
| Year 5 | Interrupted (injury) | Broken bone, surgeries |
| Year 6 | TTer confirmed | FTP improvement lifts everything -- "when FTP rises, even sprint rises with it" |
| Year 7 | TTer (peaked) | TSS 37,000+ mid-August |

**Key takeaways:**
- True phenotype takes years to emerge [E]
- Phenotype can oscillate between all-arounder and TTer depending on training focus [E]
- FTP improvements often lift the entire curve including sprint [E]

### Expected Improvement Rates (Diminishing Returns)

| Training Year | Expected FTP Gain | Source |
|--------------|-------------------|--------|
| Year 1 | 30-50W | WD-61, TMT-52 [E] |
| Year 2-3 | 10-30W | TMT-52 [E] |
| Year 4+ | 5-10W | WD-61 [E] |
| Well-trained plateau | 0-5W (mostly TTE extension) | WD-61 [E] |
| Post-layoff return | 2-4 weeks to recent levels | WD-61 [E+R] |
| 3-month return from couch | Previous year's best FTP | WD-61 [E] |

Long-term FTP improvement follows a **logarithmic growth curve** -- log-transformed time yields a linear fit. Approximately 25% improvement over untrained baseline is a common long-term ceiling (WD-61) [R].

Platform module: `wko5/training_load.py` -- FTP growth curve modeling with log-transform

---

## 6. Rolling PD vs. Test-Day PD

### The Case for Rolling PD Curves

**EC position (strong):** Rolling PD curves from training data are more reliable than isolated test days [R] (WD-62, TMT-66):

1. **Power meter error (~2%) makes single tests unreliable for detecting small changes.** At 300W, the error band is 294-306W. A "5W gain" is within noise [R].
2. **Testing introduces anxiety and protocol variability.** Some athletes do not test well [E].
3. **Rolling curves incorporate ALL maximal efforts.** A hard group ride, a race, a hill repeat session -- all contribute to the envelope MMP, providing a richer dataset than any single test [R].
4. **Eliminates testing burden.** Formal testing of all physiological zones is time-consuming and schedule-disruptive [E].

### How Rolling PD Works

The platform computes envelope MMP: for each duration, the maximum average power achieved across all rides in a rolling window (typically 90 days). The PD model is then fit to this envelope [R].

```
For each duration d from 1 second to max:
    envelope_MMP[d] = max across all activities of (best average power for d seconds)
```

The model auto-updates with each new file uploaded. If an athlete achieves a new personal best at any duration, it immediately propagates through the model, updating mFTP, Pmax, FRC, TTE, and iLevels [E] (Cusick, iLevels article).

### When Test-Day PD Is Still Appropriate

Despite the superiority of rolling curves, formal testing still has a role [E]:

- **Hour record attempts or specific race predictions** -- "the best predictor of performance is performance itself" (Coggan) [R]
- **Validating rolling PD model** -- when PDM vs. actual MMP shows gaps, targeted tests can fill them [E] (Griffin, "Using WKO4 for Faster Insights")
- **New athlete onboarding** -- insufficient ride history for a valid rolling curve [E]
- **After long breaks** -- stale data in the rolling window [E]

### Rolling PD Implementation Details

| Parameter | Default | Notes |
|-----------|---------|-------|
| Window size | 90 days | Standard in WKO5; shorter windows are noisier, longer may lag fitness changes |
| Step size | 7 days (rolling_ftp) or 14 days (rolling_pd_profile) | Trade-off between resolution and compute |
| Minimum data | 60 seconds of MMP data | Below this, model fitting is unreliable |
| Sub-sport filtering | Optional | Can compute separate PD curves for road, MTB, indoor, etc. |

Platform module: `wko5/pdcurve.py` -- `compute_envelope_mmp()`, `rolling_ftp()`, `rolling_pd_profile()`, `compare_periods()`

---

## 7. PD Curve at Grade

An advanced application: separate PD curves for different gradient ranges (e.g., flat < 2%, grade 4-8%, grade 8%+). This reveals how climbing grade affects an individual's power output due to changes in kinetic energy, pedal force application, and motor unit recruitment patterns [E] (Cusick, "Individualized Analytics for Climbing").

**Key findings:**
- Some riders produce MORE power on steep grades; others produce LESS [E]
- Low kinetic energy of climbing requires application of force longer or with more maximal force per pedal stroke, changing contractile properties of leg muscles [R]
- mFTP can differ significantly by grade for the same rider [E]
- Grade-specific PD curves enable targeted pacing strategies for specific course profiles [E]

---

## 8. Individualized Training Levels (iLevels)

The PD model enables training zones that go beyond the classic Coggan 7-zone system [R]:

**Classic Coggan Levels (L1-L7):** Anchored to FTP as 100%. Works well for predominantly aerobic intensities (L1-L5), but L6 (anaerobic capacity) and L7 (neuromuscular power) are not meaningfully defined relative to FTP [R].

**The problem illustrated:** Consider a match sprinter (World Champion) vs. a time trialist (World Champion) with similar FTP. The sprinter can maintain 150% FTP for ~4 minutes; the time trialist for only ~1 minute. No single percentage-based system can accommodate this ~4x difference in supra-FTP capability [R] (Coggan, iLevels article).

**iLevels solution (9 zones):**
- L1-L4 remain anchored to FTP [R]
- L4a (Sweet Spot) added at 88-94% FTP [E]
- L5-L8 individualized based on PD curve shape, reflecting unique physiology [R]
- Each iLevel includes both power AND duration targets [R]
- iLevels auto-update with each uploaded file as fitness changes [E]

---

## 9. Fatigue Resistance and the PD Curve Under Load

### The Elite Differentiator

Fatigue resistance -- the ability to maintain PD curve power after accumulated work -- is the defining characteristic separating professionals from strong amateurs [E] (Cusick, "Fatigue Resistance at the Tour de France").

**Amber Neben (pro, 50 kg) vs. "Joe Rider" (Cat 3, 65 kg) after 2000 kJ:**

| Metric | Neben (Pro) | Joe Rider (Cat 3) |
|--------|------------|-------------------|
| 5-min power loss | -22W | -21W |
| 20-min power loss | -4W | -32W |
| Relative 20-min degradation | ~1.5% | ~12% |

Source: Cusick, "Fatigue Resistance at the Tour de France" [E]

### Durability Benchmarks (van Erp World Tour Data)

| Category | Start Power | Drop at 50 kJ/kg |
|----------|------------|------------------|
| Successful sprinters | 18.25 W/kg (10s) | ~8% |
| Less successful sprinters | 17.7 W/kg (10s) | ~18% |
| Successful climbers | 6.28 W/kg (20min) | ~4% |
| Less successful climbers | 5.99 W/kg (20min) | ~9% |

Source: EC Master Reference, WD-60 [R]

**Key finding:** "Better cyclists start with more power AND lose less" (WD-60) [R]. Need sufficient absolute power first before durability becomes the decisive factor [E].

Platform module: `wko5/durability.py` -- degradation factor modeling; `wko5/gap_analysis.py` -- Monte Carlo demand simulation with PD + durability parameters

---

## 10. Conflicts, Caveats, and Common Mistakes

### Model Limitations

| Issue | Detail | Severity |
|-------|--------|----------|
| Short-duration data quality | Many power meters are inaccurate at < 5 seconds; Pmax may be an artifact | Moderate [R] |
| CP model overestimation | Critical power models can overestimate sustainable power beyond TTE | High [R] |
| Data completeness | Rolling PD requires varied efforts across durations; monotone training creates gaps | Moderate [E] |
| Stale data | Data older than 90 days may not reflect current fitness | Moderate [E] |
| Indoor/outdoor discrepancy | Indoor power often reads differently; separate sub-sport PD curves recommended | Low-Moderate [E] |

### Common Analytical Mistakes

1. **Mono-metrically focusing on FTP** -- race results, not FTP, are the ultimate metric (TMT-70) [E]
2. **FTP stagnation does NOT mean fitness stagnation** -- race results can improve through durability, repeatability, race craft, and specificity improvements, even with flat/declining FTP (TMT-70) [E]
3. **Over-testing** -- using formal tests instead of progressive workout performance as fitness indicator (TMT-66) [E]
4. **Stacking gains from multiple studies** -- the arrow-gains fallacy. A 10% gain from study A + 8% from study B does not equal 18% (WD-61, TMT-68) [E]
5. **Treating phenotype as prescriptive rather than descriptive** -- phenotype describes what you are, not what you should be. A sprinter does not need to "fix" their sprinting (WD-51) [R]
6. **"Train your weaknesses" without considering trainability** -- some weaknesses cannot be trained away; opportunity cost matters (TMT-64) [E]
7. **Switching power meters and expecting continuity** -- single-to-dual-sided can show zero FTP gain even with massive actual improvement (TMT-70) [E]

### Conflicts with Conventional Wisdom

| Claim | PD Model / EC Position | Evidence |
|-------|----------------------|----------|
| "FTP is your 1-hour power" | FTP = MLSS, sustainable 30-70 min; not specifically 1 hour | [R] |
| "20-min test * 0.95 = FTP" | Rough estimate only; model-derived mFTP is more robust | [R] |
| "Higher phenotype = better athlete" | Phenotype describes shape, not height; a Cat 5 sprinter is not better than a Cat 1 TTer | [E] |
| "Train low (glycogen) for durability" | Explicitly dismissed; no performance evidence | WD-60 [E] |
| "30/15 intervals are the best VO2max training" | No VO2max superiority; gains likely reflect W'/FRC | WD-55 [R] |
| "Aerobic and anaerobic are zero-sum" | Both can improve simultaneously | WD-60 [E] |
| "More mitochondria = better performance" | 40% mitochondrial increase did NOT correlate with VO2peak | WD-53 [R] |

---

## 11. Platform Implementation Summary

| Module | Function | Role |
|--------|----------|------|
| `wko5/pdcurve.py` | `compute_mmp()` | Cumulative-sum MMP computation from power series |
| `wko5/pdcurve.py` | `compute_envelope_mmp()` | Envelope MMP across rides in date range |
| `wko5/pdcurve.py` | `_pd_model()` | 3-component PD model: Pmax*e^(-t/tau) + FRC*1000/(t+t0) + mFTP |
| `wko5/pdcurve.py` | `fit_pd_model()` | Scipy curve_fit with configurable bounds; returns Pmax, FRC, mFTP, TTE, mVO2max |
| `wko5/pdcurve.py` | `rolling_ftp()` | 90-day window, 7-day step rolling mFTP + Pmax + FRC + TTE |
| `wko5/pdcurve.py` | `rolling_pd_profile()` | Full PD profile at 14-day intervals |
| `wko5/pdcurve.py` | `decompose_pd_change()` | Attributes power changes to CP vs W' vs Pmax (per WD-55) |
| `wko5/pdcurve.py` | `compare_periods()` | Compare PD curves between arbitrary date ranges |
| `wko5/profile.py` | `phenotype()` | Auto-phenotype from Pmax/FTP, FRC/FTP, TTE ratios |
| `wko5/profile.py` | `coggan_ranking()` | W/kg ranking at 5 durations against Coggan table |
| `wko5/profile.py` | `strengths_limiters()` | Best/worst duration ranking identification |
| `wko5/profile.py` | `power_profile()` | Power at key durations from envelope MMP |
| `wko5/profile.py` | `profile_trend()` | Track power at a specific duration over time |
| `wko5/physics.py` | `power_required()` | P = P_aero + P_rolling + P_gravity + P_drivetrain; used for route demands |
| `wko5/physics.py` | `speed_from_power()` | Inverse of power_required via Brent's method |
| `wko5/durability.py` | Degradation modeling | Power loss as function of accumulated kJ/kg |
| `wko5/gap_analysis.py` | Monte Carlo simulation | PD model + durability params for route feasibility |
| `wko5/bayesian.py` | Posterior sampling | Bayesian uncertainty in PD parameters |
| `wko5/stan/pd_model.stan` | Stan model | Bayesian PD model fitting |

---

## 12. Cross-References

### Related Wiki Pages
- [FTP & Threshold Testing](ftp-threshold-testing.md) — mFTP is the aerobic steady-state component of the PD model; testing protocols and the 0.95 correction factor derive from PD curve analysis
- [VO2max Training](vo2max-training.md) — VO2max power (~5-min peak) is derived from the PD curve; decomposing PD changes reveals whether gains are aerobic (VO2max) or anaerobic (W'/FRC)
- [Durability & Fatigue](durability-fatigue.md) — the fatigued PD curve (fresh MMP x degradation factor) is the operational model for race-day power projection
- [Interval Design](interval-design.md) — iLevels from the PD model individualize interval intensity and duration targeting; FTP decision tree drives interval prescription
- [Endurance Base Training](endurance-base-training.md) — Stamina (sub-FTP tail of the PD curve) improves through accumulated endurance volume; TTE extension requires adequate fueling
- [Training Periodization](training-periodization.md) — PD curve changes track within-season phenotype shifts as training emphasis moves between base, build, and peak phases
- [Pacing Strategy](pacing-strategy.md) — PD model parameters feed directly into the pacing solver; grade-specific PD curves enable terrain-based power targets
- [Training Load & Recovery](training-load-recovery.md) — FTP from the PD model anchors all zone-derived metrics (TSS, IF, CTL); rolling PD detects fitness changes without formal testing
- [Pro Race Analyses](../entities/pro-race-analyses.md) — van Erp World Tour data validates the durability dimension of PD curves; Neben vs Cat 3 case study demonstrates fatigue resistance
- [Tools & Platforms](../entities/tools-platforms.md) — WKO5 implements the Coggan PD model, iLevels, and auto-phenotyping from the PD curve

### Source Documents
- EC Master Reference: `/docs/research/empirical-cycling/ec-master-reference.md`
- Coggan, "Scientific Basis of the New PD Model in WKO4": `/docs/research/trainingpeaks/scientific-basis-of-the-new-power-duration-model-in-wko4.md`
- Coggan, "All About WKO4 iLevels": `/docs/research/trainingpeaks/individualized-training-the-what-why-and-how-of-the-new-wko4.md`
- Coggan, "Creating Your Power Profile": `/docs/research/trainingpeaks/power-profiling.md`
- Cusick, "Time to Exhaustion in WKO5": `/docs/research/trainingpeaks/introduction-of-the-new-time-to-exhaustion-metric-in-wko4.md`
- Cusick, "WKO4 Training Metrics: Introducing Stamina": `/docs/research/trainingpeaks/wko4-training-metrics-introducing-stamina.md`
- Cusick, "An Introduction to the New iLevels in WKO4": `/docs/research/trainingpeaks/an-introduction-to-the-new-ilevels-in-wko4.md`
- Cusick, "How to Use Individualized Analytics for Climbing": `/docs/research/trainingpeaks/how-to-use-individualized-analytics-to-become-a-better-climb.md`
- Cusick, "Fatigue Resistance at the Tour de France": `/docs/research/trainingpeaks/the-role-of-fatigue-resistance-at-the-tour-de-france.md`
- Allen/Cusick, "4 Key Uses for the PD Model": `/docs/research/trainingpeaks/4-key-uses-for-the-power-duration-model.md`
- Allen, "Individualizing Your Training with WKO4": `/docs/research/trainingpeaks/individualizing-your-training-with-wko4.md`
- Coggan, "Making of a Champion Cyclist (Case Study)": `/docs/research/trainingpeaks/wko4-case-study-the-making-of-a-champion-cyclist-as-viewed-t.md`
- Allen, "From Beginning Junior to Category 1 Racer (Case Study)": `/docs/research/trainingpeaks/wko4-case-study-from-beginning-junior-to-category-1-racer.md`
- Rollinson, "How to Use WKO4 to Construct Training Plans": `/docs/research/trainingpeaks/how-to-use-wko4-to-construct-training-plans.md`

### EC Episode References
- TMT-45, 60: FTP decision tree, threshold progression
- TMT-64, 70: Off-season weaknesses, fitness beyond FTP
- TMT-66: Testing frequency, rolling PD superiority
- TMT-72: Sprint PRs after rest, stimulus vs recovery
- TMT-73: TTE and fueling link
- WD-51: Phenotype != performance
- WD-53: Newbie gains, mitochondria limitation
- WD-55: VO2max training, ramp test decomposition (CP vs W')
- WD-60: Durability limitations
- WD-61: Diminishing returns, logarithmic growth curves
- WD-62: n=1 experiments, power meter error
