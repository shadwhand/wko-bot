# Ultra Nutrition

Multi-hour fueling (5+ hours), real food vs engineered nutrition, stomach issues and solutions, sleep deprivation effects, caloric deficit management, and energy deficit formulas.

Evidence levels: **[R]** = Research-backed, **[E]** = Experience-based, **[O]** = Opinion.

---

## 1. The Inevitable Energy Deficit

Ultra-endurance cycling creates energy expenditure that is physiologically impossible to match with intake. This is the central nutritional challenge. [R]

### Energy Expenditure Estimates

| Event | Duration | Total Expenditure | Notes |
|---|---|---|---|
| Century (160 km) | 5-7 hr | 3,500-5,000 kcal | Standard sports nutrition applies |
| 200 km brevet | 7-10 hr | 5,000-7,500 kcal | Transition zone to ultra strategies |
| 300 km brevet | 12-16 hr | 7,500-12,000 kcal | Ultra strategies critical |
| 600 km brevet | 20-27 hr | 12,000-18,000 kcal | Full ultra protocol |
| 1200 km brevet (PBP) | 55-90 hr | 35,000-50,000 kcal | Multi-day with sleep breaks |
| RAAM (~4,800 km) | 8-12 days | 80,000-120,000 kcal | Supported crew event |

A 75 kg rider at 200W averages ~720 kcal/hr (GE ~23%). [R]

### Maximal Realistic Intake

- Gastric + intestinal limits: 90-120 g/hr CHO (360-480 kcal/hr from carbs) under optimal conditions [R]
- Adding fat and protein from solid food: practical ceiling ~400-600 kcal/hr during sustained riding [R]
- **Most ultra cyclists actually achieve**: 200-400 kcal/hr averaged over the full event including stops [E]
- Routine deficits: 4,000-8,000 kcal in 24 hr events [R] (Enqvist et al. 2010; Knechtle et al. 2005)

### Why the Deficit Is Tolerable

- Endogenous glycogen: ~2,000 kcal when fully loaded [R]
- Adipose tissue: essentially unlimited at ultra intensity. A lean 75 kg rider at 10% body fat carries **~67,500 kcal as fat** [R]
- **The performance limiter is not total energy but carbohydrate availability** for the brain and for intensity surges [R]

### The Deficit Is Inevitable -- Manage It, Don't Fight It

Trying to match expenditure with intake in a 1200 km causes GI disaster. Accept a deficit of 4,000-8,000 kcal per 24 hours, minimize it through steady intake, and recover afterward. [E]

---

## 2. Energy Deficit Formulas

### Core Energy Budget Model

From nutrition-modeling.md:

```
EE (kcal/hr) = Power (W) x 0.8604 / GE

Net_energy_deficit (kcal/hr) = EE - Effective_intake
Effective_intake = Gross_intake x 0.90 (TEF)

Cumulative_deficit (kcal) = Integral(Net_energy_deficit) over event duration
```

### Glycogen Budget Model (Extended Duration)

```
CHO_burn_rate (g/hr) = EE x CHO_fraction / 4.0
Exogenous_CHO_rate (g/hr) = min(Intake_rate x Absorption_eff, Transporter_max)
Net_endogenous_drain (g/hr) = CHO_burn_rate - Exogenous_CHO_rate

Time_to_bonk (hr) = Usable_glycogen (g) / Net_endogenous_drain (g/hr)
```

Where:
- `CHO_fraction` at ultra pace (0.55-0.70 IF): ~0.40-0.65 [R]
- `Usable_glycogen` = Total x 0.75 (~25% trapped in inactive muscles) [R]
- After 6+ hr at moderate intensity, riders are predominantly fat-fueled regardless [R]

### Fat Oxidation as Primary Ultra Fuel

At proper ultra pacing (0.55-0.70 IF), fat provides the majority of fuel: [R]

| Pacing | IF | Fat Oxidation (kcal/hr) | CHO Needed (kcal/hr) | CHO (g/hr) |
|---|---|---|---|---|
| Easy ultra | 0.55 | ~400-500 | ~150-200 | 38-50 |
| Moderate ultra | 0.62 | ~350-450 | ~200-270 | 50-68 |
| Hard ultra | 0.70 | ~250-350 | ~300-400 | 75-100 |

**Critical insight**: Pacing slightly lower (0.60 vs 0.70 IF) dramatically shifts fuel partitioning toward fat, reducing carbohydrate requirements and extending endurance. [R]

### Quantitative Example (75 kg rider, 200W, 600 km brevet)

- Total EE: ~720 kcal/hr
- At 0.62 IF: fat provides ~450 kcal/hr (62%), CHO ~270 kcal/hr needed
- Required exogenous CHO (after glycogen depletion): 50-65 g/hr
- Practical intake over 24 hr: ~300-400 kcal/hr
- Total intake: ~7,500-10,000 kcal
- Total expenditure: ~14,000-17,000 kcal
- **Expected deficit: 4,000-7,000 kcal (manageable)** [R][E]

### Energy Availability (RED-S Framework)

- EA = (Energy Intake - Exercise Energy Expenditure) / Fat-Free Mass [R]
- Below 30 kcal/kg FFM/day = physiological impairment threshold (Mountjoy et al. 2018) [R]
- Below 25 kcal/kg FFM/day = hormonal and metabolic disruption [R]
- During a 24 hr race, EA is typically deeply negative [R]
- **Key distinction**: Acute low EA during a single event is different from chronic low EA. A single ultra does not cause RED-S, but insufficient recovery afterward can compound problems. [R]

---

## 3. Sustainable Carbohydrate Rates by Duration

Nearly all research validating 90+ g/hr was conducted in events lasting 2-5 hours. Evidence for sustained 90 g/hr beyond 12 hours is almost entirely anecdotal. [R]

### Practical Sustainable Rates

| Duration | Sustainable CHO Rate | Primary Limiters |
|---|---|---|
| 0-6 hr | 80-120 g/hr | Standard sports nutrition; well-supported |
| 6-12 hr | 60-90 g/hr | Gut fatigue onset; solid food attractive |
| 12-24 hr | 40-70 g/hr | Highly individual; palatability fatigue significant |
| 24-48 hr | 30-60 g/hr | Includes stops; nausea management critical |
| 48-72 hr | 30-50 g/hr | Real meals at stops; gels often completely rejected |

Source: nutrition-ultra.md [R][E]

### Why Intake Declines

The decline is NOT primarily an absorption limitation. It is a combination of: [R]
1. **Gut mucosal damage** -- prolonged splanchnic hypoperfusion increases intestinal permeability
2. **Palatability fatigue** -- inability to tolerate sweet foods after 8-16 hr
3. **Reduced gastric motility** -- sympathetic activation slows stomach emptying
4. **Nausea from sleep deprivation** -- independent of GI mechanical factors
5. **Psychological aversion** -- conditioned taste aversion to familiar sports products

**Key finding**: The gut's ability to absorb remains if food can be tolerated. The limiter is tolerance, not capacity. [R]

---

## 4. Solid Food vs Engineered Nutrition

### When Gels and Liquids Are Not Enough

- Liquid/semi-liquid sources provide no satiety; ghrelin is not suppressed [R]
- Psychological need for "real food" becomes overwhelming after 8-12 hours [E]
- Solid food provides fat, protein, and macronutrient diversity that liquids lack [R]

### Sweet-Savory Cycling Strategy

| Phase | Hours | Dominant Preference | Foods |
|---|---|---|---|
| Early | 0-8 | Sweet/neutral | Gels, bars, bananas, rice cakes, drink mix |
| Transition | 8-16 | Mixed, sweet declining | Sandwiches, wraps, rice balls + some gels |
| Savory dominant | 16-24 | Savory, real meals | Rice, pasta, soup, bread with cheese/meat |
| Individual | 24+ | Highly variable | Some return to sweet after sleep; others stay savory |

Source: nutrition-ultra.md [E]

### Effective Ultra Foods (Community Evidence)

| Category | Foods | Notes |
|---|---|---|
| Rice-based | Onigiri, rice cakes with nut butter, sushi rice wraps | Allen Lim "Feed Zone" staples; universal in ultra cycling |
| Potato-based | Boiled baby potatoes with salt, potato wedges | Calorie-dense, easy to carry |
| Bread-based | PB&J, cheese sandwiches, wraps | Classic; works across cultures |
| Warm food | Soup, ramen, congee, miso | Warmth + salt + fluid + calories; critical for cold/night |
| Calorie-dense | Nut butters, cheese, salami, chocolate | For carrying; high kcal/gram |
| Cultural staples | French baguette+cheese (PBP), Japanese onigiri (PBP), Turkish flatbread | Use what you know |
| Control stop | Full meals: pasta, rice, meat, bread, soup, pastries | Eat at every control; skipping costs hours later |

Source: nutrition-ultra.md, PBP/RAAM observational data [E]

### Coca-Cola Phenomenon

Widely used in European ultras. Craved by day 2-3 for its precise combination of sugar, carbonation (which can reduce nausea), caffeine, and palatability. Many finishers cite Coke as the only thing that sounded appealing during the worst hours. [E]

### Solid Food Timing Rule

- Solid food on flat or gentle terrain [E]
- Switch to liquid/gel before and during significant climbs where intensity rises above Fatmax [E]
- Gastric emptying for solids: 1-4 hr for a mixed meal vs 20-60 min for liquid carbs [R]
- Slower delivery is BENEFICIAL in ultras: steadier energy, greater satiety [E]

---

## 5. Gastrointestinal Distress

### The Most Common DNF Cause in Ultras

| Duration | GI Distress Prevalence |
|---|---|
| Events <12 hr | 30-50% |
| Events >24 hr | 60-90% |
| RAAM | Primary reason for reduced pace or withdrawal in majority of entrants |

Source: de Oliveira et al. 2014; Pfeiffer et al. 2012; Knechtle et al. 2020 review [R]

### Multi-Factorial Cause Model

| Factor | Mechanism | Severity |
|---|---|---|
| Splanchnic hypoperfusion | Blood redirected to muscles; gut ischemia | Primary cause |
| Duration-dependent mucosal damage | Increased intestinal permeability (leaky gut); I-FABP elevation | Cumulative |
| Dehydration | Further reduces gut blood flow; slows gastric emptying | Amplifier |
| Heat stress | Independently worsens gut permeability (Snipe et al. 2018) | Amplifier |
| High CHO concentration | Hypertonic solutions cause osmotic fluid shifts; bloating | Avoidable |
| Fat and fiber | Slow gastric emptying | Balancing act in ultras |
| NSAIDs | Markedly increase intestinal permeability and GI bleeding | **Avoid entirely** |
| Sleep deprivation | Impairs gut motility; increases nausea independently | Late-event factor |

Source: nutrition-ultra.md, van Wijck et al. 2012 [R]

### Prevention Strategies (Ranked by Effectiveness)

1. **Pacing** -- Keep intensity below 70-75% VO2max to preserve splanchnic blood flow. Single most protective factor. [R]
2. **Gut training** -- 2-4 weeks of high-carb practice during training rides [R]
3. **Hydration maintenance** -- Small, frequent sips; avoid large boluses [E]
4. **Avoid hypertonic intake** -- ALWAYS consume gels with water; use isotonic/hypotonic drinks [R]
5. **Avoid NSAIDs entirely** [R]
6. **Reduce intake temporarily** if symptoms begin -- better to eat less for 30-60 min than force intake and trigger vomiting [E]
7. **Reduce intensity temporarily** -- even 5-10% power reduction significantly improves splanchnic blood flow [R]
8. **Prokinetic agents** -- Low-dose ginger (anti-emetic); prescription prokinetics in extreme cases [E]
9. **Probiotics** -- Multi-strain, 4+ weeks pre-competition; modest effect sizes (Jager et al. 2019 ISSN) [R]

### Ultra-Specific GI Principle

"The gut is the limiter, not the engine. Most DNFs in ultras are GI, not musculoskeletal. Protecting GI function (pacing, hydration, avoiding NSAIDs, gut training) is the highest-return investment." [E]

---

## 6. Sleep Deprivation Effects on Nutrition

### Metabolic Impact

| Effect | Magnitude | Source |
|---|---|---|
| Insulin resistance increase | +20-30% after 1 night no sleep | Donga et al. 2010 [R] |
| Glucose tolerance impairment | Higher, more prolonged blood glucose response | [R] |
| Cortisol elevation | Promotes gluconeogenesis + muscle protein breakdown | [R] |
| Ghrelin increase / leptin decrease | Should increase appetite... | Spiegel et al. 2004 [R] |
| ... but sympathetic activation suppresses it | Net: nauseated but knowing you need to eat | [R][E] |

### Reactive Hypoglycemia Risk

- Sleep-deprived riders are more prone to blood sugar crashes 30-60 min after carb intake [R]
- **Strategy**: Favor lower glycemic index foods and mixed macronutrient meals during overnight/sleep-deprived periods [E]
- **Avoid**: Large boluses of pure sugar on empty stomach during 2-5 AM (circadian nadir of insulin sensitivity) [R]

### Sleep Enables Eating

- Even 20-minute nap can restore appetite and GI function more effectively than any pharmaceutical [E]
- Many experienced ultra riders use deliberate **sleep-then-eat** strategy: nap first, then eat a real meal upon waking [E]
- 15-20 min nap improves appetite and GI tolerance for subsequent hours [E]
- In multi-day events, the **sleep-eat-ride cycle** is as important as ride-eat-ride [E]

### Practical Multi-Day Nutrition Through the Night

| Period | Strategy |
|---|---|
| First night (hr 12-24) | On-bike intake reduces to 40-60 g/hr; caffeine begins |
| 2-5 AM | Simpler foods, avoid pure sugar boluses; warm food if available |
| Pre-sleep break | Eat a real meal even if not hungry -- stomach processes food during sleep |
| Post-sleep break | Coffee/caffeine + small easily digestible meal (toast, rice, banana) |
| Second day | Appetite often partially recovers; eat aggressively at controls |
| Second night | Hardest period; accept lower intake (30-50 g/hr); warm soup may be all that sounds appealing |

Source: nutrition-ultra.md [E]

---

## 7. Multi-Day Caffeine Strategy

### The Ultra Caffeine Problem

In a 3-hr road race, caffeine is simple. In a 60-hr brevet, it must serve dual purposes: performance enhancement AND sleep management. Using it continuously depletes effectiveness through adenosine receptor upregulation (tolerance). [R]

### Phase-Based Protocol

| Phase | Hours | Caffeine Strategy | Notes |
|---|---|---|---|
| Early | 0-12 | 100-200 mg every 3-4 hr (maintenance) | Do not exceed normal daily intake |
| First night | 12-24 | 100-200 mg at drowsiness onset | 2-5 AM is resistant regardless of caffeine |
| Second day | 24-36 | Resume moderate caffeine | Partially effective; sleep debt accumulates |
| Second night | 36-60 | 300-400 mg if needed; diminished returns | "Stops working" for many; higher doses increase side effects |
| After any nap | -- | Caffeine immediately upon waking | "Coffee nap" strategy: consume, nap 20 min, wake as caffeine peaks |

### Caffeine Budget

| Event Duration | Total Budget | Distribution |
|---|---|---|
| 24 hr | 800-1,000 mg max | Weight toward nighttime hours |
| 48 hr | 1,200-1,600 mg total | Weight toward nights; spare early hours |
| Coffee vs pills | Pills or gels preferred late-event | Coffee more GI-stimulating |

Source: nutrition-ultra.md [R][E]

---

## 8. Practical Fueling Plans

### 600 km Brevet (~20-27 hr)

**Assumptions**: 75 kg trained rider, 24 hr total including stops, moderate climate.

| Phase | Hours/km | CHO Target | Fluid | Key Foods | Notes |
|---|---|---|---|---|---|
| Pre-event (24-48 hr) | -- | 8-10 g/kg/day | Extra hydration | Rice, potato, familiar | Na loading: +1,500-2,000 mg/day |
| Phase 1 | 0-8 hr / 200 km | 70-90 g/hr | 500-750 mL/hr | Gels, bars, bananas, rice cakes | Eat modestly at first control |
| Phase 2 | 8-16 hr / 200 km | 50-70 g/hr | Maintain | Wraps, onigiri, potatoes, savory | Begin sweet-to-savory transition |
| Phase 3 | 16-24 hr / 200 km | 40-60 g/hr | Maintain | Warm food, familiar comfort foods | Caffeine; reduce intake if nausea |

**Total intake**: ~10,000-14,000 kcal. **Expenditure**: ~14,000-18,000 kcal. **Deficit**: ~4,000-6,000 kcal (manageable). [E]

### 1200 km Brevet (~55-90 hr)

**Key difference**: Multi-day with sleep breaks. Recovery meals matter.

| Phase | Hours | Strategy |
|---|---|---|
| Day 1 (0-16 hr) | ~300 km | Standard 600 km Phase 1-2; eat well at controls; 55-80 g/hr |
| Night 1 (16-24) | ~100 km | Full dinner before night riding; caffeine; 40-60 g/hr on bike |
| Sleep break 1 | 1-3 hr | Eat before sleeping; coffee + small meal upon waking |
| Day 2 (24-40) | ~300 km | Appetite may recover; real meals critical; 40-70 g/hr; hydration discipline |
| Night 2 (40-55) | ~100 km | Hardest period; 30-50 g/hr; warm soup; second sleep break transforms remaining hours |
| Day 3 (55-75+) | ~300 km | Second wind for eating if sleep was achieved; eat aggressively; 50-70 g/hr |

**Total intake**: ~25,000-35,000 kcal. **Expenditure**: ~35,000-50,000 kcal. **Deficit**: ~10,000-20,000 kcal (1.5-3 kg fat equivalent). [E]

### What Finishers Actually Eat (Observational Data)

**Paris-Brest-Paris**: Full French meals at controls (pasta, rice, meat, bread, cheese, soup); most finishers eat 5-8 meals. Crepes (sweet and savory) are a staple. Japanese participants carry onigiri and miso packets. [E]

**RAAM**: Crew-prepared food; successful finishers consume 8,000-10,000 kcal/day. Riders eat less than half of what is offered. Preferences change unpredictably. [E]

**Transcontinental Race**: Gas stations, bakeries, restaurants. "Everything in sight" at restaurants. Coca-Cola becomes craved by day 2-3. [E]

---

## 9. Ultra-Specific Principles (vs Racing)

| Principle | Racing | Ultra |
|---|---|---|
| **Primary fuel strategy** | Maximize carb-fueled intensity | Pace to maximize fat oxidation; use carbs for brain + surges |
| **Primary limiter** | Fitness / power | GI function (most DNFs are GI, not musculoskeletal) |
| **Food selection** | Engineered nutrition (gels, drink mix) | Palatability > macros; variety is non-negotiable |
| **Sweet/savory** | Sweet products work for hours | Savory mandatory beyond 12 hr |
| **Eating skill** | Natural for most | Degrades with fatigue; must practice eating when tired |
| **Sleep-eat interaction** | N/A | Even 20 min nap restores appetite more than any drug |
| **Deficit management** | Preventable (match intake to expenditure) | Inevitable (manage it, don't fight it) |

Source: nutrition-ultra.md [R][E]

---

## 10. Pre-Event Nutrition & Taper-Week Pitfalls

### Under-Fueling Threshold Sessions Before an Event

- **Under-fueling threshold sessions during the build phase sabotages multi-day adaptation** -- this applies directly to taper week. Athletes reducing volume often also unconsciously reduce food intake, creating an energy deficit that impairs glycogen supercompensation and hormonal recovery. Maintain caloric intake even as training load drops [E] (TMT-74)

### Morning Pre-Hydration for Race Day

- **Morning pre-hydration is a requirement for race-day starts** -- begin hydrating 2-3 hours before the start with 500-750 mL containing sodium (400-600 mg). This is especially critical for evening starts (like a 6 PM brevet start) where riders may not have been drinking deliberately during the day. Dehydration at the start line compounds every subsequent hour [E] (TMT-74)

---

## 11. Common Mistakes

1. **Trying to match expenditure with intake** -- causes GI disaster in ultras [E]
2. **All gels and drink mix beyond 12 hr** -- palatability fatigue and nausea; need real food [E]
3. **Skipping control stop meals to save time** -- eating costs 15-20 min; not eating costs hours later [E]
4. **Using NSAIDs during the event** -- markedly increases intestinal permeability and bleeding [R]
5. **Not practicing eating during long training rides** -- eating is a skill that degrades with fatigue [E]
6. **Forcing intake during nausea** -- 30-60 min pause is better than vomiting (which creates larger deficit) [E]
7. **Caffeine continuously from hour 0** -- depletes effectiveness; save for when needed [E]
8. **No savory food options** -- mandatory beyond 12 hr; carry variety [E]
9. **Ignoring sleep's effect on eating** -- 20 min nap is the best anti-nausea intervention [E]
10. **Large sugar boluses at 2-5 AM** -- reactive hypoglycemia risk from circadian insulin sensitivity nadir [R]

---

## 12. Key Numbers for Computational Modeling

| Parameter | Value | Source |
|---|---|---|
| Energy expenditure at 200W | ~720 kcal/hr | GE ~23% [R] |
| Practical carb intake 0-6 hr | 80-120 g/hr | Well-supported [R] |
| Practical carb intake 6-12 hr | 60-90 g/hr | Gut fatigue onset [R][E] |
| Practical carb intake 12-24 hr | 40-70 g/hr | Palatability/GI limited [E] |
| Practical carb intake 24-48 hr | 30-60 g/hr | Highly individual [E] |
| Fat oxidation at Fatmax (trained) | 0.5-1.0 g/min | Venables et al. 2005 [R] |
| Fatmax intensity (trained) | 55-70% VO2max | Achten & Jeukendrup 2003 [R] |
| Adipose energy (75 kg, 10% BF) | ~67,500 kcal | Essentially unlimited [R] |
| GI distress prevalence (24+ hr) | 60-90% | de Oliveira et al. 2014 [R] |
| Max caffeine/24 hr | 800-1,000 mg | Side-effect threshold [E] |
| Insulin resistance after 1 night no sleep | +20-30% | Donga et al. 2010 [R] |
| Metabolic increase cold (shivering) | 2-5x resting | Haman et al. 2002 [R] |
| EA impairment threshold | <30 kcal/kg FFM/day | Mountjoy et al. 2018 [R] |
| Typical 600 km deficit | 4,000-6,000 kcal | Manageable [E] |
| Typical 1200 km deficit | 10,000-20,000 kcal | 1.5-3 kg fat equivalent [E] |

---

## Platform Module Hints

- Duration-adjusted CHO intake rate recommendations (decay function from 120 to 30 g/hr)
- Fat oxidation model: as glycogen depletes, fat contribution rises even at fixed intensity
- GI risk scoring: intensity x duration x temperature x sleep debt
- Sleep-eat-ride cycle optimizer for multi-day events
- Energy deficit tracker with RED-S warning thresholds
- Pacing optimizer: show how 5-10% power reduction extends sustainable fueling

## Cross-References

- [Fueling Fundamentals](fueling-fundamentals.md) — Core oxidation models, glycogen math, and crossover concept that ultra pacing leverages for fat-dominant fueling
- [Race-Day Nutrition](race-day-nutrition.md) — Protocols for events up to 8 hours; ultra strategies diverge beyond this threshold
- [Hydration & Electrolytes](hydration-electrolytes.md) — Multi-day cumulative fluid/sodium challenges and hyponatremia risk in slow-paced ultras
- [Supplements & Ergogenic Aids](supplements-ergogenic.md) — Multi-day caffeine budget strategy and creatine for sleep-deprived cognition
- [Ultra-Endurance](../concepts/ultra-endurance.md) — Training specifics for 200km+ events including durability, pacing, and kJ/kg methodology
- [Pacing Strategy](../concepts/pacing-strategy.md) — 5-10% power reduction at ultra pace dramatically shifts fuel partitioning toward fat
- [Durability & Fatigue](../concepts/durability-fatigue.md) — GI function degrades with cumulative fatigue; most ultra DNFs are nutritional, not musculoskeletal
- Source: nutrition-ultra.md (primary), nutrition-modeling.md, nutrition-racing.md, ec-master-reference.md, Persp-41, WD-59, TMT-50
- TrainingPeaks: "Differentiating Training and Racing Nutrition" (Hodges), "Understanding Nutrition Periodization" (Odell)
