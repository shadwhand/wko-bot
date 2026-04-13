# Quantitative Models for a Cycling Nutrition Engine

This is a synthesis of the published exercise physiology and applied sports science literature, organized into the eight subsystems you requested. All parameter values are calibrated for your reference cyclist: 78 kg, FTP 290 W, VO2max ~60 ml/min/kg (4.68 L/min).

---

## 1. Energy Expenditure from Power

### The core conversion

The fundamental relationship is:

```
EE (kJ/hr) = P (watts) × 3.6 / GE
```

where P is mechanical power output and GE is gross efficiency (the ratio of mechanical work to total metabolic energy). The factor 3.6 converts W·hr to kJ (1 W = 1 J/s, × 3600 s/hr = 3600 J/hr = 3.6 kJ/hr).

To get kilocalories:

```
EE (kcal/hr) = P × 3.6 / (GE × 4.184)
   or equivalently:
EE (kcal/hr) = P × 0.8604 / GE
```

### Efficiency definitions

- **Gross Efficiency (GE):** mechanical work / total metabolic cost. This is the operationally useful value. For trained cyclists, GE typically ranges 20-25%, with 22-24% being representative at moderate intensities.

- **Net Efficiency:** mechanical work / (total metabolic cost − resting metabolic cost). Typically 25-28%.

- **Delta Efficiency:** change in mechanical work / change in metabolic cost. Typically 25-30%. Delta efficiency is the most physiologically meaningful (it reflects the marginal cost of additional work) but GE is the one you need for total energy accounting.

### How GE varies

GE is not constant. It changes with:

1. **Intensity:** GE peaks around 50-75% VO2max and declines at higher intensities as anaerobic contribution rises and the O2 cost of ventilation increases. A reasonable model:

```
GE(intensity) ≈ GE_peak × (1 − α × (IF − IF_peak)²)
```

where IF = intensity factor (power / FTP), IF_peak ≈ 0.65-0.75, and α ≈ 0.08-0.12. At threshold (IF = 1.0), GE drops roughly 1-2 percentage points from peak. Above threshold, the decline accelerates because the lactate/H+ buffering and clearance costs are substantial and the caloric equivalent of oxygen shifts (more carbohydrate oxidation → ~5.05 kcal/L O2 vs ~4.69 for fat).

2. **Training status:** Trained cyclists have higher GE than untrained (typically 22-24% vs 18-21%). This is driven by fiber type recruitment patterns, mitochondrial density, and pedaling technique.

3. **Substrate mix:** Carbohydrate oxidation is ~5-8% more "efficient" per liter of O2 than fat oxidation (higher P/O ratio, lower O2 cost per ATP). As intensity rises and carb fraction increases, the caloric equivalent per liter O2 rises, but the absolute efficiency in watts per kcal actually stays fairly stable because the higher O2 cost of high-intensity work offsets this.

4. **Fatigue/duration:** GE declines 1-3% over prolonged exercise (>2 hr), likely due to recruitment of less efficient motor units, increased ventilatory work, and thermal strain.

### Practical parameterization for the reference cyclist

| Parameter | Value |
|---|---|
| GE at sweet spot (88% FTP, ~255 W) | 23.5% |
| GE at threshold (FTP, 290 W) | 22.5% |
| GE at VO2max (~410 W) | 20.5% |
| GE at endurance pace (65% FTP, ~190 W) | 23.0% |
| GE decline over time | −0.5% per hour after hour 2 |

**Example calculation at FTP:**

```
EE = 290 × 3.6 / 0.225 = 4640 kJ/hr = 1109 kcal/hr
```

At endurance pace (190 W):

```
EE = 190 × 3.6 / 0.230 = 2974 kJ/hr = 711 kcal/hr
```

### Heat production

This falls out directly:

```
Heat (W) = P / GE × (1 − GE) = P × (1/GE − 1)
```

At 290 W with GE = 0.225: Heat = 290 × (1/0.225 − 1) = 290 × 3.44 = 999 W of heat. This is important for the thermal model below.

### Inputs needed

- Power (continuous stream, or time-averaged)
- A model of GE vs intensity (can be a lookup table or polynomial)
- Duration (for efficiency drift correction)

### Limitations

- GE measurement requires indirect calorimetry; the values above are population estimates for trained cyclists and could vary ±1-2% individually
- Very short high-power bursts (sprints) have much lower efficiency but minimal caloric impact
- Coasting/freewheeling still has a basal metabolic cost (~1.2 kcal/min at rest, higher when warmed up, roughly 80-100 kcal/hr)

---

## 2. Substrate Partitioning Model

### The Crossover Concept (Brooks & Mercier, 1994)

The crossover concept describes how the relative contribution of carbohydrate and fat to total oxidation shifts as exercise intensity increases. At low intensity, fat dominates; at high intensity, carbohydrate dominates. The "crossover point" is the intensity at which carbohydrate contribution exceeds 50%.

### Respiratory Exchange Ratio (RER) model

The simplest substrate partition uses RER:

```
CHO fraction = (RER − 0.707) / (1.000 − 0.707) = (RER − 0.707) / 0.293
Fat fraction = 1 − CHO fraction
```

RER as a function of intensity (% VO2max) for a trained cyclist can be modeled as a sigmoid:

```
RER(x) = 0.71 + 0.29 / (1 + exp(−k × (x − x_cross)))
```

where x = fraction of VO2max (0 to 1), x_cross = crossover point (~0.55-0.65 for trained, ~0.40-0.50 for untrained), and k = steepness (~8-12).

For the reference trained cyclist: x_cross ≈ 0.60, k ≈ 10.

### Oxidation rates (g/min) — the Romijn/van Loon data

The landmark studies by Romijn et al. (1993, 2000) and van Loon et al. (2001) measured substrate oxidation via indirect calorimetry combined with isotope tracers at 25%, 65%, and 85% VO2max. For a ~78 kg trained cyclist:

| Intensity (% VO2max) | ~IF | CHO ox (g/min) | Fat ox (g/min) | Total EE (kcal/min) |
|---|---|---|---|---|
| 25% (~1.17 L/min) | 0.35 | 0.5 | 0.5 | 5.7 |
| 55% (~2.57 L/min) | 0.60 | 1.5 | 0.6 | 10.7 |
| 65% (~3.04 L/min) | 0.75 | 2.2 | 0.5 | 12.6 |
| 75% (~3.51 L/min) | 0.88 | 3.0 | 0.3 | 14.5 |
| 85% (~3.98 L/min) | 1.00 | 3.8 | 0.1 | 16.5 |
| 100% (~4.68 L/min) | 1.18 | 4.5 | ~0 | 18.9 |

### Five-compartment substrate breakdown

At 65% VO2max (endurance pace, a well-studied intensity) for a trained cyclist, the approximate partition from tracer studies (van Loon et al., 2001; Romijn et al., 1993) is:

| Source | % of total EE | g/min | Notes |
|---|---|---|---|
| Muscle glycogen | 35-45% | 1.0-1.3 g CHO/min | Dominant CHO source |
| Liver glycogen → blood glucose | 10-15% | 0.3-0.5 g CHO/min | Hepatic glycogenolysis + gluconeogenesis |
| Plasma FFA (adipose lipolysis) | 25-35% | 0.3-0.4 g fat/min | Dominant fat source at this intensity |
| IMTG | 10-15% | 0.1-0.2 g fat/min | Higher in trained athletes |
| Blood glucose (exogenous, if fed) | 5-15% | 0.2-0.5 g CHO/min | Depends on feeding rate |

This partition shifts dramatically with intensity:

**At 85% VO2max (threshold):**
- Muscle glycogen: 60-70% of total EE
- Liver glycogen/blood glucose: 15-20%
- Plasma FFA: 5-10%
- IMTG: 5%
- Exogenous CHO: 5-10% (limited by absorption, and blood flow redistribution away from gut)

**At 45% VO2max (easy ride):**
- Muscle glycogen: 15-20%
- Liver glycogen/blood glucose: 5-10%
- Plasma FFA: 45-55%
- IMTG: 15-20%
- Exogenous CHO: variable

### Mathematical formulation

A continuous model for CHO and fat oxidation rates (g/min), adapted from the literature curve-fitting:

```
CHO_ox(x) = a × x^b × exp(c × x)
Fat_ox(x) = d × x × exp(−e × x²)
```

where x = fraction of VO2max.

For a trained 78 kg cyclist:
- a ≈ 0.65, b ≈ 1.2, c ≈ 1.8 → gives CHO_ox in g/min
- d ≈ 1.6, e ≈ 2.2 → gives Fat_ox in g/min, peaks around x ≈ 0.47 ("Fatmax")

The fat oxidation curve has a well-characterized peak (Fatmax) and then declines. For trained cyclists, Fatmax is typically at 55-65% VO2max (vs 45-55% in untrained). This can be modeled as a modified Gaussian or the polynomial form from Achten & Jeukendrup (2004):

```
Fat_ox(x) = Fat_max × exp(−((x − x_fatmax) / σ)²)    for x > x_fatmax
```

where Fat_max ≈ 0.55-0.65 g/min for trained cyclist, x_fatmax ≈ 0.55, σ ≈ 0.18.

### Muscle glycogen vs liver glycogen partitioning

Of total CHO oxidation, the split between muscle glycogen and liver-derived glucose depends on intensity and feeding state:

```
Muscle_glycogen_fraction = 0.55 + 0.35 × (x − 0.25) / 0.75    [clamp 0.55 to 0.90]
Liver_glucose_fraction = 1 − Muscle_glycogen_fraction − Exogenous_fraction
```

The liver contribution is relatively constant in absolute terms (~0.3-0.6 g/min) across intensities, but its fractional contribution falls as muscle glycogen use soars at high intensity.

### Effect of exogenous carbohydrate

When carbs are ingested:
- Exogenous CHO oxidation replaces liver glycogen output and some muscle glycogen use
- Muscle glycogen sparing is modest (10-25% reduction in muscle glycogen use, not 1:1)
- The primary benefit is maintaining blood glucose and sparing liver glycogen

```
Exogenous_CHO_ox = min(Ingestion_rate × Absorption_efficiency, Max_exogenous_ox)
Liver_glycogen_sparing ≈ 0.7 × Exogenous_CHO_ox
Muscle_glycogen_sparing ≈ 0.2 × Exogenous_CHO_ox
```

Max_exogenous_ox ≈ 1.0 g/min (glucose only) or 1.5-1.8 g/min (glucose + fructose at 2:1 ratio), though recent "gut training" studies show some individuals reaching ~2.0+ g/min.

### Training status effects

Training shifts the crossover point rightward (higher fat oxidation at any given absolute intensity) through:
- Increased mitochondrial density and fat transport proteins (FAT/CD36, CPT-1)
- Higher IMTG stores and turnover
- Greater capillary density
- Hormonal adaptations (lower catecholamine response at submaximal intensity)

For modeling, the key parameter to adjust is x_cross (from ~0.45 untrained to ~0.60 trained) and Fat_max (from ~0.35 g/min untrained to ~0.60 g/min trained).

### Inputs needed

- Current power / intensity (% VO2max or % FTP, with conversion)
- VO2max (to convert FTP-relative to VO2max-relative)
- Training status proxy (can use Fatmax zone, or simply training volume/years)
- Feeding state and ingestion rate

### Limitations

- Individual variation is enormous (±20-30% in fat oxidation rates)
- The partition changes with glycogen status (low glycogen → more fat oxidation, but not enough to compensate fully)
- Heat, dehydration, and altitude all shift the crossover leftward (more CHO at same intensity)
- RER-based methods cannot distinguish substrate sources, only net oxidation
- At above-threshold intensities, RER > 1.0 and substrate calculations become unreliable (CO2 from bicarbonate buffering)

---

## 3. Glycogen Storage Model

### Storage capacities

| Compartment | Typical range | Reference cyclist (78 kg, trained) | After supercompensation |
|---|---|---|---|
| Muscle glycogen (whole body) | 300-700 g | ~500 g (~450 mmol/kg dry wt) | 600-700 g (~600-700 mmol/kg dw) |
| Active leg muscles only | ~150-350 g | ~250 g (in ~8 kg active muscle) | ~350 g |
| Liver glycogen | 60-120 g | ~100 g (fasted AM: ~60g, fed PM: ~120g) | ~130 g |
| Blood glucose | 4-5 g | 4.5 g (~5 mmol/L in ~5L blood) | 4.5 g (tightly regulated) |

**Energy equivalents:**
```
1 g glycogen → 4.1 kcal (17.2 kJ)
500 g muscle glycogen → 2050 kcal
100 g liver glycogen → 410 kcal
Total endogenous CHO → ~2460 kcal
```

### Concentration units

Muscle glycogen is reported in mmol glucosyl units per kg dry weight (dw) or per kg wet weight (ww). Conversion: 1 mmol/kg dw ≈ 0.25 mmol/kg ww (muscle is ~75% water). Normal resting values:

- Untrained: 300-400 mmol/kg dw (80-100 mmol/kg ww)
- Trained, normal diet: 400-500 mmol/kg dw (100-130 mmol/kg ww)
- Supercompensated: 500-700+ mmol/kg dw (130-180 mmol/kg ww)
- Depleted (after exhaustive exercise): 50-150 mmol/kg dw

### Depletion model

Muscle glycogen depletion rate depends on intensity and is approximately:

```
dG_muscle/dt = −CHO_ox_muscle(intensity) × (G_muscle / G_muscle_initial)^β
```

The (G/G_initial)^β term captures the observation that glycogen utilization rate slows as stores deplete (partly because low glycogen upregulates fat oxidation, and partly because the enzyme glycogen phosphorylase has reduced activity at low substrate concentrations). β ≈ 0.3-0.5 provides a reasonable fit.

A simpler linear-with-floor model:

```
dG_muscle/dt = −R(intensity)     when G_muscle > G_critical
dG_muscle/dt = −R(intensity) × (G_muscle / G_critical)    when G_muscle ≤ G_critical
```

where G_critical ≈ 50-100 g (the level below which performance collapses and oxidation rate is forced to decrease).

### Depletion rates at various intensities

For the reference cyclist, starting with 500 g muscle glycogen:

| Intensity | Power | Muscle glycogen use (g/hr) | Time to depletion (hr) | Time to G_critical (hr) |
|---|---|---|---|---|
| 55% VO2max (Z2, ~190W) | 190 W | 40-55 | 9-12 | 7-9 |
| 65% VO2max (tempo, ~230W) | 230 W | 60-80 | 6-8 | 5-6 |
| 75% VO2max (SS, ~265W) | 265 W | 90-120 | 4-5.5 | 3-4 |
| 85% VO2max (FTP, ~290W) | 290 W | 140-180 | 2.8-3.5 | 2-2.5 |
| 100% VO2max (~410W) | 410 W | 200-270 | 1.8-2.5 | 1.5-2 |

These assume no exogenous CHO intake. With 60 g/hr CHO intake, depletion is slowed by roughly 20-40 g/hr (not the full 60 g/hr, because muscle glycogen sparing is partial).

### Liver glycogen model

```
dG_liver/dt = −Hepatic_glucose_output + Gluconeogenesis + Absorbed_CHO_to_liver
```

- Hepatic glucose output at rest: ~6-8 g/hr (~100-130 mg/min)
- During moderate exercise: ~20-30 g/hr (increased by catecholamines and glucagon)
- Gluconeogenesis: ~2-5 g/hr (from lactate recycling, amino acids, glycerol)
- Absorbed CHO: depends on ingestion (see section 4)

Liver glycogen can be fully depleted in ~4-6 hours of moderate exercise without feeding, or overnight fasting depletes it to ~20-30 g.

### Supercompensation

The Bergstrom & Hultman (1966) protocol:
1. Deplete with exercise
2. 3 days low-CHO diet → depletes to ~200 mmol/kg dw
3. 3 days high-CHO diet (8-12 g/kg/day) → supercompensates to 500-700+ mmol/kg dw

Modern "modified" protocol (Sherman, 1981): taper training + high CHO intake for 2-3 days achieves ~80-90% of classical supercompensation without the depletion phase.

For the reference cyclist (78 kg):
- Normal muscle glycogen: ~500 g (6.4 g/kg)
- Supercompensated: ~650 g (8.3 g/kg)
- Target CHO intake for loading: 10-12 g/kg/day = 780-936 g/day for 2-3 days

### Inputs needed

- Starting glycogen state (can estimate from diet/training history or assume defaults)
- Continuous power data
- Ingestion log (timing, quantity, composition)
- Time of day and fasting state (for liver glycogen initial condition)

### Limitations

- Muscle glycogen is not directly measurable in the field; the model always runs on estimates
- Fiber-type-specific depletion is important (Type II fibers deplete first at high intensity, Type I first at low intensity) but too complex for a practical model
- Individual variation in storage capacity is ±30%
- The glycogen sparing effect of exogenous CHO is highly variable between individuals

---

## 4. Carbohydrate Absorption Kinetics

### Intestinal transporter model

Carbohydrate absorption is limited by specific intestinal transporters:

| Transporter | Location | Substrate | Max absorption rate | Notes |
|---|---|---|---|---|
| SGLT1 | Small intestine apical | Glucose, galactose | ~60 g/hr (1.0 g/min) | Sodium-coupled, saturable |
| GLUT5 | Small intestine apical | Fructose | ~30-40 g/hr (0.5-0.7 g/min) | Facilitated diffusion |
| GLUT2 | Basolateral membrane | Glucose, fructose | Not rate-limiting | Moves into blood |

**Key insight:** Because glucose and fructose use different transporters, combining them (typically 2:1 glucose:fructose or maltodextrin:fructose) increases total absorption:

```
Max_CHO_absorption = SGLT1_max + GLUT5_max = 60 + 35 = ~90-100 g/hr
```

Recent work (Sutehall et al., 2022; King et al., 2022) suggests trained athletes with gut training can achieve 100-120+ g/hr with 1:0.8 ratios, and some elite athletes report tolerating 120-140 g/hr, though oxidation rates peak at ~1.5-1.8 g/min (~90-108 g/hr) for most.

### Gastric emptying model

Gastric emptying is the first rate-limiting step. It follows roughly exponential kinetics for liquid meals:

```
dV_stomach/dt = −k_empty × V_stomach × f(concentration) × f(intensity) × f(temperature)
```

where:
- k_empty ≈ 0.02-0.04 /min for isotonic solutions (half-life ~20-35 min for 600 mL)
- f(concentration): hyperosmolar solutions slow emptying. Optimal concentration is 4-8% (40-80 g/L). Above ~10%, emptying slows significantly.
- f(intensity): moderate exercise (up to ~70% VO2max) does not impair or slightly enhances emptying. Above ~75-80% VO2max, gastric emptying slows substantially (sympathetic nervous system diverts blood from splanchnic circulation).

```
f(intensity) = 1.0                          for x ≤ 0.70
f(intensity) = 1.0 − 0.5 × (x − 0.70)²    for 0.70 < x ≤ 1.0
f(intensity) = 0.5 − 0.5 × (x − 1.0)      for x > 1.0
```

- f(temperature): heat impairs gastric emptying (roughly −10-20% in hot conditions)

### Absorption kinetics (small intestine)

Once past the stomach, absorption follows Michaelis-Menten kinetics for each transporter:

```
Absorption_glucose(t) = Vmax_SGLT1 × [Glucose]_lumen / (Km + [Glucose]_lumen)
Absorption_fructose(t) = Vmax_GLUT5 × [Fructose]_lumen / (Km + [Fructose]_lumen)
```

For practical modeling, a simpler delay-and-rate-limit approach works:

```
Available_CHO(t) = Ingested_CHO(t − τ_delay) × Emptying_fraction(t)
Absorbed_CHO(t) = min(Available_CHO(t), Max_transporter_rate)
Oxidized_exo_CHO(t) = Absorbed_CHO(t − τ_absorption) × Oxidation_efficiency
```

where:
- τ_delay (gastric emptying lag) ≈ 5-15 min for liquids, 15-30 min for gels, 20-45 min for solids
- τ_absorption (intestinal transit to blood) ≈ 10-20 min
- Oxidation_efficiency ≈ 0.7-0.9 (not all absorbed CHO is immediately oxidized; some goes to liver glycogen resynthesis or muscle glycogen, especially at lower intensities)

**Total delay from mouth to oxidation:** approximately 15-45 min depending on form and intensity. This is critical for the nutrition engine — feeding must anticipate demand, not react to it.

### Gut training

Chronic high-CHO intake during exercise upregulates SGLT1 transporter density (shown in rodent models, inferred in humans from improved tolerance and oxidation rates). Athletes who train with high CHO intake can increase absorption capacity by ~20-40% over 2-4 weeks.

```
SGLT1_max_trained = SGLT1_max_baseline × (1 + 0.3 × gut_training_factor)
```

where gut_training_factor ranges 0 (no gut training) to 1 (fully adapted).

### Practical absorption rate lookup

| CHO source | Practical max intake (g/hr) | Max oxidation (g/min) |
|---|---|---|
| Glucose only | 60 | 1.0 |
| Maltodextrin only | 60 | 1.0 |
| Glucose + Fructose (2:1) | 90 | 1.5 |
| Maltodextrin + Fructose (1:0.8) | 90-120 | 1.5-1.8 |
| Maltodextrin + Fructose (gut trained) | 100-140 | 1.5-2.0+ |

### Inputs needed

- Ingestion events: time, amount (g), CHO type (glucose/maltodextrin/fructose/sucrose ratios), form (liquid/gel/solid)
- Current exercise intensity (for gastric emptying modifier)
- Ambient temperature (for gastric emptying modifier)
- Gut training status (binary or graded)

### Limitations

- Individual GI tolerance varies hugely; some athletes cannot tolerate >60 g/hr regardless of type
- GI distress is common above 80 g/hr and is the practical limit for many athletes
- The model cannot predict individual GI distress events (cramping, nausea)
- Solid food absorption is much less predictable than liquids/gels
- These rates are measured for steady-state; variable intensity creates more uncertainty

---

## 5. Bonking Prediction Model

### What is "bonking"?

Bonking (hypoglycemia + severe muscle glycogen depletion) occurs when:
1. Muscle glycogen falls below a critical threshold in active fibers → can't sustain contractile force
2. Liver glycogen is depleted → blood glucose drops → CNS glucose supply compromised
3. Both mechanisms combine to produce catastrophic performance loss

### The performance-glycogen relationship

Performance degradation is NOT linear with glycogen depletion. It follows a threshold/cliff pattern:

```
performance_factor = 1.0                                           when G > G_onset
performance_factor = 1.0 − α × ((G_onset − G) / G_onset)^γ       when G_critical < G ≤ G_onset
performance_factor = PF_min                                        when G ≤ G_critical
```

Parameters:
- G_onset ≈ 150-200 g (30-40% of initial stores) — the point at which subtle performance loss begins
- G_critical ≈ 50-80 g (10-15% of initial stores) — the "wall"
- γ ≈ 2-3 (convex curve: gradual at first, then cliff-like)
- α ≈ 0.6-0.8 (maximum performance loss before complete bonk)
- PF_min ≈ 0.2-0.4 (performance floor — you can still ride, but only at very low intensity, relying on fat oxidation)

### A more complete model

```
PF(t) = PF_glycogen(t) × PF_glucose(t) × PF_durability(t)
```

**Glycogen component:**
```
PF_glycogen = sigmoid(G_muscle, G_onset, k_glyc)
            = 1 / (1 + exp(−k_glyc × (G_muscle − G_half)))
```
where G_half ≈ 100 g (50% performance at this level), k_glyc ≈ 0.03-0.05 g⁻¹.

**Blood glucose component:**
```
PF_glucose = 1.0                              when BG ≥ 4.0 mmol/L
PF_glucose = 1.0 − β × (4.0 − BG)²          when 2.5 < BG < 4.0
PF_glucose = 0.3                              when BG ≤ 2.5 (severe hypoglycemia)
```
where β ≈ 0.15-0.20.

Blood glucose drops significantly when liver glycogen is depleted AND exogenous CHO intake is insufficient:

```
BG(t) = BG_0 + ∫(Liver_output(t) + Absorbed_CHO(t) − Muscle_uptake(t) − Brain_uptake(t)) dt × k_BG
```

Brain glucose uptake ≈ 5-6 g/hr (relatively constant), which is why the brain is the first organ to suffer when glucose supply drops.

**Carb intake rescue factor:**
Ingesting carbs when bonking can partially rescue performance because:
- Blood glucose rises within 10-20 min (fast-acting CHO)
- But muscle glycogen does NOT resynthesise appreciably during exercise
- So the rescue is partial: blood glucose normalizes, CNS function recovers, but muscle power remains limited

```
PF_rescue(t) = PF_min + (PF_glucose_restored − PF_min) × (1 − exp(−t_since_intake / τ_rescue))
```
where τ_rescue ≈ 15-20 min, and PF_glucose_restored reflects restored blood glucose but still-depleted muscle glycogen.

### Time-to-bonk estimator

A useful simplified prediction:

```
T_bonk = (G_muscle_0 − G_critical + Exo_CHO_rate × T_bonk × Sparing_factor) / Glycogen_use_rate(intensity)
```

Solving for T_bonk:

```
T_bonk = (G_muscle_0 − G_critical) / (Glycogen_use_rate − Exo_CHO_rate × Sparing_factor)
```

For the reference cyclist at sweet spot (265 W), no feeding:
- G_muscle_0 = 500 g, G_critical = 75 g, Glycogen_use_rate = 105 g/hr
- T_bonk = (500 − 75) / 105 = 4.0 hours

With 80 g/hr glucose+fructose intake, sparing factor = 0.35:
- T_bonk = (500 − 75) / (105 − 80 × 0.35) = 425 / 77 = 5.5 hours

With 120 g/hr intake:
- T_bonk = 425 / (105 − 120 × 0.35) = 425 / 63 = 6.7 hours

### Inputs needed

- Current glycogen estimate (from depletion model)
- Current and planned intensity
- CHO ingestion rate and type
- Blood glucose estimate (from liver model + absorption model)

### Limitations

- "Bonking" is a spectrum, not a binary event — some athletes experience gradual fadeout, others hit a wall
- The glycogen depletion threshold varies by individual and by which fiber types are depleted
- Psychological/motivational factors strongly modulate the performance response to low glycogen
- Ketone/IMTG availability can buffer performance loss somewhat in fat-adapted athletes (but this is controversial and limited at high intensities)
- The model cannot capture the heterogeneity of glycogen depletion across muscle groups (quads vs glutes vs calves)

---

## 6. Hydration Model

### Sweat rate model

Sweat rate (L/hr) is a function of metabolic heat production, environmental conditions, and individual factors:

```
SR (L/hr) = (H_metabolic − H_convective − H_radiative − H_evap_resp) / H_vap
```

where H_vap = latent heat of vaporization of sweat ≈ 2426 kJ/L at skin temperature.

A more practical empirical model:

```
SR = SR_base × f(power) × f(temperature) × f(humidity) × f(body_mass) × f(acclimation)
```

**Power factor:**
```
f(power) = 0.3 + 0.7 × (P / P_max)^0.8
```
More power → more heat → more sweat. At rest, f ≈ 0.3; at FTP, f ≈ 0.85.

**Temperature factor:**
```
f(temperature) = 0.5 + 0.5 × (T_ambient − 10) / 25    [clamp 0.5 to 1.5]
```
At 10°C: f = 0.5; at 22°C: f = 0.74; at 35°C: f = 1.0; hot conditions can exceed 1.5.

**Humidity factor:**
```
f(humidity) = 1.0 + 0.3 × (RH − 0.50) / 0.50          [clamp 0.85 to 1.30]
```
In humid conditions, evaporative cooling is impaired, so the body sweats more (even though less evaporates). Note: this factor is somewhat counterintuitive — sweating rate may increase or stay high but *effective* cooling drops.

**Body mass factor:**
```
f(body_mass) = BM / 75                                   [linear scaling]
```

**Acclimation factor:**
Heat-acclimated athletes sweat more (and earlier), with more dilute sweat:
```
f(acclimation) = 1.0 (unacclimated) to 1.3 (fully heat acclimated, ~10-14 days)
```

**Reference values for the 78 kg cyclist at various conditions:**

| Condition | Power | Temperature | Humidity | SR (L/hr) |
|---|---|---|---|---|
| Indoor trainer | 200 W | 22°C | 60% | 1.2-1.5 |
| Temperate ride | 200 W | 20°C | 50% | 0.7-0.9 |
| Hot outdoor | 200 W | 35°C | 40% | 1.0-1.5 |
| Hot humid | 200 W | 33°C | 80% | 1.3-1.8 |
| Race effort, hot | 280 W | 30°C | 50% | 1.5-2.0 |

### Sodium loss model

```
Na_loss (mg/hr) = SR (L/hr) × Sweat_Na_concentration (mg/L)
```

Sweat Na concentration ranges widely: 200-1500 mg/L (mean ~800-1000 mg/L). Heat acclimation reduces concentration by ~20-40%.

For the reference cyclist: ~800 mg/L × 1.0 L/hr = ~800 mg/hr Na loss at moderate effort in temperate conditions.

### Performance degradation from dehydration

The relationship between body mass loss (from dehydration) and performance:

```
PF_hydration = 1.0                                        when BM_loss < 2%
PF_hydration = 1.0 − k_dehy × (BM_loss% − 2%)           when 2% ≤ BM_loss < 5%
PF_hydration = 1.0 − k_dehy × 3 − k_severe × (BM_loss% − 5%)   when BM_loss ≥ 5%
```

where k_dehy ≈ 0.03-0.05 per 1% BM loss (3-5% performance drop per 1% BM lost beyond 2%), k_severe ≈ 0.08-0.10 per 1% above 5%.

However, this "2% threshold" model is increasingly contested. Recent work (Goulet, 2011; Wall et al., 2015) suggests:
- In laboratory time-trials with ad libitum drinking, the relationship is more gradual
- In real-world conditions (outdoor, airflow, self-paced), up to 3-4% loss may be tolerable with modest performance impact
- The performance hit is strongly mediated by thermal strain — dehydration at 35°C is far worse than at 15°C

**Temperature-modified dehydration model:**
```
PF_hydration = 1.0 − k_base × max(0, BM_loss% − threshold%) × T_modifier
T_modifier = 0.5 + 0.5 × (T_ambient − 15) / 20         [clamp 0.5 to 1.5]
threshold% = 3.0 − T_modifier × 1.0                      [clamp 1.5 to 3.0]
```

This captures that dehydration is much more harmful in hot conditions.

### Fluid balance model

```
BM_loss(t) = ∫SR(t)dt − ∫Fluid_intake(t)dt − Metabolic_water_production(t) + Respiratory_water_loss(t)
```

- Metabolic water: ~0.13 L per hour of moderate exercise (byproduct of substrate oxidation; CHO oxidation produces ~0.6 g H2O per g CHO; fat produces ~1.07 g per g fat)
- Respiratory water loss: ~0.1-0.3 L/hr depending on ventilation rate and ambient humidity

### Inputs needed

- Power (continuous)
- Ambient temperature and humidity
- Body mass
- Fluid intake log (timing, volume)
- Acclimation status
- Optional: individual sweat rate from prior testing

### Limitations

- Individual sweat rates vary by 2-3x even at same conditions
- Sweat sodium concentration is highly individual and requires a sweat test
- The "dehydration threshold" for performance degradation is debated and context-dependent
- Plasma volume shifts (from posture, exercise onset, carb intake) confound simple body mass tracking
- Overhydration (hyponatremia) is a real risk with aggressive fluid intake and must be modeled as a floor on sodium concentration

---

## 7. Thermal Model

### Heat balance equation

The fundamental thermal balance during exercise:

```
dT_core/dt = (H_metabolic − H_evap − H_convective − H_radiative − H_respiratory) / (BM × c_body)
```

where c_body ≈ 3.49 kJ/(kg·°C) (specific heat of human body).

### Heat production

From section 1:
```
H_metabolic (W) = P / GE × (1 − GE) = P × (1/GE − 1)
```

At 290 W, GE = 0.225: H_metabolic ≈ 999 W
At 190 W, GE = 0.23: H_metabolic ≈ 636 W

### Cooling mechanisms

**Evaporative cooling (dominant mechanism):**
```
H_evap = SR_effective × H_vap / 3600
       = SR_effective (L/hr) × 2426 (kJ/L) / 3.6 → in watts
       = SR_effective × 674 W per L/hr
```

But effective evaporation depends on humidity:
```
SR_effective = SR × (1 − RH × 0.8)     [simplified; full model uses wet-bulb temperature]
```

At SR = 1.0 L/hr, 50% humidity: H_evap ≈ 674 × 1.0 × 0.60 = 404 W. This is often insufficient to balance H_metabolic at race intensities.

**Convective cooling:**
```
H_convective = h_c × A_skin × (T_skin − T_ambient)
```
where h_c depends on air velocity:
```
h_c ≈ 8.3 × v_air^0.6    (W/m²/°C)
```
For cycling at 35 km/h (9.7 m/s): h_c ≈ 8.3 × 9.7^0.6 ≈ 36 W/m²/°C
A_skin ≈ 1.9 m² for 78 kg athlete (DuBois formula)
T_skin ≈ 33-35°C

At 20°C ambient: H_convective ≈ 36 × 1.9 × (34 − 20) = 958 W → very significant. This is why outdoor cycling is thermally much easier than indoor training.

At 35°C ambient: H_convective ≈ 36 × 1.9 × (34 − 35) = −68 W → net heat GAIN (convection works against you in hot weather).

**Radiative cooling:**
```
H_radiative = ε × σ × A_eff × (T_skin⁴ − T_environment⁴)
```
This is usually small (50-100 W) and partially offset by solar radiation gain (~100-300 W in direct sun). For modeling, a net radiative term of −50 to +200 W covers most scenarios.

**Respiratory cooling:**
```
H_respiratory ≈ VE × (c_air × (T_exhaled − T_inspired) + H_vap_resp × (W_exhaled − W_inspired))
```
Typically 30-80 W at exercise ventilation rates. Relatively minor.

### Core temperature dynamics

Solving the heat balance with typical values for the reference cyclist at 265 W (sweet spot) outdoors at 30°C, 50% humidity, 30 km/h:

- H_metabolic ≈ 880 W
- H_evap ≈ 400-500 W (depending on SR and humidity)
- H_convective ≈ 200-300 W (depends on speed and T_ambient)
- H_radiative ≈ −50 to +100 W
- H_respiratory ≈ 40 W
- Net heat storage ≈ 880 − 500 − 250 − 40 = ~90 W

```
dT_core/dt = 90 / (78 × 3490) = 0.00033 °C/s = 0.020 °C/min = 1.2 °C/hr
```

Starting from 37.0°C, reaching 39.0°C in ~100 min. At 39.5-40.0°C, central governor mechanisms begin limiting output.

### Performance degradation from hyperthermia

```
PF_thermal = 1.0                                      when T_core < 38.5°C
PF_thermal = 1.0 − k_therm × (T_core − 38.5)        when 38.5 ≤ T_core < 40.0
PF_thermal = 0.3                                       when T_core ≥ 40.0
```

where k_therm ≈ 0.25-0.35 (25-35% performance drop per °C above 38.5°C).

### Interaction with nutrition

Heat stress increases CHO utilization (higher catecholamines → more glycogenolysis):
```
CHO_ox_heat = CHO_ox_thermoneutral × (1 + 0.15 × max(0, T_core − 38.0))
```

Approximately 15% increase in CHO oxidation rate per °C of core temperature above 38.0°C. This means hot conditions accelerate glycogen depletion and bonking.

Heat stress also impairs gastric emptying and intestinal absorption (splanchnic blood flow reduced by up to 60-80% during hard exercise in the heat):
```
Absorption_rate_heat = Absorption_rate_thermoneutral × (1 − 0.3 × max(0, T_core − 38.0))
```

This creates a vicious circle: hot conditions increase CHO demand while reducing the ability to absorb exogenous CHO.

### Inputs needed

- Power
- Ambient temperature, humidity, wind speed / cycling speed
- Solar radiation (time of day, cloud cover, or direct measurement)
- Body mass, body surface area
- Clothing (affects evaporation and convection)
- Acclimation status

### Limitations

- Core temperature is not directly measurable in the field (though ingestible pills exist)
- The thermal model is highly sensitive to wind speed and evaporative conditions, which are hard to predict
- Individual variation in heat tolerance is substantial
- Indoor vs outdoor cycling has dramatically different thermal profiles (lack of convective cooling indoors makes it ~2x harder to cool)

---

## 8. Fatigue Interaction — Glycogen-Durability Coupling

### The durability framework

"Durability" in recent exercise science (Maunder et al., 2021; Van Erp et al., 2021) is defined as the resistance to deterioration of physiological parameters (critical power, FTP, VO2max, efficiency) over prolonged exercise. The durability decay curve for power at a given physiological threshold can be modeled as:

```
CP(t) = CP_0 × (1 − d × (t / τ_dur)^n)
```

where CP_0 = initial critical power, d = maximum fractional decline (0.05-0.15), τ_dur = time constant (3-6 hours), n = shape parameter (1-2).

For the reference cyclist:
```
CP(t) = 290 × (1 − 0.10 × (t / 4.5)^1.5)
```
Predicting: CP at 2 hr = 282 W, at 4 hr = 264 W, at 6 hr = 248 W.

### Glycogen as a durability modulator

The central hypothesis: glycogen depletion is a primary *mechanism* of durability loss, not just a parallel process. Evidence:

1. **Low glycogen impairs calcium release** from the sarcoplasmic reticulum (Ørtenblad et al., 2011, 2013). Glycogen is physically associated with the SR Ca²+ release channels, and depletion of this specific pool impairs excitation-contraction coupling even when other glycogen pools are not fully depleted. This is a peripheral fatigue mechanism.

2. **Low glycogen increases central fatigue.** Brain serotonin synthesis increases (via free tryptophan competing with BCAAs for transport across the blood-brain barrier — the "central fatigue hypothesis" of Newsholme, 1987). Also, hypoglycemia directly impairs CNS motor drive.

3. **Low glycogen reduces efficiency.** GE drops 2-4% when glycogen is depleted, because fat oxidation is less efficient per ATP and motor unit recruitment shifts to less efficient patterns.

### Mathematical coupling

The durability decay should be modified by glycogen status:

```
CP(t) = CP_0 × PF_durability(t) × PF_glycogen(t) × PF_thermal(t) × PF_hydration(t)
```

But there's an interaction term — glycogen depletion accelerates durability decay:

```
PF_durability(t, G) = 1 − d × (W_accumulated / (τ_dur × CP_0))^n × (1 + k_glyc_dur × max(0, 1 − G/G_onset))
```

where:
- W_accumulated = total work done (kJ)
- k_glyc_dur ≈ 0.3-0.5 (the glycogen-durability interaction coefficient)
- When G > G_onset (glycogen is fine), the interaction term is 0 and durability decays at baseline rate
- When G approaches G_critical, the interaction term adds 30-50% to the decay rate

### Central vs peripheral fatigue partition

```
Fatigue_total = Fatigue_peripheral + Fatigue_central
```

**Peripheral fatigue (muscle level):**
- Metabolite accumulation (H+, Pi, K+ — primarily during high-intensity efforts)
- Glycogen depletion → impaired SR Ca²+ release
- Substrate limitation (can't produce ATP fast enough for desired power)

```
F_peripheral(t) = F_metabolite(t) + F_glycogen_SR(t) + F_substrate(t)

F_glycogen_SR = k_SR × max(0, 1 − (G_muscle / G_SR_threshold))^2
```
where G_SR_threshold ≈ 200-250 g (SR-associated glycogen depletes first), k_SR ≈ 0.15.

**Central fatigue (CNS level):**
- Reduced motor drive
- Affected by brain glucose supply, serotonin/dopamine balance, core temperature, and perceived effort

```
F_central(t) = k_cent_time × t + k_cent_glucose × max(0, 4.0 − BG(t))² + k_cent_temp × max(0, T_core − 38.5)
```

where k_cent_time ≈ 0.01/hr (time-dependent component), k_cent_glucose ≈ 0.05 per (mmol/L)², k_cent_temp ≈ 0.08 per °C.

### Glycogen depletion → efficiency loss → vicious cycle

Low glycogen forces greater reliance on fat oxidation. Fat oxidation:
- Requires more O2 per ATP (~5-8% more)
- Produces less ATP per unit time (fat oxidation rate is limited by mitochondrial capacity)
- Results in lower GE

```
GE_depleted = GE_normal × (1 − k_eff × max(0, 1 − G/G_onset)^1.5)
```
where k_eff ≈ 0.08-0.12. At G_onset, GE starts dropping; when G approaches G_critical, GE may be 8-12% lower than normal.

This creates a positive feedback loop:
1. Glycogen depletes → GE drops
2. Lower GE → more metabolic energy needed for same power → more heat, more substrate consumed
3. More substrate consumed → faster glycogen depletion
4. Faster depletion → lower GE...

This vicious cycle is one reason the bonk feels like a cliff rather than a gradual slide.

### Complete coupled model

```
dG_muscle/dt = −CHO_ox_muscle(P, GE(G), T_core) × f(G)
             + Muscle_glycogen_sparing(Exo_CHO_absorbed)

dG_liver/dt  = −HGO(P, G_liver) + GNG + Absorbed_to_liver(Exo_CHO)

dBG/dt       = (HGO + Intestinal_absorption − Muscle_uptake − Brain_uptake) × k_BG

dT_core/dt   = (H_met(P, GE) − H_cooling(T_amb, RH, v_air, SR)) / (BM × c_body)

dBM_water/dt = −SR(P, T_core, T_amb, RH) + Fluid_intake − Resp_loss + Met_water

PF(t) = PF_durability(t, G) × PF_glycogen(G) × PF_glucose(BG) × PF_thermal(T_core) × PF_hydration(BM_water)
```

This is a system of coupled ODEs that can be integrated numerically (Euler method with 1-minute time steps is adequate given the uncertainty in parameters).

### Inputs for the complete system

| Input | Source | Update frequency |
|---|---|---|
| Power | Power meter | Continuous (1s) |
| Heart rate | HR monitor | Continuous |
| Ambient temperature | Weather/sensor | Periodic |
| Humidity | Weather/sensor | Periodic |
| Wind speed / cycling speed | GPS/speed sensor | Continuous |
| Body mass | Pre-ride measurement | Once |
| FTP / VO2max | Testing / model | Pre-ride |
| Starting glycogen | Estimate from diet/training | Pre-ride |
| CHO intake events | User logging | Event-based |
| Fluid intake events | User logging | Event-based |
| Gut training status | User profile | Static |
| Heat acclimation status | User profile | Static |

### Limitations of the coupled model

1. **Parameter uncertainty is the dominant issue.** Most parameters have ±20-50% individual variation. The model should be treated as a "best estimate with wide confidence bands" rather than a precise prediction.

2. **No fiber-type resolution.** Real glycogen depletion is heterogeneous across fiber types and even within individual fibers (subcellular compartments). The whole-muscle average is a crude approximation.

3. **No learning/calibration framework described here.** In practice, the model would need to be calibrated per individual using past ride data (e.g., "this rider bonked at hour 4.5 of a 270 W effort with 50 g/hr intake" → update G_critical and substrate partition parameters).

4. **Psychological and motivational factors** are not modeled but strongly influence performance, especially near the bonk threshold.

5. **Altitude** effects are omitted (hypoxia shifts substrate use toward more CHO, increases ventilation, and changes fluid balance).

6. **Race dynamics** — drafting, surges, and variable intensity introduce non-steady-state conditions that are harder to model than constant-power scenarios. The model handles variable power through integration, but the transient kinetics of substrate switching (VO2 slow component, EPOC, lactate dynamics) add uncertainty.

7. **The absorption model is the weakest link** for real-time prediction, because GI function is highly individual and highly sensitive to stress, heat, and mechanical factors (vibration, position on the bike).

---

## Summary of the System Architecture

The eight models form a coupled system where the key state variables are:

- **G_muscle(t)** — muscle glycogen (g)
- **G_liver(t)** — liver glycogen (g)
- **BG(t)** — blood glucose (mmol/L)
- **T_core(t)** — core temperature (°C)
- **BM_water(t)** — fluid deficit (L, or % BM)
- **CHO_gut(t)** — carbohydrate in GI tract awaiting absorption (g)

And the primary output is **PF(t)** — performance factor, a multiplicative combination of all degradation pathways, representing the fraction of "fresh" capacity available at time t.

The nutrition engine's job is to optimize the ingestion schedule {(t_i, amount_i, type_i)} to maximize PF over the ride duration, subject to GI tolerance constraints. This is a constrained optimization (or model-predictive control) problem that can be solved with the ODE system above as the plant model.
