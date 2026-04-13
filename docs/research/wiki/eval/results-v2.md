# Eval v2 Results -- Index-First Retrieval

## Per-Question Scores (3-way)

### Q1: FTP Plateau at 280W

| Q | Topic | Dim | Baseline | v1 (direct) | v2 (index-first) | v1->v2 Delta |
|---|-------|-----|----------|-------------|-------------------|--------------|
| 1 | FTP plateau | Specificity | 4 | 5 | 5 | 0 |
| 1 | FTP plateau | Evidence | 2 | 5 | 5 | 0 |
| 1 | FTP plateau | Correctness | 4 | 5 | 5 | 0 |
| 1 | FTP plateau | Actionability | 4 | 5 | 4 | -1 |

**Notes:**

- Specificity: v2 provides exact watt targets (308-336W at 110-120% FTP), a 6-week progression table with rep/duration changes, RPE targets, IF thresholds for rest weeks (<0.50), and the >6W/>2% meaningful-change threshold. Matches v1 quality.
- Evidence: v2 cites 10 EC episode IDs (TMT-45, TMT-55, TMT-58, TMT-60, TMT-66, TMT-69, TMT-71, WD-55, WD-62), wiki page names, evidence tags ([E], [R]), and Seiler 2010. Comparable density and traceability to v1.
- Correctness: Both v1 and v2 correctly identify the utilization ceiling as the root cause, properly sequence the diagnostic logic (plateau after threshold block + rest + retest = VO2max needed), and include the "what NOT to do" section. v2 adds the valuable point that "threshold intervals progress in duration, not power" (TMT-45) and warns against judging progress by FTP alone (TMT-70). No errors detected in either.
- Actionability: v1 has a slightly more structured week-by-week progression table (6 weeks with exact week-by-week detail plus rest-week criteria and post-block retest protocol). v2 provides the same table but the prose structure is slightly less formatted for execution -- it reads more like an explanation with embedded prescriptions than a ready-to-execute plan. The "What NOT to do" section in v2 is excellent and arguably more useful than v1's, but v1's tabular format wins on immediate executability. Minor regression.

---

### Q2: VO2max-FTP Relationship

| Q | Topic | Dim | Baseline | v1 (direct) | v2 (index-first) | v1->v2 Delta |
|---|-------|-----|----------|-------------|-------------------|--------------|
| 2 | VO2max-FTP | Specificity | 4 | 4 | 4 | 0 |
| 2 | VO2max-FTP | Evidence | 3 | 5 | 5 | 0 |
| 2 | VO2max-FTP | Correctness | 4 | 5 | 5 | 0 |
| 2 | VO2max-FTP | Actionability | 3 | 4 | 4 | 0 |

**Notes:**

- Specificity: v2 adds the TTE stagnation diagnostic (60-75 min signals ceiling reached), VO2max trainability ceiling (~25%), phlebotomy study detail (WD-53 -- 40% mitochondrial density increase erased by blood removal), and cross-stimulation disappearance with training age. v1 covers the same conceptual ground with slightly different emphasis. Both provide concrete fractional utilization ranges and VO2max interval targets (105-120% FTP, 4-5 min). Equivalent.
- Evidence: v2 cites EC episodes TMT-45, TMT-60, WD-52, WD-53, WD-55, WD-61, plus TP articles by Santos, Baddick, Bobo, Johnston, and wiki page names. v1 cites a comparable set (TMT-60, WD-55, WD-61, WD-52, Baddick, Santos, Johnston). Both use evidence-type tags. Equivalent.
- Correctness: Both correctly explain the ceiling/utilization framework, cross-stimulation loss, and the diagnostic signal for when VO2max blocks are needed. v2 adds the phlebotomy study (WD-53) which is a strong, specific piece of evidence that central factors dominate VO2max. No errors in either. Both correctly note efficiency as an independent pathway. Equivalent.
- Actionability: Both provide a decision tree (stalled FTP + threshold work -> VO2max blocks). Neither provides a full training plan, which is appropriate for this explanatory question. Equivalent.

---

### Q3: 200km Fueling Plan

| Q | Topic | Dim | Baseline | v1 (direct) | v2 (index-first) | v1->v2 Delta |
|---|-------|-----|----------|-------------|-------------------|--------------|
| 3 | 200km fueling | Specificity | 5 | 5 | 5 | 0 |
| 3 | 200km fueling | Evidence | 2 | 4 | 4 | 0 |
| 3 | 200km fueling | Correctness | 4 | 5 | 5 | 0 |
| 3 | 200km fueling | Actionability | 5 | 4 | 4 | 0 |

**Notes:**

- Specificity: v2 adds the GE-based energy expenditure calculation (EE = Power x 0.8604 / GE at 23%), CHO fraction at 0.70 IF (0.65, yielding 115-128 g/hr endogenous + exogenous burn), and starting glycogen estimate (2,000-2,400 kcal). These are excellent coaching-level details. v1 already included the 1:0.8 glucose:fructose ratio, splanchnic blood flow numbers (60-80% drop), and the GE decline of ~0.5%/hr after hour 2. Both provide hour-by-hour tables with CHO/fluid/sodium targets. Equivalent at the top.
- Evidence: Both cite wiki sections (fueling-fundamentals, race-day-nutrition, ultra-nutrition), evidence tags, and researchers (Jeukendrup, Romijn, Podlogar & Wallis, King, Burke). v1 cited the same set. Equivalent.
- Correctness: Both use the updated 1:0.8 glucose:fructose ratio (Podlogar/Wallis), correctly start at 80-90 g/hr (not the baseline's conservative 60g/hr for hour 1), and include the splanchnic blood flow rationale. v2 adds the CHO fraction calculation and GE estimation, both correct. No errors in either. Equivalent.
- Actionability: v2 groups into phases (Early 0-2, Mid 2-4, Late-mid 5-6, Final 7-8) rather than v1's hour-by-hour breakdown. v1's format (individual rows for hours 1-8 with specific food combinations per hour) is marginally easier to tape to a top tube or handlebar. However, v2 includes "eat every 15-20 minutes in small doses (~22g per feed at 90g/hr)" which is a very practical execution cue. Both match v1's regression from baseline: neither matches the baseline's extreme hour-by-hour granularity with specific food combinations. Equivalent to v1.

---

### Q4: 3-Week VO2max Block

| Q | Topic | Dim | Baseline | v1 (direct) | v2 (index-first) | v1->v2 Delta |
|---|-------|-----|----------|-------------|-------------------|--------------|
| 4 | VO2max block | Specificity | 4 | 5 | 5 | 0 |
| 4 | VO2max block | Evidence | 2 | 5 | 5 | 0 |
| 4 | VO2max block | Correctness | 4 | 5 | 5 | 0 |
| 4 | VO2max block | Actionability | 4 | 5 | 5 | 0 |

**Notes:**

- Specificity: v2 provides a day-by-day weekly template, VO2max interval progression (Wk1: 4x3min, Wk2: 5x3min Tue + 4x4min Sat), rest-week volume (40-60% of normal, ~4-5 hours), IF caps (<0.50 rest week, 0.50-0.65 endurance), and gating test details (sprint + 5 min at FTP). v1 includes the same level of detail with slightly different formatting (session label table + progression + recovery week). Both exceed baseline's TSS-only approach. Equivalent.
- Evidence: v2 cites vo2max-training.md (Sections 3, 4, 7), interval-design.md (Sections 3.3, 5, 6), training-periodization.md (Section 2.2, 3.2), training-load-recovery.md (Section 4.1, 10), plus EC episodes WD-55, TMT-45, TMT-49, TMT-52, TMT-55, TMT-60, Seiler 2010, Santos/Simone (TP). v1 cites a comparable set. Both far exceed baseline's zero-citation approach. Equivalent.
- Correctness: Both correctly use 2:1 load:recovery mesocycle, limit VO2max sessions to 2/week (Seiler 2010), prescribe classic long intervals as the starting protocol, include the duration-first principle, and address fueling/glycogen requirements. v2 explicitly includes "progressive overload before protocol change" and the gating test -- both important safety details. Baseline's 30/15s short-short protocol in week 1 remains the key v1 vs baseline correctness difference, and both v1 and v2 handle this correctly. Equivalent.
- Actionability: Both are ready-to-execute. v2's gating test (Day 6-7: sprint power + 5 min at FTP; if both feel good, resume loading) and warning signs (HRV depression >7 days, failed session + failed retest 2-3 days later = immediate rest) make it slightly safer for unsupervised execution. v1 has the same elements. Equivalent.

---

### Q5: Durability

| Q | Topic | Dim | Baseline | v1 (direct) | v2 (index-first) | v1->v2 Delta |
|---|-------|-----|----------|-------------|-------------------|--------------|
| 5 | Durability | Specificity | 3 | 5 | 5 | 0 |
| 5 | Durability | Evidence | 2 | 5 | 5 | 0 |
| 5 | Durability | Correctness | 4 | 5 | 5 | 0 |
| 5 | Durability | Actionability | 3 | 4 | 4 | 0 |

**Notes:**

- Specificity: v2 provides the Neben vs Cat 3 case study (272W vs 274W fresh, 4W vs 32W drop at 2000 kJ), van Erp World Tour data (6.28 W/kg vs 5.99 W/kg, 4% vs 9% loss at 50 kJ/kg), a 4-tier benchmark table (Elite pro <2%, Strong amateur 2-10%, Good amateur 10-20%, Average amateur 20-40%), and the dual exponential decay model. v1 has the same core data points. Both far exceed baseline's single hypothetical example. Equivalent.
- Evidence: v2 cites Maunder et al. 2021, van Erp et al. 2021, Cusick case study, WD-60, TMT-70, TMT-73, wiki sections with section numbers, evidence tags. v1 has the same set. Both correct baseline's erroneous "Maarten Munten" attribution. Equivalent.
- Correctness: Both correctly attribute the formal definition to Maunder et al. (August 2021), include the "absolute power first" caveat, note confounding factors (nutrition, pre-effort intensity, missing baselines), and correctly distinguish kJ-based from time-based fatigue. v2 adds the platform warning about not showing durability in isolation (Section 16). No errors in either. Equivalent.
- Actionability: Both are primarily explanatory (appropriate for the question asked). v2 adds training implications (long rides 4-6+ hours monthly, late-ride intervals) and notes that fueling at 60-90 g/hr is the single most actionable lever for apparent durability improvement. v1 includes the WKO5 modeling framework. Equivalent.

---

## Summary Averages

| Dimension | Baseline | v1 | v2 | v1->v2 |
|-----------|----------|-----|-----|--------|
| Specificity | 4.0 | 4.8 | 4.8 | 0.0 |
| Evidence | 2.2 | 4.8 | 4.8 | 0.0 |
| Correctness | 4.0 | 5.0 | 5.0 | 0.0 |
| Actionability | 3.8 | 4.4 | 4.2 | -0.2 |
| **Overall** | **3.5** | **4.8** | **4.7** | **-0.1** |

## Token & Efficiency Comparison

| Metric | Baseline | v1 (direct) | v2 (index-first) | v2 vs v1 |
|--------|----------|-------------|-------------------|----------|
| Avg total tokens | 13,661 | 40,490 | ~35,000-38,000 (est) | ~5-10% fewer |
| Tool calls (est) | 2 | 6.2 | 4-5 (1 index + 2-3 pages) | ~20-30% fewer |
| Pages read | 0 | 3-4 (fixed) | 1 index + 2-3 selected | Similar total, but index is small |
| Output quality | 3.5 avg | 4.8 avg | 4.7 avg | -0.1 (negligible) |

v2 reads one fewer full wiki page on average (the index page is substantially smaller than a full wiki article). The efficiency gain is modest -- roughly 1 fewer tool call per question and slightly less input token consumption. For a 5-question eval this saves perhaps 10-15K tokens total.

## Key Observations

### Did the index-first approach select the right pages?

Yes, in all 5 cases. The pages selected by v2 closely match the pages v1 was hard-coded to read. For example:
- Q1: v2 selected FTP & Threshold Testing, VO2max Training, Training Periodization -- the same 3 core pages v1 read.
- Q4: v2 selected VO2max Training, Interval Design, Training Periodization, Training Load & Recovery -- matching and slightly exceeding v1's page set.
- Q5: v2 selected Durability & Fatigue, FTP & Threshold Testing, and the durability episode notes -- matching v1.

The index-first approach demonstrated reliable page selection. It did not make obviously wrong choices on any question.

### Did it miss pages that v1 read directly?

No clear misses. In Q3 (fueling), v2 selected fueling-fundamentals, race-day-nutrition, and ultra-nutrition -- the same pages v1 used. The answers show equivalent coverage of the source material.

One possible minor difference: v2 occasionally cites sources that suggest it may have read slightly different wiki sections than v1 (e.g., v2's Q5 cites Section 16 of durability-fatigue wiki, which v1 also cited but with different emphasis). These differences appear to be in answer construction, not page selection.

### Quality vs efficiency tradeoff

The tradeoff is minimal. v2 achieves 98% of v1's quality (4.7 vs 4.8 overall average) while reading slightly fewer total tokens. The single dimension where v2 slightly underperforms is actionability on Q1 (-1), where v1's more structured tabular format edges ahead. This is an answer formatting difference, not a knowledge retrieval difference.

The efficiency gain of index-first retrieval is real but small for a 20-page wiki. The approach would likely show larger gains as the knowledge base grows: with 100+ pages, hard-coding 3-4 pages per question becomes fragile, while index-first selection scales naturally.

### Any regressions from v1?

One minor regression: Q1 actionability dropped from 5 to 4. The v2 answer is slightly less structured as an execution plan -- it reads more as an explanation with embedded prescriptions rather than a step-by-step protocol. The v1 answer's week-by-week progression table with exact rest-week IF thresholds was marginally more ready to execute directly.

No regressions on evidence, correctness, or specificity for any question. The -0.1 overall average difference is within scoring noise.

### Overall verdict

v2 (index-first) matches v1 (direct) on answer quality across all meaningful dimensions. The approach successfully selects relevant pages from the index without human curation. The small efficiency gain in token consumption is a bonus. The real value of index-first retrieval is scalability: as the wiki grows, the index approach will maintain selection quality while hard-coded page lists will require constant maintenance.

For this 5-question eval on a 20-page wiki, the two approaches are effectively equivalent. The recommendation is to adopt index-first as the default retrieval strategy for its scaling properties, not for its current quality advantage (which is negligible).
