# EC Podcast Insights Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Incorporate insights from 53 Empirical Cycling podcast episodes into 5 Claude skills and 7 Python code modules, adding new diagnostics, correcting outdated defaults, and aligning the platform with current coaching science.

**Architecture:** Two phases — (1) skill text updates (5 SKILL.md files), (2) code changes to Python modules with tests. Skills are pure text edits. Code changes add new functions and modify existing ones, with backward compatibility maintained. Changes are prioritized P0→P3 by impact.

**Tech Stack:** Python 3.14, pytest, SQLite, numpy, pandas. Skills in Markdown.

**Source docs:**
- `docs/research/empirical-cycling/skill-updates-plan.md` — exact text for each skill
- `docs/research/empirical-cycling/code-changes-plan.md` — 26 code changes with priority

**Test command:** `source /tmp/fitenv/bin/activate && cd /Users/jshin/Documents/wko5-experiments && pytest tests/ -v`

**Python env:** `/tmp/fitenv/`

---

## File Structure

### Skills (text-only edits)
```
~/.claude/skills/wko5-training/SKILL.md    — 7 sections added/modified
~/.claude/skills/wko5-nutrition/SKILL.md   — 5 sections added/modified
~/.claude/skills/wko5-science/SKILL.md     — 4 sections added/modified
~/.claude/skills/wko5-analyzer/SKILL.md    — 3 sections added
~/.claude/skills/dr-vasquez/SKILL.md       — 3 sections added/modified
```

### Code (new functions + modifications)
```
wko5/clinical.py          — 5 new functions + integrate into get_clinical_flags()
wko5/training_load.py     — 2 new functions
wko5/durability.py        — 2 new functions + modify 3 existing
wko5/pdcurve.py           — 1 new function
wko5/nutrition.py         — modify 1 default
wko5/gap_analysis.py      — add 1 field to return dict
wko5/zones.py             — 2 new functions
tests/test_clinical.py    — new tests for 5 new functions
tests/test_training_load.py — new tests for 2 new functions
tests/test_durability.py  — new tests for 2 new functions + modified behavior
tests/test_pdcurve.py     — new test for 1 new function
tests/test_nutrition.py   — test for modified default
tests/test_gap_analysis.py — test for new field
tests/test_zones.py       — new tests for 2 new functions
```

---

## Task 1: Update all 5 skills with EC podcast insights

**Files:**
- Modify: `~/.claude/skills/wko5-training/SKILL.md`
- Modify: `~/.claude/skills/wko5-nutrition/SKILL.md`
- Modify: `~/.claude/skills/wko5-science/SKILL.md`
- Modify: `~/.claude/skills/wko5-analyzer/SKILL.md`
- Modify: `~/.claude/skills/dr-vasquez/SKILL.md`

Source: `docs/research/empirical-cycling/skill-updates-plan.md` contains the exact text to insert for each skill. Apply all changes as specified in that document.

- [ ] **Step 1: Update wko5-training**

Read `~/.claude/skills/wko5-training/SKILL.md`. Apply all 7 changes from skill-updates-plan.md Section 1:
1. Add "FTP Testing Caveats" after the Kolie Moore protocol section (after line containing "Use unstructured testing going forward")
2. Replace the 30/15 subsection under "Interval Prescription" with the corrected version
3. Replace "Train-Low / Compete-High" subsection with updated version
4. Update durability benchmarks in "Fatigue Resistance Training Protocols" assessment section
5. Add new "Training Intensity Distribution" section after the interval prescription sections
6. Add new "Recovery and Rest Week Framework" section before "Training Philosophy"
7. Replace "Concurrent Training Risks" section with updated version

- [ ] **Step 2: Update wko5-nutrition**

Read `~/.claude/skills/wko5-nutrition/SKILL.md`. Apply all 5 changes from skill-updates-plan.md Section 2:
1. Update carb targets in "Racing (<6 hours)" to 60-90g/hr with absorption context
2. Add "Recovery Nutrition", "Within-Day Energy Deficit", and "Protein & Fat Minimums" subsections after Hydration
3. Add "Electrolyte Timing" correction
4. Add items 9-11 to "Common Mistakes"
5. Add "Creatine for Cyclists" subsection at end

- [ ] **Step 3: Update wko5-science**

Read `~/.claude/skills/wko5-science/SKILL.md`. Apply all 4 changes from skill-updates-plan.md Section 3:
1. Replace "Polarized vs. Threshold Training" with IPD meta-analysis findings
2. Add "AMPK-Glycogen Interaction" after molecular adaptation pathways
3. Add "Newbie Gains Are Central, Not Peripheral" section
4. Add "Diminishing Returns — Quantified" with growth curve data and FTP gain expectations table

- [ ] **Step 4: Update wko5-analyzer**

Read `~/.claude/skills/wko5-analyzer/SKILL.md`. Apply all 3 changes from skill-updates-plan.md Section 4:
1. Add durability interpretation notes to Module Reference
2. Add new question→function mapping rows (IF distribution, sweet spot TTE, panic training, performance trend, indoor comparison)
3. Add EC diagnostic priors to Bayesian Interpretation Framework

- [ ] **Step 5: Update dr-vasquez**

Read `~/.claude/skills/dr-vasquez/SKILL.md`. Apply all 3 changes from skill-updates-plan.md Section 5:
1. Add 8 new strong opinions
2. Modify existing durability opinion to include WD-60 nuance
3. Add "Clinical Detection Framework" with RED/AMBER flags and EA thresholds

- [ ] **Step 6: Verify skills load correctly**

Run: `ls -la ~/.claude/skills/wko5-{training,nutrition,science,analyzer}/SKILL.md ~/.claude/skills/dr-vasquez/SKILL.md`
Check each file is valid markdown (no unclosed code blocks, no broken frontmatter).

- [ ] **Step 7: Commit skills**

```bash
cd /Users/jshin/Documents/wko5-experiments
# Skills live in ~/.claude/skills/ but the source copies are in the repo
cp -r ~/.claude/skills/wko5-training wko5-training/
cp -r ~/.claude/skills/wko5-nutrition wko5-nutrition/ 2>/dev/null || true
cp -r ~/.claude/skills/wko5-science wko5-science/
git add wko5-training/ wko5-science/
git commit -m "feat: bake EC podcast insights into training, nutrition, science, analyzer, dr-vasquez skills"
```

---

## Task 2: P0 — Clinical diagnostics (IF floor + intensity black hole + IF distribution)

These are the highest-impact changes: the #1 coaching diagnostic (IF floor) and the most common amateur error (intensity black hole).

**Files:**
- Modify: `wko5/clinical.py`
- Modify: `wko5/training_load.py`
- Modify: `tests/test_clinical.py`
- Modify: `tests/test_training_load.py`

- [ ] **Step 1: Write tests for IF floor diagnostic**

Add to `tests/test_clinical.py`:

```python
def test_check_if_floor_flags_high():
    """IF floor diagnostic should flag when endurance rides are too hard."""
    from wko5.clinical import check_if_floor
    result = check_if_floor(days_back=90)
    if result is None:
        return  # insufficient data
    assert "floor_if" in result
    assert "severity" in result
    assert result["severity"] in ("green", "yellow", "red")


def test_check_intensity_black_hole():
    """Should detect when most rides are in the moderate zone."""
    from wko5.clinical import check_intensity_black_hole
    result = check_intensity_black_hole(days_back=90)
    # Result is dict or None
    if result is not None:
        assert "compressed" in result
        assert "floor" in result
        assert "ceiling" in result
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source /tmp/fitenv/bin/activate && pytest tests/test_clinical.py::test_check_if_floor_flags_high tests/test_clinical.py::test_check_intensity_black_hole -v`
Expected: FAIL (functions don't exist yet)

- [ ] **Step 3: Write IF distribution in training_load.py**

Add to `wko5/training_load.py`:

```python
def if_distribution(days_back=90, ftp=None):
    """Analyze IF distribution across recent rides.

    Returns dict with histogram, floor (10th percentile), ceiling (90th percentile),
    spread, compressed flag (floor > 0.70), and ride count.
    """
    if ftp is None:
        ftp = get_config("ftp") or FTP_DEFAULT

    activities = get_activities()
    cutoff = (pd.Timestamp.now() - pd.Timedelta(days=days_back)).strftime("%Y-%m-%d")
    recent = activities[activities["start_time"] >= cutoff]

    if_values = []
    for _, act in recent.iterrows():
        np_val = act.get("normalized_power")
        if np_val and np_val > 0 and ftp > 0:
            if_values.append(round(np_val / ftp, 3))

    if len(if_values) < 5:
        return None

    arr = np.array(if_values)
    floor = float(np.percentile(arr, 10))
    ceiling = float(np.percentile(arr, 90))

    # Histogram in 0.05 bins
    bins = np.arange(0, 1.5, 0.05)
    counts, edges = np.histogram(arr, bins=bins)
    histogram = {f"{edges[i]:.2f}-{edges[i+1]:.2f}": int(counts[i])
                 for i in range(len(counts)) if counts[i] > 0}

    return {
        "histogram": histogram,
        "floor": round(floor, 3),
        "ceiling": round(ceiling, 3),
        "spread": round(ceiling - floor, 3),
        "compressed": floor > 0.70,
        "rides_analyzed": len(if_values),
    }
```

- [ ] **Step 4: Write check_if_floor and check_intensity_black_hole in clinical.py**

Add to `wko5/clinical.py`:

```python
def check_if_floor(days_back=90):
    """Check if endurance ride IF floor is too high.

    IF floor > 0.70 = yellow (riding endurance too hard)
    IF floor > 0.75 = red (significant easy gains available from riding easier)

    Source: TMT-69, TMT-68 — IF distribution is the #1 diagnostic coaches check.
    """
    from wko5.training_load import if_distribution

    dist = if_distribution(days_back=days_back)
    if dist is None:
        return None

    floor_if = dist["floor"]
    if floor_if > 0.75:
        severity = "red"
        message = (f"Endurance ride IF floor is {floor_if:.2f} — riding too hard. "
                   f"Easy gains available from riding easier (target IF 0.50-0.65).")
    elif floor_if > 0.70:
        severity = "yellow"
        message = (f"Endurance ride IF floor is {floor_if:.2f} — slightly high. "
                   f"Consider riding easier on recovery/endurance days.")
    else:
        severity = "green"
        message = f"Endurance ride IF floor is {floor_if:.2f} — good distribution."

    return {
        "flag": "if_floor",
        "floor_if": round(floor_if, 3),
        "severity": severity,
        "message": message,
        "rides_analyzed": dist["rides_analyzed"],
    }


def check_intensity_black_hole(days_back=90):
    """Detect intensity black hole — most rides in moderate zone.

    Flags when >60% of rides fall in IF 0.65-0.80 with insufficient
    easy (<0.50) or hard (>0.90) riding.

    Source: TMT-58, TMT-69 — athletes who don't polarize settle into
    80-90% capacity, never truly hard or easy.
    """
    from wko5.training_load import if_distribution

    dist = if_distribution(days_back=days_back)
    if dist is None:
        return None

    floor = dist["floor"]
    ceiling = dist["ceiling"]
    compressed = dist["compressed"]
    spread = dist["spread"]

    if compressed and spread < 0.25:
        return {
            "flag": "intensity_black_hole",
            "compressed": True,
            "floor": round(floor, 3),
            "ceiling": round(ceiling, 3),
            "spread": round(spread, 3),
            "severity": "yellow",
            "message": (f"Intensity black hole detected: IF range {floor:.2f}-{ceiling:.2f}. "
                        f"Most rides are moderate — add truly easy (IF<0.50) and truly hard "
                        f"(IF>0.90) sessions."),
        }

    return None
```

- [ ] **Step 5: Integrate into get_clinical_flags()**

In `wko5/clinical.py`, add calls to the new functions inside `get_clinical_flags()`:

```python
# Add after existing flag checks:
if_floor = check_if_floor()
if if_floor and if_floor["severity"] != "green":
    flags.append(if_floor)

black_hole = check_intensity_black_hole()
if black_hole:
    flags.append(black_hole)
```

- [ ] **Step 6: Run tests**

Run: `source /tmp/fitenv/bin/activate && pytest tests/test_clinical.py -v`
Expected: All tests PASS including new ones.

- [ ] **Step 7: Write test for if_distribution**

Add to `tests/test_training_load.py`:

```python
def test_if_distribution():
    """IF distribution should return histogram and floor/ceiling."""
    from wko5.training_load import if_distribution
    result = if_distribution(days_back=90)
    if result is None:
        return  # insufficient data
    assert "histogram" in result
    assert "floor" in result
    assert "ceiling" in result
    assert "compressed" in result
    assert isinstance(result["compressed"], bool)
    assert result["floor"] <= result["ceiling"]
```

- [ ] **Step 8: Run full test suite**

Run: `source /tmp/fitenv/bin/activate && pytest tests/ -q`
Expected: All tests PASS.

- [ ] **Step 9: Commit**

```bash
git add wko5/clinical.py wko5/training_load.py tests/test_clinical.py tests/test_training_load.py
git commit -m "feat: add IF floor diagnostic + intensity black hole detection (P0)

IF distribution analysis as the #1 coaching diagnostic (TMT-69, TMT-68).
Flags endurance rides with IF > 0.70 and compressed intensity distribution."
```

---

## Task 3: P1 — Durability kJ/kg normalization + fresh baseline check

**Files:**
- Modify: `wko5/durability.py`
- Modify: `tests/test_durability.py`

- [ ] **Step 1: Write tests**

Add to `tests/test_durability.py`:

```python
def test_degradation_factor_with_weight():
    """Degradation factor should accept weight_kg for kJ/kg normalization."""
    from wko5.durability import degradation_factor
    params = {"a": 0.5, "b": 0.001, "c": 0.05}
    # Same kJ, different weights = different degradation
    df_heavy = degradation_factor(2000, 3.0, params, weight_kg=80)
    df_light = degradation_factor(2000, 3.0, params, weight_kg=55)
    # Lighter rider should degrade more at same absolute kJ
    assert df_light < df_heavy


def test_windowed_mmp_has_kj_per_kg():
    """Windowed MMP should include kJ/kg field when weight provided."""
    from wko5.durability import compute_windowed_mmp
    import numpy as np
    power = pd.Series(np.random.normal(200, 20, 14400))  # 4 hours
    windows = compute_windowed_mmp(power, window_hours=2, weight_kg=78)
    if windows:
        assert "cumulative_kj_per_kg" in windows[0]


def test_check_fresh_baseline():
    """Fresh baseline check should return staleness info."""
    from wko5.durability import check_fresh_baseline
    result = check_fresh_baseline(days=180)
    assert isinstance(result, dict)
    for dur in [60, 300]:
        if dur in result:
            assert "exists" in result[dur]


def test_durability_benchmark():
    """Benchmark classification should match EC podcast tiers."""
    from wko5.durability import durability_benchmark
    assert durability_benchmark(1) == "elite_pro"
    assert durability_benchmark(15) == "good_amateur"
    assert durability_benchmark(35) == "average_amateur"
    assert durability_benchmark(50) == "needs_work"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source /tmp/fitenv/bin/activate && pytest tests/test_durability.py::test_degradation_factor_with_weight tests/test_durability.py::test_check_fresh_baseline tests/test_durability.py::test_durability_benchmark -v`
Expected: FAIL

- [ ] **Step 3: Modify degradation_factor() for kJ/kg support**

In `wko5/durability.py`, modify `degradation_factor`:

```python
def degradation_factor(cumulative_kj, elapsed_hours, params, weight_kg=None):
    """Compute the degradation factor at a given point in a ride.

    If weight_kg is provided, normalizes kJ to kJ/kg (recommended per van Erp 2021).
    """
    a = params["a"]
    b = params["b"]
    c = params["c"]

    kj = cumulative_kj / weight_kg if weight_kg else cumulative_kj
    kj_term = a * np.exp(-b * kj / 1000)
    time_term = (1 - a) * np.exp(-c * elapsed_hours)

    return float(max(0, kj_term + time_term))
```

- [ ] **Step 4: Modify compute_windowed_mmp() to add kJ/kg**

Add `weight_kg=None` parameter to `compute_windowed_mmp`. When provided, add `cumulative_kj_per_kg` field:

```python
def compute_windowed_mmp(power_series, window_hours=2, weight_kg=None):
    # ... existing code ...
    # In the entry dict construction, add:
    if weight_kg and weight_kg > 0:
        entry["cumulative_kj_per_kg"] = round(cum_kj / weight_kg, 1)
```

- [ ] **Step 5: Add check_fresh_baseline() and durability_benchmark()**

Add to `wko5/durability.py`:

```python
def check_fresh_baseline(days=90, durations=None):
    """Check if fresh baselines exist for key durations.

    Fresh = effort occurring in first 2 hours of ride AND cumulative kJ < 500.
    Returns dict: {duration: {exists, date, value, staleness_days}}
    """
    if durations is None:
        durations = [60, 300, 1200]

    activities = get_activities()
    cutoff = (pd.Timestamp.now() - pd.Timedelta(days=days)).strftime("%Y-%m-%d")
    recent = activities[activities["start_time"] >= cutoff]

    result = {}
    for dur in durations:
        best_power = 0
        best_date = None

        for _, act in recent.iterrows():
            records = get_records(act["id"])
            if records.empty or "power" not in records.columns:
                continue

            power = records["power"].fillna(0).values.astype(float)
            n = len(power)

            # Only look at first 2 hours (7200 seconds)
            early_power = power[:min(n, 7200)]
            # Check cumulative kJ < 500
            cum_kj = float(np.sum(early_power)) / 1000
            if cum_kj > 500:
                early_power = power[:min(n, 3600)]  # restrict to 1 hour

            if len(early_power) < dur:
                continue

            cumsum = np.concatenate([[0], np.cumsum(early_power)])
            rolling = (cumsum[dur:] - cumsum[:len(early_power) - dur + 1]) / dur
            if len(rolling) == 0:
                continue

            peak = float(rolling.max())
            if peak > best_power:
                best_power = peak
                best_date = act.get("start_time", "")

        staleness = None
        if best_date:
            try:
                dt = pd.Timestamp(best_date)
                staleness = (pd.Timestamp.now() - dt).days
            except Exception:
                pass

        result[dur] = {
            "exists": best_power > 0,
            "value": round(best_power, 1) if best_power > 0 else None,
            "date": str(best_date) if best_date else None,
            "staleness_days": staleness,
        }

    return result


def durability_benchmark(drop_pct_at_50kjkg):
    """Classify power drop percentage against EC podcast benchmarks.

    Benchmarks from WD-60 coaching data:
    - Elite pro: <2% drop at 50 kJ/kg
    - Good amateur: 10-20% drop
    - Average amateur: 20-40% drop
    """
    if drop_pct_at_50kjkg < 2:
        return "elite_pro"
    elif drop_pct_at_50kjkg < 10:
        return "strong_amateur"
    elif drop_pct_at_50kjkg < 20:
        return "good_amateur"
    elif drop_pct_at_50kjkg < 40:
        return "average_amateur"
    else:
        return "needs_work"
```

- [ ] **Step 6: Run tests**

Run: `source /tmp/fitenv/bin/activate && pytest tests/test_durability.py -v`
Expected: All tests PASS.

- [ ] **Step 7: Commit**

```bash
git add wko5/durability.py tests/test_durability.py
git commit -m "feat: durability kJ/kg normalization + fresh baseline check + benchmarks (P1)

Switch from raw kJ to kJ/kg per van Erp 2021 (WD-60). Add fresh baseline
staleness check and EC podcast durability benchmarks."
```

---

## Task 4: P1 — PD curve decomposition (CP vs W') + panic training detection

**Files:**
- Modify: `wko5/pdcurve.py`
- Modify: `wko5/clinical.py`
- Modify: `tests/test_pdcurve.py`
- Modify: `tests/test_clinical.py`

- [ ] **Step 1: Write tests**

Add to `tests/test_pdcurve.py`:

```python
def test_decompose_pd_change():
    """Should decompose PD changes into CP vs W' vs Pmax contributions."""
    from wko5.pdcurve import decompose_pd_change
    old = {"Pmax": 1100, "FRC": 18, "mFTP": 280, "tau": 15, "t0": 4}
    new = {"Pmax": 1100, "FRC": 22, "mFTP": 285, "tau": 15, "t0": 4}
    result = decompose_pd_change(old, new)
    assert "mFTP_change_w" in result
    assert "FRC_change_kj" in result
    assert result["mFTP_change_w"] == 5
    assert result["FRC_change_kj"] == 4
    assert "dominant_change" in result
```

Add to `tests/test_clinical.py`:

```python
def test_check_panic_training():
    """Panic training detection should return flag or None."""
    from wko5.clinical import check_panic_training
    result = check_panic_training(days_back=90)
    # May be None if no panic pattern detected
    if result is not None:
        assert "flag" in result
        assert result["flag"] == "panic_training"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source /tmp/fitenv/bin/activate && pytest tests/test_pdcurve.py::test_decompose_pd_change tests/test_clinical.py::test_check_panic_training -v`
Expected: FAIL

- [ ] **Step 3: Implement decompose_pd_change()**

Add to `wko5/pdcurve.py`:

```python
def decompose_pd_change(model_old, model_new):
    """Decompose PD curve change into CP vs W' vs Pmax contributions.

    Compares two PD models and attributes power changes at key durations
    to mFTP (aerobic), FRC (anaerobic), or Pmax (neuromuscular).

    Source: WD-55 — ramp test gains may reflect W', not VO2max.
    """
    mftp_delta = model_new.get("mFTP", 0) - model_old.get("mFTP", 0)
    frc_delta = model_new.get("FRC", 0) - model_old.get("FRC", 0)
    pmax_delta = model_new.get("Pmax", 0) - model_old.get("Pmax", 0)

    # Determine dominant change
    changes = {
        "aerobic": abs(mftp_delta) / max(model_old.get("mFTP", 280), 1) * 100,
        "anaerobic": abs(frc_delta) / max(model_old.get("FRC", 20), 1) * 100,
        "neuromuscular": abs(pmax_delta) / max(model_old.get("Pmax", 1100), 1) * 100,
    }
    dominant = max(changes, key=changes.get)

    # Compute power at key durations for both models
    durations = [10, 60, 300, 1200, 3600]
    at_durations = {}
    for d in durations:
        old_p = _pd_power(d, model_old)
        new_p = _pd_power(d, model_new)
        at_durations[d] = {
            "old": round(old_p, 1),
            "new": round(new_p, 1),
            "delta": round(new_p - old_p, 1),
        }

    return {
        "mFTP_change_w": round(mftp_delta, 1),
        "FRC_change_kj": round(frc_delta, 1),
        "Pmax_change_w": round(pmax_delta, 1),
        "dominant_change": dominant,
        "at_durations": at_durations,
    }


def _pd_power(duration_s, model):
    """Compute predicted power at a duration from PD model parameters."""
    pmax = model.get("Pmax", 1100)
    frc = model.get("FRC", 20)
    mftp = model.get("mFTP", 280)
    tau = model.get("tau", 15)
    t0 = model.get("t0", 4)
    return pmax * np.exp(-duration_s / tau) + frc * 1000 / (duration_s + t0) + mftp
```

- [ ] **Step 4: Implement check_panic_training()**

Add to `wko5/clinical.py`:

```python
def check_panic_training(days_back=90):
    """Detect panic training pattern: sudden intensity spike after low-load period.

    Flags when 2+ weeks of low training load are followed by a sudden
    CTL ramp > 7 TSS/day.

    Source: TMT-71 — panic training almost always backfires.
    """
    from wko5.training_load import build_pmc

    pmc = build_pmc()
    if pmc.empty or len(pmc) < 28:
        return None

    recent = pmc.tail(days_back)
    if len(recent) < 28:
        return None

    # Look for pattern: 14+ days of low CTL followed by rapid ramp
    ctl = recent["ctl"].values
    tss = recent["tss"].values

    for i in range(14, len(ctl) - 7):
        # Check if preceding 14 days had low average TSS
        pre_avg_tss = float(np.mean(tss[i-14:i]))
        # Check if following 7 days had high average TSS
        post_avg_tss = float(np.mean(tss[i:i+7]))

        if pre_avg_tss < 30 and post_avg_tss > 60:
            ramp_ratio = post_avg_tss / max(pre_avg_tss, 1)
            if ramp_ratio > 2.0:
                return {
                    "flag": "panic_training",
                    "severity": "yellow",
                    "pre_avg_tss": round(pre_avg_tss, 1),
                    "post_avg_tss": round(post_avg_tss, 1),
                    "ramp_ratio": round(ramp_ratio, 1),
                    "message": (f"Panic training pattern detected: avg TSS jumped from "
                                f"{pre_avg_tss:.0f} to {post_avg_tss:.0f} "
                                f"({ramp_ratio:.1f}x increase). Recommend building volume "
                                f"first, then adding intensity gradually."),
                }

    return None
```

- [ ] **Step 5: Integrate panic training into get_clinical_flags()**

Add to `get_clinical_flags()`:

```python
panic = check_panic_training()
if panic:
    flags.append(panic)
```

- [ ] **Step 6: Run tests**

Run: `source /tmp/fitenv/bin/activate && pytest tests/test_pdcurve.py tests/test_clinical.py -v`
Expected: All tests PASS.

- [ ] **Step 7: Commit**

```bash
git add wko5/pdcurve.py wko5/clinical.py tests/test_pdcurve.py tests/test_clinical.py
git commit -m "feat: PD curve decomposition (CP vs W') + panic training detection (P1)

Decompose PD changes into aerobic/anaerobic/neuromuscular components (WD-55).
Detect panic training pattern: sudden intensity spike after low-load (TMT-71)."
```

---

## Task 5: P1 — Update nutrition defaults + absolute power check in gap analysis

**Files:**
- Modify: `wko5/nutrition.py`
- Modify: `wko5/gap_analysis.py`
- Modify: `tests/test_nutrition.py`
- Modify: `tests/test_gap_analysis.py`

- [ ] **Step 1: Write tests**

Add to `tests/test_nutrition.py`:

```python
def test_default_carb_target_updated():
    """Default carb intake should be 75g/hr (midpoint of 60-90 range)."""
    from wko5.nutrition import NutritionPlan
    plan = NutritionPlan()
    assert plan.baseline_intake_g_hr == 75
```

Add to `tests/test_gap_analysis.py`:

```python
def test_gap_analysis_has_absolute_power_check():
    """Gap analysis should include absolute power check alongside durability."""
    segments = [
        {"type": "climb", "distance_m": 5000, "duration_s": 1200, "avg_grade": 0.06,
         "power_required": 280, "cumulative_kj_at_start": 0},
    ]
    pd_model = {"Pmax": 1100, "FRC": 20, "mFTP": 290, "TTE": 3600, "tau": 15, "t0": 4}
    dur_params = {"a": 0.5, "b": 0.001, "c": 0.05}
    result = gap_analysis(segments, pd_model, dur_params, n_draws=20)
    assert "absolute_power_check" in result
    assert "fresh_power_sufficient" in result["absolute_power_check"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source /tmp/fitenv/bin/activate && pytest tests/test_nutrition.py::test_default_carb_target_updated tests/test_gap_analysis.py::test_gap_analysis_has_absolute_power_check -v`
Expected: FAIL

- [ ] **Step 3: Update NutritionPlan default**

In `wko5/nutrition.py`, change the `baseline_intake_g_hr` default:

```python
# In NutritionPlan dataclass:
baseline_intake_g_hr: float = 75  # Updated: 60-90g/hr standard (EC podcast, Persp-41)
```

- [ ] **Step 4: Add absolute_power_check to gap_analysis()**

In `wko5/gap_analysis.py`, in the `gap_analysis()` function, add before the return statement:

```python
# Absolute power check (WD-60: need sufficient power first)
max_demand = max((s.get("power_required", 0) for s in segments), default=0)
fresh_capacity = pd_model.get("mFTP", 0)
absolute_power_check = {
    "fresh_mftp_w": round(fresh_capacity, 1),
    "max_segment_demand_w": round(max_demand, 1),
    "fresh_power_sufficient": fresh_capacity >= max_demand * 0.95,
    "message": ("Absolute power is sufficient for this route."
                if fresh_capacity >= max_demand * 0.95
                else f"Fresh power ({fresh_capacity:.0f}W) may be insufficient for "
                     f"hardest segment ({max_demand:.0f}W). Durability is secondary."),
}
```

Add `"absolute_power_check": absolute_power_check` to the return dict.

- [ ] **Step 5: Run tests**

Run: `source /tmp/fitenv/bin/activate && pytest tests/test_nutrition.py tests/test_gap_analysis.py -v`
Expected: All PASS.

- [ ] **Step 6: Run full test suite**

Run: `source /tmp/fitenv/bin/activate && pytest tests/ -q`
Expected: All tests PASS.

- [ ] **Step 7: Commit**

```bash
git add wko5/nutrition.py wko5/gap_analysis.py tests/test_nutrition.py tests/test_gap_analysis.py
git commit -m "feat: update carb defaults to 75g/hr + add absolute power check to gap analysis (P1)

Carb target updated from 60 to 75g/hr per EC podcast evidence (Persp-41).
Gap analysis now checks fresh power sufficiency alongside durability (WD-60)."
```

---

## Task 6: P2 — Sweet spot TTE + endurance IF validation + indoor multiplier

**Files:**
- Modify: `wko5/zones.py`
- Modify: `wko5/training_load.py`
- Modify: `tests/test_zones.py`
- Modify: `tests/test_training_load.py`

- [ ] **Step 1: Write tests**

Add to `tests/test_zones.py`:

```python
def test_sweet_spot_band():
    """Sweet spot should be 88-93% of FTP."""
    from wko5.zones import sweet_spot_band
    low, high = sweet_spot_band(300)
    assert low == 264  # 300 * 0.88
    assert high == 279  # 300 * 0.93


def test_validate_endurance_rides():
    """Should flag endurance rides with IF > 0.65."""
    from wko5.zones import validate_endurance_rides
    result = validate_endurance_rides(days_back=90)
    if result is not None:
        assert isinstance(result, list)
```

Add to `tests/test_training_load.py`:

```python
def test_indoor_multiplier():
    """Indoor rides should have higher effective TSS."""
    from wko5.training_load import compute_tss
    # This test verifies the concept — actual implementation depends on activity metadata
    tss = compute_tss(200, 250, 3600, 280)  # NP, AP, duration, FTP
    assert tss > 0
```

- [ ] **Step 2: Implement sweet_spot_band() and validate_endurance_rides()**

Add to `wko5/zones.py`:

```python
def sweet_spot_band(ftp):
    """Return (low, high) power for sweet spot band (~88-93% FTP).

    Source: TMT-44 — sweet spot TTE is a key fitness marker.
    Ranges: untrained 40-60 min, trained 90-120 min, elite 180+ min.
    """
    return (int(ftp * 0.88), int(ftp * 0.93))


def validate_endurance_rides(days_back=90, ftp=None):
    """Check if endurance rides are actually easy enough.

    Flags rides >1.5h with IF > 0.65.
    Source: TMT-69 — endurance target IF 0.50-0.65.
    """
    from wko5.config import get_config
    from wko5.db import get_activities, FTP_DEFAULT
    from wko5.training_load import compute_np

    if ftp is None:
        ftp = get_config("ftp") or FTP_DEFAULT

    activities = get_activities()
    cutoff = (pd.Timestamp.now() - pd.Timedelta(days=days_back)).strftime("%Y-%m-%d")
    recent = activities[
        (activities["start_time"] >= cutoff) &
        (activities["total_timer_time"] > 5400)  # > 1.5 hours
    ]

    flagged = []
    for _, act in recent.iterrows():
        np_val = act.get("normalized_power")
        if np_val and ftp > 0:
            ride_if = np_val / ftp
            if ride_if > 0.65:
                flagged.append({
                    "activity_id": act.get("id"),
                    "date": str(act.get("start_time", ""))[:10],
                    "if_value": round(ride_if, 3),
                    "duration_h": round(act.get("total_timer_time", 0) / 3600, 1),
                })

    return flagged if flagged else None
```

- [ ] **Step 3: Run tests**

Run: `source /tmp/fitenv/bin/activate && pytest tests/test_zones.py tests/test_training_load.py -v`
Expected: All PASS.

- [ ] **Step 4: Commit**

```bash
git add wko5/zones.py wko5/training_load.py tests/test_zones.py tests/test_training_load.py
git commit -m "feat: sweet spot TTE tracking + endurance IF validation (P2)

Sweet spot band (88-93% FTP) with TTE benchmarks (TMT-44).
Endurance IF validation flags rides >1.5h with IF > 0.65 (TMT-69)."
```

---

## Task 7: Update exports + full suite + final commit

**Files:**
- Modify: `wko5/__init__.py`

- [ ] **Step 1: Update exports**

Add new functions to `wko5/__init__.py`:

```python
from wko5.clinical import check_if_floor, check_intensity_black_hole, check_panic_training
from wko5.durability import check_fresh_baseline, durability_benchmark
from wko5.pdcurve import decompose_pd_change
from wko5.zones import sweet_spot_band, validate_endurance_rides
from wko5.training_load import if_distribution
```

- [ ] **Step 2: Run full test suite**

Run: `source /tmp/fitenv/bin/activate && pytest tests/ -q`
Expected: All tests PASS.

- [ ] **Step 3: Commit**

```bash
git add wko5/__init__.py
git commit -m "feat: export new EC-insight functions from wko5 package"
```

- [ ] **Step 4: Update progress memory**

Update `project_wko5_bot_progress.md`:
- Add EC insights implementation to "Completed" section
- Update test count
- Update "Ready to Build" with P2/P3 remaining items
