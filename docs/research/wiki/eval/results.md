# qmd Knowledge Layer Eval Results

## Token & Speed Metrics (Actual)

| Q | Baseline Tokens | Augmented Tokens | Baseline Duration | Augmented Duration |
|---|-----------------|------------------|-------------------|--------------------|
| 1 | 13,670 | 40,120 | 37.2s | 47.6s |
| 2 | 13,604 | 39,907 | 39.2s | 51.8s |
| 3 | 13,755 | 38,805 | 41.4s | 74.5s |
| 4 | 13,751 | 46,590 | 34.5s | 54.0s |
| 5 | 13,523 | 37,027 | 32.3s | 54.9s |

| Metric | Baseline (avg) | Augmented (avg) | Ratio |
|--------|---------------|-----------------|-------|
| Total tokens | 13,661 | 40,490 | **3.0x** |
| Duration | 36.9s | 56.5s | **1.5x** |
| Tool calls | 2 | 6.2 | 3.1x |
| Output words | 444 | 485 | ~same |

**Cost analysis:** Augmented agents use 3x total tokens (reading 3-4 wiki files adds ~25K input tokens). Duration overhead is only 1.5x — the reads are fast, it's the generation that takes time. Output length is equivalent (~400 words, capped by prompt).

**Cost-effectiveness:** The +2.6 evidence quality gain and +1.0 correctness gain cost 3x tokens and 1.5x latency. For a platform where trust and traceability matter (coaching advice that athletes act on), this is a strong ROI. For quick conversational Q&A, baseline is acceptable.

## Per-Question Scores

| Q | Topic | Dim | Baseline | Augmented | Delta | Notes |
|---|-------|-----|----------|-----------|-------|-------|
| 1 | FTP plateau | Specificity | 4 | 5 | +1 | Both give concrete watts/percentages. Augmented adds week-by-week progression table with exact power targets, RPE values, rest-week IF thresholds, and a meaningful-change threshold (>6W / >2%). Baseline is already strong with specific block prescriptions. |
| 1 | FTP plateau | Evidence | 2 | 5 | +3 | Baseline name-drops Stoggl/Sperlich 2014, Billat, and Seiler but without episode/section specificity -- reads like LLM general knowledge. Augmented cites 9 distinct sources with evidence tags ([E], [R]) and episode IDs (TMT-60, WD-55, WD-62, TMT-71, TMT-45, TMT-69). Every major claim is traced to a source. |
| 1 | FTP plateau | Correctness | 4 | 5 | +1 | Baseline is mostly correct but recommends 8-10x30s all-out efforts which is a neuromuscular session, not wrong but questionable priority for an FTP-plateau athlete. Augmented correctly identifies the core issue (utilization ceiling), includes a "what NOT to do" section catching common errors (threshold intervals progress in duration not power; never double intensity to catch up), and properly sequences the diagnostic logic. |
| 1 | FTP plateau | Actionability | 4 | 5 | +1 | Both are highly actionable. Augmented edges ahead with a structured 6-week progression table, explicit rest-week criteria (IF < 0.50), and post-block retest protocol. Baseline spreads across 3 separate blocks but lacks week-by-week detail within the VO2max block. |
| 2 | VO2max-FTP | Specificity | 4 | 4 | 0 | Both provide the key numbers: fractional utilization ranges (50-60% untrained, 70-80% trained, 80-90% elite), efficiency deltas (15-25W in baseline), VO2max trainability ceiling (~25% in augmented). Roughly equivalent. |
| 2 | VO2max-FTP | Evidence | 3 | 5 | +2 | Baseline cites Coyle 1991, Lucia 2000, Holloszy & Coyle 1984, Joyner & Coyle 2008 -- solid academic references but generic physiology textbook knowledge. Augmented cites wiki sections, EC episodes (TMT-60, WD-55, WD-61, WD-52), TP articles (Baddick, Santos, Johnston), and uses evidence-type tags ([R] vs [E]). The augmented answer connects research to practitioner frameworks. |
| 2 | VO2max-FTP | Correctness | 4 | 5 | +1 | Both are scientifically sound. Augmented adds the important nuance that cross-stimulation (FTP work raising VO2max) disappears with training age, and that VO2max trainability follows a logarithmic curve with ~25% ceiling -- both correct and practically relevant details the baseline omits. Baseline's claim about WKO5 modeling is unsourced and vague. |
| 2 | VO2max-FTP | Actionability | 3 | 4 | +1 | Baseline is more theoretical -- it explains the physiology well but the "bottom line" advice is generic ("threshold and sweet-spot training"). Augmented provides a diagnostic decision tree: stalled FTP + consistent threshold work = introduce VO2max blocks. Still not a full training plan, but more actionable as a decision framework. |
| 3 | 200km fueling | Specificity | 5 | 5 | 0 | Both are excellent. Baseline gives hour-by-hour CHO targets (60-100g/hr with progression), sodium (500-700mg/hr), fluid (500-750mL/hr), caffeine timing, and totals. Augmented adds GE-based energy expenditure calculation, CHO fraction at 0.70 IF, and starting glycogen estimate (2000-2400 kcal). Augmented uses 1:0.8 glucose:fructose ratio (newer research); baseline uses 2:1 (older but still defensible). Both earn top marks. |
| 3 | 200km fueling | Evidence | 2 | 4 | +2 | Baseline cites no sources -- all advice is presented as assertions, albeit correct ones. Augmented cites wiki sections (fueling-fundamentals, race-day-nutrition, ultra-nutrition), and named researchers (Jeukendrup 2004/2010, Romijn 1993, Podlogar & Wallis 2022, King 2022, Burke 2011). Not perfect -- the wiki citations are internal, not peer-reviewed -- but substantially better. |
| 3 | 200km fueling | Correctness | 4 | 5 | +1 | Both are correct. Baseline's 2:1 glucose:fructose ratio is slightly dated -- the more recent Podlogar/Wallis work supports ratios closer to 1:0.8. Augmented correctly notes this and adds the physiological rationale for shifting to liquids at high intensity (splanchnic blood flow drops 60-80%). Baseline's hour-1 target of only 60g/hr is conservative; augmented starts at 80-90g which better reflects current best practice for trained gut athletes. |
| 3 | 200km fueling | Actionability | 5 | 4 | -1 | Baseline is slightly MORE actionable here: it breaks every single hour into its own section with specific food combinations (1 gel + 1 bar + 500ml carb drink = 95g). Augmented groups into 2-hour blocks and provides less granular food-by-food breakdown. Both include summary tables. The baseline's hour-by-hour format is easier to tape to a top tube. |
| 4 | VO2max block | Specificity | 4 | 5 | +1 | Both give day-by-day templates with power targets. Augmented adds rest-week volume (40-60% of normal), specific IF caps (< 0.50 for rest week, < 0.65 for endurance), RPE targets (9-9.5/10 on final rep), and a gating test protocol before resuming loading. Baseline gives TSS targets (450-500, 500-550, 300-350) which is useful but less specific on execution details. |
| 4 | VO2max block | Evidence | 2 | 5 | +3 | Baseline cites zero sources. All prescriptions are presented as coaching knowledge with no traceability. Augmented cites Seiler 2010 [R], 8 EC episode numbers (WD-55, TMT-45, TMT-49, TMT-52, TMT-55, TMT-60), TP contributors (Santos, Simone), and wiki sections with page-level specificity. |
| 4 | VO2max block | Correctness | 4 | 5 | +1 | Both are physiologically sound. Baseline includes 30/15s short-short intervals which are valid but an aggressive protocol choice for week 1 of a VO2max block -- most coaches would start with classic long intervals and progress to short-shorts. Augmented explicitly addresses this: "progressive overload before protocol change -- add one rep or extend interval duration before switching to 30/15s." Augmented also includes the no-caloric-restriction rule during VO2max blocks, which is a commonly violated and important point. |
| 4 | VO2max block | Actionability | 4 | 5 | +1 | Both are ready-to-execute. Augmented adds recovery-week gating test (sprint + 5 min at FTP), monitoring warning signs (HRV depression >7 days, failed session protocol), post-block retest metric (5-min peak power, >5% gain threshold), and the 36-48hr spacing rule. These details make it safer to execute unsupervised. |
| 5 | Durability | Specificity | 3 | 5 | +2 | Baseline explains the concept clearly but with only one hypothetical example (4.5 W/kg vs 4.2 W/kg). Augmented provides real data: Neben vs Cat 3 rider (272W vs 274W fresh, 4W vs 32W drop at 2000 kJ), van Erp et al. World Tour data (6.28 W/kg, 4% loss vs 5.99 W/kg, 9% loss at 50 kJ/kg), and the dual exponential decay model parameters. Concrete, named, verifiable. |
| 5 | Durability | Evidence | 2 | 5 | +3 | Baseline mentions "Maarten Munten" and "Cycling Science podcast" but no paper citations, no episode IDs, and no data. Augmented cites Maunder et al. 2021, van Erp et al. 2021, Tim Cusick case study, wiki sections with specific section numbers, and EC episodes (WD-60, TMT-70) with evidence tags. |
| 5 | Durability | Correctness | 4 | 5 | +1 | Both are correct on fundamentals. Baseline's mention of "Maarten Munten" as a durability researcher appears to be an error -- the primary authors are Maunder, van Erp, and Leo. Augmented correctly attributes the foundational paper to Maunder et al. 2021 and adds the important caveat that durability improvements without sufficient absolute power yield diminishing returns -- a nuance the baseline misses. |
| 5 | Durability | Actionability | 3 | 4 | +1 | Baseline gives a vague training prescription: "sustained aerobic volume, long rides with intensity in the final hours, heat acclimation, dialed nutrition." Augmented is still more conceptual than prescriptive (it is answering a "what is" question, not a "how to train" question) but provides the WKO5 modeling framework (kJ-based + time-based fatigue) and platform-specific guidance for evaluation. Neither answer is a training plan, which is appropriate for the question asked. |

## Summary

| Dimension | Avg Baseline | Avg Augmented | Avg Delta |
|-----------|-------------|---------------|-----------|
| Specificity | 4.0 | 4.8 | +0.8 |
| Evidence | 2.2 | 4.8 | +2.6 |
| Correctness | 4.0 | 5.0 | +1.0 |
| Actionability | 3.8 | 4.4 | +0.6 |
| **Overall** | **3.5** | **4.8** | **+1.3** |

## Key Observations

### What improved dramatically

**Evidence quality is the standout gain (+2.6 avg).** The baseline answers read like a competent coach speaking from memory -- assertions are generally correct but unverifiable. The augmented answers consistently cite episode IDs (TMT-60, WD-55, etc.), wiki section numbers, named researchers with publication years, and use evidence-type tags ([R] for research, [E] for expert opinion). This is the single largest differentiator and the primary value-add of the knowledge layer.

**Correctness improved meaningfully (+1.0 avg).** The knowledge base appears to prevent subtle errors: the baseline's potentially hallucinated "Maarten Munten" attribution in Q5, the outdated 2:1 glucose:fructose ratio in Q3, and the aggressive short-short protocol placement in Q4. The augmented answers also consistently include appropriate caveats and "what NOT to do" guidance that prevents common misapplication.

### What improved modestly

**Specificity (+0.8) and actionability (+0.6) showed smaller gains.** The baseline model already produces reasonably specific, actionable coaching advice. The knowledge layer adds precision at the margins -- rest-week IF thresholds, gating test protocols, meaningful-change thresholds -- but does not transform fundamentally weak answers into strong ones.

### One regression noted

**Q3 actionability: baseline scored higher (-1).** The baseline's hour-by-hour breakdown with specific food combinations is more practical for race-day execution than the augmented version's 2-hour groupings. The augmented answer traded some granularity for physiological depth (GE calculations, CHO fraction estimates). For a question explicitly asking "how should I fuel it hour by hour," the baseline format better matches the request.

### Structural patterns

The augmented answers consistently include a **sources section** at the end, which adds transparency and allows the athlete to verify claims. The baseline never does this. The augmented answers also tend to be more structured around **decision logic** (if FTP stalled + threshold work consistent -> introduce VO2max blocks) rather than generic recommendation lists.

The knowledge layer's value is highest when the question requires **diagnostic reasoning** (Q1, Q2) or **specific data points** (Q5) and lowest when the question is primarily about **practical logistics** (Q3 hour-by-hour format). This suggests the knowledge base excels at encoding coaching frameworks and research but should not override practical execution formatting.
