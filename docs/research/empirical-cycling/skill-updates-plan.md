# Skill Updates Plan — Empirical Cycling Podcast Synthesis

Cross-referenced from all 53 episodes. Organized by skill, not by episode.
Evidence levels: [R] = Research-backed, [E] = Experience-based, [O] = Opinion.

---

## 1. wko5-training SKILL

### Section: "Kolie Moore FTP Testing Protocol" — ADD after existing protocol text

Insert after the line `After this initial baseline, no additional formal testing is needed. Use unstructured testing going forward.`

```markdown
### FTP Testing Caveats (from EC Podcast)

- **Over-testing is counterproductive** — use progressive workout performance as the primary fitness indicator; formal tests every 3-4 months max (TMT-66) [E]
- **Rolling PD curves from training data are more reliable than isolated test days** — single tests have ~2% power meter error making 5W changes meaningless (WD-62) [R]
- **Erg mode hides true readiness** — free-ride mode reveals daily capacity; wean athletes off erg for key sessions (TMT-73) [E]
- **Ramp test gains can reflect W' (anaerobic capacity), not VO2max** — decompose PD curve changes into CP vs W' contributions (WD-55) [R]
- **Insufficient rest before testing is the most common testing error** — ensure 3-5 days easy before any formal test (TMT-66) [E]
```

### Section: "Interval Prescription — Research Highlights" — MODIFY

Replace the 30/15 subsection with this corrected version:

```markdown
### Short Intervals (30/15) — Nuanced Evidence

Ronnestad et al. (2020) showed 30/15 intervals (30s-on/15s-off at ~94% Wmax) produced improvements in ramp test power and 20-min power vs effort-matched 5-min intervals.

**Critical correction (WD-55):** The study abstract states "no group difference in change of VO2max" (p = 0.49). The performance gains in the 30/15 group most likely reflect W' (anaerobic capacity) improvement, not VO2max gains. The word "anaerobic" appears only once in the entire paper. 30/15 blocks remain a valid tool — they are effective for anaerobic capacity development and useful for athletes who have plateaued on long-interval structures. They are NOT magic for VO2max.
```

### Section: "Fueling Strategy for Training" — MODIFY

Replace the "Train-Low / Compete-High" subsection:

```markdown
### Train-Low / Compete-High — Molecular Dead End for Performance

Periodized CHO availability has molecular support (AMPK amplification via glycogen-binding domain on AMPK beta subunit [WD-54]) but **performance evidence consistently negative** [R]:
- In-vitro mechanism does NOT translate to in-vivo performance gains
- Low glycogen training increases fat oxidation but impairs high-intensity training capacity
- Delayed feeding impairs recovery, disrupts metabolic health, decreases next-day performance

**Platform stance:** Do NOT build "train low" recommendations. Model glycogen depletion as a cost to recovery, not a training stimulus. If implementing glycogen periodization at all, restrict to easy/moderate sessions only (WD-54, TMT-73).
```

### Section: "Fatigue Resistance Training Protocols" — MODIFY

Update the assessment benchmarks:

```markdown
**Assessment (updated from EC podcast, WD-60):**
- Use **kJ/kg** bins (not raw kJ) — 10 kJ/kg intervals are the standard
- Top pros: **<2% power drop** from fresh to 50-60 kJ/kg
- Good amateurs: **10-20% drop**
- Average amateurs: **20-40% drop**
- **Total time riding is the best predictor of durability** [E] — 4x15min FTP efforts spread across 4-hour ride = excellent durability training
- **Always show durability alongside absolute power** — Goodhart's Law warning: over-indexing on kJ/kg can lead to bad strategies
- **Fresh baseline must exist** — flag when fresh baseline is missing or stale
```

### Section: NEW — Add "Training Intensity Distribution" after "Polarized vs. Threshold Training" references

```markdown
## Training Intensity Distribution — IPD Meta-Analysis Findings

From Perspectives #38 (Jem Arnold, IPD meta-analysis, ~350 athletes, 13 studies) [R]:

- **No single training intensity distribution is statistically superior overall**
- Subgroup: competitive athletes slightly favor polarized; recreational slightly favor pyramidal
- Magnitude: ~1-2% VO2max difference — within day-to-day noise (~5%)
- ~20% of study participants were re-categorized when actual behavior was analyzed
- Individual responses ranged from -20% to +30% around group averages

**Platform implication:** Describe distributions without prescribing one as superior. The platform should support multiple zone models (3-zone physiological + 5-7 zone power) without privileging polarized over pyramidal or vice versa.
```

### Section: NEW — Add "Recovery and Rest Week Framework" before "Training Philosophy"

```markdown
## Recovery and Rest Week Framework (EC Podcast Synthesis)

### Planned Rest Weeks
| Block Intensity | Rest Frequency | Rest Duration |
|----------------|---------------|---------------|
| VO2max / threshold+ | Every 2-3 weeks | 7+ days after VO2max |
| Base / endurance | Every 3-5 weeks | 4-5 days minimum |
| Mixed / moderate | Every 3-4 weeks | 5-7 days |

### Reactive Rest Triggers (any one sufficient)
- Performance regression despite maintained training load
- Persistent low motivation (most reliable single indicator)
- Illness frequency > 1x per 6-8 weeks
- Failed mid-block workout + failed retest 2-3 days later
- **If athlete requests rest week: ALWAYS grant it** (100% of the time)

### Rest Week Structure
1. Pure recovery 2-3 days (IF < 0.50)
2. Progress to easy endurance rides
3. Test legs by day 5-7: sprint power + 5min at FTP as gating workout
4. 10+ days fully off bike = measurable fitness loss

### Recovery Model Parameters
| Parameter | Value |
|-----------|-------|
| Indoor training recovery multiplier | 1.1-1.2x outdoor equivalent TSS |
| Days off before measurable detraining | ~10 days |
| Time to exit non-functional overreaching | 2 weeks to 3 months |
| Maximum sustainable metabolic scope | 2.5x BMR (3x for elites) |
| Performance test freshness interval | Every 8-12 weeks |

### The "Intensity Black Hole" Diagnostic
If most rides are IF 0.65-0.80, with no true recovery (IF < 0.50) and no true high-intensity — flag as suboptimal distribution. This is the most common amateur training error (TMT-58, TMT-69).

### Allostatic Load Model
The body has ONE pool for ALL stress — training + work + family + sleep debt (McEwen allostatic load theory). High work stress doubles recovery cost (TMT-57). During high-stress periods, switch from "improve" to "maintain" mode [E].
```

### Section: "Concurrent Training Risks" — MODIFY

Update with EC podcast nuance:

```markdown
## Concurrent Training (Updated from EC Podcast)

- **Aerobic and anaerobic are NOT zero-sum** — Kolie trains sprinters from 1500W/400W FTP to 1900W/430W FTP; both improve simultaneously (WD-60) [E]
- **Heavy lifting does NOT hurt durability long-term** (WD-60) [E]
- **Strength is a skill (neural drive)** — can be maintained with very low volume: 1x/week heavy singles at RPE 7/10 (TMT-42) [R]
- **For strength without weight gain:** 1-3 heavy singles at RPE 9-9.5, avoid back-off sets and AMRAPs (WD-56) [R]
- **Periodization:** Off-season 2-3x/week heavy -> in-season 1x/week singles for maintenance
- **Cyclists over 35-40:** strength training is essential for health even if bike performance isn't the primary goal (TMT-73) [E]
- Separate hard cycling and heavy lifting by at least 6 hours
```

---

## 2. wko5-nutrition SKILL

### Section: "Key Nutrition Principles > Racing (<6 hours)" — MODIFY

Update carb targets and add context:

```markdown
### Racing (<6 hours)
- Target **60-90g/hr carbs** as standard; up to 120g/hr for elite athletes with trained guts (glucose:fructose ~1:0.8)
- **Carb absorption is individual** — ranges from 50-150g/hr; lab test with 13C tracer can personalize (Persp-41) [R]
- **>67g/hr spares liver glycogen** — threshold for meaningful sparing (Persp-41) [R]
- **120g/hr vs 90g/hr tradeoff:** higher on-bike intake means fewer carbs for recovery; can impair next-day glycogen if recovery carb budget is squeezed (Persp-41) [R]
- Start eating in first 15-20 minutes
- Every 15-20 min for gels, constant sipping for drink mix
- Caffeine: 3-6mg/kg, 40-60min before start
- Above 85% FTP: liquids/gels only, gut blood flow drops
```

### Section: "Key Nutrition Principles" — ADD new subsection after "Hydration"

```markdown
### Recovery Nutrition (Critical — from EC Podcast)

- **Delayed post-exercise carbs impair next-day performance by ~30%** even when 24hr glycogen levels equalize (WD-59) [R]
  - Effect size: 2.03 (massive); RPE ~2 units higher in delayed group
  - The "glycogen window" is real for PERFORMANCE, not just glycogen quantity
- **Post-exercise carb repletion target:** 1.2 g/kg/hr for 4-5 hours (Persp-41) [R]
- **Glycogen supercompensation:** 10-12 g/kg carbs day before key event (Persp-41) [R]
  - Rice/potato preferred over pasta (gluten causes bloating even in non-intolerant)
  - Haribo/sweets: no gluten, no fiber, no extra sodium, no fat — just carbs
- **Back-to-back hard days:** eat immediately post-ride, do NOT delay >1 hour
- **Dieting + training:** create deficit away from hard sessions; fuel on-bike, restrict off-bike
- **Sleep disruption from hunger:** sign of inadequate fueling — eat immediately

### Within-Day Energy Deficit (CRITICAL)

Even at adequate 24hr totals, prolonged intra-day deficits impair performance and health (WD-59, Persp-36) [R]:
- A 1,100 kcal deficit at 9am (from fasted morning training) triggers hormonal stress response
- Groups with same daily calories but larger hourly deficits have worse outcomes
- Associated with: elevated cortisol, suppressed RMR, menstrual disruption
- **Platform implication:** track within-day energy balance, not just daily totals

### Protein & Fat Minimums

| Nutrient | Target | Source |
|----------|--------|--------|
| Protein | 2-2.5 g/kg/day total body mass | Daniel Moore's lab (Persp-41) [R] |
| Fat minimum | 0.8 g/kg/day | Persp-41 [E] |
| Signs of insufficient fat | Lethargy, low libido (similar to LEA) | Persp-41 [E] |
```

### Section: "Key Nutrition Principles > Hydration" — MODIFY

Add electrolyte correction:

```markdown
### Electrolyte Timing (Correction from EC Podcast)

- **No evidence you need to replace electrolytes during exercise <4 hours** (Persp-41) [R]
- Daily sodium balance matters more than acute replacement
- **Sweat composition tests are nearly useless** — composition changes with training state, intensity, diet, and day-to-day (Persp-41) [R]
```

### Section: "Common Mistakes" — ADD items

```markdown
9. **Trusting energy estimation precision** — ~900 kcal swing from efficiency assumptions alone (20-25% GE); nutrition labels 20% error; absorption 85-95%. Display confidence intervals, not point estimates (Persp-41) [R]
10. **"Replace the carbs you burned"** — must replace total energy, not just carb substrate; body is a good energy accountant, not a substrate accountant (TMT-50) [R]
11. **Creating acute energy deficit for weight loss on training days** — sets up binge patterns; body is an "excellent energy accountant"; deep acute deficit from hard long rides worsens diet outcomes (TMT-69) [E]
```

### Section: NEW — Add "Creatine for Cyclists" subsection at end

```markdown
### Creatine for Cyclists (WD-58 — Full Review)

- **Zero effect on aerobic/endurance performance** (meta-analysis, N=277, effect size -0.07) [R]
- **Small effect on repeated sprint mean power** (~27W on 1000W sprint, ES 0.61) but wide CI [R]
- **Largest reliable effect is body mass gain** (~0.8-1.0 kg water weight, ES 0.79) [R]
- **Weight gain may negate sprint gains on W/kg basis** — net negative for climbing [R]

| Athlete Type | Recommendation | Rationale |
|---|---|---|
| Road racer (climbing) | No | Weight gain negates sprint benefit |
| Flat sprinter | Maybe | Small sprint gain if weight gain minimal |
| Track (gym-heavy) | Yes | Supports gym work |
| Ultra-endurance | Consider | Possible cognitive benefit in sleep deprivation |

**Platform stance:** Creatine is irrelevant to endurance performance modeling. Do not factor into power predictions. Flag unexplained 1-2kg jumps as water weight annotation.
```

---

## 3. wko5-science SKILL

### Section: "Polarized vs. Threshold Training" — MODIFY

Replace existing text with updated evidence:

```markdown
## Training Intensity Distribution (Updated — IPD Meta-Analysis)

From Perspectives #38 (Jem Arnold), the most comprehensive analysis to date [R]:

- **IPD meta-analysis (~350 athletes, 13 studies): NO single distribution is statistically superior**
- Uses 3-zone physiological model (Zone 1 below VT1, Zone 2 between VT1-VT2, Zone 3 above VT2)
- Note: "Zone 2" here encompasses what cyclists call tempo, sweet spot, AND threshold
- Subgroup: competitive athletes slightly favor polarized; recreational slightly favor pyramidal
- Magnitude: ~1-2% VO2max — within day-to-day noise (~5%)
- **~20% of participants did different distributions than assigned** — compliance is a huge confounder
- Individual responses ranged from -20% to +30% around group average

**Key insight from EC podcast:** The polarized vs. threshold vs. pyramidal debate is resolved at the population level — none wins decisively. Individual variation dwarfs distribution effects. The platform should describe distributions without prescribing one.
```

### Section: "Molecular Adaptation" — ADD after existing three pathways

```markdown
### AMPK-Glycogen Interaction (WD-54)

AMPK has a glycogen-binding domain (GBD) on its beta subunit [R]:
- Glycogen physically binds and inhibits AMPK — it's not that low glycogen activates AMPK, it's that high glycogen suppresses it
- This inhibition is independent of AMP/ATP status
- This provides the molecular basis for "train low" approaches
- **However:** practical "train low" interventions do NOT improve performance despite higher AMPK activation
- **Mechanism is not outcome** — discovering a molecular pathway does NOT validate a training intervention
```

### Section: "Central vs. Peripheral Adaptation" — ADD

```markdown
### Newbie Gains Are Central, Not Peripheral (WD-53)

Key finding from Montero et al. 2015 [R]:
- 16 untrained men, 6 weeks at ~65% VO2peak
- VO2peak up 9%, mitochondrial volume up 40%
- **Phlebotomy (removing gained blood volume) erased VO2peak improvements back to baseline**
- Mitochondrial gains did NOT correlate with VO2peak
- Strongest predictors: cardiac output, blood volume, plasma volume, hemoglobin (R ~0.8)
- **Blood volume super-compensation does NOT work in trained athletes** — cardiac function is the limiter

**Platform implication:** Flag new/returning athletes for different adaptation expectations. Rapid FTP gains in newbies are NOT indicative of long-term trajectory.
```

### Section: "Fatigue Resistance Benchmarks" — MODIFY

Update with kJ/kg standard and WD-60 data:

```markdown
## Fatigue Resistance / Durability Benchmarks (Updated — WD-60)

**Standard metric: kJ/kg** (not raw kJ) in bins of 10 kJ/kg (van Erp et al. 2021)

| Level | Power Drop at 50 kJ/kg | Source |
|-------|----------------------|--------|
| Elite pro | <2% | EC coaching [E] |
| Good amateur | 10-20% | EC coaching [E] |
| Average amateur | 20-40% | EC coaching [E] |

**van Erp World Tour data (WD-60):**
- Successful sprinters: start 18.25 W/kg 10s, lose ~8% at 50 kJ/kg
- Less successful: start 17.7 W/kg 10s, lose ~18%
- Successful climbers: start 6.28 W/kg 20min, lose ~4%
- Less successful: start 5.99 W/kg 20min, lose ~9%
- **Better group starts with more power AND loses less** — correlation, not causation

**Critical measurement caveats (WD-60):**
1. Fresh baseline often missing — misleading "0% loss" if best effort happened after 20 kJ/kg
2. Intensity before test matters enormously — endurance preload vs race preload
3. Body weight scaling — 2000 kJ is huge for 55kg woman, warmup for 75kg pro
4. Anaerobic capacity confounds lab protocols
5. Nutrition is a dangling confounder — massive effect, uncontrolled in field data
6. Environment (heat, cold, altitude, wind) all affect measurements
```

### Section: "Trainability of Physiological Systems" — ADD

```markdown
### Diminishing Returns — Quantified (WD-61)

From Steel et al. (N=14,690) + EC coaching case series [R]:
- **Diminishing returns follow a logarithmic growth curve**
- Change point (knee) mode: 26-31 weeks; some individuals: 250+ weeks
- Cycling: ~25% improvement over baseline is common long-term ceiling
- Early growth curve stimuli are non-specific (sprint and threshold both raise VO2max)
- Cross-stimulation disappears as you move right on the growth curve
- **After a layoff, athletes rejoin their long-term growth curve within weeks** [R+E]

| Training Age | Expected FTP Gain/Year |
|-------------|----------------------|
| Year 1 (beginner) | 30-50W |
| Year 2-3 (intermediate) | 10-30W |
| Year 4+ (experienced) | 5-10W |
| Well-trained plateau | 0-5W (mostly TTE extension) |

**Genetic plateau is a diagnosis of exclusion** — must first exclude: insufficient stimulus, insufficient recovery, life stress, nutrition, sleep. Most amateurs are limited by stimulus AND recovery, not genetics.
```

---

## 4. wko5-analyzer SKILL

### Section: "Module Reference > Durability Model" — ADD context note

```markdown
### Durability Model — Interpretation Notes (EC Podcast)
- Use **kJ/kg** (not raw kJ) as the primary unit — normalize for body weight
- Always check for **fresh baseline** — if missing, reduce confidence in durability metrics
- Track **pre-effort intensity distribution** — endurance preload vs race preload produce very different results
- Always present durability **alongside absolute power** — durability without sufficient power is meaningless (WD-60)
- Total ride time is the best predictor of durability — not specific "durability workouts"
```

### Section: "Question -> Function Mapping" — ADD rows

```markdown
| IF distribution / intensity audit | `period_distribution()` + check IF floors |
| Sweet spot TTE | `time_in_zones()` at sweet spot band + duration tracking |
| Panic training detection | Compare recent CTL ramp vs historical; flag sudden spikes after low periods |
| Day-to-day performance trend | `rolling_ftp(window_days=30, step_days=1)` — trending down = red flag |
| Indoor vs outdoor comparison | Filter by `sub_sport`, apply 1.1-1.2x TSS multiplier for indoor |
```

### Section: "Bayesian Interpretation Framework > Step 1: State the Prior" — ADD

After the existing bullet points, add:

```markdown
- EC Podcast evidence base: intensity distribution (no single best), recovery framework (rest week timing by block type), durability benchmarks (kJ/kg), diminishing returns model (log growth curve), within-day energy deficit risks
- Key EC diagnostic: IF distribution over time with floor analysis — floor at 0.70-0.75 = "easy gains available" from riding easier (TMT-69, TMT-68)
- TTE stagnation at FTP signals need for VO2max work, not more threshold (TMT-60)
- Performance declining + CTL rising = rest needed, not more stimulus (TMT-72)
```

---

## 5. dr-vasquez SKILL

### Section: "Her Strong Opinions" — ADD

```markdown
- **IF distribution is the first thing she checks** for any new athlete — floor at 0.70 means the athlete is riding endurance too hard. "Easy gains" from simply riding easier are the most common coaching intervention she makes.
- **Within-day energy deficit matters as much as daily totals** — a 1,100 kcal deficit at 9am triggers hormonal stress even if dinner restores balance. She tracks meal timing, not just daily macros.
- **RED-S and overtraining syndrome are "almost just a circle"** as a Venn diagram (Stellingwerff) — she differentiates by checking fueling adequacy before assuming training volume is the issue.
- **Panic training is her #1 red flag in January/February** — sudden intensity spikes after low-load periods almost always backfire. She prescribes volume first, intensity second.
- **"The body has ONE pool for ALL stress"** — she models allostatic load (McEwen), not just training stress. High work stress doubles recovery cost.
- **Creatine is irrelevant for her endurance athletes** — zero aerobic effect, marginal sprint effect within power meter error, reliable weight gain. She only considers it for track sprinters doing heavy gym work.
- **"Eating ain't cheating"** — she considers 60-90g/hr carbs on the bike as baseline, not a luxury. The old 25g/hr paradigm was destructive.
- **She demands large effect sizes from n=1 experiments** — 5W FTP changes are within measurement error. She uses rolling averages over 90 days, not single test days.
```

### Section: "Her Strong Opinions" — MODIFY existing bullet

Change:
```
- Durability (fatigue resistance) is the most undervalued metric in endurance sports. Fresh-state PD curves tell you almost nothing about ultra performance.
```

To:
```
- Durability (fatigue resistance) is undervalued but not a silver bullet. She cites WD-60: "You need sufficient power to begin with." Better cyclists start with more power AND lose less. She always shows durability alongside absolute power and warns against Goodhart's Law — over-indexing on kJ/kg can lead to bad race strategy.
```

### Section: NEW — Add "Clinical Detection Framework" after "When to Use Her"

```markdown
## Clinical Detection Framework (from EC Podcast Synthesis)

### RED FLAGS (Immediate Intervention)
| Signal | Detection |
|--------|-----------|
| Performance declining + training load maintained + weight stable | Power trend + TSS trend + weight |
| Illness frequency > 1x per 6-8 weeks | Calendar annotations |
| Athlete requests rest week mid-block | Direct request — ALWAYS grant |
| Recovery time progressively increasing | RPE recovery, HRV trends |
| Male: low libido/erections; Female: irregular/absent cycle | Self-report — RED-S screen |
| Rest period >2-3 weeks to restore baseline | Non-functional overreaching or RED-S |

### AMBER FLAGS (Monitor Closely)
| Signal | Detection |
|--------|-----------|
| Weight-stable + cold extremities, low energy, disturbed sleep | Subjective feedback |
| Intensity black hole: most rides IF 0.65-0.80 | IF distribution |
| Weight loss during high-intensity block | Block type + deficit detection |
| Boom-bust CTL pattern | CTL time series |
| RPE at constant power trending up 2+ weeks | RPE:power tracking |
| HRV sustained depression >7 days | HRV trends |
| "Radio silence" — no workout comments | Comment frequency |
| Endurance rides consistently IF > 0.70 | IF audit |

### Energy Availability Thresholds (Persp-36)
- **EA >= 45 kcal/kg FFM/day**: optimal function (female athletes)
- **EA 30-45 kcal/kg FFM/day**: gray zone — negative effects begin
- **EA < 30 kcal/kg FFM/day**: RED FLAG — significant risk
- **Male thresholds**: not yet established; use libido/erection quality as proxy
- **Diet duration limit**: no longer than ~8 weeks, max 6-8 lbs per cycle
```
