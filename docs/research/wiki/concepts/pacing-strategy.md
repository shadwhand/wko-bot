# Pacing Strategy & Race Execution

Evidence levels: **[R]** = Research-backed, **[E]** = Experience-based, **[O]** = Opinion.

---

## 1. Even Pacing: The Default Strategy

### Core Principle

The single most reliable finding across endurance-sport research is that **even pacing produces faster finishing times than any other strategy** for events where the course and conditions are uniform. The mechanism is physiological: above-threshold efforts deplete anaerobic capacity (W'/FRC) at a rate disproportionate to the small time gains they produce, and the resulting degradation compounds over the remaining distance. [R]

- Variability in power output increases metabolic cost beyond what normalized power alone captures -- muscle recruitment patterns shift, lactate clearance degrades, and glycogen consumption accelerates [R]
- The cost of surges is asymmetric: 30 seconds at 120% FTP costs more total energy and more recovery time than 30 seconds saved at that speed warrants (TMT-60, WD-60) [E]
- **Variability Index (VI) is the primary diagnostic.** VI = NP / AP. Optimal VI for time trials and triathlon bike legs: <= 1.05 (Friel, Coggan). Pro Kona files consistently show VI of 1.01-1.05 [E]

### Specific Numbers

| Context | Optimal VI | Optimal IF Range | Source |
|---------|-----------|-----------------|--------|
| Time trial (< 1 hr) | <= 1.02 | 0.95-1.05 | Coggan [R] |
| Half-Ironman bike | <= 1.05 | 0.80-0.87 | Allen/Coggan, TP coaches [E] |
| Full Ironman bike (pro) | <= 1.05 | 0.76-0.82 | Kona power analyses [E] |
| Full Ironman bike (AG) | <= 1.05 | 0.60-0.72 | Kona AG data [E] |
| 100-mile MTB | <= 1.10 | 0.55-0.65 | Wallenfels [E] |
| 24-hour solo | <= 1.15 | 0.45-0.55 | Wilhelm (MTBCoach) [E] |

### Evidence: Pro Power Files

Craig Alexander's 2011 Kona win: NP 270W, IF 0.81, VI 1.05. Second-half watts only 10W below first half -- textbook even pacing. [E]

Lionel Sanders' 2016 IRONMAN Arizona record (7:44:29): NP 317W, AP 315W, VI 1.01, IF 0.79. "I tried to bike as evenly as possible throughout." [E]

Maik Twelsiek's fastest Kona bike split (2015): IF 0.80, VI 1.04. "These are the numbers we consistently see from successful pro male athletes." [E]

Anna-Leeza Hull's junior world TT bronze: VI 1.02 over a 15km course -- even at junior level, minimal variability correlates with medal performance. [E]

### Common Mistakes

1. **"Banking time"** -- going out fast to build a cushion. Universally condemned by coaching literature. Jeff Vicario (TP): an athlete who habitually banked 20-30 sec/mile in marathons experienced late cramping and never PR'd until switching to conservative starts with negative-split progression. [E]
2. **Chasing other riders' pace** -- Chris Thomas (40 half-Ironmans): "My effort on race day is dictated by triangulating my perceived effort, heart rate, and power in that order." Even at worlds, he ignored the field and rode his own numbers. [E]
3. **Confusing normalized power with even effort** -- NP can mask surges. Check AP vs NP gap, not just NP alone. [E]

### Platform Module: `pacing.py`

- `solve_pacing()` solves for a single base power that produces the target riding time across all segments -- this IS even pacing by construction
- Actual per-segment power = `base_power * degradation_factor(cumulative_kj, elapsed_hours)` -- durability-adjusted even effort
- Enriched segments include `degradation` factor showing how much power declines due to fatigue at each segment

---

## 2. Negative Splits

### When Negative Splitting Works

Negative splitting (second half faster than first) is a **variant of conservative even pacing**, not a separate strategy. It works when:

- The athlete has an uncertain fitness ceiling and wants to minimize blowup risk [E]
- The course front-loads difficulty (headwinds, climbs) and back-loads assistance (tailwinds, descents) [E]
- The event is a mass start where early congestion forces conservative pacing anyway [E]
- The athlete is transitioning from one discipline to another (triathlon bike-to-run) and needs to arrive at the transition with reserves [E]

### Practical Implementation

Jeff Vicario (TP) trained his athlete to practice negative-split pacing via progressive long runs: start 1:20/mile slower than tempo, then increase 20 sec every 2 miles. The athlete's half-marathon had 0.2% Pa:HR decoupling -- strong aerobic fitness confirmed by the strategy. [E]

Hal Higdon: "An even pace usually is the best approach. You may think you are banking some time, but when you get into the final six miles ... you'll lose more than you saved." For runners who consistently have energy left at the finish, the solution is faster overall pace, not deliberately slow starts. [E]

### Negative Splitting Is NOT

- A license to sandbag the first half -- running 1-2 min/mile slower than capability wastes potential [E]
- Superior to even pacing in controlled conditions -- when an athlete knows their capacity well, perfectly even is faster than conservative-then-fast [R]
- Appropriate for short events (crits, TTs under 1 hour) where full commitment from the start is required [E]

---

## 3. Terrain-Based Pacing: Climbs, Flats, Descents

### The Physics

On flat ground, aerodynamic drag dominates (P_aero proportional to v^3). On climbs, gravity dominates (P_gravity proportional to weight * grade * speed). This asymmetry means **constant power does NOT mean constant speed** -- and the time-optimal strategy shifts power toward climbs. [R]

The reason is mathematical: on a climb, a small increase in power produces a proportionally larger speed increase (gravity-dominated regime), while on the flat the same power increment yields diminishing speed returns (aero-dominated cubic relationship). Therefore, to minimize total time over varied terrain, **push harder on climbs and ease off on flats/descents.** [R]

### Recommended Power Adjustments by Terrain

| Segment Type | Power Relative to Base | Rationale | Source |
|-------------|----------------------|-----------|--------|
| Flat, no wind | 100% base power | Reference condition | physics.py [R] |
| Sustained climb (> 5%) | 105-115% base power | Gravity-dominant; speed scales linearly with power | Coggan, BBS [R] |
| Rolling terrain (1-4%) | 100-105% base power | Mixed regime | BBS [E] |
| Descent (< -3%) | 0-50% base power | Aero drag makes extra watts nearly useless at high speed | physics.py [R] |
| Headwind | 95-105% base power | Aero cost increases; treat like moderate climb | BBS [E] |
| Tailwind | 90-95% base power | Aero savings; treat like moderate descent | BBS [E] |

### Descent Speed Capping

The platform caps descent speed at **70 km/h (19.4 m/s)** for safety and realism. Beyond this speed:

- Risk increases non-linearly with speed (kinetic energy proportional to v^2) [R]
- Marginal time savings are minimal (an extra 10 km/h on a 2 km descent saves ~6 seconds) [R]
- Pedaling above 70 km/h requires extreme gearing and adds negligible propulsive power vs drag [E]
- The platform's `_segment_time()` enforces: "if seg type in (descent, rolling_descent) and v > MAX_DESCENT_SPEED: v = MAX_DESCENT_SPEED" [platform]

Pete Jacobs at 2012 Kona: spinning out at 120 rpm descending Hawi on a 54-tooth chainring, lost positions to riders with 55-tooth -- gearing limits matter, but the time cost was small relative to the risk of descending harder. [E]

Ben Hoffman at 2014 Kona: kept power down to 275W on the Hawi descent (vs 313W on the climb) at 38.7 mph -- textbook terrain-appropriate restraint. [E]

### Platform Module: `segments.py`, `physics.py`, `pacing.py`

- `segments.py` classifies terrain into `climb`, `rolling`, `flat`, `rolling_descent`, `descent` using grade thresholds (CLIMB_THRESHOLD = 0.03, ROLLING_THRESHOLD = 0.01)
- `physics.py` `power_required()` computes P_aero + P_rolling + P_gravity for any grade/speed combination; `speed_from_power()` inverts this via Brent's method
- `pacing.py` `_segment_time()` applies durability decay to base power, computes speed for each segment's grade, and caps descent speed

---

## 4. Drafting Effects

### Aerodynamic Savings

Drafting (riding in the slipstream of another rider) reduces aerodynamic drag significantly. The magnitude depends on position, gap, group size, and speed. [R]

| Position | Typical Aero Savings | Source |
|----------|---------------------|--------|
| Single rider behind one other | 25-35% | Wind tunnel + field studies [R] |
| 3rd wheel in paceline | 30-40% | [R] |
| Deep in peloton (20+ riders) | 40-50% | Tour de France estimates [R] |
| Triathlon legal draft (12m gap) | 5-10% | Minimal at legal distance [E] |
| No-draft triathlon | 0% (illegal) | Rules enforce solo effort [E] |

### Pacing Implications

- In road races and group rides, drafting fundamentally changes the power-speed relationship -- a rider at 200W in a peloton matches a solo rider at 270-300W [R]
- **Draft-legal races are tactically complex** -- energy conservation via positioning is as important as raw power [E]
- Criterium strategy: "The guy who wins the race is often the one who does the least amount of work" (Marin, TP). Stay in top 10 wheels, surf wheels, avoid unnecessary pulls. [E]
- In non-drafting triathlon, pacing is pure physics -- the only variable is the rider's power allocation [E]

### Kona Example

2017 Kona: Josh Amberger led the bike pack into the headwind to Hawi. "All of the front pack pros were happy to sit in and take advantage of the headwind draft effect behind him all the way to the turnaround." The pros who drafted Amberger saved an estimated 25-35W over 2+ hours. Amberger's tactical error was leading into the wind instead of sharing the pace. [E]

### Platform Module: `pacing.py`

- `RidePlan` includes `drafting_pct` (fraction of flat/rolling time in draft, 0-1) and `drafting_savings` (default 0.30 = 30% aero reduction)
- `_effective_cda()` reduces CdA on flat/rolling/descent segments when drafting is active: `cda * (1 - drafting_pct * drafting_savings)`
- Drafting is NOT applied on climbs (speed too low for meaningful aero savings; grade-dependent)

---

## 5. Power-Based Pacing vs HR vs RPE

### Hierarchy of Pacing Signals

| Signal | Strengths | Weaknesses | Best Use |
|--------|-----------|------------|----------|
| Power | Objective, instantaneous, unaffected by fatigue/heat/altitude | Does not reflect internal cost; same watts feel harder when fatigued | Primary pacing metric for cycling [R] |
| Heart rate | Reflects cardiovascular load; integrates internal state | Cardiac drift, heat, caffeine, anxiety all confound; lags effort by 30-60s | Secondary metric; useful for confirming sustainable effort over hours [E] |
| RPE | Integrates ALL physiological and psychological signals | Subjective; requires training to calibrate; hard to communicate precisely | Primary metric when devices fail; essential for ultra-duration [E] |
| Speed | Easy to understand | Useless without controlling for grade, wind, draft | Meaningless for pacing decisions in isolation [R] |

### The Case for Power as Primary

Chris Thomas (40+ half-Ironmans): "My effort on race day is dictated by triangulating my perceived effort, heart rate, and power in that order." Note: RPE first, then HR, then power -- even a data-driven racer puts internal feel first. [E]

Curt Wilhelm (24-hour MTB solo): "It was a significant advantage having a power meter. I found I can sustain level 2 power literally all day long. The last few laps my power was still at level 2, but my heart rate was in active recovery (zone 1)." This HR-power dissociation is expected in ultra events due to cardiac drift and fatigue -- power stays reliable, HR becomes unreliable. [E]

### The Case for RPE Calibration

Laura Marcoux (TP): "Over-reliance on data can come at the expense of reaching your potential." Devices fail, batteries die, and conditions change. Athletes should practice covering their power display and estimating effort, then checking afterward. [E]

Todd Parker (TP) uses track pacing sessions specifically to teach RPE calibration: 400m repeats at various efforts, focusing on perceived exertion rather than pace readout. "Once learned, it makes sustainable pacing performance much easier to identify -- whether you use a HRM or not." [E]

### EC Podcast Position

Kolie Moore explicitly recommends RPE as the gold standard for internal load (TMT-68). Power tells you what you are doing; RPE tells you what it costs. For well-trained athletes, the two should be calibrated against each other. When they diverge (RPE rising at constant power over 2+ weeks), it signals overreaching or under-fueling (TMT-51). [E]

### Heart Rate Caveat

Matt Fitzgerald (TP): "Ignore heart rate until after the race. This data will not help you pace yourself more effectively." Post-race average HR is useful for setting targets in future race-intensity training, but real-time HR is too noisy for pacing decisions. [E]

---

## 6. Ultra-Distance Pacing Specifics

### Fundamental Differences from Short Events

Ultra-distance events (> 6 hours, up to multi-day) follow different pacing rules than events under 4 hours:

1. **Durability replaces VO2max as the primary limiter** -- the athlete who loses the least power over time wins, not the one who starts strongest (WD-60) [R]
2. **Nutrition becomes a pacing variable** -- fueling failures cause power drops that dwarf any strategy error (Persp-41, TMT-73) [E]
3. **Sleep deprivation degrades decision-making** before it degrades physical capacity -- cognitive errors (navigation, nutrition timing, equipment choices) accumulate [E]
4. **The race is managed aid-station to aid-station**, not as one continuous effort -- Jason Koop's ADAPT framework (Accept, Diagnose, Analyze, Plan, Take action) for managing inevitable bad patches [E]

### Ultra Pacing Numbers

| Event Duration | Target IF | Target Carb Rate | Power Decline Expected | Source |
|---------------|-----------|------------------|----------------------|--------|
| 4-6 hrs | 0.65-0.75 | 60-90 g/hr | 5-10% | EC, nutrition-ultra [E] |
| 6-12 hrs | 0.55-0.65 | 60-90 g/hr | 10-20% | nutrition-ultra [E] |
| 12-24 hrs | 0.45-0.55 | 40-70 g/hr | 20-35% | nutrition-ultra, Wilhelm [E] |
| 24-48 hrs | 0.35-0.50 | 30-60 g/hr | 30-50% | nutrition-ultra [E] |
| 48-72 hrs (brevets) | 0.30-0.45 | 30-50 g/hr | 40-60% | nutrition-ultra [E] |

### Key Ultra Pacing Principles

- **"Undercook by 5-20%" as a pacing rule for events >6 hours** -- when debating between pushing and holding back, always hold back. The asymmetry is stark: undercooking by 5-20% costs minutes; overcooking by 10% costs hours or a DNF. This applies to every segment, not just the start [E] (TMT-75)
- **Autoregulation overrides power targets after hour 15** -- RPE should take priority over the power meter in ultra events. Cardiac drift, thermal load, and cumulative fatigue decouple watts from internal cost. "Breathing > power" -- if breathing feels labored at target watts, drop watts immediately rather than chasing a number that no longer represents sustainable effort [E] (TMT-75)
- **"Start smart, finish fast"** -- Lynda Wallenfels (100-mile MTB): "Start at a speed that feels conservative, then increase perceived exertion gradually as start-line excitement wears off and fatigue sets in. Starting faster than you have trained to do is the biggest mistake in a 100-mile mountain bike race." [E]
- **If you are too fast to eat in the first hour, you are over-pacing** (Wallenfels). Fueling ability is a proxy for sustainable intensity. [E]
- **High early cadence preserves legs** -- "Pedal with cadence on the high side early. This puts more stress on cardiovascular system than muscular system and saves legs for later." Allow cadence to drift lower as fatigue accumulates. [E]
- **The "mile 60 problem"** -- fatigue accumulates non-linearly. The last 40% of a 100-mile event feels like 60% of the total effort. Mental strategies (mantras, segment-by-segment focus) become as important as physical pacing. [E]
- **Power meter enables fueling** -- Wilhelm: "My power meter told me I was using 800-900 kJ each hour, which requires a lot of fuel." Knowing energy expenditure in real-time prevents under-fueling. [E]

### Durability Model Integration

The platform's durability model quantifies power decline:

`degradation_factor = a * exp(-b * kJ/1000) + (1-a) * exp(-c * hours)`

This captures both energy-dependent fatigue (kJ term) and time-dependent fatigue (hours term). For pacing:

- The kJ term is partially controllable via fueling -- better fueling slows degradation [E]
- The hours term reflects circadian, neural, and biomechanical fatigue -- not modifiable in real-time [E]
- `fueling_confound_warning` flag in `fit_durability_model()`: when `b > 0.003`, steep degradation may reflect poor fueling habits rather than poor fitness (WD-60) [E]

### Platform Module: `durability.py`, `pacing.py`

- `pacing.py` `solve_pacing()` uses durability model to predict per-segment power decline and adjusts target power accordingly
- `durability.py` `degradation_factor()` computes fatigue at any point; `durability_benchmark()` classifies drop % against EC benchmarks (elite pro < 2% at 50 kJ/kg, average amateur 20-40%)
- `durability.py` `frc_budget_simulate()` tracks FRC depletion across segments -- critical for ultra events with repeated climbs where above-threshold bursts accumulate

---

## 7. Time Trial Strategy

### Pure TT Pacing

Time trials are the purest test of pacing because there is no drafting, no tactical positioning, and the objective function is simple: minimize time over a fixed distance.

**Key principles:**

- **Even power is the baseline.** For flat courses, the goal is the highest sustainable constant power for the expected duration. VI should be <= 1.02. [R]
- **Terrain adjustment is the primary deviation.** On hilly TT courses, push climbs 5-15% above target and ease descents -- the same physics-based argument as Section 3. [R]
- **Start intensity matters.** A common error is starting 5-10% above target due to adrenaline. The first 2-3 minutes should feel controlled. Sanders at Kona 2017: started at IF 0.81 to Hawi (slightly above the 0.80 typical for winning files) -- even a 1% deviation from optimal is noticeable at this level. [E]
- **Riegel model for duration adjustment.** For TTs longer than 1 hour, power must decrease with duration. The Monster TT case study: 122.5 km, expected duration 2:39, coach Guido Vroemen calculated that power should be 93% of FTP (350W from 375-380W FTP). Actual NP was 356W. BBS predicted time was within 1% of actual. [E]

### IF Guidelines by TT Duration

| Duration | Expected IF | Source |
|----------|-----------|--------|
| 5 min | 1.10-1.20 | WKO5 PD curve [R] |
| 20 min | 1.00-1.05 | Coggan [R] |
| 40 min | 0.95-1.00 | Coggan [R] |
| 60 min (FTP by definition) | ~1.00 | [R] |
| 2-3 hrs | 0.85-0.95 | Vroemen, BBS [E] |
| 4-5 hrs (Ironman bike) | 0.76-0.82 | Kona pro data [E] |

### Best Bike Split Approach

Best Bike Split (BBS) uses course profile, weather, rider CdA, power capacity, and equipment to generate per-segment power targets. Key insight: **BBS optimizes for minimum time, not even power** -- it redistributes effort toward segments where watts-per-second-saved is highest (climbs, headwinds). [R]

Jim Vance (TP): "Best Bike Split allows athletes to take data from their training and racing to better determine which power output will yield the best performance overall, over each specific course they will race." Athletes can compare multiple race plans (flat power target vs TSS target vs terrain-adjusted) and see which produces the fastest total time. [E]

### Platform Analogy

The platform's `solve_pacing()` is a simplified BBS: it solves for one base power that produces the target total time given segment grades, durability decay, and drafting. It does NOT currently optimize power distribution across segments (push more on climbs, less on descents) -- that would require a more complex variational optimization. This is a known limitation.

---

## 8. Mass-Start Race Tactics

### Pacing in the Peloton

Mass-start road races (crits, road races, gran fondos) break all solo-pacing rules because **draft, positioning, and race dynamics dominate power allocation.**

**Key tactical principles:**

- **Energy conservation is the primary objective until the decisive moment** -- Sofia Marin (Cat 1 crit racer, TP): "Don't show off. Be calculated with your efforts and save energy for when it really matters." [E]
- **Position = free watts.** Staying in the top 10 wheels costs less energy than being at the back and yo-yoing through surges and decelerations. [E]
- **Surf wheels, minimize braking.** Smooth cornering and anticipation of accelerations conserve far more energy than raw power. [E]
- **Know your strengths and the competition's weaknesses** -- Jim Vance (TP): six questions for race strategy: What are your strengths? Weaknesses? Competition's strengths? Weaknesses? Course demands? Climate factors? [E]

### Power Distribution in Road Races

Unlike TTs, road race power files are highly variable (VI often 1.15-1.40). This is unavoidable and acceptable because:

- Drafting means that high-power surges produce proportionally larger gaps than in solo riding [R]
- Recovery in the draft between surges is genuine recovery (50-100W vs 200W+ solo) [R]
- The repeatability of above-threshold efforts matters more than average power -- `repeatability_index()` in `durability.py` tracks 3rd-best to 1st-best effort ratio at key durations [platform]

### FRC Budget in Road Racing

The FRC (Functional Reserve Capacity) budget is critical in mass-start events:

- Every above-FTP surge costs FRC (W')
- FRC recovery below FTP is incomplete -- each successive deep depletion reduces the recovery ceiling
- `frc_budget_simulate()` tracks depletion and recovery across segments with degrading recovery ceiling: `recovery_ceiling = max(0.5, 1.0 - depletion_count * 0.1)`
- Practical implication: an athlete who makes 5 big surges in the first half of a race may have only 50% of their FRC ceiling available for the decisive final surge [platform]

---

## 9. When to Deviate from the Plan

### Valid Reasons to Go Harder Than Planned

- **Feeling genuinely good AND it is past the halfway point** -- never deviate in the first half based on feel alone; adrenaline is deceptive [E]
- **Tactical necessity in a road race** -- a critical selection is happening and missing it means losing the race [E]
- **Final 10% of the event** -- the cost of a blowup is limited by the remaining distance. Wallenfels: "Start smelling the barn at mile 90 and go for it." [E]
- **Environmental conditions are better than predicted** -- tailwind, cool temperatures, downhill. BBS updates plan based on real conditions. [E]

### Valid Reasons to Go Easier Than Planned

- **GI distress or nutrition failure** -- reduce intensity 5-10% to improve splanchnic blood flow and allow absorption to resume (nutrition-ultra) [R]
- **Heat beyond what was trained for** -- cardiac output is redirected to thermoregulation; maintaining planned watts at higher internal cost risks collapse [R]
- **Mechanical or equipment issues** -- a flat, broken spoke, or shifting problem demands power conservation until resolved [E]
- **Bad legs / elevated RPE at planned power** -- Laura Marcoux (TP): "If you try to hit your pre-planned objective measures regardless of feel, you could run out of steam before the finish or even DNF." Trust RPE over power when they diverge. [E]
- **Mid-race catastrophe** -- Koop's ADAPT system: Accept, Diagnose, Analyze, Plan, Take action. "The acronym is ADAPT, not PANIC. Making small, incremental changes is always better than drastically revising your well-thought-out race strategy all at once." [E]

### Lionel Sanders Case Study: Deviating Both Ways

Arizona 2016 (record ride): Sanders executed near-perfect even pacing on the bike (VI 1.01) but deliberately went out slightly fast on the run (first half marathon ~1:18). "I was certain that I would not have the legs to go the full distance, regardless of what pace I ran at, so I did go out a little faster than I probably should have, with the intention of building up some fat on the competition." He hit the wall at mile 17, slowed to 7:20 pace at mile 23, then rallied for 6:20 pace in the final 3 miles when told the record was in reach. [E]

Kona 2017: Sanders averaged IF 0.79 for the first 94 miles but only IF 0.68 for the final 20 miles -- a 13% power drop. This was either deliberate (saving for the run) or involuntary (durability limit reached). Lange ran him down with 3 miles to go. The lesson: even a world-class athlete can miscalculate the cost of early aggression. [E]

BBS analysis for Kona 2017: Sanders could have started his run at 2:45 marathon pace instead of 2:42, and the saved energy might have been the difference in holding off Lange. [E]

---

## 10. Pre-Race Pacing Preparation

### Testing the Plan

- **Do 2 race-distance training rides at projected race power** with race-day gear and nutrition (Matt Mauney, TP). Changes can be made if the target % of FTP proves unsustainable. [E]
- **Test equipment and nutrition in B/C races** -- Jim Vance (TP): "Whatever your strategy, it is best to test it a few times in a race before, so you can have confidence in it." [E]
- **Practice progressive-effort long sessions** -- Vicario's method: start 1:20/mile below tempo, increase 20 sec every 2 miles. This builds the neural pattern of finishing strong on fatigued legs. [E]
- **Cover your power meter occasionally in training** to calibrate RPE (Marcoux, TP). Build the skill of knowing your output without looking. [E]
- **Know your device accuracy** -- Matt Fitzgerald (TP): "Through experience I know my Garmin consistently overestimates my speed by 1%. Thus when I race I mentally add 3-4 seconds per mile." A 2% error at the start can mean bonking or leaving time on the table. [E]

### Race-Morning Checklist

1. Confirm target power / IF for the event duration
2. Know power adjustments for key terrain features (major climbs, descents, crosswind sections)
3. Set power meter lap alerts or load BBS targets to device
4. Have RPE anchors memorized ("this effort = sustainable all day" vs "this effort = 2 hours max")
5. Have a contingency plan: what do you do if power is 10% below target at hour 2? (Adjust goal, not panic)

---

## Conflicts with Conventional Wisdom

| Claim | Position from Sources | Evidence |
|-------|----------------------|----------|
| "Negative splitting is always best" | Even pacing is faster when capacity is well-known; negative split is a conservative variant for uncertain fitness | TP coaching articles, Higdon [E] |
| "Push hard on descents to make up time" | Diminishing returns from aero drag (v^3); descent speed capped at 70 km/h; risk-reward unfavorable | physics.py [R], pacing.py [platform] |
| "Heart rate is the best pacing metric" | Power is primary for cycling; RPE is primary when devices fail; HR lags and drifts | Fitzgerald, Moore (TMT-68) [E] |
| "Drafting saves 50% in road races" | 25-35% for single wheel; 40-50% deep in large peloton; varies enormously with speed and gap | Wind tunnel data [R] |
| "Just ride to your power number" | RPE should override power when they diverge; internal feel integrates what power cannot | Thomas, Marcoux, Moore [E] |
| "Ultra pacing = just go slow" | Ultra pacing requires active management: terrain adjustment, nutrition timing, cadence strategy, sleep management, crisis response | Wallenfels, Wilhelm, Koop [E] |
| "A plan is a plan -- stick to it" | Plans are written in sand (TMT-73); ADAPT, don't panic; small incremental adjustments beat wholesale strategy changes | Koop, Vance [E] |

---

## Platform Integration Summary

| Module | Pacing Role |
|--------|------------|
| `pacing.py` | Core solver: durability-aware base power calculation, segment-level power/speed/time targets, descent speed capping, drafting CdA adjustment |
| `segments.py` | Route decomposition: grade computation, terrain classification (climb/rolling/flat/descent), physiological demand classification |
| `physics.py` | Power equation: `power_required()` and `speed_from_power()` with aero/rolling/gravity components, air density from temperature/altitude |
| `durability.py` | Fatigue model: `degradation_factor()` for kJ+time decay, `frc_budget_simulate()` for above-threshold surge costing, `repeatability_index()`, fresh baseline checking |
| `nutrition.py` | Fueling integration: carb rate targets by duration, energy deficit tracking, glycogen budget -- fueling is a pacing variable in ultra events |

---

## Episode & Article Index

| Source | Topic | Key Insight |
|--------|-------|-------------|
| TMT-60 | FTP Decision Tree | Above-threshold surges deplete W' disproportionately |
| TMT-68 | Using Data in Coaching | RPE is gold standard for internal load |
| TMT-73 | Things We Wish We Knew | "Plans are written in sand" |
| WD-60 | Durability Limitations | Durability is the limiter in ultra events; fueling is a confounder |
| Persp-39 | Balance (McKay) | Durability and pacing integration |
| Persp-41 | Macros/Timing (Podlogar) | On-bike fueling rates by duration |
| TP: Sanders Arizona | IRONMAN Record | VI 1.01, IF 0.79 -- textbook even pacing |
| TP: Sanders Kona 2017 | World Championship | 13% power fade last 20 miles -- cost of early aggression |
| TP: Alexander Kona 2011 | IRONMAN Win | VI 1.05, IF 0.81, 10W second-half drop |
| TP: Monster TT | 122.5 km TT | 93% FTP for 2:39 duration; BBS within 1% of actual |
| TP: Wallenfels 100-mile MTB | Ultra pacing | "If too fast to eat in first hour, you're over-pacing" |
| TP: Wilhelm 24-hr MTB | Ultra power meter use | L2 power all day; HR drifted to Z1 |
| TP: Vicario Marathon | Negative split training | Progressive long runs to build finishing speed |
| TP: Koop Ultra | Mid-race crisis | ADAPT framework for managing catastrophe |
| TP: Thomas 70.3 Worlds | Triathlon pacing | Triangulate RPE > HR > power |
| TP: Marin Criterium | Crit tactics | Energy conservation + positioning > raw power |
| TP: Vance Race Tactics | Race strategy | Six questions framework for race planning |
| TP: Marcoux Internal Pacing | RPE development | Cover devices occasionally to build feel |

---

## Cross-References

- [Power-Duration Modeling](power-duration-modeling.md) — PD curves define the power ceiling that pacing plans must respect; FRC budget drives surge costing in road races
- [Durability & Fatigue](durability-fatigue.md) — degradation model directly feeds pacing solver; durability is the primary limiter in ultra-distance pacing
- [Ultra-Endurance](ultra-endurance.md) — ultra-specific pacing targets (IF 0.40-0.60), nutrition-as-pacing-variable, and multi-day TSS ceiling
- [Training Load & Recovery](training-load-recovery.md) — TSS/IF/NP metrics underpin all pacing target calculations and race-day TSB determines readiness
- [Heat, Altitude & Environment](heat-altitude-environment.md) — environmental conditions force pacing adjustments of 5-15% FTP; race-day power targets must account for heat and altitude
- [FTP & Threshold Testing](ftp-threshold-testing.md) — accurate FTP is the foundation for all IF-based pacing targets
- [Ironman Triathlon](../entities/ironman-triathlon.md) — Kona pro power files (Sanders, Alexander, Hoffman) are primary pacing case studies
- [Race-Day Nutrition](../nutrition/race-day-nutrition.md) — fueling execution is a pacing variable; GI distress requires real-time power reduction
