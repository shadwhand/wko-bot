# Race-Day Nutrition

Pre-race fueling, during-race protocols by duration, post-race recovery, product strategies, and gut training timelines.

Evidence levels: **[R]** = Research-backed, **[E]** = Experience-based, **[O]** = Opinion.

---

## 1. Pre-Race Fueling

### Glycogen Loading Protocols

| Protocol | Duration | CHO Intake | Glycogen Achieved | Notes |
|---|---|---|---|---|
| Classical (Bergstrom 1967) | 3-day depletion + 3-day load | 10-12 g/kg/day | 700+ mmol/kg dw | Outdated -- unnecessary suffering |
| Modified (Sherman 1981) | Taper + 2-3 day load | 10-12 g/kg/day | ~600-700 mmol/kg dw | Current standard |
| 1-Day (Bussau 2002) | Exhaustive bout + 24 hr | 10-12 g/kg/day | ~90% of classical | Good for time-constrained |

Source: nutrition-racing.md, Bussau et al. 2002, Burke et al. 2011 [R]

### Practical Loading (78 kg cyclist)

- Target: 10-12 g/kg/day = 780-936 g CHO/day for 2-3 days [R]
- Rice/potato preferred over pasta (gluten causes bloating even in non-intolerant) [E] (Persp-41)
- High-carb loading inadvertently increases sodium intake, causing water retention [R]
- Haribo/sweets used by pros: no gluten, no fiber, no extra sodium, no fat -- just carbs [E] (Persp-41)

### Pre-Race Meal (3-4 hours before start)

| Parameter | Recommendation | Example (70 kg rider) |
|---|---|---|
| CHO amount | 2-4 g/kg body mass | 140-280 g CHO |
| Calories | 560-1,120 kcal from carbs | -- |
| Composition | Low fiber, low fat, moderate protein | Bagel + PB + banana + sports drink |
| Timing | 3-4 hours before start | -- |
| Critical rule | Familiar, practiced foods ONLY | Never try new foods race morning |

Source: nutrition-racing.md, Burke et al. 2011, Thomas et al. 2016 [R]

### Final 60 Minutes Before Race

- "Reactive hypoglycemia" concern is largely overblown -- insulin response is overridden once exercise begins (Moseley et al. 2003) [R]
- 30-60 g CHO in last 30 min is acceptable if tolerated [R]
- **Avoid**: 75-150 g simple sugars exactly 30-45 min before start without exercise onset -- this narrow window can cause rebound hypoglycemia in susceptible individuals [R]
- Practical: sip sports drink or have a gel 15-20 min before start [E]

---

## 2. During-Race Protocols by Duration

### When to Start

- **Begin fueling within the first 15-20 minutes of racing** [R]
- Do NOT wait until hungry or fatigued
- Gastric emptying is rate-limited; early intake ensures supply at hours 2-3+ [R]
- In criteriums (<60 min): typically only fluids + possible mouth rinse [E]

### Feeding Frequency

- Every 15-20 minutes for solid/semi-solid [R]
- Every 5-10 minutes for sips of drink mix [E]
- Smaller, more frequent doses yield better absorption and less GI distress than large boluses [R]
- `dose_per_feeding = target_g_hr / feedings_per_hr` (e.g., 90 g/hr / 4 = ~22 g every 15 min)

### Protocol by Race Duration

| Duration | CHO Target | Fluid | Sodium | Primary Fuel Form |
|---|---|---|---|---|
| < 45 min | Mouth rinse | Ad libitum | Not needed | -- |
| 45-75 min | 30 g/hr | 400-600 mL/hr | Optional | Sports drink |
| 1-2.5 hr | 60-90 g/hr | 500-800 mL/hr | 300-600 mg/hr | Drink mix + gels |
| 2.5-5 hr | 90-120 g/hr | 500-800 mL/hr | 500-1,000 mg/hr | Drink mix + gels + bars |
| 5-8 hr | 80-100 g/hr | 500-800 mL/hr | 500-1,000 mg/hr | Mixed: liquid + solid food |
| 8+ hr | See [Ultra Nutrition](ultra-nutrition.md) | -- | -- | -- |

Sources: nutrition-racing.md, ec-master-reference.md, King et al. 2022 [R]

### Professional Standard (Tour de France)

"During the race, we rarely go below 80 grams an hour. And as soon as the race starts to get harder, towards the end or even from the middle, almost every stage nowadays is at least 120 grams." -- Bob Jungels (TrainingPeaks webinar with James Morton) [E]

### Form Factor by Duration and Intensity

| Form | Best Use | Absorption Speed | GI Risk |
|---|---|---|---|
| Drink mix | All durations; base fueling layer | Fast (~5-10 min) | Low |
| Gels | >1 hr; high-intensity moments | Moderate (~10-15 min) | Moderate (take with water) |
| Chews/blocks | 2+ hr; moderate intensity | Moderate (~15-20 min) | Moderate |
| Solid food (bars, rice cakes) | 3+ hr; lower intensity phases | Slow (~20-30 min) | Higher at intensity |
| Liquid meal (e.g., Maurten mix) | Very high intake targets | Fast | Low |

Source: nutrition-racing.md [R]

### Intensity Interaction

- At >85% FTP: strongly favor liquids and gels [R]
- At 60-75% FTP (peloton cruising): solids well tolerated, provide satiety [E]
- Solid fraction heuristic: `solid_fraction = max(0, 1 - (intensity_fraction - 0.60) / 0.30)` -- above ~90% FTP, solids approach zero [E]

### Delay from Mouth to Oxidation

| Form | Gastric Emptying Lag | Intestinal Absorption | Total Delay |
|---|---|---|---|
| Liquid | 5-15 min | 10-20 min | 15-35 min |
| Gel | 15-30 min | 10-20 min | 25-50 min |
| Solid food | 20-45 min | 10-20 min | 30-65 min |

**Critical implication**: Feeding must anticipate demand, not react to it. [R]

---

## 3. Higher On-Bike Carbs: Not Always Better

### The 90 vs 120 g/hr Tradeoff (Persp-41)

- At 120 g/hr vs 90 g/hr: you burn more carbs (less fat), finish with same glycogen [R]
- But you consume 120 g more of your daily carb budget [R]
- This can leave insufficient carbs for recovery, impairing next-day glycogen stores [R]
- Dose-response relationship: more post-exercise carbs = more glycogen next day [R]

### When Higher Is Better

- Single-day races where tomorrow does not matter [E]
- Races where intensity is very high (>85% FTP sustained) [R]
- Athletes with lab-confirmed high absorption ceiling (>100 g/hr) [R]

### When Moderate Is Better

- Stage races where next-day readiness is critical [E]
- Training rides where recovery quality matters more than peak performance [E]
- Athletes without gut training who risk GI distress above 80 g/hr [E]

**Platform implication**: Model on-bike vs off-bike carb distribution. Higher on-bike intake is not always better if it squeezes post-ride replenishment. (Persp-41, ec-master-reference.md) [R]

---

## 4. Post-Race Recovery Nutrition

### The Glycogen Window

The "anabolic window" is real but wider than traditionally claimed -- and misunderstood [R]:

- For **total muscle glycogen**: the window is wide (24 hr is fine if total intake is sufficient) [R]
- For **performance**: immediate post-exercise fueling matters via non-glycogen pathways [R] (WD-59)
- **Critical when**: next hard effort <24 hours away (stage races, doubles, track meets) [R]

### The WD-59 Paradox: Delayed Carbs Impair Performance by ~30%

- Double-blind crossover, n=9 [R]
- Immediate vs delayed carb group (both received identical total daily macros) [R]
- Muscle glycogen returned to near-baseline in BOTH groups (~10% difference = normal variation) [R]
- But immediate group: avg 18 reps. Delayed group: avg 12-13 reps. Effect size: 2.03 (massive) [R]
- **Implication**: Recovery involves more than glycogen replenishment. Liver glycogen, systemic catabolic state, and hormonal milieu matter. [R]

### Specific Recovery Recommendations

| Parameter | Recommendation | Notes |
|---|---|---|
| CHO intake (0-2 hr post) | 1.0-1.2 g/kg/hr | Rapid glycogen resynthesis; critical for stage races |
| CHO intake (2-24 hr post) | 8-12 g/kg/day total | If next-day event |
| Protein (0-2 hr post) | 0.3-0.4 g/kg (~20-30 g) | Maximize MPS |
| Protein:CHO ratio | 1:3 to 1:4 | In recovery meal/drink |
| Leucine threshold | 2.5-3.0 g per serving | Triggers maximal MPS |
| Total daily protein | 1.6-2.2 g/kg/day | Spread across 4-5 meals (2-2.5 g/kg for high-volume, Persp-41) |
| Fat minimum | 0.8 g/kg/day | Can go lower on acute weight-loss days |
| Glycemic index | High GI in acute phase | Faster glycogen resynthesis |

Source: nutrition-racing.md, Burke et al. 2017, Beelen et al. 2010, Persp-41 [R]

### Glycogen Resynthesis Rate

- Optimal fueling (0-2 hr post): 5-8 mmol/kg dw/hr [R]
- After 2 hr: 3-5 mmol/kg dw/hr [R]
- Full restoration: 24-48 hr with adequate intake regardless of timing [R]
- Adding protein to CHO does NOT increase glycogen resynthesis when CHO is already optimal (1.2 g/kg/hr). Helps only when CHO intake is suboptimal (<0.8 g/kg/hr). [R] (Beelen et al. 2010)

### Context-Dependent Timing

| Context | Timing Urgency | Strategy |
|---|---|---|
| Single-day race, 3+ days to next event | Low | Total daily intake matters most |
| Stage race / event <24 hr away | HIGH | Start within 15-30 min; 1.0-1.2 g CHO/kg/hr for 4 hr |
| Doubles (two-a-days) | HIGH | Post-session fueling critical; even gels immediately better than waiting |
| Dieting / intentional deficit | Moderate | Fuel on-bike, create deficit elsewhere; do NOT stack hard days back-to-back |

Source: WD-59, ec-master-reference.md [R][E]

---

## 5. Within-Day Energy Deficit

### The Problem

Even at adequate daily totals, prolonged intra-day deficits impair performance and health markers. [R]

- Groups with same daily calories but larger hourly deficits have worse outcomes [R]
- Suppressed RMR group: largest hourly deficit ~3,000 kcal vs ~1,300 kcal in normal group [R]
- Associated with elevated cortisol, suppressed RMR, menstrual disruption [R]
- A 5 hr / 3,500 kcal ride creates massive deficit even if all carb calories are replaced [R]

### Acute Deficit Cascade

1. Large acute deficit triggers leptin crash [R]
2. Ravenous hunger for days, metabolic slowdown [R]
3. Cortisol elevation promotes protein catabolism [R]
4. Impaired immune function [R]

**Platform implication**: Track within-day energy deficit patterns, not just daily totals. Flag prolonged fasted periods after hard sessions. (WD-59, TMT-50, Persp-36) [R]

---

## 6. Gut Training Timeline

### 8-Week Pre-Race Protocol

| Week | On-Bike CHO Target | Notes |
|---|---|---|
| 1-2 | 50-60 g/hr | Baseline; liquid-only carbs |
| 3-4 | 60-75 g/hr | Add gels; practice at race intensity |
| 5-6 | 75-90 g/hr | Mixed sources; add solid food on long rides |
| 7-8 | 90-110+ g/hr | Race simulation at target rate; full product rehearsal |

Source: Cox et al. 2010; Jeukendrup 2017; nutrition-racing.md [R]

### Principles

- Practice during training at race intensity (not just easy rides) [E]
- SGLT1 transporter expression upregulates with repeated exposure over 2-4 weeks [R]
- Always consume gels with water (hypertonic intake without water is the #1 nausea trigger) [E]
- Test EXACT products and quantities you will use on race day [E]
- Never try anything new on race day [E]

---

## 7. Common Mistakes

1. **Not eating early enough** -- start at km 0, not when hungry [E] (ec-master-reference.md)
2. **Creating acute energy deficit for weight loss on training days** -- sets up binge patterns [E] (TMT-69)
3. **Trusting energy estimation precision** -- display confidence intervals [R] (Persp-41)
4. **"Glycogen window is a myth"** -- overcorrection; the window IS real for performance, not glycogen quantity [R] (WD-59)
5. **Stacking calorie deficit on hard training days** -- fuel on-bike, create deficit elsewhere [E] (Persp-36)
6. **Skipping recovery nutrition** -- even 30 min delay measurably impairs next-day performance [R] (WD-59)
7. **Trying new foods on race day** -- GI distress risk is enormous [E]
8. **All liquid nutrition for events >4 hr** -- satiety signals, palatability fatigue, and ghrelin suppression require solid food [R]

---

## Platform Module Hints

- `nutrition.py`: Race-day nutrition plan generator from power targets + duration + environmental conditions
- Glycogen budget visualization: starting stores -> depletion curve -> exogenous supply -> time-to-bonk
- Recovery timing engine: flag when post-ride fueling appears delayed based on ride end time vs next meal
- Stage race carb distribution optimizer: on-bike vs recovery allocation

## Cross-References

- [Fueling Fundamentals](fueling-fundamentals.md) — Core oxidation science, glycogen depletion math, and dual-transporter model underlying these protocols
- [Ultra Nutrition](ultra-nutrition.md) — Protocols extending beyond 8 hours where palatability fatigue and GI distress dominate
- [Hydration & Electrolytes](hydration-electrolytes.md) — Fluid and sodium race-day protocol integrated with feeding schedules
- [Supplements & Ergogenic Aids](supplements-ergogenic.md) — Caffeine timing and dosing for race-day performance enhancement
- [Pacing Strategy](../concepts/pacing-strategy.md) — Intensity determines absorption capacity; >85% FTP cuts splanchnic blood flow by 60-80%
- [Ironman Triathlon](../entities/ironman-triathlon.md) — Practical application of these protocols in 4.5-5+ hr bike legs and marathon runs
- [Training Load & Recovery](../concepts/training-load-recovery.md) — Post-race recovery nutrition timing (WD-59 paradox) affects next-day readiness
- Source: nutrition-racing.md, nutrition-modeling.md, ec-master-reference.md Sec 4, Persp-41, WD-59, TMT-50, TMT-73
- TrainingPeaks: "Race Fueling: How Many Calories" (Odell), "A Guide to Race Day Nutrition" (Kattouf), "Fueling for Tour de France" (Jungels/Morton), "The 5 Golden Rules of Sports Nutrition" (David), "Differentiating Training and Racing Nutrition" (Hodges)
