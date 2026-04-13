# Fueling Fundamentals

Core science of exercise metabolism, carbohydrate oxidation, glycogen dynamics, and energy expenditure models for cycling.

Evidence levels: **[R]** = Research-backed, **[E]** = Experience-based, **[O]** = Opinion.

---

## 1. Energy Expenditure from Power

The definitive advantage cyclists have over other athletes: a power meter converts directly to caloric cost.

### Core Formula

```
EE (kcal/hr) = Power (W) x 3.6 / (GE x 4.184)
             = Power (W) x 0.8604 / GE
```

where GE = Gross Efficiency (mechanical work / total metabolic cost). [R]

### Gross Efficiency Ranges

| Athlete Level | GE Range | Typical |
|---|---|---|
| Untrained | 18-21% | 19.5% |
| Recreational cyclist | 20-22% | 21% |
| Trained cyclist | 22-24% | 23% |
| Elite cyclist | 23-25% | 24% |

Source: nutrition-modeling.md, Coyle 1995, Jeukendrup & Wallis 2005 [R]

### How GE Varies

GE is not constant. Critical modifiers [R]:

1. **Intensity** -- GE peaks at ~50-75% VO2max and declines above threshold as anaerobic costs rise. At FTP, GE drops ~1-2 percentage points from peak. Above threshold the decline accelerates.
2. **Training status** -- Trained > untrained by 2-4 percentage points (mitochondrial density, pedaling technique, fiber recruitment).
3. **Substrate mix** -- CHO oxidation is ~5-8% more "efficient" per liter O2 than fat (higher P/O ratio). As intensity rises and CHO fraction increases, caloric equivalent per liter O2 rises.
4. **Fatigue/duration** -- GE declines ~0.5% per hour after hour 2 due to motor unit recruitment shifts, ventilatory work, and thermal strain.

### Worked Example (78 kg reference cyclist, FTP 290W)

| Intensity | Power | GE | EE (kcal/hr) |
|---|---|---|---|
| Endurance (65% FTP) | 190W | 23.0% | 711 |
| Sweet spot (88% FTP) | 255W | 23.5% | 934 |
| Threshold (FTP) | 290W | 22.5% | 1,109 |
| VO2max | 410W | 20.5% | 1,722 |

Source: nutrition-modeling.md [R]

### Energy Estimation Error is Massive

- GE assumption alone creates ~900 kcal swing on a 4,000 kJ day [R] (Persp-41)
- Nutrition labels have 20% error allowed [R]
- Absorption efficiency is 85-95%, not 100% [R]
- Thermic effect of food: ~10% of ingested kcal lost to digestion [R]
- Doubly labeled water (DLW) studies show 10-15% overestimation vs actual intake [R]
- **Platform implication**: Display confidence intervals, not point estimates (Persp-41) [R]

### TDEE Is Not BMR + Bike kJ

- Off-bike expenditure in active athletes = 1.6-2.3x predicted BMR [R] (TMT-50)
- Ignoring TEF (~10%) and NEAT produces systematic underestimates
- Tour de France DLW studies confirm athletes chronically undercount energy needs

**Conflict with conventional wisdom**: "TDEE = BMR + bike kJ" is wrong. Must model off-bike expenditure. [R]

---

## 2. Substrate Partitioning (Fat vs Carbohydrate)

### The Crossover Concept

At low intensity, fat dominates. At high intensity, carbohydrate dominates. The crossover point is where CHO contribution exceeds 50%. [R] (Brooks & Mercier, 1994)

| Athlete Type | Crossover Point (% VO2max) | Fatmax (% VO2max) |
|---|---|---|
| Untrained | 40-50% | 35-45% |
| Trained endurance | 55-65% | 50-60% |
| Elite / fat-adapted | 60-70% | 55-65% |

Source: Achten & Jeukendrup 2003, Venables et al. 2005 [R]

### Oxidation Rates by Intensity (78 kg trained cyclist)

| Intensity (% VO2max) | ~IF | CHO (g/min) | Fat (g/min) | Total EE (kcal/min) |
|---|---|---|---|---|
| 25% | 0.35 | 0.5 | 0.5 | 5.7 |
| 55% | 0.60 | 1.5 | 0.6 | 10.7 |
| 65% | 0.75 | 2.2 | 0.5 | 12.6 |
| 75% | 0.88 | 3.0 | 0.3 | 14.5 |
| 85% | 1.00 | 3.8 | 0.1 | 16.5 |
| 100% | 1.18 | 4.5 | ~0 | 18.9 |

Source: Romijn et al. 1993, 2000; van Loon et al. 2001 [R]

### CHO Fraction Formula

```
cho_fraction = 0.30 + 0.70 x ((IF - 0.40) / 0.60)    [clamped 0-1]
```

Source: nutrition-racing.md [R]

### Fat Oxidation Peak (Fatmax)

- Trained cyclist Fatmax: 0.55-0.65 g/min at ~55-65% VO2max [R]
- Ultra-trained riders may hit 0.8-1.0 g/min (Venables et al., 2005)
- Fat oxidation at Fatmax = 324-540 kcal/hr from fat alone
- **Critical for ultras**: At proper pacing (0.55-0.70 IF), fat provides majority of fuel

### Key Principle: Body is an Energy Accountant, Not a Substrate Accountant

Total energy balance matters more than whether calories came from fat or carbs. Burning more carbs on the bike vs off the bike self-balances over 24 hours. [R] (Persp-41, TMT-50)

**Conflict with conventional wisdom**: "Replace the carbs you burned" is wrong. Must replace total energy, not just carb substrate. [R]

---

## 3. Carbohydrate Oxidation Rates

### Dual Transporter Model

The old ceiling of 60 g/hr (single transporter) has been replaced by dual-transporter strategies. [R]

| Transporter | Location | Substrate | Max Rate |
|---|---|---|---|
| SGLT1 | Small intestine apical | Glucose, galactose | ~60 g/hr (1.0 g/min) |
| GLUT5 | Small intestine apical | Fructose | ~30-40 g/hr (0.5-0.7 g/min) |
| GLUT2 | Basolateral membrane | Glucose, fructose | Not rate-limiting |

Source: Jeukendrup 2004, 2010; Podlogar & Wallis 2022 [R]

### Intake Recommendations by Duration

| Race Duration | Recommended CHO | Notes |
|---|---|---|
| < 45 min | Mouth rinse only | Central governor effect; no gut absorption needed |
| 45-75 min | Up to 30 g/hr | Single source sufficient |
| 1-2.5 hr | 60-90 g/hr | Dual transport beneficial above 60 g/hr |
| 2.5-6 hr | 90-120 g/hr | Dual transport required; gut training essential |

Source: King et al. 2022; Podlogar & Wallis 2022 [R]

### Glucose:Fructose Ratios

- Classic: **2:1** (Jeukendrup 2004) -- ~108 g/hr max exogenous oxidation [R]
- Revised: **1:0.8** (Rowlands et al. 2015; O'Brien et al. 2013) -- yields higher exogenous oxidation (~1.7-1.8 g/min vs ~1.5 g/min) because GLUT5 capacity is higher than assumed [R]
- Theoretical max: ~120 g/hr (1.2 g/min glucose + 0.8-1.0 g/min fructose) [R]

### Absorption Is Individual

- Lab test with 13C tracer can personalize max absorption rate [R] (Persp-41)
- Range: some absorb only 50 g/hr, others up to 150 g/hr [R]
- Gut training evidence for increasing absorption is currently weak [R] (Podlogar, Persp-41)
- **Platform implication**: Cap fueling recommendations at ~90 g/hr unless athlete has lab-tested higher ceiling

### Practical Absorption Rate Lookup

| CHO Source | Practical Max Intake (g/hr) | Max Oxidation (g/min) |
|---|---|---|
| Glucose only | 60 | 1.0 |
| Maltodextrin only | 60 | 1.0 |
| Glucose + Fructose (2:1) | 90 | 1.5 |
| Maltodextrin + Fructose (1:0.8) | 90-120 | 1.5-1.8 |
| Maltodextrin + Fructose (gut trained) | 100-140 | 1.5-2.0+ |

Source: nutrition-modeling.md [R]

### Intensity Modifier on Absorption

At >85% FTP, splanchnic blood flow decreases by 60-80%, impairing absorption. [R]

```
effective_absorption_rate = base_rate x (1 - 0.5 x max(0, (intensity_pct - 0.80) / 0.20))
```

- At moderate intensity (60-75% FTP): full 90-120 g/hr feasible with training
- At high intensity (>85% FTP): practical cap ~60-80 g/hr regardless of gut training
- **Heuristic**: Favor liquids and gels above 85% FTP; solid food absorption drops dramatically

Source: nutrition-racing.md [R]

---

## 4. Glycogen Stores and Depletion

### Storage Capacities

| Compartment | Normal (trained) | Supercompensated | Energy (kcal) |
|---|---|---|---|
| Muscle glycogen (whole body) | ~500 g | 600-700 g | 2,050-2,870 |
| Active leg muscles only | ~250 g | ~350 g | 1,025-1,435 |
| Liver glycogen | 60-120 g | ~130 g | 246-533 |
| Blood glucose | 4.5 g | 4.5 g | 18 |
| **Total endogenous CHO** | **~575-625 g** | **~735-835 g** | **~2,300-3,400** |

Note: 1 g glycogen = 4.1 kcal. Source: nutrition-modeling.md [R]

### Muscle Glycogen Concentration Units

- Untrained: 300-400 mmol/kg dry weight [R]
- Trained, normal diet: 400-500 mmol/kg dw [R]
- Supercompensated: 500-700+ mmol/kg dw [R]
- Depleted (post-exhaustive exercise): 50-150 mmol/kg dw [R]

### Depletion Rates by Intensity (500 g starting glycogen, no exogenous CHO)

| Intensity | Power | Muscle Glycogen Use (g/hr) | Time to Depletion (hr) |
|---|---|---|---|
| Z2 (~55% VO2max) | 190W | 40-55 | 9-12 |
| Tempo (~65% VO2max) | 230W | 60-80 | 6-8 |
| Sweet Spot (~75% VO2max) | 265W | 90-120 | 4-5.5 |
| Threshold (~85% VO2max) | 290W | 140-180 | 2.8-3.5 |
| VO2max (100%) | 410W | 200-270 | 1.8-2.5 |

Source: nutrition-modeling.md [R]

### Glycogen Budget Model

```
Starting glycogen (supercompensated): ~3,000-3,200 kcal (750-800 g)
Starting glycogen (normal diet):      ~2,000-2,400 kcal (500-600 g)

Net glycogen burn rate (kcal/hr) = CHO_burn_rate - Exogenous_supply_rate
Time to bonk (hr) = Usable_glycogen_kcal / Net_glycogen_burn_rate

where Usable_glycogen = Total x 0.75 (~25% trapped in inactive muscles)
```

Source: nutrition-racing.md [R]

### Worked Example: 70 kg rider, supercompensated, 250W @ 75% FTP

- Total metabolic: 935 kcal/hr
- CHO fraction at 75% FTP: ~0.75
- CHO burn: 175 g/hr (700 kcal/hr from CHO)
- Exogenous intake at 90 g/hr: 360 kcal/hr
- Net endogenous drain: 340 kcal/hr
- Usable glycogen: 2,250 kcal
- **Time to bonk: ~6.6 hr** (with fueling) vs **~3.2 hr** (without fueling)

Source: nutrition-racing.md [R]

### On-Bike Fueling Does NOT Spare Muscle Glycogen

- Confirmed by Podlogar (Persp-41): exogenous carbs spare liver glycogen, not muscle glycogen [R]
- >67 g/hr on bike is the threshold for meaningful liver glycogen sparing [R]
- Muscle glycogen sparing from exogenous CHO is only ~10-25% (modest, not 1:1) [R]

### kJ as Bonk Predictor

- Bonk risk significant at ~1,500-2,000 kJ cumulative work without adequate fueling [E]
- With good fueling: 3,000-5,000+ kJ sustainable [E]

---

## 5. Gut Training

### Mechanism

Chronic high-CHO intake during exercise upregulates SGLT1 transporter density in intestinal mucosa. [R] (Cox et al. 2010)

```
SGLT1_max_trained = SGLT1_max_baseline x (1 + 0.3 x gut_training_factor)
```

where gut_training_factor ranges 0 (no training) to 1 (fully adapted). [R]

### Protocol

- Systematic increase over 2-4 weeks [R]
- Start at ~60 g/hr, add ~10 g/hr per week
- Practice during training rides at race intensity
- GI distress incidence drops from ~30-50% to <10% at high intake rates with training [R]

### Caveats

- Evidence for increasing absorption is currently weaker than commonly believed (Podlogar, Persp-41) [R]
- Individual GI tolerance varies hugely; some athletes cannot tolerate >60 g/hr regardless of type [E]
- GI distress is common above 80 g/hr and is the practical limit for many athletes [E]

---

## 6. "Train Low" -- A Molecular Dead End

### AMPK Mechanism

- AMPK beta subunit has a glycogen-binding domain (GBD) [R] (WD-54)
- High glycogen physically binds and inhibits AMPK; low glycogen releases the inhibition [R]
- This is independent of AMP/ATP status [R]

### Performance Evidence: Consistently Negative

- Low glycogen training increases fat oxidation but impairs high-intensity training capacity [R]
- Delayed feeding impairs recovery, disrupts metabolic health, decreases next-day performance [R]
- **Platform stance**: Do NOT build "train low" recommendations. Model glycogen depletion as a cost to recovery, not a training stimulus. (WD-54) [R]

**Conflict with conventional wisdom**: "Train low to get fat-adapted" has real molecular mechanism but zero performance benefit. [R]

---

## 7. Key Parameters for Computational Modeling

| Parameter | Symbol | Typical Value | Unit |
|---|---|---|---|
| Gross mechanical efficiency | GE | 0.20-0.25 | fraction |
| Max exogenous CHO oxidation (trained gut) | exo_max | 90-120 | g/hr |
| Glucose:fructose ratio | GF_ratio | 1:0.8 | -- |
| Glycogen store (supercompensated) | gly_super | 34-46 | kcal/kg BM |
| Glycogen store (normal) | gly_norm | 23-29 | kcal/kg BM |
| Usable fraction of glycogen | gly_usable | 0.70-0.80 | fraction |
| CHO fraction at % FTP | cho_frac | 0.30 + 0.70x((I-0.40)/0.60) | clamped [0,1] |
| Thermic effect of food | TEF | 0.10 | fraction |
| TDEE off-bike multiplier | tdee_mult | 1.6-2.3x BMR | -- |
| Absorption reduction at high intensity | abs_penalty | see formula Sec 3 | fraction |
| GE decline with duration | ge_drift | -0.5%/hr after hr 2 | %/hr |
| Max sustainable metabolic scope | met_scope | 2.5x BMR (3x elite) | ratio |
| Energy compensation factor | comp | ~30% at moderate exercise | fraction |

Source: nutrition-racing.md, nutrition-modeling.md, ec-master-reference.md

---

## Platform Module Hints

- `nutrition.py`: Update default `baseline_intake_g_hr` to 75 (midpoint of 60-90 range)
- Add absorption ceiling check based on individual lab data or 90 g/hr default
- Display energy estimation with confidence intervals, not point estimates
- Model on-bike vs off-bike carb distribution (higher on-bike can squeeze recovery budget)
- kJ-based bonk prediction with glycogen budget overlay

## Cross-References

- [Race-Day Nutrition](race-day-nutrition.md) — Applied competition protocols built on these oxidation and expenditure models
- [Ultra Nutrition](ultra-nutrition.md) — Extended-duration energy deficit management and fat oxidation at ultra intensity
- [Hydration & Electrolytes](hydration-electrolytes.md) — Sweat rate models depend on metabolic heat production calculated here
- [Supplements & Ergogenic Aids](supplements-ergogenic.md) — Caffeine, nitrates, and their interaction with substrate utilization
- [Endurance Base Training](../concepts/endurance-base-training.md) — Zone 2 and LT1 training directly relates to crossover point and fat oxidation
- [Durability & Fatigue](../concepts/durability-fatigue.md) — GE decline with duration (~0.5%/hr after hr 2) links metabolic cost to fatigue modeling
- [Ironman Triathlon](../entities/ironman-triathlon.md) — Energy expenditure estimates (8,000-10,000 kcal) and caloric deficit in long-course racing
- Source: nutrition-modeling.md, nutrition-racing.md, ec-master-reference.md Sec 4, Persp-41, WD-59, TMT-50, TMT-73
- TrainingPeaks: "Fueling Insights vs Gross Efficiency" (San Millan), "Fueling for Performance" (Bobo), "Zone 2 Training and Fat Burning" (Bobo)
