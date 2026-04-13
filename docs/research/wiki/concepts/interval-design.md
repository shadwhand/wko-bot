# Interval Design: Principles, Structures, and Progression

Evidence levels: **[R]** = Research-backed, **[E]** = Experience-based, **[O]** = Opinion.

Cross-references: [endurance-base-training](endurance-base-training.md) | EC Master Reference | WKO5 iLevels

_(See [Cross-References](#cross-references) section for full wiki links.)_

---

## 1. Core Philosophy

- **Intervals are tools, not the training program** -- they must be embedded in a broader plan that includes endurance volume and recovery [E] (TMT-45, TMT-54)
- **"Intervals are like hot sauce: they give you a good kick, but more is not always better"** -- every interval session has a cost-to-benefit ratio; fatigue cost must justify the adaptive benefit (Bobo, TP) [E]
- **No single "best" interval protocol exists** -- different methods are tools in a toolbox; 5x5 vs 4x8 vs 3x8 are effectively equivalent for VO2max stimulus (WD-55, TMT-46) [R]
- **Progressive overload before protocol change** -- exhaust simple duration/volume progression before switching to exotic protocols; most athletes change too often and never fully capture adaptation (TMT-44, 45, 52, 60) [E]
- **Current evidence suggests no added benefit in doing more than ~2 high-intensity sessions per week** -- anything beyond increases overtraining risk without creating additional beneficial adaptations (Seiler 2010, Hawley & Bishop 2021) [R]

---

## 2. The Four Design Variables

When constructing any interval workout, four variables interact (Cusick, TP):

| Variable | Description | Primary Lever |
|----------|-------------|---------------|
| **Intensity** | Power target as % FTP or absolute watts | Energy system targeted |
| **Duration** | Length of each work interval | Stimulus depth |
| **Rest** | Recovery between intervals (duration + intensity) | Lactate clearance, readiness for next rep |
| **Volume** | Total number of intervals or sets | Cumulative dose |

**Key principle:** Adjusting any one variable changes the stimulus. Increasing duration at the same power is a different (and often superior) progression path than increasing power at the same duration [E] (TMT-45, TMT-60).

---

## 3. Interval Structures by Target System

### 3.1 Neuromuscular Power (Pmax)

| Parameter | Value | Source |
|-----------|-------|--------|
| Duration | 5-15 seconds | iLevels [R] |
| Intensity | Maximal (typically >150% FTP) | WKO5 Pmax [R] |
| Rest | 2-5 minutes (full recovery) | TMT-64 [E] |
| Sets | 3-8 sprints | TMT-45 [E] |
| Cadence | Varies by goal (low = torque, high = speed) | Cadence analysis (Moore, TP) [E] |

**Notes:**
- Sprint training has low opportunity cost -- a few 10-15 sec sprints at the start of endurance rides costs almost nothing in fatigue [E] (TMT-45, TMT-64)
- Sprints can be added year-round as maintenance without interfering with other goals [E]
- Lower cadence sprints (55-75 RPM) are more glycolytic and recruit more fast-twitch fibers; higher cadence (>100 RPM) shifts stress toward aerobic pathways [R] (Moore cadence analysis, TP)

**Platform module:** `pdcurve.py` -- Pmax tracking; `blocks.py` -- sprint add-on templates

### 3.2 Anaerobic Capacity / Functional Reserve Capacity (FRC)

| Parameter | Value | Source |
|-----------|-------|--------|
| Duration | 30 sec - 3 min (individualized via iLevels) | WKO5 iLevels [R] |
| Intensity | Well above FTP; iLevel-specific watts | Cusick optimized intervals (TP) [R] |
| Rest | 1:1 to 1:2 work:rest ratio | TMT-46 [E] |
| Sets | 4-10 reps depending on duration | iLevels [R] |

**Notes:**
- FRC intervals target the total work capacity above FTP, not a single watt number [R]
- iLevels individualize the optimal duration and intensity intersection based on each athlete's PD curve -- two athletes with identical FTPs may have very different FRC time ranges (Cusick, TP) [R]
- After the first few seconds of a maximal 30-second effort, the majority of fuel from second 6 to 30 is aerobically derived -- FRC work is never purely "anaerobic" [R] (Moore cadence analysis, TP)
- Specificity matters: race-specific duration may differ from the optimal FRC training duration; periodize by building the energy system first, then applying to event-specific durations (Cusick, TP) [E]

**Platform module:** `pdcurve.py` -- FRC tracking; iLevels optimized interval targeting

### 3.3 VO2max

| Parameter | Value | Source |
|-----------|-------|--------|
| Total time at intensity | ~15-25 min per session | WD-55 [E] |
| Interval formats | 8x3, 5x5, 4x5, 3x8 -- all viable | WD-55 [E] |
| Intensity | 105-120% FTP (varies by individual) | TMT-45 [E] |
| Rest | 50-100% of work duration | WD-55 [E] |
| Target RPE | 9-9.5/10 | TMT-49 [E] |
| Cadence | 100-120 RPM reduces muscular fatigue | WD-55 [R+E] |
| Minimum dose | 1 session/week | TMT-45 [E] |

**Notes:**
- "VO2max power" is not a fixed number -- achievable at a range of powers depending on the individual and the protocol [R] (WD-55)
- High-cadence intervals cause less muscular fatigue, making them preferable for many athletes [R+E]
- Evenly paced efforts are fine, possibly preferable to "start hard" protocols [E] (WD-55)
- Sporadic dosing can work -- one athlete did 3 sessions month 1, 6 sessions month 2 alongside other training and saw massive FTP gains [E] (TMT-60)
- VO2max work "raises the roof" for FTP to grow into -- essential even in minimal plans [E] (TMT-60)

**Conflicts:**
- **30/15 protocol (Ronnestad):** The original study abstract states "no group difference in change of VO2max" (p=0.49). Performance gains are most parsimoniously explained by W' (anaerobic capacity) improvement, not VO2max [R] (WD-55). Cyclocross racing, which delivers massive intermittent effort doses similar to 30/15, never improves VO2max in trained athletes [E]. Conclusion: 30/15s are "super cool but not magic" (Jem Arnold, Persp-38) -- useful for repeatability and FRC, but do not claim VO2max superiority.

**Platform module:** `pdcurve.py` -- VO2max estimation; `blocks.py` -- VO2max block templates

### 3.4 Threshold / FTP

| Parameter | Value | Source |
|-----------|-------|--------|
| Target power | 95-105% FTP | TMT-44, TMT-60 [E] |
| Optimal format | 3x20 or 2x30 min at FTP | TMT-60 [E] |
| Target RPE | ~8/10 | TMT-49 [E] |
| Rest | 5-10 min easy spinning | TP articles [E] |
| TTE tracking | 40-55 min typical trained range | WKO5 [R] |

**Duration progression model (the canonical EC sequence):**

```
4x10 -> 3x15 -> 2x20 -> 2x25 -> 1x40+  (all at FTP)
```

This is THE primary progression path: **extend duration before increasing power** [E] (TMT-45, TMT-60). Power will naturally rise as TTE extends; forcing power up leads to failed sessions.

**Notes:**
- Maximum useful TTE is ~60-75 minutes -- beyond this, opportunity cost is too high; shift to raising FTP itself via VO2max work [E] (TMT-60)
- TTE stagnation at FTP signals the need for VO2max work, not more threshold training [E] (TMT-60)
- Over-under protocol (90%/105% FTP alternating) is effective for race-specific surge simulation [E] (TMT-44)
- In-season maintenance: 1 threshold/sweet spot session every 1-2 weeks at RPE 6-7/10 [E] (TMT-60)

**Platform module:** `training_load.py` -- TTE tracking; `blocks.py` -- FTP decision tree

### 3.5 Sweet Spot

| Parameter | Value | Source |
|-----------|-------|--------|
| Target power | ~88-93% FTP | TMT-44 [E] |
| TTE (untrained) | 40-60 min | TMT-44 [E] |
| TTE (trained) | 90-120 min | TMT-44 [E] |
| TTE (elite) | 180+ min | TMT-44 [E] |

**Notes:**
- Sweet spot provides nearly identical adaptations to threshold work -- difference is cost-benefit ratio, not adaptation type [E] (TMT-44)
- Sweet spot is a tool, not a training philosophy -- must integrate with endurance volume and higher-intensity work [E]
- Becomes time-inefficient as fitness improves: well-trained athletes need 2+ hour sessions for equivalent stimulus to shorter threshold work [E]
- Excellent when fatigued -- good "third hard day" or mid-week option between races [E]
- Overestimated FTP makes sweet spot accidentally productive -- if ramp test inflates FTP, "sweet spot" may actually be threshold training [E]
- For equivalent stimulus, sweet spot intervals must be pushed to near-exhaustion at that intensity [E]

**Platform module:** `zones.py` -- sweet spot band definition; `gap_analysis.py` -- event-specific recommendation

---

## 4. The FTP Training Decision Tree

From TMT-60, the three-branch decision framework:

```
Branch 1: Season Point
  Early season --> Extend threshold duration (4x10 -> ... -> 1x40+)
  Late season  --> Introduce VO2max if FTP has plateaued

Branch 2: Training Age
  Novice      --> Duration progression first, always
  Experienced --> Auto-regulate based on response

Branch 3: Opportunity Cost
  FTP plateau --> Invest in VO2max, durability, sprint, race skills
  TTE > 60-75 min --> Stop extending TTE, raise FTP via VO2max
```

**Plateau detection signal:** FTP unchanged after threshold block + rest + retest --> trigger VO2max block [E]

---

## 5. Work:Rest Ratio Science

| Energy System | Typical Work:Rest | Rationale | Source |
|---------------|------------------|-----------|--------|
| Neuromuscular (5-15s) | 1:10 to 1:20 | Full phosphocreatine resynthesis | [R] |
| FRC/Anaerobic (30s-3min) | 1:1 to 1:2 | Partial lactate clearance, fatigue accumulation | [E] |
| VO2max (3-8 min) | 1:0.5 to 1:1 | Maintain elevated VO2; too much rest lets it drop | [R+E] |
| Threshold (10-40+ min) | 1:0.25 to 1:0.5 | Brief recovery between long sustained efforts | [E] |

**Key insight:** Rest intervals are not "wasted time" -- they are a critical design variable. In VO2max work, shorter rest keeps oxygen consumption elevated. In FRC work, rest duration determines whether subsequent intervals target the same or a different energy system [R].

---

## 6. Progression Models

### 6.1 The Duration-First Principle

The single most repeated theme across EC episodes (TMT-44, 45, 52, 60): **exhaust duration progression before any protocol change.**

| Week | Threshold Example | VO2max Example |
|------|------------------|----------------|
| 1-2 | 4x10 @ FTP | 6x3 @ 110% |
| 3-4 | 3x15 @ FTP | 5x4 @ 110% |
| 5-6 | 2x20 @ FTP | 4x5 @ 110% |
| 7-8 | 2x25 @ FTP | 3x7 @ 110% |
| 9+ | 1x40+ @ FTP | 3x8 @ 108% |

**When duration plateaus** (athlete cannot extend further at the same power):
1. First: check recovery, nutrition, sleep, life stress [E]
2. Second: try a rest week, then retry [E]
3. Third: if still stagnated, consider raising intensity slightly or switching energy system focus [E]

### 6.2 Block Training (Training Density)

From Kolie Moore's work (TP article) and Ronnestad, Hansen, & Ellefsen (2014):

- Block periodization (5 HIT sessions in week 1, then 1/week for 3 weeks) produced significant VO2max increases over traditional periodization (2 HIT/week for 4 weeks) -- despite identical total HIT sessions [R]
- Montero & Lundby (2017): adding 2 hours/week of training eliminated "non-responders" -- there are no true non-responders, only under-dosed athletes [R]
- Block training should be monitored daily for fatigue; always err on the side of more rest [E]
- "With great training stress comes great recovery" -- nutrition and sleep become critical during dense blocks [E]

### 6.3 The Anti-Panic Protocol (TMT-71)

If behind schedule before a target event:

| Time to Event | Recommended Action |
|---------------|-------------------|
| 8+ weeks | Add volume first for 3-4 weeks, THEN start intensity progression |
| 4-8 weeks | Moderate adjustments; accept some limitation |
| <4 weeks | Pivot goals (finish, enjoy, treat as training race) |
| **NEVER** | Double intensity immediately to "catch up" |

---

## 7. ERG Mode vs Free Ride

| Aspect | ERG Mode | Free Ride |
|--------|----------|-----------|
| Precision | Holds exact watts regardless of cadence | Requires athlete self-regulation |
| Skill development | Minimal -- hides true readiness | High -- reveals daily capacity |
| Appropriate for | Beginners learning pacing; specific watt targets | Key sessions; threshold tests; race preparation |
| Risk | Masks fatigue; athlete doesn't learn to pace | Requires more discipline and experience |

**EC recommendation:** Wean off ERG mode for key sessions. Free-ride mode reveals daily capacity and builds pacing skill -- critical for racing [E] (TMT-73).

---

## 8. Indoor vs Outdoor Considerations

| Factor | Indoor | Outdoor |
|--------|--------|---------|
| Interval execution | Non-stop pedaling; precise power control | Terrain, traffic, wind interrupt efforts |
| Thermal load | Higher (less cooling) -- recovery cost 1.1-1.2x outdoor TSS | Natural cooling; more sustainable |
| Skill development | Zero bike handling | Critical for racing -- cornering, descending, pack riding |
| Session duration | Best for <90 min focused sessions | Essential for long endurance rides and race simulation |
| Mental load | Higher RPE at same power for many athletes | More engaging; terrain variation provides natural stimulus |

**Key insight from EC:** Indoor training recovery multiplier is 1.1-1.2x outdoor TSS [E] (TMT-51). An indoor 200 TSS session may cost as much as a 220-240 TSS outdoor ride in recovery terms.

**Warning:** Riders who only train indoors risk losing bike handling skills. Power without handling skills is useless in racing [E] (Hatzis, TP).

---

## 9. When Intervals Stop Working

Intervals cease to produce adaptation when:

1. **Duration progression has been exhausted** and TTE has reached 60-75 min at FTP -- shift to VO2max to "raise the roof" [E] (TMT-60)
2. **Overtraining / under-recovery** -- CTL rising while performance declines is a classic over-reaching signal, not a sign to train harder [E] (TMT-72)
3. **The wrong intervals for the limiter** -- if FTP is the ceiling but VO2max is the limiter, more threshold work will only extend TTE without raising FTP [E] (TMT-60)
4. **Protocol staleness** -- repeating beginner training will NOT produce intermediate gains; yesterday's potent stimulus is today's maintenance [E] (TMT-52)
5. **Life stress exceeds recovery capacity** -- the body has ONE pool for ALL stress (training + work + family + sleep debt); high work stress doubles recovery cost [R] (TMT-48, TMT-57)

**Diagnostic flow:**
```
Performance stagnating?
  --> Check recovery (sleep, nutrition, life stress) first
  --> Check if duration progression is exhausted
  --> Check if energy system target matches the limiter
  --> Consider a rest week (the most underused tool)
  --> THEN consider protocol change
```

---

## 10. Conflicts and Common Misconceptions

| Claim | Evidence-Based Position | Source |
|-------|------------------------|--------|
| "30/15s are the best VO2max training" | No VO2max superiority; gains likely W' (anaerobic capacity) | WD-55 [R] |
| "Start hard to reach VO2max faster" | Evenly paced efforts are fine, possibly preferable | WD-55 [E] |
| "More intervals = more fitness" | >2 hard sessions/week shows no added benefit; increases overtraining risk | Seiler 2010, Hawley 2021 [R] |
| "Micro-optimizing interval structure matters most" | Sustainable training template (basics) outperforms session-level optimization long-term | Persp-38 [E] |
| "You can stack 1-3% gains from different protocols" | Arrow-gains fallacy; micro-optimizations do NOT compound when stacked | WD-61, TMT-68 [E] |
| "100% plan compliance = dedication" | Warning sign; indicates lack of auto-regulation | TMT-52 [E] |
| "ERG mode is better for intervals" | Hides true readiness; free ride reveals daily capacity | TMT-73 [E] |
| "All FTP gains come from threshold work" | FTP stagnation from threshold work requires VO2max to "raise the roof" | TMT-60 [E] |

---

## 11. Practical Quick Reference

### Minimum Viable Interval Plan (TMT-45)

| Day | Session | Detail |
|-----|---------|--------|
| Hard Day 1 | Threshold | Progressive duration: 4x10 -> ... -> 1x40+ at FTP |
| Hard Day 2 | VO2max | 5x4 or 4x5 min at 105-120% FTP |
| All other days | Endurance fill | <65% FTP; ride as much as sustainably possible |
| Optional | Sprint add-on | 3-5 x 10-15 sec at start of endurance ride |
| Every 3-4 weeks | Rest week | >25% normal volume, genuinely easy, IF < 0.50 |

### Session Quality Triangulation (TMT-49)

After every interval session, assess:
- **Power:** Did I hit the target? Trend over weeks at same protocol?
- **Heart rate:** Consistent with previous sessions at same power?
- **RPE:** "Can I do it again?" -- if yes at same power, stimulus was appropriate

**Never** assess any single metric in isolation. Power + HR + RPE together is the gold standard [E].

---

## Platform Integration Notes

| Module | Interval Design Feature |
|--------|------------------------|
| `blocks.py` | Progressive overload tracking; "try longer before trying different" |
| `blocks.py` | FTP decision tree (plateau --> VO2max trigger) |
| `blocks.py` | Block training templates with density management |
| `pdcurve.py` | iLevels for individualized interval intensity + duration targeting |
| `pdcurve.py` | FRC, Pmax, mFTP, TTE, Stamina tracking |
| `training_load.py` | TTE trend monitoring; plateau detection |
| `training_load.py` | Power + HR + RPE triangulation for session quality |
| `zones.py` | RPE targets per zone for interval prescription |
| `gap_analysis.py` | Limiter identification to select correct interval type |
| `clinical.py` | Overtraining detection; panic training flags |

---

## Cross-References

- [FTP & Threshold Testing](ftp-threshold-testing.md) — threshold interval progression (4x10 -> 1x40+) is the canonical FTP development sequence; TTE stagnation triggers protocol shift
- [VO2max Training](vo2max-training.md) — VO2max interval protocols (classic, 30/15, micro-bursts) and the FTP plateau decision tree that triggers a VO2max block
- [Power-Duration Modeling](power-duration-modeling.md) — iLevels from the PD curve individualize interval intensity and duration; FRC tracking guides anaerobic interval prescription
- [Endurance Base Training](endurance-base-training.md) — intervals must be embedded within sufficient endurance volume; the minimum viable plan is 2 hard days + endurance fill
- [Durability & Fatigue](durability-fatigue.md) — late-ride intervals (threshold efforts after 2+ hours of endurance) build fatigue resistance without extra training time
- [Training Periodization](training-periodization.md) — block periodization (5 HIT in week 1 then 1/week) outperformed traditional distribution; anti-panic protocol governs pre-event timing
- [Training Load & Recovery](training-load-recovery.md) — power + HR + RPE triangulation assesses session quality; CTL rising with declining performance signals overreaching
- [Tools & Platforms](../entities/tools-platforms.md) — WKO5 iLevels auto-calculate individualized interval targets from the PD curve; ERG vs free-ride mode considerations

---

## Sources

### Empirical Cycling Podcast
- TMT-44 (Sweet Spot), TMT-45 (Simplest Plan), TMT-46 (Science Interpretation), TMT-49 (Proxies for Stimulus), TMT-52 (Intermediate Mistakes), TMT-54 (Junk Miles), TMT-55 (Rest Weeks), TMT-60 (FTP Decision Tree), TMT-64 (Off-Season), TMT-68 (Using Data), TMT-69 (Riding Easier), TMT-71 (Panic Training), TMT-72 (Stimulus vs Recovery), TMT-73 (Things We Wish We Knew)
- Perspectives-38 (TID, NIRS, FLIA -- Jem Arnold)
- Watts Doc-55 (VO2max Training + 30/15 Reanalysis), WD-56 (Strength Without Weight)

### TrainingPeaks Articles
- Cusick, T. "How to Optimize Interval Training" (iLevels, optimized intervals)
- Cusick, T. "Time to Exhaustion in WKO4" (TTE metric)
- Cusick, T. "An Introduction to the New iLevels in WKO4"
- Moore, K. "Break Through Your Performance Plateau by Increasing Training Density" (block training)
- Moore, K. "Cadence Analysis in WKO4" (cadence and energy system interaction)
- Martinez, P.S. "3 Workouts to Raise Your Functional Threshold Power"
- Fitzgerald, M. "Super-Simple Cycling Interval Progressions"
- Novak, J. "Race Stronger, Longer: How to Build Fatigue Resistance"
- Hatzis, P. "The Problem With Only Training Indoors"
- Mosley, P. "Why High-Intensity Training is Vital for Athletes"
- Araujo, F.C. "Optimizing Performance: Skeletal Muscle Science for Athletes"

### Research
- Ronnestad, Hansen, & Ellefsen (2014). Block periodization of high-intensity aerobic intervals. Scand J Med Sci Sports.
- Montero & Lundby (2017). Refuting the myth of non-response to exercise training. J Physiol.
- Seiler (2010). Best practice for training intensity and duration distribution. Int J Sports Physiol Perform.
- Hawley & Bishop (2021). High-intensity exercise training: too much of a good thing? Nature Reviews Endocrinology.
- Burgomaster et al. (2005). Six sessions of sprint interval training. J Appl Physiol.
- Helgerud et al. (2007). Aerobic high-intensity intervals improve VO2max more than moderate training. Med Sci Sports Exerc.
