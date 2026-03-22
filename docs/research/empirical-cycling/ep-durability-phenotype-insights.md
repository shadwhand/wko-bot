# Empirical Cycling Podcast Insights: WD #51-60

Extracted from transcripts and community notes. Focus: actionable training science for cycling power analysis platform.

---

## WD #60: Durability's Limitations (CRITICAL for our platform)

**Host:** Kolie Moore, **Co-host:** Kyle Helsen | Late December 2025

### Definition and Conceptual Framework

**Claim: Durability is not a new concept, just newly formalized** (experience-based)
- Coaches have been looking at power output post-kJ expenditure since power meters existed (~late 1990s)
- WKO4/5 users were measuring mean-max power after X kilojoules long before academic literature caught up
- The concept is essentially what coaches always called "endurance" or "fatigue resistance"

**Claim: The durability literature is weaker than media interpretations suggest** (research-backed)
- Kolie read every published paper on durability -- evidence base is surprisingly thin
- Media interpretations are "much more strongly advised than the evidence would suggest"
- Still in definitional squabbling phase

### Key Papers Reviewed

**Paper 1: Maunder et al. (August 2021) -- First "durability" paper**
- Defines durability as: "the time of onset and magnitude of deterioration in physiological characteristics over time during prolonged exercise"
- **Kolie's critique**: It is deterioration of *performance* that shows deterioration of measurements, not physiology deteriorating. Your heart's capacity to pump blood is not impaired because your legs fatigue. What is lost is *ability to express performance*.
- Introduces W' accumulation as a durability metric (multiples of W' done over time) -- **Kolie implemented this in WKO5 immediately**
- Discusses heart rate decoupling as "internal workload" indicator

**Paper 2: van Erp et al. (September 2021) -- First kJ/kg paper**
- **First paper to use kilojoules per kilogram** (not raw kJ) for durability measurement
- Cross-sectional study: pro-conti vs World Tour teams
- Analysis binned at 10 kJ/kg intervals (10, 20, 30, 40, 50)
- 75% training files, 22% racing, 3% TTs
- Climbers classified as >5.8 W/kg for 20 min; sprinters by team role assignment
- Success threshold: >400 ProCyclingStats points
- **Key finding**: decline is lower for better-performing cyclists regardless of category
- **Critical caveat**: how data is generated matters enormously -- sprinter 20-min power after X kJ/kg is meaningless since sprinters never do max 20-min efforts in races

**Paper 3: Definitions paper -- durability/fatigability/repeatability/resilience**

Four overlapping terms proposed:
1. **Durability**: decline of CP, VO2max, etc. during *steady* power output
2. **Fatigability**: acute impairment of max power output post-kJ/kg (Enoka's definition)
3. **Repeatability**: capacity to recover and reproduce high-intensity across bouts/stages/heats
4. **Resilience**: ability to resist fatigue and maintain performance; includes mental aspects

**Kolie's assessment**: Highly correlated, different sides of same coin. Likely not separately trainable. Coaches settled on kJ/kg as catch-all.

**Relevance to platform: `durability` module**
- Our model should NOT decompose these four sub-types -- practically inseparable
- kJ/kg is the standard metric; use bins of 10 kJ/kg

### Measurement Criticisms (CRITICAL for implementation)

**Claim: Testing durability is harder than people think** (experience-based, strong)

1. **Missing fresh baseline**: If your only 1-min max effort happened after 20 kJ/kg, that becomes your "0% loss" baseline -- completely misleading
2. **Intensity before test matters enormously**: 2000 kJ at endurance pace then testing is VERY different from racing 2000 kJ then testing
3. **Body weight scaling**: 2000 kJ is huge for a 55 kg woman, "just getting warmed up" for a 75 kg pro male
4. **Anaerobic capacity confound**: Lab protocols at 105-108% threshold mean large W' athletes coast while small W' athletes are near max. Track sprinters (largest W') have WORST real-world durability
5. **Nutrition as dangling confounder**: Cannot control in field data, massive effect
6. **Environment**: Heat, cold, altitude, wind all affect measurements

**Relevance to platform: `durability` module**
- Flag when fresh baseline is missing or stale
- Separate by intensity context (endurance vs race pre-load)
- Track pre-effort intensity distribution, not just total kJ/kg

### What Literature Shows About Training Durability

**Claim: Training evidence is underwhelming** (research-backed, weak)
- Cross-sectional study (Pro U23): correlation between low-intensity riding (under VT1) and fatigue resistance. **R = 0.4, R-squared ~ 0.2** -- only 20% of variability explained
- One PhD thesis with volume confound, 6W vs 12W improvement, tiny sample
- Maintaining fatigue resistance later in season correlated with higher training load at lower intensities (weak R values)

### The Core Argument: Why Durability Will Not Save You

**Claim: You need sufficient power to begin with** (research-backed + experience-based, strong)

From van Erp data:
- Successful sprinters: start at 18.25 W/kg 10s, lose ~8% over 50 kJ/kg
- Less successful: start at 17.7 W/kg 10s, lose ~18%
- Successful climbers: start at 6.28 W/kg 20min, lose ~4%
- Less successful: start at 5.99 W/kg 20min, lose ~9%
- **Better group starts with more power AND loses less.** Correlation only, no causality.

**Claim: Aerobic and anaerobic are NOT zero-sum** (experience-based, strong)
- Kolie trains sprinters from 1500W/400W FTP to 1900W/430W FTP -- both improve
- Heavy lifting does NOT hurt durability long-term

**Coaching durability numbers** (experience-based):
- Top pros: <2% power drop from fresh to 50-60 kJ/kg
- Good amateurs: 10-20% drop
- Average amateurs: 20-40% drop

**Claim: Total time riding is the best predictor of durability** (experience-based, strong)
- 4x15min FTP efforts spread across 4-hour ride = excellent durability training
- Efforts throughout > efforts clustered at end (compliance issue)
- One longer ride once a month makes noticeable difference

**Goodhart's Law Warning**: Over-indexing on kJ/kg could lead to spending less energy in races (bad strategy), only doing long easy rides (missing power development), weight manipulation. Low-carb training for durability: "I checked my list... there is nothing here."

---

## WD #55: The "Right" VO2max Training, and 30/15s Epilogue

**Host:** Kolie Moore, **Co-host:** Rory Porteus

### Key Claims

**Claim: No single "right" VO2max training method** (research-backed + experience-based)
- Episode is explicitly corrective to Kolie's earlier WD #23-24 recommendations
- Different methods are tools in a toolbox

**Claim: "VO2max power" is not a fixed number** (research-backed)
- VO2max achievable at a range of powers depending on duration, fatigue state, training status

**Claim: "Start hard" was misinterpreted** (experience-based, correction)
- Original intent: start 10-20% above sustainable pace, then hang on -- NOT an all-out sprint
- **Evenly paced efforts are totally fine, possibly preferable**

**Claim: High-cadence (100-120 RPM) intervals cause less muscular fatigue** (research-backed + experience-based)
- Origin: pursuit cyclists in 1990s (Dean Golich, David Martin)
- Preload theory: enhanced venous return -> greater stroke volume
- Power 20-30W lower at high cadence -- expected and fine
- O2 saturation does NOT change with cadence, only intensity

**Claim: Hickson protocol = largest published VO2max improvement (25%)** (research-backed)
- 6x5min with 2-min rests alternating with 30-40min TTs, 1 rest day/week, 10 weeks, untrained
- Brutal -- documented immune suppression, iron depletion

### 30/15s Epilogue (CRITICAL)

**Claim: 30/15 study does NOT show superior VO2max improvements** (research-backed, reanalysis)
- Abstract states: "no group difference in change of VO2max"
- P = 0.49 for VO2max (L/min) between groups -- 50% chance due to chance
- Yet paper reported effect sizes despite non-significance
- What 30/15 group DID improve: ramp test power and 20-min power
- **Most parsimonious explanation: anaerobic capacity (W') improvement**, not VO2max
- Word "anaerobic" appears once in entire paper (in Tabata reference)
- CX racing (massive intermittent effort dose) never improves VO2max in trained athletes

**Actionable guidelines:**
- ~20 min interval time is typical; athletes naturally stop ~25 min
- Formats: 8x3, 5x5, 3x8 all viable
- Auto-regulation preferred over rigid prescriptions

**Relevance to platform: `pdcurve`, `gap_analysis`**
- Decompose PD curve changes into CP vs W' contributions
- Ramp test improvements may reflect W', not aerobic ceiling

---

## WD #53: The Origins of Newbie Gains

**Host:** Kolie Moore, **Co-host:** Kyle Helsen

### Key Claims

**Claim: Newbie gains driven by CENTRAL (blood volume) adaptations, not peripheral (muscle)** (research-backed, strong)

Key paper: Montero et al. 2015
- 16 untrained men, 6 weeks at ~65% VO2peak
- W_peak up ~16%, VO2peak up 9%, mitochondrial volume up 40%
- **Phlebotomy (removing gained blood volume) erased VO2peak improvements back to baseline**
- Mitochondrial gains did NOT correlate with VO2peak
- Strongest predictors: cardiac output, blood volume, plasma volume, hemoglobin (R ~0.8, p < 0.001)

**Mechanism: Frank-Starling Law**
- More blood volume -> more ventricular filling -> stronger contraction -> higher stroke volume -> higher cardiac output -> higher VO2max

**Claim: Sprint intervals produce same blood-volume-driven gains** (research-backed)
- 2023 paper: 3x30s sprints, 3x/week, 6 weeks -- similar results, more time-efficient

**Claim: Blood volume super-compensation does NOT work in trained athletes** (research-backed)
- Extra plasma infusion in trained athletes: no additional VO2max
- **Cardiac function is the limiter** in trained athletes, not blood volume

**Claim: Non-stoichiometric mitochondrial expansion** (research-backed)
- Volume up 40%, ETS protein density ratio down 20%
- Mitochondria expand first, then fill with functional proteins

**Relevance to platform: `training_load`, `pdcurve`**
- Flag new/returning athletes for different adaptation expectations
- Rapid FTP gains in newbies NOT indicative of long-term trajectory
- Model logarithmic improvement curve with diminishing returns

---

## WD #52: Hypoxia-Inducible Factor's Diminishing Returns

**Host:** Kolie Moore, **Co-host:** Kyle Helsen

### Key Claims

**Claim: In elite endurance athletes, HIF-1alpha is massively suppressed** (research-backed)
- PHD2: 2.6x higher in elite vs moderate; FIH: 3.5x higher; Sirtuin 6: 5x higher
- PDK1 mRNA (HIF target): 3-4x lower in elite
- 6-week training: PHD2 protein up 1.6x; mRNAs for regulators up ~2.4x

**Claim: Pasteur Effect has no practical negative impact in well-trained athletes** (research-backed + speculation)
- HIF's negative regulators so elevated in trained that Pasteur Effect may not occur
- No evidence of HIF impairing endurance adaptations in trained athletes

**Claim: Capillary density hits a ceiling in well-trained athletes** (research-backed)
- No improvement except with VO2max-type training; structural limit exists

**Claim: mRNA != protein != phenotype** (research-backed, methodological)
- 5% mRNA change may not matter; protein differences of 160-500% are the relevant scale

**Relevance to platform: `training_load`, `zones`**
- FTP work eventually stops raising VO2max -> model plateau detection
- Training maturity should inform expectations

---

## WD #51: Performance vs Phenotype

**Host:** Kolie Moore, **Co-host:** Kyle Helsen

### Key Claims

**Claim: Phenotype is NOT performance** (research-backed, strong)
- HIF knockout mice had "trained" muscle phenotype but untrained performance
- Still needed 6 weeks training to improve performance identically to wild-type mice
- AMPK constitutively active as compensation -- not superior fitness but underlying deficiency

**Claim: Hypoxic != Anaerobic** (research-backed)
- Hypoxia = low instantaneous O2; high consumption rate creates local hypoxia even with max delivery

**Relevance to platform: `pdcurve`, `gap_analysis`**
- PD curve is integrated output; avoid over-decomposing into single mechanisms
- Training process matters more than biomarker targets

---

## Cross-Cutting Platform Implementation Table

### For `durability.py` / Bayesian Model

| Insight | Action |
|---------|--------|
| kJ/kg bins of 10 is standard | Primary analysis unit |
| Fresh baseline often missing | Flag stale baselines with confidence reduction |
| Pre-effort intensity matters | Track intensity distribution before test efforts |
| Pro: <2% drop at 50 kJ/kg | Elite benchmark |
| Amateur: 10-40% drop | Normal range benchmarks |
| W' confounds lab protocols | Normalize for anaerobic capacity |
| Goodhart's Law | Always show alongside absolute power |

### For `pdcurve`

| Insight | Action |
|---------|--------|
| Ramp test gains can be W' not VO2max | Decompose into CP vs W' |
| VO2max at range of powers | No fixed "VO2max power" point |
| Phenotype != performance | Curve is integrated; avoid over-decomposition |

### For `training_load`

| Insight | Action |
|---------|--------|
| Newbie gains = blood volume | Flag new athletes, different expectations |
| Total ride time best durability predictor | Track cumulative hours |
| FTP work stops raising VO2max | Detect plateau, suggest intensity shift |
| R = 0.4 for training correlations | Label "suggestive" not "established" |

### For `gap_analysis`

| Insight | Action |
|---------|--------|
| Need sufficient power first | Check absolute thresholds before durability flags |
| Aerobic/anaerobic NOT zero-sum | No trade-off modeling |
| Sub-FTP endurance varies ~36% | Wide normal range for TTE metrics |

## Conflicts with Conventional Wisdom

1. **"30/15s are best VO2max training"** -- No. VO2max gains not significantly different; performance gains likely W'/anaerobic capacity.
2. **"Start VO2max intervals with hard sprint"** -- No. Evenly paced is fine, possibly preferable.
3. **"Durability is the missing piece"** -- Partially. Need sufficient absolute power first.
4. **"More mitochondria = better performance"** -- Not directly. 40% mitochondrial increase did NOT correlate with VO2peak.
5. **"Aerobic and anaerobic are zero-sum"** -- False. Both can improve simultaneously.
6. **"One optimal VO2max protocol"** -- False. Individuation matters more.
7. **"Low-carb training improves durability"** -- No evidence. Explicitly dismissed.
8. **"Strength training hurts durability"** -- No long-term negative impact.
