# Empirical Cycling Podcast — Master Reference

Consolidated from 53 episodes (TMT 42-73, Perspectives 36-41, Watts Doc 51-62, Community Notes, 1M AMA). This is the definitive reference document for the platform.

Evidence levels: **[R]** = Research-backed, **[E]** = Experience-based, **[O]** = Opinion.

---

## 1. FTP & Testing

### Key Principles

- **FTP = MLSS (Maximal Lactate Steady State)** — sustainable for 30-70 minutes depending on the athlete; not specifically "1-hour power" [R]
- **FTP stagnation does NOT mean fitness stagnation** — race results can improve substantially even with flat/declining FTP through durability, repeatability, race craft, and specificity improvements (TMT-70) [E]
- **Rolling PD curves from training data are more reliable than isolated test days** — single tests have ~2% power meter error making 5W changes meaningless (WD-62) [R]
- **Ramp test improvements may reflect W' (anaerobic capacity), not VO2max** — decompose PD curve changes into CP vs W' contributions (WD-55) [R]
- **FTP training alone hits a ceiling** — VO2max work needed to raise it further; VO2max "raises the roof" for FTP to grow into (TMT-60) [E]
- **TTE (Time to Exhaustion) stagnation at FTP signals need for VO2max work**, not more threshold training (TMT-60) [E]
- **Maximum useful TTE: ~60-75 minutes** — beyond this, opportunity cost too high; shift to raising FTP itself (TMT-60) [E]

### Specific Numbers & Thresholds

| Metric | Value | Source |
|--------|-------|--------|
| FTP test frequency | Every 3-4 months max | TMT-66 [E] |
| Power meter error | ~2% (300W = 294-306W) | WD-62 [R] |
| Meaningful FTP change | >6W (>2%) | WD-62 [R] |
| TTE typical trained range | 40-55 minutes | WKO5 [R] |
| Max useful TTE | 60-75 minutes | TMT-60 [E] |
| FTP interval progression | 4x10 -> 3x15 -> 2x20 -> 2x25 -> 1x40+ | TMT-45, 60 [E] |
| Optimal threshold interval format | 3x20 or 2x30 min at FTP | TMT-60 [E] |
| VO2max block trigger | FTP unchanged after threshold block + rest + retest | TMT-60 [E] |

### Common Mistakes

1. **Over-testing** — using formal tests instead of progressive workout performance as fitness indicator (TMT-66) [E]
2. **Insufficient rest before testing** — need 3-5 days easy; most common testing error (TMT-66) [E]
3. **Erg mode hiding true readiness** — free-ride mode reveals daily capacity; wean off erg for key sessions (TMT-73) [E]
4. **Mono-metrically focusing on FTP** — race results, not FTP, are the ultimate metric (TMT-70) [E]
5. **Forcing power up instead of extending duration** — threshold intervals should progress in duration, not power (TMT-45) [E]
6. **Switching power meters and expecting continuity** — single to dual sided can show zero FTP gain even with massive improvement (TMT-70) [E]

### Platform Module: `pdcurve.py`, `training_load.py`

- `rolling_ftp()` for continuous monitoring instead of isolated tests
- Decompose PD changes into CP vs W' contributions
- FTP growth curve modeling with log-transformed time

---

## 2. Training Zones & Intensity Distribution

### Key Principles

- **No single training intensity distribution is statistically superior** — IPD meta-analysis (~350 athletes, 13 studies) found no meaningful overall difference (Persp-38) [R]
- **Individual variation (-20% to +30%) dwarfs distribution effects (~1-2%)** (Persp-38) [R]
- **"Zone 2 has nothing special about it"** — total volume matters more than sitting in a specific zone (TMT-69) [E]
- **No physiological switch at zone boundaries** — adaptations are a continuum; excursions out of zone do NOT "ruin" a ride (TMT-69) [R]
- **LT1 varies from 45-85% FTP** — far wider than most zone models assume (TMT-69) [E]
- **LT1 rises best from lots of hours WELL UNDER it**, not training at LT1 specifically (TMT-73) [E]
- **"All roads lead to PGC-1alpha"** — tempo, sweet spot, threshold all stimulate mitochondrial biogenesis similarly (TMT-54) [R]
- **Training in zones (ranges) rather than exact watts** is appropriate because underlying physiology operates in ranges (TMT-46) [R]

### Specific Numbers & Thresholds

| Zone Parameter | Value | Source |
|---------------|-------|--------|
| Endurance ride IF target | 0.50-0.65 | TMT-69 [E] |
| Recovery ride IF target | < 0.30 | TMT-69 [E] |
| Endurance RPE | 1-3/10 | TMT-69 [E] |
| Hill excursion cap (endurance) | < 75% FTP | TMT-69 [E] |
| Sweet spot target | ~88-93% FTP | TMT-44 [E] |
| Sweet spot TTE (untrained) | 40-60 min | TMT-44 [E] |
| Sweet spot TTE (trained) | 90-120 min | TMT-44 [E] |
| Sweet spot TTE (elite) | 180+ min | TMT-44 [E] |
| Threshold RPE | ~8/10 | TMT-49 [E] |
| VO2max RPE | ~9-9.5/10 | TMT-49 [E] |
| IF floor red flag | > 0.70-0.75 | TMT-68, 69 [E] |
| Intensity black hole | IF 0.65-0.80 on most rides | TMT-58 [E] |
| "Fat burning zone" | NOT a meaningful training zone | TMT-50 [R] |

### Common Mistakes

1. **Riding endurance too hard** (IF 0.70-0.75) — the #1 most common amateur error, identified across every coaching episode [E]
2. **Confusing rising endurance pace with LT1 improvement** — usually just pushing endurance rides harder (TMT-69) [E]
3. **"High Zone 2"** generates significantly more fatigue than "low Zone 2," compromising interval quality (TMT-48) [E]
4. **Over-prescribing zone precision** — RPE is the gold standard for internal load (TMT-68) [E]
5. **Treating zone boundaries as physiological switches** — they are descriptive landmarks, not prescriptive thresholds (TMT-69) [R]

### Platform Module: `zones.py`

- Support multiple zone models (3-zone physiological + 5-7 zone power)
- Sweet spot band definition and TTE tracking
- Endurance IF validation
- RPE targets per zone

---

## 3. Durability & Fatigue

### Key Principles

- **Durability is not a new concept, just newly formalized** — coaches have measured post-kJ power since power meters existed (WD-60) [E]
- **kJ/kg is the standard metric** — use bins of 10 kJ/kg; raw kJ is misleading across body weights (WD-60, van Erp 2021) [R]
- **You need sufficient power to begin with** — better cyclists start with more power AND lose less (WD-60) [R]
- **Total time riding is the best predictor of durability** — not specific "durability workouts" (WD-60) [E]
- **Aerobic and anaerobic are NOT zero-sum** — both can improve simultaneously; heavy lifting does NOT hurt durability long-term (WD-60) [E]
- **The durability literature is weaker than media interpretations suggest** — still in definitional squabbling phase (WD-60) [E]
- **Goodhart's Law warning** — over-indexing on durability can lead to bad race strategies (spending less energy, only doing long easy rides, weight manipulation) (WD-60) [E]
- **Fueling is a dangling confounder** in all field durability data — cannot be controlled, has massive effect (WD-60) [E]
- **TTE extension is tied to better fueling** — can't extend TTE without adequate carbs (TMT-73) [E]

### Specific Numbers & Thresholds

| Benchmark | Power Drop at 50 kJ/kg | Source |
|-----------|----------------------|--------|
| Elite pro | < 2% | WD-60 [E] |
| Strong amateur | 2-10% | WD-60 [E] |
| Good amateur | 10-20% | WD-60 [E] |
| Average amateur | 20-40% | WD-60 [E] |

**van Erp World Tour data:**
| Category | Start Power | Drop at 50 kJ/kg |
|----------|------------|------------------|
| Successful sprinters | 18.25 W/kg 10s | ~8% |
| Less successful sprinters | 17.7 W/kg 10s | ~18% |
| Successful climbers | 6.28 W/kg 20min | ~4% |
| Less successful climbers | 5.99 W/kg 20min | ~9% |

### Measurement Caveats (Critical for Implementation)

1. **Fresh baseline often missing** — best effort after 20 kJ/kg becomes misleading "0% loss" baseline [E]
2. **Pre-effort intensity matters enormously** — endurance preload vs race preload produce very different results [E]
3. **Body weight scaling** — 2000 kJ is huge for 55kg woman, warmup for 75kg pro [E]
4. **Anaerobic capacity confounds lab protocols** — large W' athletes coast at 105-108% threshold while small W' athletes are near max [E]
5. **Nutrition as confounder** — cannot control in field data, massive effect [E]
6. **Environment** — heat, cold, altitude, wind all affect measurements [E]

### Common Mistakes

1. **Treating durability as "the missing piece"** — need sufficient absolute power first (WD-60) [E]
2. **Using raw kJ instead of kJ/kg** — distorts cross-athlete comparisons [R]
3. **No fresh baseline** — all durability metrics become meaningless [E]
4. **Ignoring pre-effort context** — same kJ from endurance vs racing is completely different [E]
5. **Low-carb training for durability** — explicitly dismissed by Kolie Moore: "I checked my list... there is nothing here" (WD-60) [E]
6. **Strength training hurts durability** — no long-term negative impact (WD-60) [E]

### Platform Module: `durability.py`

- Use kJ/kg bins of 10 as standard unit
- Flag stale/missing fresh baselines
- Track pre-effort intensity distribution
- Show durability alongside absolute power always
- Fueling confound warning when degradation is steep

---

## 4. Nutrition & Fueling

### Key Principles

- **Fueling on the bike is the #1 thing coaches wish they knew earlier** — old 25g/hr paradigm was destructive (TMT-73) [E]
- **60-90g/hr carbs is the modern standard** — up to 120g/hr for elite with trained guts (Persp-41, TMT-73) [R]
- **Carb absorption is individual** — ranges from 50-150g/hr; lab test with 13C tracer can personalize (Persp-41) [R]
- **Body is a good energy accountant, not a substrate accountant** — total energy balance > substrate tracking (Persp-41, TMT-50) [R]
- **Higher on-bike carbs is not always better** — 120g/hr can impair next-day readiness if recovery carb budget is squeezed (Persp-41) [R]
- **On-bike fueling does NOT spare muscle glycogen, only liver glycogen** — confirmed by Podlogar (Persp-41) [R]
- **Delayed post-exercise carbs impair next-day performance by ~30%** even when 24hr glycogen levels equalize (WD-59, ES=2.03) [R]
- **Within-day energy deficits matter even at equal 24hr totals** — hourly deficits trigger cortisol, suppress RMR (WD-59, Persp-36) [R]
- **"Train low" is a molecular dead end for performance** — AMPK mechanism is real but performance evidence consistently negative (WD-54) [R]
- **Energy estimation is guesswork** — ~900 kcal swing from efficiency assumptions; labels 20% error; absorption 85-95% (Persp-41) [R]
- **Eating enough on bike often leads to weight loss** because it prevents post-ride overeating and energy compensation (TMT-73) [E]
- **Coaching cue: "feel the same as when you left"** = properly fueled ride (TMT-73) [E]

### Specific Numbers & Thresholds

| Parameter | Value | Source |
|-----------|-------|--------|
| On-bike carbs (standard) | 60-90 g/hr | TMT-73, Persp-41 [R] |
| On-bike carbs (elite) | 90-120+ g/hr | Persp-41 [R] |
| Liver glycogen sparing threshold | > 67 g/hr | Persp-41 [R] |
| Post-exercise repletion rate | 1.2 g/kg/hr for 4-5 hrs | Persp-41 [R] |
| Glycogen supercompensation | 10-12 g/kg carbs day before | Persp-41 [R] |
| Protein target | 2-2.5 g/kg/day total BW | Persp-41 [R] |
| Fat minimum | 0.8 g/kg/day | Persp-41 [E] |
| Max sustainable metabolic scope | 2.5x BMR (3x elite) | Persp-40 [R] |
| Electrolytes during exercise <4h | Not required | Persp-41 [R] |
| Calibration period for energy estimates | 4-8 weeks | Persp-41 [E] |
| TDEE off-bike multiplier (active athletes) | 1.6-2.3x predicted BMR | TMT-50 [R] |
| Energy compensation factor | ~30% at moderate exercise levels | Persp-40 [R] |
| Max safe diet duration | ~8 weeks per cycle | Persp-36 [E] |

### Creatine Summary (WD-58)

| Effect | Evidence | Magnitude |
|--------|----------|-----------|
| Aerobic/endurance performance | Zero effect | ES -0.07, N=277 [R] |
| Repeated sprint mean power | Small positive | ES 0.61, ~27W on 1000W [R] |
| Body mass gain (water) | Largest reliable effect | ES 0.79, 0.8-1.0 kg [R] |
| Cognitive (sleep-deprived) | Preliminary | 1-2 sec/question at 4am [R] |

**Platform stance:** Creatine irrelevant to endurance performance modeling. Do not factor into power predictions.

### Common Mistakes

1. **Not eating early enough** — start at km 0, not when hungry [E]
2. **"Replace the carbs you burned"** — must replace total energy, not just carb substrate (TMT-50) [R]
3. **Creating acute energy deficit for weight loss on training days** — sets up binge patterns (TMT-69) [E]
4. **Trusting energy estimation precision** — display confidence intervals, not point estimates (Persp-41) [R]
5. **Sweat tests for electrolyte prescription** — nearly useless; composition changes daily (Persp-41) [R]
6. **"Glycogen window is a myth"** — overcorrection; the window IS real for performance, not glycogen quantity (WD-59) [R]
7. **Stacking calorie deficit on hard training days** — fuel on-bike, create deficit elsewhere (Persp-36) [E]
8. **Believing "train low" improves performance** — molecular mechanism exists but performance evidence is negative (WD-54) [R]

### Platform Module: `nutrition.py`

- Update default baseline_intake_g_hr to 75 (midpoint of 60-90 range)
- Add absorption ceiling check
- Add glycogen budget with recovery timing model
- Add energy estimation confidence intervals
- Model on-bike vs off-bike carb distribution

---

## 5. Recovery & Overtraining

### Key Principles

- **Performance plateaus are a dynamic equilibrium between stimulus and recovery** — inverted U: beyond recovery capacity = regression (TMT-72) [E]
- **Low-volume athletes CAN be recovery-limited, not just stimulus-limited** — life stress limits recovery more than training volume (TMT-72) [E]
- **Holiday recovery >> normal-life recovery** — reduced work stress, better sleep, better eating (TMT-72) [E]
- **CTL/TSS chasing is counterproductive** — athletes who doubled down on TSS when performance declined; resting fixed everything (TMT-72) [E]
- **CTL going up while performance goes down = classic over-reaching signal**, not a sign to train harder (TMT-72) [E]
- **TSB/Form is widely misinterpreted** — positive TSB does NOT mean peaked; "best way to make TSB positive is to get sick" (TMT-68) [E]
- **The body has ONE pool for ALL stress** — training + work + family + sleep debt (allostasis, McEwen) (TMT-48) [R]
- **High work stress doubles recovery cost** when combined with hard training (TMT-57) [E]
- **Fear of rest = signal rest is needed** — athletes most afraid to rest typically need it most (TMT-58) [E]
- **"I perform well fatigued" belief: almost always false** — operating at 80-90% without realizing it (TMT-58) [E]
- **Sprint PRs after time off are common** — don't chase more sprint training if sprint is down late-season (TMT-72) [E]
- **After a layoff, athletes rejoin their long-term growth curve within weeks** (WD-61) [R+E]
- **2 weeks off the bike is NOT the end of the world** — 10+ days for measurable detraining (TMT-55, WD-61) [E]
- **Motivation is a physiological signal, not a character flaw** (TMT-48) [E]
- **No ice bath, theragun, or supplement measurably speeds recovery** — consistency of basic habits (sleep, nutrition, stress) is the single most important factor (TMT-52) [E]
- **100% plan compliance is a warning sign**, not a badge of honor — indicates lack of auto-regulation (TMT-52) [E]

### Specific Numbers & Thresholds

| Parameter | Value | Source |
|-----------|-------|--------|
| Rest week: VO2max/threshold+ blocks | Every 2-3 weeks | TMT-55 [E] |
| Rest week: base/endurance blocks | Every 3-5 weeks | TMT-55 [E] |
| Rest week minimum duration | 4-5 days; 7+ after VO2max | TMT-55 [E] |
| Rest week minimum activity | >25% normal volume, genuinely easy | TMT-58 [E] |
| Rest week ride IF | < 0.50 | TMT-55 [E] |
| Days off before detraining | ~10 days | TMT-55 [E] |
| Mid-season break recovery | 1 week off = ~2-3 weeks to return | TMT-43 [E] |
| Non-functional overreaching exit | 2 weeks to 3 months | TMT-58 [E] |
| Severe overtraining recovery | 2-3 months off before productive training | TMT-58 [E] |
| Indoor training recovery multiplier | 1.1-1.2x outdoor TSS | TMT-51 [E] |
| Hard workout success rate target | >= 90% | TMT-69 [E] |
| Illness frequency red flag | > 1x per 6-8 weeks | TMT-55 [E] |
| Performance test staleness | >90 days = flag zones as stale | TMT-51 [E] |

### Reactive Rest Triggers (any one sufficient)

1. Performance regression despite maintained training load
2. Persistent low motivation (most reliable single indicator)
3. Illness
4. Failed mid-block workout + failed retest 2-3 days later
5. Athlete requests rest week — **ALWAYS grant it, 100% of the time** (TMT-55) [E]

### Subjective Metrics to Track

- Motivation to train (most reliable single indicator)
- Mood/irritability ("ask your partner")
- Sleep quality
- RPE drift at constant power
- Dissociated RPE: legs vs lungs
- Brain fog
- "Radio silence" (no workout comments) = probable motivational collapse

### Common Mistakes

1. **More training when performance declines** — rest is usually the answer, not more stimulus (TMT-72) [E]
2. **Treating CTL as "fitness"** — specifically objected to by Kolie Moore (TMT-68) [E]
3. **Getting up earlier to train** — literally cuts into recovery (TMT-72) [E]
4. **Time-crunched athlete doing more intervals** — may need more rest, not more intervals (TMT-72) [E]
5. **Using HRV for workout prescription** — useful only for illness detection and during high-stress VO2max blocks; trends over 3-7 days, not single readings (TMT-51) [E]
6. **Trusting "I feel fine" in Type-A athletes** — when performance data shows regression, data wins over feelings (TMT-55) [E]
7. **Boom-bust CTL pattern** — rapid ramp + crash, repeated annually; produces same annual training with more misery (TMT-48) [E]

### Platform Module: `clinical.py`, `training_load.py`

- Rest-week recommendation engine with intensity-weighted block duration triggers
- Performance vs subjective conflict detector
- IF floor diagnostic
- Intensity black hole detection
- Indoor training TSS multiplier
- Allostatic load model integrating life stress proxies

---

## 6. Periodization & Block Design

### Key Principles

- **The simplest effective plan: 2 hard days + fill remaining time with endurance** — 1 threshold day + 1 VO2max day + endurance fill (TMT-45) [E]
- **Progressive overload before protocol change** — exhaust simple duration/volume progression before switching protocols (TMT-44, 45, 52, 60) [E]
- **Sweet spot is a tool, not a philosophy** — becomes time-inefficient as fitness improves; well-trained athletes need 2+ hour sessions for equivalent stimulus (TMT-44) [E]
- **Sporadic VO2max dosing can work** — 3 sessions month 1, 6 month 2 alongside other training (TMT-60) [E]
- **Training plans are "written in sand"** — flexibility is essential, not optional (TMT-73) [E]
- **Panic training almost always backfires** — too much intensity too soon leads to fatigue, not fitness (TMT-71) [E]
- **Off-season breaks are essential** — 1-2 weeks minimal/no riding, then slow re-entry (TMT-43) [E]
- **Sprint training has low opportunity cost** — short sprints year-round costs almost nothing in fatigue (TMT-45, 64) [E]
- **Weight loss should NEVER coincide with high-intensity blocks** (TMT-48, 52) [E]
- **In-season FTP maintenance: 1 threshold/sweet spot session every 1-2 weeks** at RPE 6-7/10 (TMT-60) [E]
- **Consistency beats optimization** — boom-bust cycle produces same annual training with more misery (TMT-48) [E]

### Specific Numbers & Thresholds

| Parameter | Value | Source |
|-----------|-------|--------|
| Minimum viable plan | 2 hard days + endurance fill | TMT-45 [E] |
| VO2max minimum dose | 1 session/week | TMT-45 [E] |
| Threshold progression | 4x10 -> 3x15 -> 2x20 -> 1x40+ | TMT-45, 60 [E] |
| VO2max interval time | ~20 min total; formats 8x3, 5x5, 3x8 all viable | WD-55 [E] |
| Sprint add-on | 3-5 x 10-15 sec at start of endurance rides | TMT-45 [E] |
| Over-under protocol | 90%/105% FTP alternating | TMT-44 [E] |
| In-season maintenance | 1 session/1-2 weeks, RPE 6-7/10 | TMT-60 [E] |
| Off-season break | 1-2 weeks minimal riding | TMT-43 [E] |
| Gym: off-season build | 2-3x/week heavy, low reps | WD-56, TMT-42 [R] |
| Gym: in-season maintain | 1x/week heavy singles RPE 7/10 | TMT-42, WD-56 [R] |
| Iron panel correction time | 3-4+ months | TMT-64 [E] |
| New training experiment | 2-month proof of concept with build + taper | TMT-64 [E] |

### FTP Training Decision Tree (TMT-60)

1. **Branch 1 — Season point:**
   - Early = extend duration (threshold focus)
   - Late = introduce VO2max if plateaued
2. **Branch 2 — Training age:**
   - Novice = duration progression first
   - Experienced = auto-regulate
3. **Branch 3 — Opportunity cost:**
   - When FTP plateaus, invest elsewhere (durability, sprint, race skills)

### Anti-Panic Protocol (TMT-71)

If behind schedule:
- **8+ weeks to event:** Add volume first for 3-4 weeks, THEN start intensity progression
- **<4 weeks to event:** Pivot goals (finish, enjoy, treat as training race)
- **NEVER:** Double intensity immediately to "catch up"

### Common Mistakes

1. **Changing protocols too often** — most athletes never fully capture adaptation from one approach (TMT-52) [E]
2. **Panic training** — sudden intensity spikes after low-load periods (TMT-71) [E]
3. **Neglecting sprint training** — low opportunity cost, applicable to all disciplines (TMT-64) [E]
4. **100% plan compliance** — indicates lack of auto-regulation (TMT-52) [E]
5. **Rigid adherence to specific interval structures** — small variations (5x5 vs 4x8) are effectively equivalent (TMT-46) [R]
6. **Training on only one bike** — must practice on TT/MTB/CX bike for specificity (TMT-70) [E]

### Platform Module: `blocks.py` (referenced but not modified)

- Progressive overload tracking with "try longer before trying different"
- Rest week scheduling by block intensity type
- Anti-panic protocol with calendar-aware recommendations
- FTP decision tree implementation

---

## 7. Strength Training

### Key Principles

- **Strength is a skill (neural drive)** — neural adaptations can be maintained with very low volume (TMT-42) [R]
- **Heavy singles produce strength gains with minimal body weight change** — back-off sets and AMRAPs produce more hypertrophy (WD-56) [R]
- **Cyclists are already somewhat protected from hypertrophy** due to AMPK pathway interference with mTOR from high aerobic volume (WD-56) [R]
- **Caloric surplus is required for significant hypertrophy** — cyclists in energy balance are unlikely to gain meaningful mass (WD-56) [R]
- **Cyclists over 35-40: strength training is essential for health** even if bike performance isn't the primary goal (TMT-73) [E]
- **Strength training can unlock 1-min power PRs** especially for riders who rarely train >120% FTP (TMT-70) [E]
- **Aerobic and anaerobic are NOT zero-sum** — heavy lifting does NOT hurt durability long-term (WD-60) [E]

### Specific Protocols

| Phase | Protocol | Source |
|-------|----------|--------|
| Off-season build | 2-3x/week, 1-3 heavy singles at RPE 9-9.5 | WD-56 [R] |
| In-season maintain | 1x/week, 3 heavy singles at RPE 7/10 | TMT-42 [R] |
| Strength without mass | Avoid back-off sets, AMRAPs; keep reps 1-3 | WD-56 [R] |
| Limited equipment | Single-leg elevated heel squats + slow eccentrics | TMT-47 [E] |
| If weight increases | Reduce volume (sets) before reducing intensity (load) | WD-56 [R] |

### Common Mistakes

1. **Confusing strength maintenance with hypertrophy** — low reps/heavy vs moderate reps/moderate weight (TMT-42) [R]
2. **Exclusively unilateral work** — mix in bilateral when possible (TMT-47) [E]
3. **High-rep AMRAPs for cyclists** — increasingly aerobic at higher reps, taxing differently (TMT-47) [R]
4. **Skipping gym work after 35** — health benefits independent of performance (TMT-73) [E]

---

## 8. Psychology & Motivation

### Key Principles

- **ACT framework: thoughts and emotions are indicators, not commands** — assess "workability" (Persp-37) [R]
- **Pre-race anxiety is normal and often not actionable** — workability depends on timing (Persp-37) [E]
- **Psychological flexibility = knowing which signals to act on vs let pass** (Persp-37) [R]
- **Fear of losing identity if performance drops is a major barrier** (Persp-37) [E]
- **Motivation is a physiological signal, not a character flaw** (TMT-48) [E]
- **Comparison is the thief of joy** — social media comparisons are pure selection bias (TMT-65) [E]
- **Loss of motivation after bad season/injury is normal** — forced goals lead to worse outcomes (TMT-56) [E]
- **"Periodize fun"** — mental health rides have tangible training value (TMT-54) [E]
- **"Fatigue security blanket"** — athletes mistake chronic fatigue for productive training (TMT-69) [E]

### Actionable Guidelines

- **Before a race:** "Is this thought workable right now?" 3 weeks out = act on it. 1 minute before = let it pass (Persp-37)
- **Practice "dropping the rope"** in tug-of-war with unhelpful thoughts (Persp-37)
- **If training has collapsed:** pivot event goals from "race" to "experience/finish" (TMT-56)
- **Some riding > no riding** for both physical and mental health maintenance (TMT-56)
- **Process goals in racing** (learn leadouts, contest preems) > outcome goals for skill development (TMT-73)
- **Don't crack yourself mentally in off-season** — burnout before season starts is real (TMT-64) [E]

### Common Mistakes

1. **Sunk-cost fallacy around accumulated TSS** — athletes resist riding easier (TMT-69) [E]
2. **Social media comparison** — nobody posts bad workouts (TMT-65) [E]
3. **Forcing high-intensity when motivation is low** — ride at whatever feels good (TMT-56) [E]
4. **Type-A self-deception about fatigue** — external accountability needed (TMT-55) [E]

### Platform Module: `clinical.py`, `gap_analysis.py`

- Psychological limiters alongside physiological ones in gap analysis
- Motivational decline as clinical amber flag
- "Radio silence" (no workout comments) detection

---

## 9. Clinical Red Flags

### Key Principles

- **RED-S and overtraining syndrome have near-complete overlap** — "almost just a circle" Venn diagram (Persp-36, Stellingwerff) [R]
- **Athletes can be in chronic LEA without being underweight** — metabolic adaptation masks the deficit (Persp-36) [R]
- **Energy Availability (EA) below 30 kcal/kg FFM/day causes significant health consequences** (Persp-36) [R]
- **Bone damage from LEA in adolescence is largely irreversible** (Persp-36) [R]
- **Hormonal contraception masks amenorrhea**, preventing early RED-S detection (Persp-36) [R]
- **Weight-stable athletes can experience significant energy compensation** — low T3, amenorrhea, reduced NEAT (Persp-40) [R]
- **Constrained Energy Model: TDEE does NOT scale linearly with activity** — ~2.5x BMR is the long-term ceiling (Persp-40) [R]
- **FLIA (iliac artery flow limitation) is underdiagnosed** — severe unilateral leg pain at high intensity ONLY; requires provocative test (Persp-38) [R]
- **One stress fracture strongly predicts subsequent stress fractures** at increasing rates (Persp-36) [R]

### RED FLAGS (Immediate Intervention)

| Signal | Detection Method | Source |
|--------|-----------------|--------|
| Performance declining + training load maintained + weight stable | Power + TSS + weight trends | Persp-36 [R] |
| Illness frequency > 1x per 6-8 weeks | Calendar annotations | TMT-55 [E] |
| Athlete requests rest week mid-block | Direct request — ALWAYS grant | TMT-55 [E] |
| Recovery time progressively increasing | RPE recovery, HRV trends | TMT-55 [E] |
| Male: low libido/erections | Self-report — suppressed testosterone | Persp-36 [R] |
| Female: irregular/absent menstrual cycle | Self-report — RED-S screen | Persp-36 [R] |
| Rest >2-3 weeks to restore baseline | Non-functional overreaching or RED-S | TMT-58 [E] |
| Power-HR inversion (HR rising, power dropping) | Ride data analysis | clinical.py [E] |
| HR decoupling >10% at moderate intensity | Ride data analysis | clinical.py [E] |

### AMBER FLAGS (Monitor Closely)

| Signal | Detection Method | Source |
|--------|-----------------|--------|
| Weight-stable + cold extremities, low energy, disturbed sleep | Subjective feedback | Persp-40 [R] |
| Intensity black hole: most rides IF 0.65-0.80 | IF distribution | TMT-58 [E] |
| Weight loss during high-intensity block | Block type + deficit | TMT-48 [E] |
| Boom-bust CTL pattern | CTL time series | TMT-48 [E] |
| RPE at constant power trending up 2+ weeks | RPE:power tracking | TMT-51 [E] |
| HRV sustained depression >7 days | HRV trends | TMT-51 [E] |
| "Radio silence" — no workout comments | Comment frequency | TMT-55 [E] |
| Endurance rides consistently IF > 0.70 | IF audit | TMT-69 [E] |
| Panic training: sudden intensity spike after low-load | CTL ramp rate | TMT-71 [E] |

### Energy Availability Thresholds

| Threshold | Value | Significance |
|-----------|-------|-------------|
| Optimal (female) | >= 45 kcal/kg FFM/day | Full hormonal function |
| Gray zone | 30-45 kcal/kg FFM/day | Negative effects begin |
| Critical | < 30 kcal/kg FFM/day | Amenorrhea, stress fractures |
| Male thresholds | Not established | Use libido/erection quality as proxy |

### Recovery from Chronic LEA

- Menstrual cycle resumption: 3-12+ months (Persp-36) [R]
- Best predictor of weight regain: amount of fat-free mass lost (Persp-40) [R]
- "Reverse dieting" signal: adding 200 kcal/day doesn't cause weight gain but restores hormonal markers = was in compensated LEA (Persp-40) [E]

### Cramping (TMT-59)

- EAMC driven by duration + intensity + novelty, not just electrolytes [R]
- Neural fatigue theory stronger than electrolyte depletion theory [R]
- First high-intensity race of season often triggers cramps from lack of race-specific conditioning [E]
- Heat compounds cramping risk independently of hydration [R]

### Platform Module: `clinical.py`

- IF floor diagnostic (>0.70)
- RED-S screening from training data patterns
- Within-day energy deficit tracking
- Panic training detection
- Intensity black hole detection
- All integrated into `get_clinical_flags()`

---

## 10. Diminishing Returns & Growth Curves

### Key Principles

- **Diminishing returns follow a logarithmic growth curve** — log-transformed time yields linear fit (WD-61) [R]
- **~25% improvement over baseline is common long-term ceiling** (WD-61) [E]
- **Early growth curve stimuli are non-specific** — sprint and threshold both raise VO2max early; cross-stimulation disappears with training maturity (WD-61) [R]
- **Changing intervention rate of early growth != changing the asymptote** — faster protocols may get to plateau sooner, not a higher plateau (WD-61) [O]
- **You cannot stack gains from multiple studies** — arrow-gains fallacy (WD-61, TMT-68) [E]
- **Genetic plateau is a diagnosis of exclusion** — rule out recovery, nutrition, sleep, life stress first (WD-61) [E]
- **Study results from early growth curve may not transfer to well-trained athletes** — 0.1%/week improvement at far right of curve is nearly impossible to detect (WD-61) [R]

### Expected Improvement Rates

| Training Year | Expected FTP Gain | Source |
|--------------|-------------------|--------|
| Year 1 | 30-50W | WD-61, TMT-52 [E] |
| Year 2-3 | 10-30W | TMT-52 [E] |
| Year 4+ | 5-10W | WD-61 [E] |
| Well-trained plateau | 0-5W (mostly TTE) | WD-61 [E] |
| Post-layoff return | 2-4 weeks to recent levels | WD-61 [E+R] |
| 3-month return from couch | Previous year's best FTP | WD-61 [E] |

### Platform Module: `training_load.py`

- FTP growth curve modeling with log-transform
- Expected improvement rate based on training age
- Plateau detection and VO2max block trigger

---

## 11. Science & Physiology (Reference)

### Newbie Gains Are Central (WD-53)

- Phlebotomy erased VO2peak improvements back to baseline despite 40% mitochondrial gains [R]
- Strongest predictors: cardiac output, blood volume, hemoglobin (R ~0.8)
- Blood volume super-compensation does NOT work in trained athletes — cardiac function is the limiter [R]

### HIF-1alpha Is Suppressed in Elites (WD-52)

- PHD2: 2.6x higher in elite vs moderate; FIH: 3.5x; Sirtuin 6: 5x [R]
- Capillary density hits a ceiling in well-trained athletes [R]
- FTP work eventually stops raising VO2max — model plateau detection [R]

### Phenotype != Performance (WD-51)

- HIF knockout mice had "trained" phenotype but untrained performance [R]
- PD curve is integrated output — avoid over-decomposing into single mechanisms [R]

### VO2max Training (WD-55)

- No single "right" method — different methods are tools in a toolbox [E]
- "VO2max power" is not a fixed number — achievable at a range of powers [R]
- High-cadence (100-120 RPM) intervals cause less muscular fatigue [R+E]
- Hickson protocol = largest published improvement (25%) but brutal — immune suppression, iron depletion [R]
- Evenly paced efforts are fine, possibly preferable to "start hard" [E]

### 30/15 Study Reanalysis (WD-55)

- Abstract states "no group difference in change of VO2max" (p = 0.49) [R]
- Performance gains most parsimoniously explained by W' improvement, not VO2max [R]
- CX racing (massive intermittent effort dose) never improves VO2max in trained athletes [E]

### AMPK-Glycogen Interaction (WD-54)

- AMPK beta subunit has glycogen-binding domain [R]
- High glycogen suppresses AMPK (not: low glycogen activates) [R]
- Mechanism does NOT validate "train low" interventions for performance [R]

### Constrained Energy Model (Persp-40)

- TDEE does NOT scale linearly with activity — ceiling ~2.5x BMR long-term [R]
- Energy compensation: BMR reduction + NEAT reduction are primary culprits [R]
- Rest-day expenditure was 3x BMR after ultra-running (small study, n=2) [R]
- Wearable calorie estimates are unreliable [R]

---

## Conflicts with Conventional Wisdom (Consolidated)

| Claim | EC Position | Evidence |
|-------|-------------|---------|
| "Zone 2 is special" | Total volume matters more than zone specificity | TMT-69 [E] |
| "Fat burning zone for weight loss" | Total caloric balance is what matters | TMT-50 [R] |
| "Higher endurance power = better stimulus" | 6hr at 150W beats failed 5hr at 200W | TMT-69 [E] |
| "Endurance kills sprint power" | Speed loss comes from riding endurance too hard, not volume | TMT-64 [E] |
| "30/15s are best VO2max training" | No VO2max superiority; gains likely W' | WD-55 [R] |
| "Durability is the missing piece" | Need sufficient absolute power first | WD-60 [E] |
| "More mitochondria = better performance" | 40% increase did NOT correlate with VO2peak | WD-53 [R] |
| "Aerobic and anaerobic are zero-sum" | Both can improve simultaneously | WD-60 [E] |
| "Low-carb training improves durability" | Explicitly dismissed; no evidence | WD-60 [E] |
| "Glycogen window is a myth" | Overcorrection; real for performance, not quantity | WD-59 [R] |
| "Replace the carbs you burned" | Replace total energy, not just substrate | TMT-50 [R] |
| "Creatine is a game-changer" | Zero aerobic effect; marginal sprint | WD-58 [R] |
| "Sweat tests guide electrolyte intake" | Too variable day-to-day; nearly useless | Persp-41 [R] |
| "More training always better for time-crunched" | May need more rest, not more intervals | TMT-72 [E] |
| "CTL = fitness" | Specifically objected to | TMT-68 [E] |
| "You must load creatine" | Not necessary; 3-5g/day reaches saturation | WD-58 [R] |
| "Women need more creatine" | Based on misreferenced MDPI paper | WD-58 [R] |
| "Study X shows 15% gains" | Cannot stack gains from multiple studies | WD-61 [E] |
| "Short-term protocol superiority = long-term superiority" | May only reflect rate, not asymptote | WD-61 [O] |
| "Train your weaknesses" | Must consider trainability, opportunity cost | TMT-64 [E] |
| "Train specifically at LT1" | LT1 rises from hours below it, not at it | TMT-73 [E] |

---

## Episode Index

| Episode | Topic | Key Module |
|---------|-------|------------|
| TMT-42 | Strength as a Skill | blocks, training_load |
| TMT-43 | Off-Season Breaks | blocks, training_load |
| TMT-44 | Sweet Spot | zones, blocks |
| TMT-45 | Simplest Training Plan | blocks |
| TMT-46 | Science Interpretation | zones, pdcurve |
| TMT-47 | Strength: Limited Equipment | blocks |
| TMT-48 | Avoiding Over-Optimization | training_load, clinical |
| TMT-49 | Proxies for Stimulus | training_load |
| TMT-50 | Fat/Carb Burning Myths | nutrition |
| TMT-51 | RPE, Workout Feedback | training_load, clinical |
| TMT-52 | Intermediate Mistakes | blocks, clinical |
| TMT-53 | Parenting and Training | training_load |
| TMT-54 | Junk Miles | training_load, durability |
| TMT-55 | Rest Weeks / Subjective Metrics | blocks, clinical |
| TMT-56 | Resetting Goals | clinical, gap_analysis |
| TMT-57 | Coaches Q&A: Stress | training_load, clinical |
| TMT-58 | Why Rest Is Scary | training_load, clinical |
| TMT-59 | Cramps | durability, clinical |
| TMT-60 | FTP Decision Tree | blocks, training_load |
| TMT-61 | Limiters, Low Volume, Rest | gap_analysis, blocks |
| TMT-64 | Off-Season Weaknesses | gap_analysis, clinical |
| TMT-65 | Experience != Volume | training_load, gap_analysis |
| TMT-66 | Best/Worst Training Habits | pdcurve, training_load |
| TMT-67 | Winter Training | blocks, durability |
| TMT-68 | Using Data in Coaching | training_load, zones |
| TMT-69 | Riding Easier | zones, training_load |
| TMT-70 | Fitness Beyond FTP | gap_analysis, durability |
| TMT-71 | Panic Training | blocks, gap_analysis |
| TMT-72 | Stimulus vs Recovery | training_load, clinical |
| TMT-73 | Things We Wish We Knew | nutrition, zones, training_load |
| Persp-36 | Chronic Underfueling (Carson) | clinical, nutrition |
| Persp-37 | Performance Psychology (Ryan) | clinical, gap_analysis |
| Persp-38 | TID, NIRS, FLIA (Arnold) | zones, blocks, clinical |
| Persp-39 | Balance (McKay) | durability, pacing |
| Persp-40 | Energy Expenditure (Trexler) | nutrition, clinical |
| Persp-41 | Macros/Timing (Podlogar) | nutrition |
| WD-51 | Performance vs Phenotype | pdcurve, gap_analysis |
| WD-52 | HIF Diminishing Returns | training_load, zones |
| WD-53 | Newbie Gains | training_load, pdcurve |
| WD-54 | Glycogen & AMPK | nutrition, training_load |
| WD-55 | VO2max Training + 30/15 | pdcurve, gap_analysis |
| WD-56 | Strength Without Weight | training_load, blocks |
| WD-58 | Creatine | nutrition |
| WD-59 | Glycogen Paradox | nutrition, durability |
| WD-60 | Durability Limitations | durability |
| WD-61 | Diminishing Returns | training_load |
| WD-62 | n=1 Experiments | pdcurve, training_load |
| CN TMT-50 | Fat/Carb Myths | nutrition |
| CN TMT-54 | Junk Miles | training_load, durability |
| CN TMT-55 | Rest Weeks | blocks, clinical |
| CN WD-54 | AMPK/Glycogen | nutrition |
| 1M AMA | Various | pdcurve, durability, training_load |
