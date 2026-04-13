# Eval: Local LLM (Gemma 4 31B) vs Cloud Methods

## Per-Question Scores (4-way)

### Q1: FTP Plateau at 280W

| Q | Topic | Dim | Baseline | v2 (Claude+wiki) | Local (Gemma+wiki) | Notes |
|---|-------|-----|----------|-------------------|---------------------|-------|
| 1 | FTP plateau | Specificity | 4 | 5 | 3 | Local gives no watt targets, no progression table, no rep/set scheme. Just "begin a VO2max block" and "progress duration not power" without any numbers. |
| 1 | FTP plateau | Evidence | 2 | 5 | 4 | Local cites TMT-45, TMT-58, TMT-60 with [E] tags -- correct and traceable. But only 3 episodes vs v2's 10. No wiki page names, no researchers cited. |
| 1 | FTP plateau | Correctness | 4 | 5 | 5 | Core diagnosis is correct: utilization ceiling hit, VO2max is the bottleneck. TTE stagnation at 60-75 min correctly identified. Duration-first principle correctly stated. No errors. |
| 1 | FTP plateau | Actionability | 4 | 4 | 2 | Not actionable at all. No specific intervals prescribed (no "4x4 min at 320-335W"), no week structure, no rest-week protocol, no retest criteria. An athlete reading this knows *what* to do conceptually but has zero execution detail. |

**Notes:** This is the starkest gap in the eval. The local answer is 163 words -- barely a paragraph. v2 provides 400 words with a complete 6-week plan, watt targets, IF thresholds, and a "What NOT to do" section. The local answer reads like a correct summary of the wiki rather than a coaching response. The diagnosis is right; the prescription is absent.

---

### Q2: VO2max-FTP Relationship

| Q | Topic | Dim | Baseline | v2 (Claude+wiki) | Local (Gemma+wiki) | Notes |
|---|-------|-----|----------|-------------------|---------------------|-------|
| 2 | VO2max-FTP | Specificity | 4 | 4 | 3 | Local mentions 70-85% utilization range and TTE stagnation at 60-75 min, but omits phlebotomy study, trainability ceiling (~25%), cross-stimulation loss with training age, and efficiency as independent pathway. |
| 2 | VO2max-FTP | Evidence | 3 | 5 | 3 | Cites TMT-45, TMT-60 with [E]/[R] tags. But only 2 episode references. No researchers (Santos, Baddick, Bobo, Johnston), no WD episodes, no TP articles. |
| 2 | VO2max-FTP | Correctness | 4 | 5 | 5 | Everything stated is accurate. Ceiling/utilization framework correct. FTP-as-fraction-of-VO2max correct. TTE diagnostic correct. No errors -- but significant omissions (phlebotomy study, cross-stimulation, efficiency). |
| 2 | VO2max-FTP | Actionability | 3 | 4 | 3 | Same as baseline: provides diagnostic signal (TTE stagnation) but no interval prescription, no training plan. Matches baseline's explanatory depth without the wiki-backed specifics v2 adds. |

**Notes:** The local answer is competent but thin. At 185 words it covers the ceiling/utilization framework correctly and includes the TTE stagnation diagnostic, which baseline missed. But it lacks the multi-study evidence base and the nuanced points (cross-stimulation disappearance, efficiency as independent pathway, VO2max trainability cap) that make v2 a genuinely richer answer.

---

### Q3: 200km Fueling Plan

| Q | Topic | Dim | Baseline | v2 (Claude+wiki) | Local (Gemma+wiki) | Notes |
|---|-------|-----|----------|-------------------|---------------------|-------|
| 3 | 200km fueling | Specificity | 5 | 5 | 4 | Local provides CHO targets by phase (80-120, 60-90, 40-70 g/hr), pre-race loading (10-12 g/kg, 780-936g), glucose:fructose ratio missing, and body-weight-specific post-ride numbers. Phase table is less granular than v2's hour-by-hour. |
| 3 | 200km fueling | Evidence | 2 | 4 | 3 | Cites nutrition-racing.md and nutrition-ultra.md with section references, [R]/[E] tags, and pacing-strategy.md. But no researchers (Jeukendrup, Podlogar, Wallis, Burke, King), no EC episodes. |
| 3 | 200km fueling | Correctness | 4 | 5 | 4 | Mostly correct. Phase-based tapering is sound. Pre-race loading at 10-12 g/kg is standard. But 80-120 g/hr in Phase 1 is aggressive for the first 6 hours straight -- v2 correctly targets 80-90 g/hr for first 5-6 hours. Also uses outdated glucose:fructose guidance implicitly (does not mention 1:0.8 ratio). The 12+ hour Phase 3 is irrelevant for a 7-8 hour ride. |
| 3 | 200km fueling | Actionability | 5 | 4 | 4 | Phase table is structured and executable. Includes practical rules (eat within 15-20 min, liquids on climbs, gels with water, pacing-for-nutrition). Post-ride recovery protocol included. Loses a point vs baseline because the phases are too coarse for a 7-8 hour ride (3 phases vs baseline's 7 hourly rows). |

**Notes:** Q3 is the local model's strongest showing. At 400 words it provides a structured, phased plan with pre-race, during-race, and post-race protocols. The main weaknesses: the phase structure assumes a 12+ hour event (Phase 3 starts at "12+ hours" -- this is a 7-8 hour ride), the glucose:fructose ratio is not mentioned, and the CHO range in Phase 1 (80-120 g/hr) is wider than optimal. Still, this is a usable fueling plan.

---

### Q4: 3-Week VO2max Block

| Q | Topic | Dim | Baseline | v2 (Claude+wiki) | Local (Gemma+wiki) | Notes |
|---|-------|-----|----------|-------------------|---------------------|-------|
| 4 | VO2max block | Specificity | 4 | 5 | 4 | Local provides a weekly table with interval progression (5x3min -> 5x4min -> 4x5min), intensity targets (105-120% FTP), cadence (100-120 RPM), RPE (9-9.5), and endurance fill IF (0.50-0.65). Missing: day-by-day template, threshold session detail, gating test, rest-week volume/duration specifics. |
| 4 | VO2max block | Evidence | 2 | 5 | 4 | Cites TMT-45, TMT-49, TMT-55, TMT-60, WD-54, WD-55, Persp-41, Santos (TP), plus wiki page names with section references. Good density for a local model. |
| 4 | VO2max block | Correctness | 4 | 5 | 4 | Core structure is correct: duration-first progression, 1-2 VO2max sessions/week, classic long intervals, high cadence, fueling emphasis. But only includes 1 VO2max session/week in the schedule (v2 correctly uses 2/week). The progression jumps from 5x3 to 5x4 to 4x5 -- the rep drop in week 3 while extending duration is unusual and not clearly justified. Rest week mentions 7+ days at IF < 0.50, which is correct. |
| 4 | VO2max block | Actionability | 4 | 5 | 3 | The weekly schedule has only 2 columns (VO2max session + maintenance/endurance) -- an athlete cannot build a full week from this. No day-by-day structure, no total ride counts, no session durations. v2 provides a 7-day template with specific sessions for every day. The post-block rest week instruction is present but vague. |

**Notes:** The local model's Q4 answer (293 words) is structurally competent but incomplete as a training plan. It reads as an interval progression guide rather than a complete 3-week block. The one-session-per-week VO2max dose is a meaningful error -- the wiki and v2 both prescribe 2 sessions/week, which is the evidence-supported dose. The missing day-by-day template means an athlete still needs to figure out how to distribute 10 hours across the week.

---

### Q5: Durability

| Q | Topic | Dim | Baseline | v2 (Claude+wiki) | Local (Gemma+wiki) | Notes |
|---|-------|-----|----------|-------------------|---------------------|-------|
| 5 | Durability | Specificity | 3 | 5 | 4 | Local includes kJ-based measurement, the Neben vs Cat 3 case study (272W/274W, 4W/32W drop), and the power drop benchmarks (< 2% to 20-40%). Missing: van Erp W/kg data, dual exponential model, specific training recommendations. |
| 5 | Durability | Evidence | 2 | 5 | 4 | Cites Maunder et al. August 2021, WD-60, WD-62, TMT-70, and Cusick/TrainingPeaks. Correctly attributes the formal definition. No van Erp citation despite using the benchmark table. |
| 5 | Durability | Correctness | 4 | 5 | 5 | All claims are accurate. Formal definition correctly attributed to Maunder. Cusick case study numbers match. "Absolute power first" caveat correctly stated. "Race results can improve through durability gains even if FTP remains flat" is nuanced and correct. No errors. |
| 5 | Durability | Actionability | 3 | 4 | 3 | Explains the concept well but offers no training prescriptions. Does not include v2's training implications (long rides 4-6+ hours, late-ride intervals) or the fueling lever (60-90 g/hr as most actionable durability improvement). |

**Notes:** Q5 is the local model's second-best result. At 208 words it correctly defines durability, provides the Cusick case study with exact numbers, includes the benchmark table, and nails the "absolute power first" caveat. The main gap vs v2 is the absence of training implications and the fueling connection. For a pure "what is durability?" question, this is a solid answer. For "how do I improve it?" the answer is silent.

---

## Summary Averages

| Dimension | Baseline | v2 (Claude+wiki) | Local (Gemma+wiki) |
|-----------|----------|-------------------|---------------------|
| Specificity | 4.0 | 4.8 | 3.6 |
| Evidence | 2.2 | 4.8 | 3.6 |
| Correctness | 4.0 | 5.0 | 4.6 |
| Actionability | 3.8 | 4.2 | 3.4 |
| **Overall** | **3.5** | **4.7** | **3.8** |

## Performance Comparison

| Metric | Baseline | v2 (Claude+wiki) | Local (Gemma+wiki) |
|--------|----------|-------------------|---------------------|
| Avg words | 444 | 487 | 250 |
| Avg tokens (API) | 13,661 | 34,711 | 0 (local) |
| Avg duration | 36.9s | 53.6s | 52.1s |
| API cost | ~$0.04 | ~$0.12 | $0.00 |

## Dimension-by-Dimension Analysis

### Specificity (Local 3.6 vs v2 4.8, gap: -1.2)
The largest deficit. The local model consistently omits concrete numbers that the wiki provides and that v2 extracts. Q1 has no watt targets at all. Q4 is missing a day-by-day schedule. The local model appears to summarize wiki concepts rather than extract and present specific data points. This is likely a model-size limitation: 31B parameters underperform at the "find the number in the source and put it in the answer" task that larger models handle naturally.

### Evidence (Local 3.6 vs v2 4.8, gap: -1.2)
The local model cites episode IDs and uses evidence tags, which shows it understands the wiki's citation format. But citation density is roughly 40% of v2's. Researcher names are almost entirely absent. Wiki section numbers appear in Q3 and Q4 but not Q1 or Q2. The local model seems to cite what it remembers rather than systematically extracting all relevant sources.

### Correctness (Local 4.6 vs v2 5.0, gap: -0.4)
The smallest gap and the local model's strongest dimension. Nothing in the local answers is wrong. The Q4 one-session-per-week issue is the only functional error, and even that is "incomplete" rather than "incorrect." The local model is conservative -- it says less, but what it says is accurate. This is a good failure mode for a coaching knowledge base.

### Actionability (Local 3.4 vs v2 4.2, gap: -0.8)
The local model's answers are consistently less executable. Q1 is the worst case: a correct diagnosis with no prescription. Q4 provides intervals but not a complete training week. Q5 explains durability but does not say how to train it. The pattern is clear: the local model explains concepts from the wiki but does not synthesize them into actionable plans. v2 (and even baseline) are better at the "so what do I actually do?" step.

## Key Observations

### Where does the local LLM match or beat v2?

**Correctness only.** The local model scores 4.6 vs 5.0 -- a narrow gap. On Q1, Q2, and Q5, the local model's core claims are factually correct and properly sourced. It never hallucinates studies, never invents numbers, and never makes the kind of confident-but-wrong statements that baseline occasionally produces (e.g., baseline's 30/15s short-short protocol in week 1 for Q4, baseline's "Maarten Munten" attribution in Q5). For a model running entirely offline on consumer hardware, this is a meaningful result.

The local model also slightly beats baseline on evidence (3.6 vs 2.2) thanks to wiki access. It can extract and cite episode IDs, which baseline cannot.

### Where does it fall short?

**Everywhere except correctness, and significantly so.**

1. **Brevity is the main problem.** At 250 words average vs v2's 487, the local answers are roughly half the length. This is not a virtue -- the missing content is not filler but specific numbers, training tables, execution details, and nuanced caveats.

2. **Synthesis is weak.** The local model summarizes what the wiki says. v2 synthesizes wiki content into coaching responses. Compare Q1: local says "begin a VO2max block" (wiki summary), v2 says "4x4 min at 115-120% FTP (~320-335W for you), 3 min easy recovery, progress weekly" (synthesized prescription). This synthesis gap appears in every question.

3. **Q3 fueling plan has a structural error.** The 3-phase template with Phase 3 starting at "12+ hours" is copy-pasted from ultra-nutrition wiki content that covers events beyond 12 hours. The local model failed to adapt the template to the 7-8 hour ride duration specified in the question. v2 correctly scopes its phases to the actual ride.

4. **Q4 VO2max block prescribes half the dose.** One VO2max session per week vs the evidence-supported two sessions per week. This is the single most consequential error in the eval because an athlete following this plan would get a suboptimal training stimulus.

### Is the quality difference worth the cost savings?

**No, not for coaching-quality answers.** The gap is 0.9 points on a 5-point scale (3.8 vs 4.7 overall). In practical terms:

- v2 produces answers an athlete can execute immediately. Local produces answers an athlete would need a coach to interpret.
- The $0.12/question cost of v2 is trivially small. Even at 100 questions/month, that is $12.
- The local model's latency (52.1s) is comparable to v2 (53.6s), so there is no speed advantage.

The cost savings are real but the quality delta is too large for the primary use case (athlete self-coaching). At $0.00 vs $0.12 per query, you save money but deliver materially worse answers.

### When to use each method

| Method | Best use case |
|--------|--------------|
| **v2 (Claude+wiki)** | Primary method for all coaching questions. Best quality, traceable evidence, actionable plans. Worth the $0.12/query. |
| **Local (Gemma+wiki)** | Offline scenarios (no internet), privacy-sensitive contexts, or high-volume low-stakes queries (e.g., wiki content lookup, quick concept checks). Acceptable for "what does X mean?" but not for "design my training plan." |
| **Baseline (no wiki)** | Fallback only. Useful for general knowledge questions outside the wiki's scope. Not recommended for training-specific queries where the wiki has content. |

### Summary verdict

The local Gemma 4 31B model with wiki access scores 3.8/5.0 overall -- above baseline (3.5) but well below v2 (4.7). It proves that RAG with a local model works: wiki access lifts correctness and evidence above no-wiki baseline. But the 31B model lacks the synthesis and detail-extraction capabilities that make v2's answers coaching-grade. The gap is not subtle -- it is the difference between "here is what the research says" and "here is your training plan for the next 6 weeks."

For a knowledge base meant to support athlete self-coaching, v2 remains the clear choice. The local model is a viable offline fallback, not a replacement.
