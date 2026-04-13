# Training Load & Recovery

This page covers the mathematics and interpretation of TSS, CTL, ATL, and TSB; the Performance Management Chart (PMC); recovery protocols; overtraining detection; ramp rate guidelines; deload weeks; sleep; active recovery; and HRV monitoring. These are the quantitative foundations for managing training stress and recovery on the platform.

Evidence levels: **[R]** = Research-backed, **[E]** = Experience-based (practitioner consensus), **[O]** = Opinion/emerging.

---

## 1. Training Stress Score (TSS)

### 1.1 Definition and Formula

TSS quantifies the physiological cost of a single workout by combining duration and intensity relative to threshold.

```
TSS = (Duration_seconds x NP x IF) / (FTP x 3600) x 100
```

Where:
- **NP** = Normalized Power (accounts for variability of effort)
- **IF** = Intensity Factor = NP / FTP
- **FTP** = Functional Threshold Power
- **Duration** = total ride time in seconds

**Simplified:** TSS = (IF^2) x (Duration_hours) x 100

A one-hour ride at exactly FTP produces TSS = 100 by definition. [R]

### 1.2 Interpretation

| TSS | Recovery Time | Perceived Effort |
|-----|---------------|-----------------|
| < 150 | Low: recovery typically by next day | Easy to moderate ride |
| 150-300 | Medium: some residual fatigue next day, gone by 2nd day | Moderate endurance ride or hard group ride |
| 300-450 | High: residual fatigue possible for 2+ days | Long hard ride, road race, or hard century |
| > 450 | Very high: may require several days of recovery | Ultra-endurance event, stage race day |

### 1.3 Limitations of TSS

- **TSS does not capture how the stress was accumulated** -- a 200 TSS ride could be 4 hours easy or 2 hours of brutal intervals, producing very different fatigue profiles [E]
- **IF has known limitations during HIIT** -- Normalized Power can underestimate or overestimate the true physiological cost of highly intermittent efforts (TrainingPeaks: Understanding the Limitations of TSS and IF During HIIT) [R]
- **TSS requires accurate FTP** -- if FTP is set too high, TSS/IF read low, which can drive a coach to push too hard. If set too low, TSS reads artificially high. (TrainingPeaks: Understanding Ramp Rate) [E]
- **TSS only captures training stress** -- it does not account for life stress, work, sleep debt, or other allostatic loads (EC TMT-48) [R]
- **Indoor training generates 1.1-1.2x the recovery cost** of equivalent outdoor TSS due to thermoregulation strain (EC TMT-51) [E]

### 1.4 TSS Across Disciplines

For multi-sport athletes, TSS variants exist:
- **bTSS** (bike) -- power-based, most reliable
- **rTSS** (run) -- pace- or power-based; 1 rTSS is harder on the body than 1 bTSS due to weight-bearing (TrainingPeaks: Planning with TSS) [E]
- **sTSS** (swim) -- pace-based; more variable due to technique, pool vs open water
- **hrTSS** (heart rate) -- used when no power/pace data; less accurate

**Critical:** 1 TSS point is NOT equal across disciplines. Running CTL is harder on the body than cycling CTL at the same value. Ramp rates should be evaluated per sport. [E]

---

## 2. The Performance Management Chart (PMC)

The PMC is the primary tool for visualizing the interplay of fitness, fatigue, and form over time. It plots three derived metrics from daily TSS.

### 2.1 Chronic Training Load (CTL) -- "Fitness"

```
CTL(today) = CTL(yesterday) + (TSS(today) - CTL(yesterday)) / tc_CTL
```

Where tc_CTL = 42 days (default time constant).

CTL is the exponentially weighted moving average of daily TSS over approximately 42 days. It represents the training load the body has adapted to -- a proxy for fitness.

**Key principles:**
- CTL going up generally means fitness is increasing [E]
- CTL should build steadily throughout the season, peaking 2-3 weeks before the A-race (TrainingPeaks: Managing Training Stress Balance) [E]
- CTL should never decrease for 2 consecutive weeks during active training -- this indicates detraining (TrainingPeaks: Managing Training Stress Balance) [E]
- **CTL does NOT equal fitness** -- peak performances often occur after CTL dips from peak. Kolie Moore specifically objects to equating CTL with fitness. (EC TMT-68) [E]
- **CTL going up while performance goes down = classic over-reaching signal**, not a sign to train harder (EC TMT-72) [E]

### 2.2 Acute Training Load (ATL) -- "Fatigue"

```
ATL(today) = ATL(yesterday) + (TSS(today) - ATL(yesterday)) / tc_ATL
```

Where tc_ATL = 7 days (default time constant).

ATL is the exponentially weighted moving average of daily TSS over approximately 7 days. It represents recent training stress -- a proxy for fatigue.

### 2.3 Training Stress Balance (TSB) -- "Form"

```
TSB = CTL(yesterday) - ATL(yesterday)
```

TSB represents the balance between accumulated fitness and recent fatigue.

| TSB Range | Interpretation |
|-----------|---------------|
| > +25 | Very fresh but possibly detrained if sustained |
| +10 to +25 | Fresh and fit -- ideal race-day target for most athletes |
| +5 to +10 | Slightly positive -- good for race day (Fitzgerald guideline) [E] |
| 0 to -10 | Slightly fatigued -- normal training state |
| -10 to -30 | Moderately fatigued -- productive overload zone |
| -30 to -70 | Deeply fatigued -- functional overreaching zone |
| < -70 | Extreme fatigue -- risk of non-functional overreaching |

**EC critique of TSB:** "TSB/Form is widely misinterpreted -- positive TSB does NOT mean peaked. The best way to make TSB positive is to get sick." (EC TMT-68) [E]

**Pro cycling example (Boaro/Tinkoff-Saxo):** Peak performance occurred with TSB around +20 and highest possible CTL. During heavy racing blocks, TSB dropped to -79 without permanent damage, but these were followed by deliberate recovery periods. Most amateurs need rest around TSB of -30. (TrainingPeaks: How Tinkoff-Saxo Manages Fitness and Fatigue) [E]

### 2.4 PMC Management Rules

From Matt Fitzgerald and Joe Friel (TrainingPeaks consensus):

1. **Race-day TSB should be slightly positive** (+5 or so) [E]
2. **CTL should peak 2-3 weeks before race day** [E]
3. **CTL should never decline for 2 consecutive weeks** during focused preparation [E]
4. **CTL should never increase faster than 5-8 TSS/day per week** -- exceeding this typically results in performance decline or injury [E]
5. **TSB should not drop below -20 more than once every 10 days** for sustained periods [E]

**Important nuance:** You may not experience positive TSB at any point until the taper. Carrying a moderate negative TSB for weeks during a gradually increasing training load is normal and manageable. (TrainingPeaks: Managing Training Stress Balance) [E]

---

## 3. Ramp Rate

### 3.1 Definition

Ramp rate = the daily rate of change in CTL, expressed in TSS/day. It measures how quickly training load is increasing (or decreasing).

### 3.2 Guidelines

| Ramp Rate | Risk Level | Context |
|-----------|-----------|---------|
| < 3 CTL/week | Low -- possible under-training | May lack sufficient stimulus for adaptation |
| 3-5 CTL/week | Optimal sustained range | Good for long-term, multi-month builds |
| 5-8 CTL/week | Moderate-high | Sustainable for hardy athletes in short bursts |
| 8-10 CTL/week | High -- short-term only | Training camps, brief overload blocks |
| > 10 CTL/week | Very high risk | Likely to cause overreaching within 2-4 weeks |

**Per-month guidelines (Couzens):** 5-15 CTL per month is a sustainable range, with more "fragile" athletes (higher life stress) on the low end and more "hardy" athletes on the high end. [E]

### 3.3 Ramp Rate Math (Couzens Method)

To raise CTL by 10 points in a month using a 3:1 load/recovery structure:
- Loading days TSS target: current CTL + 30 TSS/day
- Recovery days TSS target: current CTL - 30 TSS/day
- Example: CTL of 100, target 110 --> loading days at ~130 TSS/d, recovery days at ~70 TSS/d

### 3.4 Individualization

- Every rider's sustainable ramp rate is a function of starting CTL, training history, life stress, and recovery capacity [E]
- Athletes with years of power data and consistently high CTL will see smaller ramp rates and smaller gains -- diminishing returns (TrainingPeaks: Understanding Ramp Rate) [E]
- Athletes new to power tracking will naturally show steep initial ramp rates [E]
- The higher the absolute CTL, the harder it is to increase ramp rate further [E]

**EC warning:** CTL/TSS chasing is counterproductive. Athletes who doubled down on TSS when performance declined made things worse. Resting fixed everything. (EC TMT-72) [E]

---

## 4. Recovery Protocols

### 4.1 Rest Week Structure (EC TMT-55, 58)

| Parameter | Value | Source |
|-----------|-------|--------|
| Rest week ride IF | < 0.50 | EC TMT-55 [E] |
| Minimum duration | 4-5 days; 7+ days after VO2max blocks | EC TMT-55 [E] |
| Minimum activity dose | > 25% of normal volume, genuinely easy | EC TMT-58 [E] |
| Rest week progression | Pure recovery 2-3 days, progress to endurance, test legs by day 5-7 | EC TMT-58 [E] |
| Openers at end of rest week | 15 min sweet spot or short efforts -- "a privilege for the well-rested" | EC TMT-58 [E] |
| End-of-rest gating test | Sprint power + 5 min at FTP; if both feel good, resume | EC TMT-55 [E] |

**Rest week frequency by block type:**

| Block Intensity | Rest Every | Source |
|----------------|------------|--------|
| VO2max / threshold+ | 2-3 weeks | EC TMT-55 [E] |
| Threshold / sweet spot | 3 weeks | EC TMT-55 [E] |
| Base / endurance | 3-5 weeks (6 for experienced) | EC TMT-55 [E] |

### 4.2 Reactive Rest Triggers

Any single trigger is sufficient to initiate rest (EC TMT-55):

1. **Performance regression** despite maintained training load
2. **Persistent low motivation** -- the most reliable single indicator
3. **Illness** -- any illness
4. **Failed mid-block workout + failed retest 2-3 days later**
5. **Athlete requests rest week** -- ALWAYS grant it, 100% of the time

### 4.3 Active Recovery

- Short, genuinely easy rides (IF < 0.50) are preferred over complete inactivity [E]
- Stopping all activity for 10+ days risks measurable detraining (EC TMT-55) [E]
- Movement-based active recovery (walking, easy spinning, yoga, mobility work) promotes circulation and nervous system recovery without adding training stress [E]
- Do not confuse active recovery with "easy" endurance -- recovery rides should feel embarrassingly slow [E]

### 4.4 Post-Race / Post-Camp Recovery

- After training camps or stage races, rest until TSB returns to positive before loading again [E]
- Producing too much TSS too quickly post-camp extends the recovery timeline and risks illness/injury [E]
- Post-camp "feeling fantastic" trap: athletes come home energized and keep hammering -- usually lasts ~1 week before collapse (TrainingPeaks: PMC for Spring Training Camp) [E]
- After a layoff, athletes rejoin their long-term growth curve within weeks (EC WD-61) [R+E]
- 2 weeks off the bike is NOT the end of the world (EC TMT-55, WD-61) [E]

---

## 5. Overtraining and Overreaching

### 5.1 Spectrum of Overload

| State | Duration to Resolve | Signs |
|-------|-------------------|-------|
| Functional overreaching | Days to 1-2 weeks | Temporary performance decline, resolved with normal rest |
| Non-functional overreaching | 2 weeks to 3 months | Prolonged performance decline, requires extended rest (EC TMT-58) [E] |
| Overtraining syndrome (OTS) | Months to years | Systemic dysfunction, similar to chronic fatigue syndrome |

### 5.2 Signs of Overtraining

**Physical:**
- Excessive fatigue/lethargy, especially off the bike
- Relentless fatigue that does not resolve with normal rest
- Higher resting heart rate and elevated resting blood pressure [R]
- Longer heart rate recovery after exercise [R]
- Increased susceptibility to illness (>1x per 6-8 weeks is a red flag; EC TMT-55) [E]
- Menstrual irregularities in female athletes [R]
- Loss of sex drive / erectile dysfunction in male athletes [R]
- Constant muscle soreness and weakness
- Power-HR inversion: heart rate rising while power drops (EC clinical.py) [E]

**Performance:**
- Declining 1-minute max power (the most sensitive early indicator; EC TMT-55) [E]
- Sprint power and supra-threshold efforts feel unusually hard -- neural drive is the most sensitive to fatigue (EC TMT-55) [E]
- RPE at constant power trending up for 2+ weeks [E]
- Failed key workouts that were previously achievable
- FTP stagnation or decline despite increased training load

**Psychological:**
- Loss of motivation, energy, drive, and enthusiasm to train -- motivation is a physiological signal, not a character flaw (EC TMT-48) [E]
- Increased stress, anxiety, irritability, depression
- Insomnia, sleep problems
- Poor concentration, inability to relax
- "Radio silence" -- no workout comments = probable motivational collapse (EC TMT-55) [E]
- Fear of rest = signal rest is needed (EC TMT-58) [E]

### 5.3 OTS Causes

- Inadequate recovery between training sessions
- Too much high-intensity training sustained for too long
- Sudden drastic increases in volume or intensity (panic training; EC TMT-71) [E]
- No vacations, breaks, or off-seasons
- Inadequate nutrition (caloric and/or carbohydrate restriction) -- OTS and RED-S have near-complete overlap (EC Persp-36, Stellingwerff) [R]
- Insufficient sleep
- High life stress (the body does not differentiate between stress sources) [R]
- High work stress doubles recovery cost when combined with hard training (EC TMT-57) [E]

### 5.4 Recovery from Overtraining

- **Functional overreaching:** Rest 4-7 days, resume gradually
- **Non-functional overreaching:** Extended rest (2 weeks to 3 months), address root causes (EC TMT-58) [E]
- **Overtraining syndrome:** May require complete cessation for weeks to months; prioritize sleep, nutrition, stress reduction. Recovery can take as long as the overtraining period itself. [R]
- **If rest period exceeds 2-3 weeks to restore baseline:** flag as non-functional overreaching or RED-S (EC TMT-58) [E]
- **Severely overtrained athletes may need 2-3 months off** before productive training can resume (EC TMT-58) [E]

### 5.5 Common Mistakes

1. **More training when performance declines** -- rest is usually the answer, not more stimulus (EC TMT-72) [E]
2. **Treating CTL as fitness** -- specifically objected to by Kolie Moore (EC TMT-68) [E]
3. **Getting up earlier to train** -- literally cuts into recovery (EC TMT-72) [E]
4. **Time-crunched athlete doing more intervals** -- may need more rest, not more intervals (EC TMT-72) [E]
5. **"I perform well fatigued" belief** -- almost always false; operating at 80-90% without realizing it (EC TMT-58) [E]
6. **Trusting "I feel fine" in Type-A athletes** -- when performance data shows regression, data wins over feelings (EC TMT-55) [E]
7. **100% plan compliance** -- indicates lack of auto-regulation; a warning sign, not a badge of honor (EC TMT-52) [E]

---

## 6. Deload Weeks

### 6.1 Structure

A deload (recovery) week reduces training volume and intensity to allow supercompensation.

| Day | Activity |
|-----|----------|
| Day 1-2 | Complete rest or very light movement (walking, yoga) |
| Day 3-4 | Short, easy rides (IF < 0.50), 30-60 min |
| Day 5-6 | Moderate endurance ride, testing legs with brief efforts |
| Day 7 | Gating test: sprint power + 5 min at FTP to assess readiness |

### 6.2 Volume and Intensity Reduction

- Volume: reduce to 40-60% of normal training week (>25% minimum; EC TMT-58) [E]
- Intensity: all rides IF < 0.50 until gating test [E]
- No structured intervals during deload except for end-of-week openers [E]

### 6.3 Deload vs. Complete Rest

- 4-5 days of easy activity is preferred to complete cessation (EC TMT-55) [E]
- Complete rest >10 days results in measurable detraining [E]
- Active recovery maintains cardiovascular and neuromuscular function while allowing metabolic and hormonal recovery [R]
- Sprint PRs after time off are common -- don't chase more sprint training if sprint power is down late-season (EC TMT-72) [E]
- End-of-rest sprint/1-min test often produces lifetime PRs (EC TMT-58) [E]

---

## 7. Sleep

### 7.1 Importance

Sleep is the single most important recovery tool. No supplement, device, ice bath, or compression garment can compensate for insufficient sleep. [R]

**EC position:** "No ice bath, theragun, or supplement measurably speeds recovery -- consistency of basic habits (sleep, nutrition, stress) is the single most important factor" (EC TMT-52) [E]

### 7.2 Guidelines

| Parameter | Target | Source |
|-----------|--------|--------|
| Minimum sleep for athletes | 7-9 hours per night | ACSM, consensus [R] |
| Optimal for high training load | 8-10 hours | Coaching consensus [E] |
| Naps | 20-30 min post-lunch can supplement night sleep | [R] |
| Sleep debt accumulation | Cumulative -- cannot be "caught up" in a single night | [R] |

### 7.3 Sleep and Training Load

- Getting up earlier to train literally cuts into recovery (EC TMT-72) [E]
- Holiday recovery >> normal-life recovery, partly due to better sleep and reduced work stress (EC TMT-72) [E]
- Athletes consistently sleeping < 6 hours will show chronic HRV depression and impaired adaptation [R]
- Sleep quality (deep sleep, REM cycles) matters as much as duration [R]
- Poor sleep is the most common modifiable limiter among age-group athletes [E]

### 7.4 Platform Relevance

Track sleep quality/duration as part of structured feedback fields. Correlation between sleep metrics and performance trends can reveal when sleep debt is the primary limiter rather than training prescription.

---

## 8. HRV Monitoring

### 8.1 What HRV Measures

Heart Rate Variability (HRV) measures the time variation between heartbeats, reflecting the balance between the sympathetic (fight-or-flight) and parasympathetic (rest-and-digest) branches of the autonomic nervous system (ANS).

- **High HRV:** robust, well-balanced ANS; ready to respond to stress [R]
- **Low HRV:** imbalanced ANS; less responsive to stress, indicating fatigue or illness [R]
- **Volatile HRV (highly variable day-to-day):** indicates high total life stress [E]

### 8.2 How to Use HRV

**EC guidelines (TMT-51, TMT-55):**

| Context | HRV Usefulness |
|---------|---------------|
| VO2max blocks with doubles | Most useful -- high sensitivity to overload |
| High-intensity blocks | Moderately useful |
| Low-intensity / endurance blocks | Unreliable -- insufficient stress signal |
| Illness prediction | Sustained depression >7 days = impending illness |
| Workout prescription | NOT recommended as primary prescription tool |

**Key rules:**
- Look at 3-7 day trends, NOT single readings (EC TMT-51) [E]
- Indoor blocks show slower HRV recovery than outdoor (EC TMT-51) [E]
- A single reading much HIGHER than normal can also indicate fatigue (paradoxical parasympathetic rebound) [R]
- HRV does not predict performance -- it is a window into fatigue and recovery state [E]
- HRV reflects the nervous system -- it won't necessarily correlate with DOMS or muscular soreness [R]

### 8.3 HRV and Total Life Stress (TLS)

HRV captures ALL stress, not just training stress. This makes it valuable for detecting life-stress impacts that TSS/CTL cannot capture. (TrainingPeaks: How to Interpret HRV) [E]

**Common HRV disruptors:**
- Alcohol consumption (sharp HRV drop, elevated RHR for 24-48 hours) [R]
- Caloric restriction / carbohydrate restriction during high training load [E]
- Poor sleep (< 6 hours consistently) [R]
- Relationship or work stress [E]
- Travel and jet lag [E]

### 8.4 Interpretation Chart

| Pattern | Meaning | Action |
|---------|---------|--------|
| High, stable HRV + low stable RHR | Healthy, resilient athlete | Continue training as planned |
| Gradually trending down | Accumulating fatigue or life stress | Consider deload or stress reduction |
| Sudden sharp drop | Acute stressor (alcohol, illness onset, poor sleep) | Identify cause; consider rest day |
| Sustained depression >7 days | Impending illness or non-functional overreaching | Mandatory rest; consider medical check |
| Highly volatile (large daily swings) | High total life stress | Address lifestyle factors before increasing training |

### 8.5 Limitations

- HRV is highly individual -- absolute values are not comparable between athletes [R]
- Gender, age, health, and fitness levels complicate direct comparisons [R]
- Must be measured at the same time and same way daily to be meaningful [E]
- Device and app accuracy varies; consistency within one system matters more than absolute accuracy [E]
- HRV should supplement, not replace, subjective feedback and performance data [E]

---

## 9. Subjective Metrics

EC identifies subjective metrics as often more reliable than objective data for detecting recovery needs (EC TMT-55, 51):

| Metric | Reliability | Notes |
|--------|------------|-------|
| Motivation to train | Highest | Most reliable single indicator of recovery status |
| Mood / irritability | High | "Ask your partner" -- external observation often more accurate |
| Sleep quality | High | Both duration and perceived quality matter |
| RPE drift at constant power | High | Same power feeling harder over time = fatigue accumulation |
| Dissociated RPE (legs vs lungs) | Moderate | Different fatigue signatures |
| Brain fog | Moderate | Often dismissed but correlates with chronic fatigue |

**The performance vs. subjective conflict detector:** If power is trending down but athlete reports feeling good, flag for review. Data wins over feelings in Type-A athletes. (EC TMT-55) [E]

---

## 10. Recovery Model Parameters (Consolidated)

| Parameter | Value | Source |
|-----------|-------|--------|
| VO2max block max before mandatory rest | 2-3 weeks | EC TMT-55 [E] |
| Threshold block max before rest | 3 weeks | EC TMT-55 [E] |
| Base/endurance block max before rest | 3-5 weeks (6 for experienced) | EC TMT-55 [E] |
| Rest week minimum duration | 4-5 days (7+ after VO2max) | EC TMT-55 [E] |
| Rest week minimum activity dose | >25% normal volume, genuinely easy | EC TMT-58 [E] |
| Rest week ride IF | < 0.50 | EC TMT-55 [E] |
| Days off before measurable detraining | ~10 days | EC TMT-55 [E] |
| Mid-season break recovery | 1 week off = ~2-3 weeks to return | EC TMT-43 [E] |
| Non-functional overreaching exit | 2 weeks to 3 months | EC TMT-58 [E] |
| Severe overtraining recovery | 2-3 months off before productive training | EC TMT-58 [E] |
| Indoor training recovery multiplier | 1.1-1.2x outdoor TSS | EC TMT-51 [E] |
| Hard workout success rate target | >= 90% | EC TMT-69 [E] |
| Illness frequency red flag | > 1x per 6-8 weeks | EC TMT-55 [E] |
| Performance test staleness | >90 days = flag zones as stale | EC TMT-51 [E] |
| Maximum sustainable metabolic scope (long-term) | 2.5x BMR (3x for elites) | EC Persp-40 [R] |
| CTL max ramp rate (sustained) | 3-5 TSS/day per week | Friel, Couzens [E] |
| CTL max ramp rate (short-term) | 5-8 TSS/day per week | Friel, Nicoli [E] |
| TSB red line | < -20 no more than 1x per 10 days | Fitzgerald [E] |
| Optimal race-day TSB | +5 to +20 | Fitzgerald, Friel [E] |

---

## 11. Clinical Integration: Red and Amber Flags

### RED FLAGS (Immediate Intervention)

| Signal | Detection Method | Source |
|--------|-----------------|--------|
| Performance declining + training load maintained + weight stable | Power + TSS + weight trends | EC Persp-36 [R] |
| Illness frequency > 1x per 6-8 weeks | Calendar annotations | EC TMT-55 [E] |
| Athlete requests rest week mid-block | Direct request -- ALWAYS grant | EC TMT-55 [E] |
| Recovery time progressively increasing | RPE recovery, HRV trends | EC TMT-55 [E] |
| Male: low libido/erections | Self-report (suppressed testosterone) | EC Persp-36 [R] |
| Female: irregular/absent menstrual cycle | Self-report (RED-S screen) | EC Persp-36 [R] |
| Rest >2-3 weeks to restore baseline | Non-functional overreaching or RED-S | EC TMT-58 [E] |
| Power-HR inversion (HR rising, power dropping) | Ride data analysis | clinical.py [E] |

### AMBER FLAGS (Monitor Closely)

| Signal | Detection Method | Source |
|--------|-----------------|--------|
| Weight-stable + cold extremities, low energy, disturbed sleep | Subjective feedback | EC Persp-40 [R] |
| Intensity black hole: most rides IF 0.65-0.80 | IF distribution audit | EC TMT-58 [E] |
| Weight loss during high-intensity block | Block type + deficit detection | EC TMT-48 [E] |
| Boom-bust CTL pattern (ramp + crash repeated) | CTL time series | EC TMT-48 [E] |
| RPE at constant power trending up 2+ weeks | RPE:power tracking | EC TMT-51 [E] |
| HRV sustained depression >7 days | HRV trends | EC TMT-51 [E] |
| "Radio silence" -- no workout comments | Comment frequency | EC TMT-55 [E] |
| Endurance rides consistently IF > 0.70 | IF audit | EC TMT-69 [E] |
| Panic training: sudden intensity spike after low-load | CTL ramp rate spike | EC TMT-71 [E] |

---

## 12. Conflicts and Debates

| Topic | Common Belief | EC/Modern Position | Evidence |
|-------|-------------|-------------------|----------|
| CTL = fitness | Higher CTL always = fitter | CTL is a proxy; peak performances often occur after CTL dips | EC TMT-68 [E] |
| Positive TSB = peaked | TSB > 0 means ready to race | "Best way to make TSB positive is to get sick" | EC TMT-68 [E] |
| More training always better | Time-crunched athletes should add intervals | May need more rest, not more intervals | EC TMT-72 [E] |
| Recovery gadgets work | Ice baths, theraguns speed recovery | No measurable effect; sleep + nutrition + stress management are what matter | EC TMT-52 [E] |
| HRV guides daily workouts | Prescribe intensity based on morning HRV | Only useful for illness detection and during VO2max blocks; trends > single readings | EC TMT-51 [E] |
| OTS and RED-S are separate | Overtraining and relative energy deficiency are different conditions | Near-complete overlap -- "almost just a circle" as a Venn diagram | EC Persp-36 [R] |
| Holiday is wasted training time | Time off = fitness lost | Holiday recovery >> normal-life recovery (better sleep, less work stress, better eating) | EC TMT-72 [E] |

---

## 13. Platform Module Mapping

| Concept | Module | Implementation Notes |
|---------|--------|---------------------|
| TSS calculation and tracking | `training_load.py` | Per-ride TSS, daily TSS, rolling CTL/ATL/TSB |
| CTL ramp rate monitoring | `training_load.py` | Individualized alert thresholds (WKO5 Hero Bar compatible) |
| Rest-week recommendation engine | `blocks.py` | Intensity-weighted block duration triggers per EC guidelines |
| Performance vs. subjective conflict detector | `training_load.py` | Power trending down + athlete reports feeling good = flag |
| IF floor diagnostic | `clinical.py` | Flag endurance rides > IF 0.70 |
| Intensity black hole detection | `clinical.py` | IF distribution: most rides 0.65-0.80, no true easy or hard |
| Indoor TSS multiplier | `training_load.py` | Apply 1.1-1.2x multiplier to indoor sessions |
| Allostatic load model | `training_load.py` | Integrate TSS with life-stress proxies (comment sentiment, missed sessions) |
| Boom-bust CTL detection | `training_load.py` | CTL time series analysis for repeated ramp-crash patterns |
| Panic training detection | `clinical.py` | Flag sudden intensity spike after low-load period |
| RPE:power ratio tracking | `training_load.py` | Rising RPE at constant power = fatigue accumulation |
| HRV trend analysis | `clinical.py` | 3-7 day rolling average; flag sustained depression >7 days |
| Clinical red/amber flags | `clinical.py` | Integrated into `get_clinical_flags()` |

---

## 14. Key References

### Empirical Cycling Episodes
- TMT-48: Avoiding Over-Optimization (allostatic load, consistency)
- TMT-51: RPE, Workout Feedback, HRV
- TMT-52: Intermediate Mistakes (plan compliance, recovery)
- TMT-55: Rest Weeks / Subjective Metrics (rest triggers, deload)
- TMT-58: Why Rest Is Scary (deload structure, fear of rest)
- TMT-68: Using Data in Coaching (CTL != fitness, TSB critique)
- TMT-69: Riding Easier (IF floor, intensity distribution)
- TMT-71: Panic Training (anti-panic protocol)
- TMT-72: Stimulus vs Recovery (overreaching, CTL chasing)
- TMT-73: Things We Wish We Knew (fueling, zone 2)
- Persp-36: Chronic Underfueling / RED-S (Carson)
- Persp-40: Energy Expenditure / Constrained Energy Model (Trexler)

### EC Podcast Insights (Batch 2)
- Rest Week Decision Tree (TMT-55)
- Recovery Model Parameters (consolidated)
- Cross-Episode Detection Rules (Red/Amber flags)

### TrainingPeaks Articles
- Managing Your Training Stress Balance (Fitzgerald)
- Why Am I So Tired? (Friel)
- Planning Your Season With TSS (Couzens, Vance)
- Understanding Ramp Rate in TrainingPeaks (Allison)
- How to Use TSS to Prepare for an Ironman (Nicoli)
- All About Detraining (Mantak)
- All About Overtraining Syndrome (Greenfield)
- How to Interpret HRV to Reduce Stress and Increase Performance (Rowe)
- The Athlete's Handbook to Training With HRV (TrainingPeaks)
- GTN Presents: Overtraining and Recovery (Legacki)
- How Tinkoff-Saxo Manages Fitness and Fatigue Over the Season (Johnson)
- Using the PMC to Maximize Your Spring Training Camp (Wallenfels)
- Ask the Experts: Building Chronic Training Load (Vicario)
- Doing Rest Days Right (White)
- Why Form Follows Fatigue (Bill)
- How to Use WKO4 to Construct Training Plans (Rollinson)

---

## Cross-References

- [Training Periodization](training-periodization.md) — base/build/peak/race phases define when CTL ramps, rest weeks, and tapers occur
- [FTP & Threshold Testing](ftp-threshold-testing.md) — accurate FTP is required for TSS/IF calculation; stale FTP corrupts all PMC metrics
- [Durability & Fatigue](durability-fatigue.md) — durability degradation model captures fatigue dimensions that TSS/CTL cannot (kJ-dependent and time-dependent decay)
- [Interval Design](interval-design.md) — workout structure determines the type of stress accumulated; high-rep HIIT generates different fatigue than steady-state
- [Endurance Base Training](endurance-base-training.md) — IF floor diagnostic (rides > 0.70) is the intensity black hole that training load audits must catch
- [Strength & Conditioning](strength-conditioning.md) — strength sessions add recovery cost not captured by cycling TSS; gym phase alignment with deload timing matters
- [Tools & Platforms](../entities/tools-platforms.md) — TrainingPeaks PMC, WKO5 Hero Bar, and HRV platforms implement these metrics
