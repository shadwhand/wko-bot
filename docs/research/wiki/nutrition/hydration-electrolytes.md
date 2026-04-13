# Hydration & Electrolytes

Fluid intake rates, sodium requirements, sweat rate calculation, temperature effects, hyponatremia risk, and practical guidelines.

Evidence levels: **[R]** = Research-backed, **[E]** = Experience-based, **[O]** = Opinion.

---

## 1. Sweat Rate Estimation

### Typical Ranges for Cycling

| Condition | Sweat Rate (L/hr) | Notes |
|---|---|---|
| Cool, easy pace | 0.3-0.5 | Low metabolic heat |
| Temperate, moderate effort | 0.7-0.9 | Standard outdoor ride |
| Indoor trainer, moderate | 1.2-1.5 | No convective cooling |
| Hot outdoor | 1.0-1.5 | Significant evaporative demand |
| Hot and humid | 1.3-1.8 | Impaired evaporation increases sweating |
| Race effort, hot | 1.5-2.5 | Extreme heat + high power |

Source: nutrition-modeling.md (78 kg reference cyclist) [R]

### Empirical Sweat Rate Model

```
SR = SR_base x f(power) x f(temperature) x f(humidity) x f(body_mass) x f(acclimation)
```

**Power factor:**
```
f(power) = 0.3 + 0.7 x (P / P_max)^0.8
```

**Temperature factor:**
```
f(temperature) = 0.5 + 0.5 x (T_ambient - 10) / 25    [clamp 0.5 to 1.5]
```

**Humidity factor:**
```
f(humidity) = 1.0 + 0.3 x (RH - 0.50) / 0.50           [clamp 0.85 to 1.30]
```

**Body mass factor:**
```
f(body_mass) = BM / 75    [linear scaling]
```

**Acclimation factor:**
```
f(acclimation) = 1.0 (unacclimated) to 1.3 (fully heat acclimated, ~10-14 days)
```

Source: nutrition-modeling.md [R]

### Metabolic Heat-Based Derivation

```
Total metabolic rate = Power / GE
Heat production = Metabolic rate - Power = Power x (1/GE - 1)
Theoretical sweat (L/hr) = Heat (kJ/hr) / 2,426 kJ/L
Actual sweat ≈ 50-70% of theoretical (convection/radiation handle rest)
```

Example at 290W, GE 0.225: Heat = 999W = 3,596 kJ/hr. Theoretical sweat = 1.48 L/hr. Actual ~0.9-1.0 L/hr outdoors at 20C with airflow. [R]

### Self-Measurement Protocol

The gold standard for individuals [E]:
1. Weigh nude before ride
2. Ride 60 min at target intensity
3. Track all fluid consumed (mL)
4. Weigh nude after ride
5. Sweat rate (L/hr) = (Pre-weight - Post-weight + Fluid consumed) / Duration(hr)

Repeat in different conditions to build a personal lookup table.

---

## 2. Fluid Intake Recommendations

### Target: Replace 50-80% of Sweat Losses

- Trying to match 100% is neither necessary nor practical [R]
- **Acceptable deficit**: Up to 2-3% body mass loss does NOT impair cycling performance in most conditions [R] (Goulet 2011; Wall et al. 2015)
- The old "2% threshold" has been increasingly challenged [R]
- **Practical intake**: 400-800 mL/hr for most conditions [R]

### The 2% Rule Is Context-Dependent

The relationship between dehydration and performance depends heavily on temperature [R]:

```
PF_hydration = 1.0 - k_base x max(0, BM_loss% - threshold%) x T_modifier

T_modifier = 0.5 + 0.5 x (T_ambient - 15) / 20      [clamp 0.5 to 1.5]
threshold% = 3.0 - T_modifier x 1.0                    [clamp 1.5 to 3.0]
```

- At 15C: threshold ~3% BM loss before performance impact; k_dehy per % is small [R]
- At 35C: threshold ~1.5% BM loss; k_dehy per % is large [R]
- Outdoor cycling with airflow is far more tolerant of dehydration than indoor/lab settings [R]

Source: nutrition-modeling.md, Goulet 2011 [R]

### "Drink to Thirst" vs Planned Intake

| Context | Strategy | Rationale |
|---|---|---|
| Events <2-4 hr | Drink to thirst | Adequate for most athletes; prevents overdrinking [R] |
| Events >4 hr | Planned intake with flexibility | Thirst may lag, especially in heat and during sleep deprivation [E] |
| Hot conditions | Planned with thirst adjustment | Thirst perception can lag thermal demand [R] |
| Cold conditions | Proactive reminders | Cold blunts thirst; insidious dehydration risk (Kenefick et al. 2008) [R] |
| Sleep-deprived riding | Proactive reminders | Thirst perception blunted [E] |

### Fluid Balance Model

```
BM_loss(t) = Integral(SR) - Integral(Fluid_intake) - Metabolic_water + Respiratory_water_loss
```

- Metabolic water: ~0.13 L/hr at moderate exercise (byproduct of substrate oxidation) [R]
- Respiratory water loss: ~0.1-0.3 L/hr depending on ventilation and humidity [R]

---

## 3. Sodium

### Sweat Sodium Concentration

- Highly individual, genetically determined: **20-80 mmol/L** (460-1,840 mg Na/L) [R]
- Average: ~40-50 mmol/L (~1,000-1,150 mg Na/L) [R]
- NOT meaningfully trainable -- does not change with diet, acclimatization, or day-to-day (Baker 2017) [R]
- Heat acclimation reduces concentration by ~20-40% (sweat more, but more dilute) [R]

### Sodium Loss Calculation

```
Na_loss (mg/hr) = Sweat_rate (L/hr) x Sweat_Na_concentration (mg/L)
```

Example: 1.0 L/hr x 1,000 mg/L = **1,000 mg Na/hr lost**

### Cumulative Sodium Loss Estimates

| Duration | Sweat Volume (moderate) | Sodium Loss (avg sweater) |
|---|---|---|
| 6 hr | 3-6 L | 3,000-6,000 mg |
| 12 hr | 6-12 L | 6,000-12,000 mg |
| 24 hr | 10-20 L | 10,000-20,000 mg |
| 48 hr | 15-30 L | 15,000-30,000 mg |

Source: nutrition-ultra.md [R]

### Sodium Replacement Guidelines

| Context | Sodium Intake | Notes |
|---|---|---|
| Events <4 hr | Not required during exercise | Daily balance is what matters (Persp-41) [R] |
| Events 4-8 hr | 300-600 mg/hr | Via electrolyte drink + food |
| Hot conditions | 700-1,500 mg/hr | Heavy/salty sweaters need more |
| Ultra events (12+ hr) | 500-1,000 mg/hr | See [Ultra Nutrition](ultra-nutrition.md) |

### Sodium Sources

| Source | Na Content |
|---|---|
| Most commercial drink mixes | 300-500 mg Na/L |
| Heavy-sweater mixes | 800-1,500 mg Na/L |
| Salt capsule | 200-400 mg per cap |
| Energy gel | 25-200 mg per packet |
| Pretzels (1 packet) | 400-600 mg |
| Broth/soup (1 cup) | 800-1,200 mg |

Source: nutrition-racing.md, nutrition-ultra.md [R][E]

### Salt Loading Pre-Event

- Consuming extra sodium in 24-48 hr before an event can expand plasma volume by 3-5% [R] (Sims et al. 2007)
- Improves thermoregulation and delays cardiovascular drift [R]
- Practical: add 1,500-2,000 mg Na/day to normal diet in 24-48 hr pre-event [E]
- Not recommended for athletes on blood pressure medications [E]

---

## 4. Sweat Tests: Useful or Not?

### EC Perspective: Nearly Useless (Persp-41)

- Sweat composition changes with training state, intensity, diet, and day-to-day [R]
- No strong evidence you need to replace electrolytes during exercise <4 hours [R]
- Daily sodium balance matters more than acute replacement [R]

### Precision Hydration Perspective (TrainingPeaks)

- Sweat sodium concentration is genetically determined and does not vary much [R]
- Advanced Sweat Test at rest gives consistent results [R]
- Athletes who replaced sodium finished a half-Ironman 26 min faster (Del Coso et al. 2015) [R]

### Synthesis

**Conflict**: EC (Podlogar) says sweat tests are nearly useless; Precision Hydration says they are valuable. The resolution: for events <4 hr, acute electrolyte replacement is likely unnecessary. For events >4 hr in heat, knowing your approximate sweat sodium range helps calibrate intake. A one-time lab test is more useful than repeated field tests. Daily overall sodium balance is the primary lever.

---

## 5. Hyponatremia

### Mechanism

Exercise-Associated Hyponatremia (EAH): serum Na drops below 135 mmol/L. Caused primarily by **overdrinking** relative to sodium intake, not by sodium loss alone. [R] (Noakes; Hew-Butler et al. 2015)

### Risk Factors

| Factor | Why |
|---|---|
| Slow pace | More time = more opportunity to overdrink |
| High fluid availability | Aid stations every mile |
| Warm conditions | Perceived need to drink more |
| Female sex | Lower body mass, less total body water |
| NSAIDs | Impair renal free water clearance |
| Low body mass | Smaller dilution buffer |

Source: nutrition-ultra.md, Hoffman et al. 2013 [R]

### Prevalence

- 5-15% asymptomatic in ultramarathons [R]
- 1-3% symptomatic [R]
- 10% of Frankfurt Ironman finishers were borderline hyponatremic (2005-2013 study) [R]
- Over 50% of ultra-run participants in some studies [R]

### Symptoms

| Severity | Symptoms |
|---|---|
| Early | Nausea, cramps, lethargy (similar to dehydration -- easy to misdiagnose) |
| Moderate | Puffy fingers/ankles, confusion, headache |
| Severe | Seizures, coma, death |

Source: TrainingPeaks "What You Should Know About Hyponatremia" (Ritter) [R]

### Prevention

1. **Drink to thirst** -- do NOT force fluid on a schedule [R]
2. Include sodium with fluid (especially events >4 hr) [R]
3. Avoid NSAIDs during events [R]
4. Know your risk profile (pace, conditions, sex, body mass) [E]
5. If urine is clear and frequent during an event, you are likely overdrinking [E]

---

## 6. Other Electrolytes

| Electrolyte | Sweat Loss | Replacement Needed? | Notes |
|---|---|---|---|
| Potassium | ~5-10 mmol/L sweat | Rarely | Bananas, potatoes, most food sufficient |
| Magnesium | ~0.5-1.5 mmol/L sweat | Chronic concern, not acute | Depletion is a training issue, not event issue |
| Calcium | Modest | No | Not a primary concern during events |

Source: nutrition-ultra.md [R]

---

## 7. Cramping -- Current Evidence

### Old Theory: Electrolyte Depletion

- Largely supplanted by the **neuromuscular fatigue theory** (Schwellnus et al. 2009) [R]
- Sodium supplementation has NOT been convincingly shown to prevent exercise-associated muscle cramps in controlled trials (Schwellnus et al. 2011) [R]

### Current Understanding

- Cramps most associated with: excessive intensity relative to training, fatigue, altered motor neuron excitability [R]
- Pickle juice / vinegar reduces cramp duration via oropharyngeal TRP channel activation (a neural reflex), NOT systemic electrolyte correction (Miller et al. 2010) [R]
- Many ultra riders report empirically that salt helps -- likely because salt is co-consumed with fluid and calories, addressing multiple deficits simultaneously [E]

---

## 8. Temperature Effects on Hydration

### Heat

- Sweat rates can reach 1.5-2.5 L/hr in extreme heat [R]
- 24-hr event in 35C+ may require 20-40 L fluid replacement [R]
- Heat stress directly increases intestinal permeability (Snipe et al. 2018) [R]
- Gastric emptying slowed in hyperthermia [R]
- Heat increases CHO utilization ~15% per C above 38C core temp [R]
- Creates vicious circle: more CHO needed, less absorbed [R]

**Practical heat adjustments:**
- Increase sodium to 1,000-1,500 mg/hr [E]
- Shift calories toward liquid/semi-liquid forms [E]
- Pre-cooling and cooling strategies reduce GI distress indirectly [R]
- Reduce intensity to preserve splanchnic blood flow [R]

### Cold

- Cold blunts thirst perception (Kenefick et al. 2008) [R]
- Cold-induced diuresis increases urine output, compounding dehydration [R]
- Riders underdrink in cold, leading to insidious dehydration [E]
- CHO demand increases (shivering thermogenesis can reach 2-5x resting metabolic rate) [R]

**Practical cold adjustments:**
- Actively remind yourself to drink (set timer if necessary) [E]
- Warm fluids (tea, broth, warm sports drink) aid compliance and core temp [E]
- Increase caloric intake by 10-20% during cold sections [E]

---

## 9. Key Parameters for Computational Modeling

| Parameter | Symbol | Typical Value | Unit |
|---|---|---|---|
| Sweat sodium concentration | sweat_Na | 20-80 (avg 45) | mmol/L |
| Sweat rate (moderate cycling) | SR | 0.5-1.5 | L/hr |
| Fluid intake target | fluid_in | 400-800 | mL/hr |
| Acceptable BM loss (temperate) | bm_threshold | 2-3 | % |
| Acceptable BM loss (hot) | bm_threshold_hot | 1.5-2 | % |
| Na replacement (events >4 hr) | na_replace | 300-1,000 | mg/hr |
| Dehydration performance penalty | k_dehy | 0.03-0.05 | per % BM beyond threshold |
| Heat acclimation sweat multiplier | accl | 1.0-1.3 | factor |

Source: nutrition-modeling.md, nutrition-racing.md, nutrition-ultra.md [R]

---

## Platform Module Hints

- Hydration model: sweat rate from power + temperature + humidity + body mass
- Sodium budget tracker: cumulative losses vs intake
- Dehydration performance penalty integrated with bonk prediction model
- Heat index overlay on ride plans
- Hyponatremia risk flag for slow-paced, long events with high fluid availability

## Cross-References

- [Fueling Fundamentals](fueling-fundamentals.md) — Metabolic heat production models that drive sweat rate estimation
- [Race-Day Nutrition](race-day-nutrition.md) — Integrated race-day fluid + food protocol where hydration and fueling interact
- [Ultra Nutrition](ultra-nutrition.md) — Multi-day hydration challenges, cumulative sodium losses (10,000-30,000 mg), and sleep-deprivation effects on thirst
- [Supplements & Ergogenic Aids](supplements-ergogenic.md) — Sodium as ergogenic aid in heat; caffeine's diuretic effects are negligible at exercise doses
- [Heat, Altitude & Environment](../concepts/heat-altitude-environment.md) — Temperature and humidity directly modulate sweat rate, dehydration threshold, and GI function
- [Ironman Triathlon](../entities/ironman-triathlon.md) — Kona heat/humidity creates extreme hydration demands; 10% of IM finishers are borderline hyponatremic
- Source: nutrition-modeling.md Sec 6, nutrition-racing.md Sec 3, nutrition-ultra.md Sec 5, ec-master-reference.md, Persp-41
- TrainingPeaks: "Why Athletes Need Sodium" (Blow), "What You Should Know About Hyponatremia" (Ritter), "Do Weather Changes Warrant Nutrition Changes" (Kattouf)
