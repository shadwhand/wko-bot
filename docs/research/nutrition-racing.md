# Nutrition for Competitive Cycling Races: Evidence-Based Research Synthesis

Below is a structured synthesis of the current scientific evidence, organized for computational modeling. All recommendations are grounded in peer-reviewed literature through early 2025.

---

## 1. Carbohydrate Intake Rates During Racing

### Current Consensus

The field has shifted significantly since ~2019. The old ceiling of 60 g/hr (single transporter) has been replaced by dual-transporter strategies exploiting separate intestinal absorption pathways for glucose (SGLT1) and fructose (GLUT5).

**Key numbers:**

| Race Duration | Recommended CHO Intake | Notes |
|---|---|---|
| < 45 min | Mouth rinse only | No gut absorption needed; central governor effect |
| 45–75 min | Up to 30 g/hr | Single source sufficient |
| 1–2.5 hr | 60–90 g/hr | Dual transport becomes beneficial above 60 g/hr |
| 2.5–6 hr | 90–120 g/hr | Dual transport required; gut training essential |

**Glucose:Fructose Ratios:**
- Classic recommendation: **2:1** (Jeukendrup, 2004; ~1.2 g/min glucose + 0.6 g/min fructose = ~108 g/hr max)
- Revised recommendation: **1:0.8** (Rowlands et al., 2015; O'Brien et al., 2013). This ratio yields higher total exogenous oxidation rates (~1.7–1.8 g/min vs ~1.5 g/min for 2:1) because GLUT5 capacity is higher than previously assumed.
- Practical upper bound of intestinal absorption: ~1.2 g/min glucose via SGLT1, ~0.8–1.0 g/min fructose via GLUT5, total ~2.0 g/min = **120 g/hr** theoretical max.

**Key references:**
- Jeukendrup AE. (2004) *Carbohydrate intake during exercise and performance.* Nutrition, 20(7-8), 669-677.
- Jeukendrup AE. (2010) *Carbohydrate and exercise performance: the role of multiple transportable carbohydrates.* Current Opinion in Clinical Nutrition & Metabolic Care, 13(4), 452-457.
- Rowlands DS et al. (2015) *Fructose-glucose composite carbohydrates and endurance performance.* Sports Medicine, 45(3), 381-400.
- King AJ et al. (2022) *An evidence-based approach for providing athletes with in-competition carbohydrate recommendations.* Sports Medicine, 52(12), 2843-2859.
- Podlogar T & Wallis GA. (2022) *New horizons in carbohydrate research and application for endurance athletes.* Sports Medicine, 52(S1), 5-23.

**Gut Training Protocol:**
- Systematic increase over 2–4 weeks, starting at ~60 g/hr, adding ~10 g/hr per week
- Practice during training rides at race intensity
- The gut is highly adaptable: repeated exposure upregulates SGLT1 transporter expression in intestinal mucosa (Cox et al., 2010)
- Gut training reduces GI distress incidence from ~30–50% to <10% at high intake rates

**Intensity modifier for modeling:**
- At higher intensities (>85% FTP), splanchnic blood flow decreases by 60–80%, impairing absorption. Practical cap at very high intensity: ~60–80 g/hr regardless of training.
- At moderate intensity (60–75% FTP), full 90–120 g/hr absorption is feasible with training.
- Formula heuristic: `effective_absorption_rate = base_rate * (1 - 0.5 * max(0, (intensity_pct - 0.80) / 0.20))`

---

## 2. Pre-Race Fueling & Glycogen Loading

### Glycogen Loading Protocols

**Classic (Bergstrom et al., 1967):** 3-day depletion + 3-day supercompensation. Outdated — unnecessary suffering.

**Modified (Sherman et al., 1981; Bussau et al., 2002):**
- **1-day protocol (Bussau):** Single exhaustive bout followed by 24 hr of 10–12 g CHO/kg/day. Achieves ~90% of multi-day protocols.
- **2–3 day taper protocol (Sherman):** Taper training + 10–12 g CHO/kg/day for 36–48 hr. This is the current standard.
- Achievable glycogen: **700–900 mmol/kg dry weight** (supercompensated) vs ~400–500 mmol/kg (normal mixed diet).
- Total body glycogen stores (supercompensated): **~600–800 g** (~2400–3200 kcal) in a 70 kg trained cyclist. Breakdown: ~400–500 g muscle, ~100–120 g liver.

**Pre-race meal (3–4 hr before start):**
- 2–4 g CHO/kg body mass
- Low fiber, low fat, moderate protein
- Example for 70 kg rider: 140–280 g CHO = 560–1120 kcal from carbs
- Familiar, practiced foods only

**Final 60 min before race:**
- Historically debated ("reactive hypoglycemia" concern). Current evidence: **not a meaningful risk** in most athletes during exercise (Moseley et al., 2003). The insulin response is overridden once exercise begins.
- 30–60 g CHO in last 30 min is acceptable if tolerated.
- Avoid consuming 75–150 g of simple sugars exactly 30–45 min before start without exercise onset — this is the narrow window where rebound hypoglycemia can transiently impair early performance in susceptible individuals.

**Key references:**
- Bussau VA et al. (2002) *Carbohydrate loading in human muscle: an improved 1 day protocol.* European Journal of Applied Physiology, 87(3), 290-295.
- Burke LM et al. (2011) *Carbohydrates for training and competition.* Journal of Sports Sciences, 29(S1), S17-S27.
- Thomas DT et al. (2016) *ACSM Joint Position Statement: Nutrition and Athletic Performance.* Medicine & Science in Sports & Exercise, 48(3), 543-568.

**For modeling:**
- `initial_glycogen_kcal = body_mass_kg * glycogen_per_kg` where `glycogen_per_kg` = 34–46 kcal/kg (supercompensated) or 23–29 kcal/kg (normal diet)
- Approximately: supercompensated ~40 kcal/kg, normal ~25 kcal/kg

---

## 3. Hydration & Electrolytes

### Sweat Rate Estimation

**Typical range for cycling:** 0.5–2.5 L/hr depending on intensity, temperature, humidity, body size, acclimatization.

**Estimation formula (rough):**
- `sweat_rate_L_hr = 0.5 + 0.013 * (temp_C - 15) + 0.004 * relative_humidity_pct + 0.3 * (intensity_fraction - 0.5)`
- This is a simplified heuristic. Real-world: weigh before/after training to individualize.

**More precise from metabolic heat:**
- Total metabolic rate from power: `metabolic_watts = power_watts / mechanical_efficiency` (efficiency ~0.20–0.25)
- Heat production: `heat_watts = metabolic_watts - power_watts`
- Evaporative cooling requirement drives sweat rate: `sweat_L_hr = heat_watts * 3600 / (2.43e6)` (latent heat of vaporization ~2.43 MJ/kg)
- This gives theoretical max; actual is modified by convective/radiative cooling (~30–50% of heat loss at moderate speeds), so real sweat ≈ 50–70% of this theoretical value.

### Drinking Recommendations

- **Target:** Replace 50–80% of sweat losses. Trying to match 100% is neither necessary nor practical.
- **Acceptable deficit:** Up to 2–3% body mass loss does not impair cycling performance in most conditions (Goulet, 2011; Wall et al., 2015). The older "2% threshold" has been challenged.
- **Hyponatremia risk:** Primarily from overdrinking (>sweat rate), not underdrinking. Slower riders in longer events are most at risk.
- **Practical intake:** 400–800 mL/hr for most conditions.

### Sodium

- Sweat sodium concentration: **20–80 mmol/L** (highly individual, genetically determined, not meaningfully trainable). Average ~40–50 mmol/L.
- Sodium loss: `sodium_mg_hr = sweat_rate_L_hr * sweat_Na_mmol_L * 23` (molar mass of Na)
- At 1.0 L/hr sweat and 50 mmol/L: **1,150 mg Na/hr lost**.
- Replacement: 300–1000 mg sodium/hr in race fluid, depending on sweat rate and concentration.
- Most commercial drink mixes: 300–500 mg Na/L. For heavy/salty sweaters: 800–1500 mg Na/L or supplemental salt capsules.

**Key references:**
- Sawka MN et al. (2007) *ACSM Position Stand: Exercise and Fluid Replacement.* Medicine & Science in Sports & Exercise, 39(2), 377-390.
- Goulet EDB. (2011) *Effect of exercise-induced dehydration on time-trial exercise performance.* British Journal of Sports Medicine, 45(14), 1101-1105.
- Baker LB. (2017) *Sweating rate and sweat sodium concentration in athletes.* Sports Medicine, 47(S1), 111-128.

---

## 4. Caffeine

### Performance Effect

Meta-analyses consistently show **2–4% improvement** in endurance time-trial performance (Southward et al., 2018; Guest et al., 2021).

### Dosing

| Parameter | Value |
|---|---|
| Optimal dose | **3–6 mg/kg body mass** |
| Minimum effective | ~2 mg/kg |
| Diminishing returns above | ~6 mg/kg (more GI distress, no additional benefit) |
| Toxic threshold | >9 mg/kg (tremor, tachycardia, GI issues) |
| For 70 kg rider | 210–420 mg (roughly 2–4 strong espressos) |

### Timing

- **Peak plasma concentration:** 30–60 min post-ingestion (oral). Half-life ~3–5 hr.
- **Pre-race protocol:** 3–6 mg/kg taken 40–60 min before start.
- **During race (long events):** Additional 1–2 mg/kg at mid-point or when fatigue accumulates. Late-race caffeine (gels with caffeine) is effective.
- Low-dose caffeine (~200 mg) taken late in a long race can be as effective as a larger pre-race dose for the final effort (Spriet, 2014).

### Habituation

- Regular caffeine consumers experience **blunted** but still meaningful performance benefit (~1.5–2% vs ~3–4% for naive users).
- **Withdrawal protocol:** 2–4 days abstinence before race restores full sensitivity. Evidence is mixed on whether this is worth the withdrawal symptoms (headache, fatigue days before competition).
- Current practical advice: do NOT withdraw before important races if habituated. The withdrawal symptoms can impair training quality leading into the event. The benefit still exists for habitual users.

### Genetic Variation

- CYP1A2 gene polymorphism: "fast metabolizers" (AA genotype, ~50% of population) get full benefit; "slow metabolizers" (AC/CC) may get less benefit or even impairment at high doses (Guest et al., 2018).
- For modeling without genetic data: assume moderate response (2–3% TT improvement).

**Key references:**
- Southward K et al. (2018) *The effect of acute caffeine ingestion on endurance performance: a systematic review and meta-analysis.* Sports Medicine, 48(8), 1913-1928.
- Guest NS et al. (2021) *International Society of Sports Nutrition position stand: caffeine and exercise performance.* JISSN, 18(1), 1.
- Spriet LL. (2014) *Exercise and Sport Performance with Low Doses of Caffeine.* Sports Medicine, 44(S2), 175-184.

---

## 5. During-Race Nutrition Timing

### When to Start

- **Begin fueling within the first 15–20 minutes** of racing. Do NOT wait until hungry or fatigued.
- Gastric emptying is rate-limited; early intake ensures a steady supply when needed at hours 2–3+.
- In criteriums (<60 min), typically only fluids + possible mouth rinse.

### Frequency

- **Every 15–20 minutes** for solid/semi-solid. Every 5–10 minutes for sips of drink mix.
- Smaller, more frequent doses yield better absorption and less GI distress than large boluses.
- `dose_per_feeding = target_g_hr / feedings_per_hr` (e.g., 90 g/hr / 4 feedings = ~22 g per feed every 15 min)

### Form Factor by Duration/Intensity

| Form | Best Use | Absorption Speed | GI Risk |
|---|---|---|---|
| Drink mix | All durations; base layer of fueling | Fast (~5–10 min) | Low |
| Gels | >1 hr; high-intensity moments | Moderate (~10–15 min) | Moderate (take with water) |
| Chews/blocks | 2+ hr; moderate intensity | Moderate (~15–20 min) | Moderate |
| Solid food (bars, rice cakes) | 3+ hr; lower intensity phases | Slow (~20–30 min) | Higher at intensity |
| Liquid meal (e.g., Maurten mix) | Extremely high intake targets | Fast | Low |

### Intensity Interaction

- At >85% FTP: strongly favor liquids and gels. Solid food absorption drops dramatically as gut blood flow is shunted to working muscles.
- At 60–75% FTP (e.g., peloton cruising in a road race): solids are well tolerated and provide satiety benefit in long races.
- Key heuristic: `solid_fraction = max(0, 1 - (intensity_fraction - 0.60) / 0.30)` — above ~90% FTP, solids approach zero fraction.

---

## 6. Caloric Expenditure Models from Power Data

### Core Formula

This is the most precise method available to cyclists with power meters.

```
total_metabolic_rate_kJ_hr = (average_power_watts * 3.6) / gross_mechanical_efficiency

where:
  gross_mechanical_efficiency (GE) = 0.20 to 0.25
  typical trained cyclist GE = 0.22 to 0.24
  elite cyclist GE = 0.23 to 0.25
```

**Example:** 250W average at GE = 0.23:
- Metabolic rate = (250 * 3.6) / 0.23 = 3913 kJ/hr = **935 kcal/hr**
- Work done = 250 * 3.6 = 900 kJ/hr = 215 kcal/hr
- Heat produced = 935 - 215 = **720 kcal/hr**

### Basal Metabolic Rate Addition

- BMR contributes ~70–80 kcal/hr at rest. During exercise, it is subsumed into the metabolic rate calculation, so do NOT add it separately to power-based estimates.

### Thermic Effect of Food

- ~10% of ingested calories are lost to digestion/absorption.
- For modeling net available energy: `net_kcal_ingested = gross_kcal_ingested * 0.90`

### Substrate Partitioning (Fuel Mix)

The fraction of energy from carbohydrate vs fat depends critically on intensity:

| Intensity (% FTP) | CHO Fraction | Fat Fraction | CHO Burn Rate (g/hr) at 250W |
|---|---|---|---|
| 50% | 0.40–0.50 | 0.50–0.60 | ~93–117 |
| 65% | 0.55–0.65 | 0.35–0.45 | ~129–152 |
| 75% | 0.70–0.80 | 0.20–0.30 | ~163–187 |
| 85% | 0.85–0.90 | 0.10–0.15 | ~199–211 |
| 95% | 0.95–1.00 | 0.00–0.05 | ~222–234 |
| >100% (anaerobic) | ~1.00 | ~0.00 | ~234+ (plus anaerobic glycolysis) |

**Crossover point** (Brooks & Mercier, 1994): The intensity at which CHO and fat contribute equally. In trained cyclists, typically ~60–65% VO2max (~55–60% FTP). Fat-adapted athletes may shift this rightward by 5–10%.

**CHO oxidation rate formula:**
```
cho_oxidation_g_hr = (total_kcal_hr * cho_fraction) / 4.0
cho_fraction = 0.30 + 0.70 * ((intensity_pct_ftp - 0.40) / 0.60)  [clamped 0–1]
```

**Key references:**
- Coyle EF. (1995) *Substrate utilization during exercise in active people.* American Journal of Clinical Nutrition, 61(4), 968S-979S.
- Brooks GA & Mercier J. (1994) *Balance of carbohydrate and lipid utilization during exercise.* Journal of Applied Physiology, 76(6), 2253-2261.
- Jeukendrup AE & Wallis GA. (2005) *Measurement of substrate oxidation during exercise by means of gas exchange measurements.* International Journal of Sports Medicine, 26(S1), S28-S34.

---

## 7. Glycogen Depletion Thresholds & Bonking

### The Physiology

"Bonking" (hitting the wall) occurs when **muscle glycogen falls below ~200 mmol/kg dry weight** (the "critical threshold" below which contraction force drops precipitously, as glycogen becomes locally unavailable at the sarcomere level even before total depletion).

Liver glycogen depletion causes **hypoglycemia** (blood glucose <3.5 mmol/L), which impairs central nervous system function — this is the "central bonk" characterized by confusion, dizziness, loss of coordination.

### Glycogen Budget Model

```
Starting glycogen (supercompensated): ~3,000–3,200 kcal (750–800 g)
Starting glycogen (normal diet):      ~2,000–2,400 kcal (500–600 g)

Depletion rate = cho_oxidation_g_hr * 4 kcal/g  (see Section 6)
Exogenous supply = ingested_cho_g_hr * absorption_efficiency (see Section 1)

Net glycogen burn rate (kcal/hr) = depletion_rate - exogenous_supply_rate

Time to bonk (hr) = usable_glycogen_kcal / net_glycogen_burn_rate
```

Where `usable_glycogen_kcal = total_glycogen_kcal * 0.75` (approximately 25% is "trapped" in non-active muscles and inaccessible).

### Worked Example

70 kg rider, supercompensated, racing at 250W average (75% FTP), GE = 0.23:
- Total metabolic: 935 kcal/hr
- CHO fraction at 75% FTP: ~0.75
- CHO burn: 935 * 0.75 / 4 = **175 g/hr** (700 kcal/hr from CHO)
- Exogenous intake: 90 g/hr absorbed = 360 kcal/hr
- Net endogenous glycogen drain: 700 - 360 = **340 kcal/hr**
- Usable glycogen: 3,000 * 0.75 = 2,250 kcal
- Time to bonk: 2,250 / 340 = **~6.6 hr**

Without fueling:
- Time to bonk: 2,250 / 700 = **~3.2 hr**

At higher intensity (90% FTP, ~300W average):
- Metabolic: 300 * 3.6 / 0.23 = 4696 kJ/hr = 1122 kcal/hr
- CHO fraction: ~0.90
- CHO burn: 1122 * 0.90 / 4 = **253 g/hr**
- Exogenous at high intensity (limited absorption): ~70 g/hr = 280 kcal/hr
- Net drain: 1012 - 280 = **732 kcal/hr**
- Time to bonk: 2,250 / 732 = **~3.1 hr** even WITH fueling

### Total Work (kJ) as Bonk Predictor

A useful heuristic used by coaches:
- **Bonk risk becomes significant at ~1,500–2,000 kJ of cumulative work** without adequate fueling
- With good fueling, riders can sustain **3,000–5,000+ kJ** before glycogen crisis
- `cumulative_kJ_threshold = usable_glycogen_kcal * 4.184 * mechanical_efficiency + cumulative_exogenous_kJ * mechanical_efficiency`

**Key references:**
- Orrru S et al. (2018) *Role of functional beverages on sport performance and recovery.* Nutrients, 10(10), 1470.
- Gonzalez JT et al. (2016) *New perspectives on nutritional interventions to augment lipid utilisation during exercise.* British Journal of Nutrition, 115(12), 2010-2015.
- Hearris MA et al. (2018) *Regulation of muscle glycogen metabolism during exercise: implications for endurance performance and training adaptations.* Nutrients, 10(3), 298.

---

## 8. Recovery Nutrition

### The Post-Race Window

The "anabolic window" is real but wider than traditionally claimed:

- **Glycogen resynthesis** is fastest in the first **0–2 hours** post-exercise due to elevated GLUT4 translocation and glycogen synthase activity (non-insulin-dependent phase).
- Rate with optimal fueling: **5–8 mmol/kg dry weight/hr** in first 2 hr vs ~3–5 thereafter.
- Full glycogen restoration takes **24–48 hr** with adequate intake regardless of timing — but the first 2 hr matter for athletes with another event within 8–24 hr (e.g., stage races).

### Specific Recommendations

| Parameter | Recommendation |
|---|---|
| CHO intake (0–2 hr post) | **1.0–1.2 g/kg/hr** for rapid resynthesis |
| CHO intake (2–24 hr post) | **8–12 g/kg/day** total if next-day event |
| Protein (0–2 hr post) | **0.3–0.4 g/kg** (~20–30 g) to maximize muscle protein synthesis |
| Protein:CHO ratio | ~1:3 to 1:4 in recovery meal/drink |
| Leucine threshold | **2.5–3.0 g leucine** per serving triggers maximal MPS (muscle protein synthesis) |
| Total daily protein (heavy training) | **1.6–2.2 g/kg/day** spread across 4–5 meals |

### Glycogen Resynthesis Enhancers

- Adding protein to CHO does NOT increase glycogen resynthesis rate when CHO is already optimal (1.2 g/kg/hr). It helps when CHO intake is suboptimal (<0.8 g/kg/hr) (Beelen et al., 2010).
- **High glycemic index** foods resynthesize glycogen faster than low GI in the acute phase.
- Fructose alone is inferior (primarily restores liver glycogen). Best: glucose/maltodextrin + fructose mix, same as during exercise.

### Timing Sensitivity by Context

- Single-day race: Timing is less critical. Total daily intake matters more.
- **Stage race or multiple events in <24 hr:** Timing is critical. Start fueling within 15–30 min post-finish. Continue 1.0–1.2 g CHO/kg/hr for 4 hr.

**Key references:**
- Burke LM et al. (2017) *Postexercise muscle glycogen resynthesis in humans.* Journal of Applied Physiology, 122(5), 1055-1067.
- Beelen M et al. (2010) *Nutritional strategies to promote postexercise recovery.* International Journal of Sport Nutrition & Exercise Metabolism, 20(6), 515-532.
- Jager R et al. (2017) *ISSN position stand: protein and exercise.* JISSN, 14(1), 20.
- Morton RW et al. (2018) *A systematic review of protein supplements and their effect on muscle mass in trained individuals.* British Journal of Sports Medicine, 52(6), 376-384.

---

## Summary: Key Parameters for Computational Modeling

| Parameter | Symbol | Typical Value | Unit |
|---|---|---|---|
| Gross mechanical efficiency | GE | 0.20–0.25 | fraction |
| Max exogenous CHO oxidation (trained gut) | exo_max | 90–120 | g/hr |
| Glucose:fructose ratio | GF_ratio | 1:0.8 | — |
| Glycogen store (supercompensated) | gly_super | 34–46 | kcal/kg BM |
| Glycogen store (normal) | gly_norm | 23–29 | kcal/kg BM |
| Usable fraction of glycogen | gly_usable | 0.70–0.80 | fraction |
| CHO fraction at % FTP | cho_frac | 0.30 + 0.70*((I-0.40)/0.60) | clamped [0,1] |
| Sweat sodium concentration | sweat_Na | 20–80 (avg 45) | mmol/L |
| Caffeine dose | caff | 3–6 | mg/kg BM |
| Caffeine TT improvement | caff_pct | 2–4 | % |
| Recovery CHO rate (acute) | recov_cho | 1.0–1.2 | g/kg/hr |
| Recovery protein (per meal) | recov_pro | 0.3–0.4 | g/kg |
| Absorption reduction at high intensity | abs_penalty | see formula in Section 1 | fraction |
| Thermic effect of food | TEF | 0.10 | fraction of ingested kcal |

This should provide a sufficient evidence base for building race nutrition planning models from power data.
