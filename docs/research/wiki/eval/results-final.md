# Final Eval: All Methods Compared

## Per-Question Scores

### Q1: FTP Plateau at 280W

| Dim | Baseline | v2 (Claude+wiki) | Local (Gemma) | Hybrid (prefetch->Claude) |
|-----|----------|-------------------|---------------|---------------------------|
| Specificity | 4 | 5 | 3 | 4 |
| Evidence | 2 | 5 | 4 | 2 |
| Correctness | 4 | 5 | 5 | 4 |
| Actionability | 4 | 4 | 2 | 4 |

**Hybrid notes:** The hybrid answer reads like a competent general-knowledge response, not a wiki-backed one. It prescribes 4-6x4 min at 105-120% FTP (correct range), over-under intervals, polarized training rationale (Stoggl and Sperlich), and periodized blocks. But it cites zero EC episodes, zero wiki pages, zero evidence tags. The specificity is a step up from a fully generic answer -- it includes watt ranges for the rider's 280W FTP and a 6-point action plan -- but it lacks v2's exact targets (308-336W at 110-120% FTP), the 6-week progression table, rest-week IF thresholds (<0.50), and the >6W/>2% meaningful-change threshold. The "Billat-style intervals" mention and the neuromuscular/force work section do not appear in the wiki and are standard sports science knowledge. **The prefetch summary was too thin to transmit the wiki's specific data points to Claude.**

Correctness gets 4 not 5: the answer suggests 3 VO2max sessions per week in Block 1, which exceeds the evidence-supported dose of 2/week (Seiler 2010). This is the same error baseline makes. Without wiki grounding, Claude defaults to its general knowledge, which is slightly aggressive here.

---

### Q2: VO2max-FTP Relationship

| Dim | Baseline | v2 (Claude+wiki) | Local (Gemma) | Hybrid (prefetch->Claude) |
|-----|----------|-------------------|---------------|---------------------------|
| Specificity | 4 | 4 | 3 | 4 |
| Evidence | 3 | 5 | 3 | 3 |
| Correctness | 4 | 5 | 5 | 4 |
| Actionability | 3 | 4 | 3 | 3 |

**Hybrid notes:** The hybrid answer covers the ceiling/utilization framework correctly, includes the FTP = VO2max x FU x GE equation, provides the 70-85% utilization range, and explains that FTP can rise through FU and efficiency gains. Structure and reasoning are sound.

However, it reads almost identically to the baseline. It cites no EC episodes, no wiki pages, no evidence tags, no researchers from the wiki (Santos, Baddick, Bobo, Johnston). It does not mention the phlebotomy study (WD-53), cross-stimulation loss with training age, the TTE stagnation diagnostic at 60-75 min, or the ~25% VO2max trainability ceiling. These are exactly the data points that distinguish wiki-backed answers from general knowledge.

Correctness gets 4 not 5: the answer states efficiency can "vary 18-25% across cyclists at similar VO2max levels" -- this is plausible but not sourced from the wiki, and the specific claim is hard to verify. More importantly, the answer lacks the nuanced diagnostic logic (TTE stagnation signal, cross-stimulation disappearance) that v2 correctly includes. Nothing is wrong, but significant wiki-sourced insights are absent.

---

### Q3: 200km Fueling Plan

| Dim | Baseline | v2 (Claude+wiki) | Local (Gemma) | Hybrid (prefetch->Claude) |
|-----|----------|-------------------|---------------|---------------------------|
| Specificity | 5 | 5 | 4 | 5 |
| Evidence | 2 | 4 | 3 | 2 |
| Correctness | 4 | 5 | 4 | 4 |
| Actionability | 5 | 4 | 4 | 5 |

**Hybrid notes:** This is the hybrid method's strongest question. The answer provides a full hour-by-hour fueling table with specific CHO targets per hour (60g -> 80-90g -> 80-90g -> 60-80g), fluid targets (500-750ml/hr), sodium (500-1000mg/hr), caffeine timing (hour 6-7), pre-ride protocol, and a totals summary table. The structure is highly actionable.

But the evidence is entirely general sports science. No EC episodes, no wiki pages, no evidence tags. The glucose:fructose ratio is mentioned both as "2:1" and "1:0.8" -- the hybrid answer uses "2:1 or 1:0.8" which hedges correctly but suggests Claude is falling back to its own knowledge rather than the wiki's definitive guidance (which favors 1:0.8 per Podlogar/Wallis). The answer does not cite Jeukendrup, Podlogar, Wallis, Burke, or King.

Correctness gets 4 not 5: starting at 60g/hr in hour 1 is more conservative than the wiki-backed recommendation of 80-90g/hr from the start. The splanchnic blood flow rationale for switching to gels on climbs is absent. The GE-based energy expenditure calculation is absent. These are not errors -- the plan is safe and executable -- but it misses the wiki's more precise physiological grounding.

Actionability gets 5: the hour-by-hour format with specific food suggestions per hour is the most directly executable format in the eval. An athlete can tape this to a top tube.

---

### Q4: 3-Week VO2max Block

| Dim | Baseline | v2 (Claude+wiki) | Local (Gemma) | Hybrid (prefetch->Claude) |
|-----|----------|-------------------|---------------|---------------------------|
| Specificity | 4 | 5 | 4 | 4 |
| Evidence | 2 | 5 | 4 | 2 |
| Correctness | 4 | 5 | 4 | 4 |
| Actionability | 4 | 5 | 3 | 4 |

**Hybrid notes:** The hybrid answer provides a complete day-by-day weekly template, three interval session types (4x4, 30/15 Billat, decreasing intervals), a 3-week progression (loading, overreach, taper+test), and execution notes covering HR targets, pacing, recovery, and Z2 strictness. This is a usable training block.

Evidence is pure general knowledge: no EC episodes, no wiki pages, no evidence tags, no Seiler 2010 citation. The answer mentions Billat but not by proper citation. The wiki's specific sources (TMT-45, TMT-49, TMT-52, TMT-55, TMT-60, WD-55, Santos/Simone TP, Ronnestad 2020) are entirely absent.

Correctness gets 4 not 5: the answer prescribes 3 VO2max sessions per week (Tue/Thu/Sat), which exceeds the evidence-supported 2/week dose. The wiki and v2 both limit to 2 VO2max sessions plus 1 threshold session. Three VO2max sessions per week in a loading block is aggressive and not supported by Seiler's research. Also, the 2:1 mesocycle structure (2 loading, 1 recovery) from the wiki is replaced by a 2-week load + 1-week "taper+test" framing, which is functionally similar but misses the explicit recovery week guidance (IF < 0.50, 40-60% volume).

The gating test (sprint + 5 min at FTP to assess readiness) and warning signs (HRV depression >7 days, failed session protocol) from v2 are absent.

---

### Q5: Durability

| Dim | Baseline | v2 (Claude+wiki) | Local (Gemma) | Hybrid (prefetch->Claude) |
|-----|----------|-------------------|---------------|---------------------------|
| Specificity | 3 | 5 | 4 | 3 |
| Evidence | 2 | 5 | 4 | 2 |
| Correctness | 4 | 5 | 5 | 3 |
| Actionability | 3 | 4 | 3 | 3 |

**Hybrid notes:** The hybrid answer defines durability correctly, provides a hypothetical two-rider comparison (300W FTP, Rider A retains 270W at hour 4 vs Rider B at 240W), lists physiological underpinnings (glycogen depletion, neuromuscular fatigue, cardiovascular drift, central fatigue), and describes measurement methods (TTE, power-duration curve decay, decoupling). Training implications are mentioned briefly (long rides, late-ride intensity, heat acclimation, nutrition).

Evidence is absent: no Maunder et al. 2021, no van Erp et al. 2021, no Cusick case study with real numbers, no EC episodes (WD-60, TMT-70, TMT-73). The answer uses a fabricated example instead of the wiki's actual data (Neben vs Cat 3 rider: 272W/274W fresh, 4W/32W drop at 2000 kJ). The benchmark table (Elite <2%, Strong amateur 2-10%, etc.) is entirely absent.

Correctness gets 3: the answer attributes durability quantification to "researchers like Maarten Munten and those at the Cycling Science podcast." Maunder (not Munten) et al. August 2021 is the correct attribution. "Cycling Science podcast" is not a standard reference -- the relevant podcast is Empirical Cycling. This is the same "Maarten Munten" error that appeared in the baseline, confirming that the prefetch summary did not transmit the correct researcher name. This is a factual error that the wiki-backed methods (v2, local) both avoid.

---

## Summary

| Dimension | Baseline | v2 (Claude+wiki) | Local (Gemma) | Hybrid (prefetch->Claude) |
|-----------|----------|-------------------|---------------|---------------------------|
| Specificity | 4.0 | 4.8 | 3.6 | 4.0 |
| Evidence | 2.2 | 4.8 | 3.6 | 2.2 |
| Correctness | 4.0 | 5.0 | 4.6 | 3.8 |
| Actionability | 3.8 | 4.2 | 3.4 | 3.8 |
| **Overall** | **3.5** | **4.7** | **3.8** | **3.5** |

## Performance & Cost

| Metric | Baseline | v2 | Local | Hybrid |
|--------|----------|-----|-------|--------|
| Duration | 37s | 54s | 52s | ~65s (prefetch+Claude) |
| Claude tokens | 13.7K | 34.7K | 0 | ~15K (est) |
| API cost | ~$0.04 | ~$0.12 | $0 | ~$0.05 |
| Output words | 444 | 485 | 250 | ~376 |

## Per-Question Overall Averages

| Question | Baseline | v2 | Local | Hybrid |
|----------|----------|-----|-------|--------|
| Q1 FTP plateau | 3.5 | 4.75 | 3.5 | 3.5 |
| Q2 VO2max-FTP | 3.5 | 4.5 | 3.5 | 3.5 |
| Q3 Fueling | 4.0 | 4.5 | 3.75 | 4.0 |
| Q4 VO2max block | 3.5 | 5.0 | 3.75 | 3.5 |
| Q5 Durability | 3.0 | 4.75 | 4.0 | 2.75 |

## Key Findings

### The hybrid prefetch adds zero measurable value over baseline

The hybrid method scores 3.5 overall -- identical to baseline (3.5). On no question does the hybrid answer demonstrate wiki-sourced knowledge that baseline lacks. The 35-150 word Gemma summaries were too compressed to transmit the wiki's specific data points (exact watt targets, episode IDs, researcher names, benchmark tables, progression protocols) to Claude. Claude received the summaries and then answered from its own general knowledge, producing answers that are structurally similar to baseline but with no evidence uplift.

### Evidence dimension: hybrid = baseline = 2.2

This is the most damning result. The entire point of the prefetch step is to inject wiki evidence into Claude's context. But the hybrid answers cite zero EC episodes, zero wiki pages, zero evidence tags across all five questions. The prefetch summaries apparently did not preserve citations, and Claude had no way to recover them.

### Hybrid is worse than baseline on Q5 correctness

The hybrid answer reproduces the baseline's "Maarten Munten" error (correct: Maunder) and misattributes the source to "Cycling Science podcast" (correct: Empirical Cycling). This means the prefetch summary either did not contain the correct attribution or contained it in a form Claude could not use. The wiki-reading methods (v2 at 5, local at 5) both get this right. The hybrid's correctness score (3.8) is the only dimension where it underperforms baseline (4.0).

### The cost savings do not justify the quality loss vs v2

Hybrid saves ~$0.07/query vs v2 ($0.05 vs $0.12) but delivers v2-minus-1.2-points quality. At 100 queries/month the savings are $7 total. The quality difference is the gap between "coaching-grade with traceable evidence" and "generic sports science with no sourcing."

### Local Gemma outperforms hybrid despite running entirely offline

Local (3.8) beats hybrid (3.5) by 0.3 points. This is because the local model reads the full wiki pages and can extract specific data points (Cusick case study numbers, episode IDs, benchmark tables), even if it under-synthesizes them. The hybrid approach loses this information in the prefetch compression step.

## Method Ranking

1. **v2 (Claude+wiki): 4.7** -- Clear winner. Coaching-grade answers with traceable evidence. Worth $0.12/query.
2. **Local (Gemma 31B): 3.8** -- Viable offline fallback. Correct but thin. Best for concept lookups and low-stakes queries.
3. **Baseline (no wiki): 3.5** -- General knowledge only. Acceptable when wiki is unavailable.
4. **Hybrid (prefetch->Claude): 3.5** -- Tied with baseline. The prefetch step adds latency and complexity without improving quality.

## Recommendation

**Drop hybrid from the pipeline.** It adds ~11s of latency, requires orchestrating two models, and produces answers indistinguishable from baseline. The prefetch summaries (35-150 words) are below the information density threshold needed to transmit wiki-specific knowledge to Claude.

**Use v2 as the default** for all coaching questions. The $0.12/query cost is trivially small for the quality it delivers.

**Use local Gemma for offline/privacy scenarios only.** It outperforms both baseline and hybrid when reading full wiki pages directly, but its synthesis and actionability gaps make it unsuitable as a primary method.

**If hybrid is revisited**, the prefetch summaries need to be 3-5x longer (150-500 words) and must preserve: (a) exact numerical data points, (b) episode/source IDs, (c) researcher names, and (d) progression tables. At that summary length, the token savings vs v2 shrink further, making the approach even harder to justify economically.
