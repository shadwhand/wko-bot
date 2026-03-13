---
name: wko5-science
description: Scientific foundations behind WKO5 and power-based training — research papers, physiological models, and evidence base. Use when the user asks about the science behind power-duration modeling, the research supporting FTP/FRC/Pmax/VO2max calculations, muscle fiber type estimation, critical power theory, training stress models, or wants to understand the physiological basis of any WKO5 metric. Also trigger for questions about Dr. Coggan's work, the mathematical model behind the PD curve, or exercise physiology concepts related to power training.
---

# WKO5 Scientific Foundations

This skill covers the research, physiological models, and scientific evidence underlying WKO5's analytics. Use it when questions go beyond "how do I use WKO5" into "why does this work" or "what's the evidence."

## The Power-Duration Relationship

### Critical Power Theory
The mathematical foundation of WKO5's Power Duration Model. The critical power (CP) concept, first described by Monod and Scherrer (1965), models the hyperbolic relationship between power output and time to exhaustion.

**Core idea:** There exists a power output (critical power / FTP) that can theoretically be sustained indefinitely, and a finite energy reserve (W' / FRC) above that threshold. Total work above CP = W' (a fixed quantity).

**Key papers:**
- Monod H, Scherrer J. "The work capacity of a synergic muscular group." *Ergonomics*. 1965;8(3):329-338.
- Morton RH. "The critical power and related whole-body bioenergetic models." *European Journal of Applied Physiology*. 2006;96(4):339-354.
- Jones AM, Vanhatalo A, et al. "Critical power: implications for determination of VO2max and exercise tolerance." *Medicine and Science in Sports and Exercise*. 2010;42(10):1876-1890.

### WKO5's Implementation (Dr. Andrew Coggan)
WKO5 extends classical critical power theory with a multi-component model that fits the entire power-duration curve from ~1 second to several hours. Dr. Coggan's model:

- Is "conceptually and statistically robust"
- Provides "precise, unbiased estimates of key parameters reflective of important physiological determinants of performance"
- Accounts for the neuromuscular (sprint) component that classical CP theory ignores
- Derives multiple physiological parameters from a single curve fit

The model identifies distinct physiological systems contributing to power at different durations:
- **Neuromuscular** (Pmax) — peak instantaneous power, dominated by muscle fiber recruitment and neural drive
- **Anaerobic/Glycolytic** (FRC) — energy from anaerobic metabolism above threshold
- **Aerobic/Oxidative** (mFTP) — sustainable power limited by oxygen delivery and utilization
- **Fatigue resistance** (TTE, Stamina) — ability to sustain threshold power over time

## Physiological Parameters — Scientific Basis

### Functional Threshold Power (FTP / mFTP)

Developed by Dr. Andrew Coggan. Defined as "the highest power a rider can maintain in a quasi-steady state without fatiguing" — an estimate of the power output corresponding most closely with maximal lactate steady state (MLSS) or metabolic control limit.

**Physiological basis:**
- Controlled by VO2max, limited by the cardiovascular system's ability to deliver O2-carrying blood to contracting muscle
- Threshold is primarily determined by muscular metabolic fitness — aerobic ATP production via mitochondrial respiration
- At low intensities, glycolysis rate is low, all pyruvate is oxidized by mitochondria, lactate production is minimal
- As intensity increases, glycolysis outpaces mitochondrial capacity, pyruvate "spills over" to lactate
- The accumulation of lactate provides a convenient (albeit indirect) marker of muscle energetics and substrate metabolism

**Two lactate transition points:**
1. **First transition** — intensity sustainable for several hours (like marathon pace). Blood lactate first begins to increase.
2. **Second transition (threshold)** — the intensity coaches/athletes perceive as "threshold." Blood lactate levels increase continuously during constant-intensity exercise. This corresponds to MLSS, EMG threshold, RER crossover (~1.0), second ventilatory threshold, and respiratory compensation point.

**Key facts about FTP duration:**
- MLSS can typically be sustained for 30-70 minutes (not specifically "one hour")
- For trained athletes, this typically falls in the 40-55 minute range
- This roughly corresponds to 40km TT duration (~40 min), which was originally proposed as the best estimate
- The power-duration relationship is very flat in this region, so higher fitness is reflected in higher power at MLSS/FTP
- Training also tends to improve the *duration* that exercise at this intensity can be maintained

**Key distinction:** mFTP from the PD model vs. manually-set FTP from a 20-min or 60-min test. The model-derived value uses the entire power-duration curve rather than a single test effort.

**Relevant research:**
- Allen H, Coggan AR. *Training and Racing with a Power Meter*. VeloPress. (Multiple editions)
- Coggan AR. "Training and racing using a power meter: an introduction." (Original FTP concept papers)

### VO2max Estimation
- WKO5 estimates VO2max from the power-duration model using the relationship between power output and oxygen consumption
- Expressed as mVO2max in L/min; convert to mL/min/kg by: `mVO2max * 1000 / weight`
- The gross efficiency assumption (~20-25%) links watts to oxygen cost

**Relevant research:**
- Åstrand PO, Rodahl K. *Textbook of Work Physiology*. McGraw-Hill.
- Joyner MJ, Coyle EF. "Endurance exercise performance: the physiology of champions." *Journal of Physiology*. 2008;586(1):35-44.

### Muscle Fiber Type Estimation
- WKO5 estimates % type I (slow-twitch) fiber area from the shape of the PD curve
- Sprinters show a steep curve (high Pmax relative to FTP) → more fast-twitch
- Time trialists show a flatter curve → more slow-twitch
- This is an *estimate* based on the power-duration profile, not a biopsy

**Relevant research:**
- Coyle EF, et al. "Physiological and biomechanical factors associated with elite endurance cycling performance." *Medicine and Science in Sports and Exercise*. 1991;23(1):93-107.

### Functional Reserve Capacity (FRC)
- Analogous to W' (W-prime) in critical power literature
- Represents the total work capacity above FTP before exhaustion
- Expressed in kJ (or kJ/kg when normalized to body weight)
- Trainable primarily through high-intensity interval training

**Relevant research:**
- Skiba PF, et al. "Modeling the expenditure and reconstitution of work capacity above critical power." *Medicine and Science in Sports and Exercise*. 2012;44(8):1526-1532.

### Time to Exhaustion (TTE)
Introduced in WKO4 by Dr. Andrew Coggan. Defined as: the maximum duration for which a power equal to model-derived FTP can be maintained.

**How it's derived:** Sustained power output reflects the length of time an athlete can hold a level of power without noticeable degradation. Although this decline happens gradually on a continuum, a deflection point ("kink") can typically be seen in most athletes' PD and MMP curves for hard, steady-state efforts around an hour. This kink is modeled as a downward deflection in the tail of the power-duration curve. TTE is visually represented by a vertical line just after this kink.

**Training implications:** The effort to increase FTP via the PD curve can be decomposed into two distinct goals:
1. **Increase mFTP** — lift the curve (increase sustainable power)
2. **Extend TTE** — shift the kink rightward (increase duration at that power)

These are partially independent — an athlete can have a high mFTP with short TTE (strong but fades) or moderate mFTP with long TTE (very durable). Tracking both reveals the nature of fitness changes.

### Pmax (Maximum Power)
- Peak instantaneous neuromuscular power
- Reflects neural drive, muscle fiber type distribution, and biomechanical efficiency
- Tested via short maximal sprints (e.g., 2x 150m in the baseline protocol)
- Limited long-term trainability (largely genetic)

## Training Stress Models

### TSS (Training Stress Score)
- Developed by Dr. Andrew Coggan
- Quantifies the physiological cost of a workout relative to the athlete's FTP
- Formula: TSS = (duration_seconds × NP × IF) / (FTP × 3600) × 100
- Where NP = Normalized Power, IF = Intensity Factor (NP/FTP)
- 100 TSS ≈ 1 hour at FTP

### Performance Management Chart (PMC)
- Uses exponentially weighted moving averages of TSS
- **CTL** (Chronic Training Load): ~42-day time constant — represents "fitness"
- **ATL** (Acute Training Load): ~7-day time constant — represents "fatigue"
- **TSB** (Training Stress Balance): CTL - ATL — represents "form" or readiness
- Based on the impulse-response model of training adaptation

**Relevant research:**
- Banister EW. "Modeling elite athletic performance." *Physiological Testing of the High-Performance Athlete*. 1991:403-424.
- Busso T. "Variable dose-response relationship between exercise training and performance." *Medicine and Science in Sports and Exercise*. 2003;35(7):1188-1195.

## Trainability of Physiological Systems

From Dr. Coggan's research (as presented in Cusick & Williams):

| System | Short-term trainability | Long-term trainability | Cost |
|--------|------------------------|----------------------|------|
| VO2max | 15-25% | 0-10% | High |
| Lactate threshold | 30-45% | 20-30% | Low-Moderate |
| Efficiency | 0-5% | 0-5% | High |
| Neuromuscular power | 15-25% | 10-20% | Low-Moderate |
| Anaerobic capacity | 15-25% | 0-10% | Very High |

Key insight: Lactate threshold/FTP has the best trainability-to-cost ratio, which is why it's central to most training plans. VO2max has high short-term trainability but plateaus. Efficiency is largely resistant to training.

## Polarized vs. Threshold Training (Seiler's Model)

Dr. Stephen Seiler's 3-zone model, referenced in WKO5 distribution analysis:
- **Zone 1**: Below aerobic/ventilatory threshold (~75-80% of training volume for elites)
- **Zone 2**: Between aerobic and lactate thresholds (minimize time here)
- **Zone 3**: Above lactate threshold (high-intensity work, ~15-20% of volume)

This "polarized" distribution is observed in successful endurance athletes across sports.

**Relevant research:**
- Seiler S. "What is best practice for training intensity and duration distribution in endurance athletes?" *International Journal of Sports Physiology and Performance*. 2010;5(3):276-291.
- Stöggl T, Sperlich B. "Polarized training has greater impact on key endurance variables than threshold, high intensity, or high volume training." *Frontiers in Physiology*. 2014;5:33.

## Molecular Adaptation — The Three Signaling Pathways

Three distinct pathways drive endurance adaptation in skeletal muscle. Understanding these explains why both volume AND intensity matter:

1. **Calcium / CaMK pathway** (volume-driven): Every pedal stroke releases Ca²⁺ → CaMK → p38 MAPK → PGC-1alpha → mitochondrial biogenesis. More contractions = more signaling. This is why training volume at any intensity contributes to aerobic adaptation.

2. **AMPK / energy-sensing pathway** (intensity-driven): When AMP/ATP ratio rises during hard exercise → AMPK activation → PGC-1alpha + glucose uptake + fat oxidation. Higher intensity = greater AMPK activation. Low glycogen amplifies this signal (train-low mechanism).

3. **p38 MAPK → PGC-1alpha** (both): Converging pathway that responds to both calcium release and metabolic stress. PGC-1alpha is the "master regulator" — each session triggers a transient mRNA spike; accumulated sessions drive structural protein changes.

Key timeline: mRNA expression of oxidative enzymes peaks at 10-24 hours post-exercise (not during or immediately after). Protein accumulation requires repeated bouts over weeks.

## Substrate Partitioning by Intensity

| Intensity Zone | Fat Oxidation | CHO Oxidation | Key Insight |
|---------------|--------------|--------------|-------------|
| ~63% VO2max (Endurance) | Peak (Fatmax) | Low | Zone 2 training maximizes fat oxidation |
| ~75-85% VO2max (Tempo/SS) | Declining | Rising | Transition zone; glycolysis accelerating |
| ~85-100% VO2max (Threshold+) | Minimal | Dominant | Near-total reliance on CHO |
| ~94% VO2max | Ceases (Fatmin) | Complete | Fat oxidation effectively zero |

Well-trained athletes burn ~3x more fat during HIT than recreationally trained (0.57 vs 0.20 g/min), with fat oxidation strongly correlated with VO2max (r=0.86). This glycogen-sparing effect is a hallmark of aerobic fitness.

## Central vs. Peripheral Adaptation

Two systems determine power output, operating on different timescales:

**Central (O2 delivery):**
- Stroke volume (diastolic function is the key advantage — trained athletes' SV rises continuously to max HR with no plateau)
- Blood volume: plasma volume expands within days; red blood cell volume takes months (up to +40% in champions)
- In moderately trained athletes, haematological adaptations are the primary driver of VO2max gains
- Blood volume is also one of the fastest-declining adaptations during detraining

**Peripheral (O2 utilization):**
- Mitochondrial density and oxidative enzyme capacity (doubles with training — Holloszy 1967)
- Capillary density (+18% with 6 weeks moderate training)
- Fiber type distribution and switching (IIb → IIa with training)
- For already well-trained athletes with maximized blood volume, peripheral adaptations drive further FTP gains

## Research Papers

For the complete annotated bibliography of 30+ papers organized by topic, read:
→ `references/research-papers.md`

Topics covered: mitochondrial biogenesis, cardiovascular adaptation, critical power/VO2 kinetics, endurance determinants, AMPK signaling, glycogen/substrate metabolism, testing validity, and training stress models.

## Further Reading

- Allen H, Coggan AR, McGregor S. *Training and Racing with a Power Meter*. VeloPress. (The foundational text)
- Cusick T, Williams K. *Advanced Training with Power and WKO*. (eBook — the practical methodology)
- WKO5 Expression Reference: http://updates.wko4.com/WKO5%20Expression%20Reference.html
- WKO5 Help Articles: https://wko5.zendesk.com/hc/en-us/sections/7849422354445-WKO5-Articles-Tips-and-Help
