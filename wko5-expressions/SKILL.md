---
name: wko5-expressions
description: WKO5 expression language reference — syntax, functions, operators, variables, and chart-building patterns. Use whenever the user mentions WKO5 expressions, asks to write/debug/explain a WKO expression, pastes an expression containing WKO5 functions like meanmax(), ftp(), bin(), tl(), pdcurve(), athleterange(), or similar, or wants to build custom WKO5 charts. Also trigger for questions about WKO5 data types, operators, or available functions.
---

# WKO5 Expression Language Reference

WKO5 is a cycling and endurance sports analytics platform by TrainingPeaks. Its core power is a custom expression language for building charts, filtering data, and modeling physiology from workout files.

## Two levels of data

1. **Athlete level** — one value per workout (e.g., `tss`, `distance`, `date`, `if`, `weight`). Used in trend charts.
2. **Workout level** — one value per second (time-series channels: `power`, `heartrate`, `cadence`, `speed`, `elevation`). Used for within-ride analysis.

Expressions compose via nesting: `ftp(meanmax(power))` builds a mean-max power curve, then extracts modeled FTP.

## Operators

| Operator | Meaning |
|----------|---------|
| `+` `-` `*` `/` `^` | Arithmetic (^ = exponent) |
| `>` `<` `>=` `<=` `==` `!=` | Comparison |
| `and` / `&&` | Logical AND |
| `or` / `||` | Logical OR |

## Data types

- **Numbers**: `42`, `3.14`, scientific notation
- **Strings**: `"quoted text"`
- **Pairs**: `(X, Y)` for scatter/curve data
- **Sets**: `{1, 2, 3}` — curly braces
- **Ranges**: `{2015:2017}` generates `{2015, 2016, 2017}`
- **na**: missing/invalid value (distinct from zero)
- **Constants**: `pi`, `e`

## Indexing

- `power[0]` — first value
- `heartrate[-1]` — last value (negative indexing from end)

## Key abbreviations

- **mFTP** — Modeled Functional Threshold Power (from the PD model, vs. manually set FTP)
- **FRC** — Functional Reserve Capacity (anaerobic energy above FTP, in kJ)
- **Pmax** — Maximum instantaneous power (neuromuscular)
- **TTE** — Time to Exhaustion at FTP
- **mVO2max** — Modeled VO2max (L/min)
- **MMP** — Mean Max Power (the raw curve before modeling)
- **PDM** — Power Duration Model
- **CTL** — Chronic Training Load ("fitness")
- **ATL** — Acute Training Load ("fatigue")
- **TSB** — Training Stress Balance ("form") = CTL - ATL
- **TSS** — Training Stress Score (per-workout stress)
- **iLevels** — Individualized training levels (auto-updating zones)
- **WACK** — Percentile ranking vs. global database

## Common expression patterns

```
# Modeled FTP from all data in range
ftp(meanmax(power))

# Daily rolling FTP over 90-day windows
ftp(meanmax(power), 90)

# Average power excluding zeros
avg(nozero(power))

# Time in zone histogram (individualized)
bin(power, "ilevels")

# Filter workouts by tag
if(hastag("race"), tss)

# Filter workouts by title keyword
if(has(title, "interval"), avg(power))

# Conditional: past vs planned
if(date < today, tss, plannedtss)

# Last 30 days total distance
athleterange(today - 30, today, sum(distance))

# Power at specific durations from PD curve (1 min, 5 min, 20 min)
li(pdcurve(meanmax(power)), {60, 300, 1200})

# Cumulative work in kJ
cumsum(power * deltatime) / 1000

# Gear combinations used
sort(unique(string(frontgear) + "x" + string(reargear)))

# Cadence only when pedaling
avg(if(cadence > 0, cadence))

# Count front gear changes
sum(delta(frontgear > 0))

# Smooth power with EWMA
ewma(power, 30)

# 5 biggest TSS days, sorted descending
sortd(greatest(tss, 5))

# Average distance by day of week
avg(distance, dayofweek(date))

# Monthly workout count
count(tss, "month")

# Second half of ride average power
workoutrange(begintime + duration/2, endtime, avg(power))

# VO2max in mL/min/kg
vo2max(meanmax(power)) * 1000 / weight

# Training load
tl(tss, ctlconstant)   # CTL
tl(tss, atlconstant)    # ATL

# Compare to standard PD curves
pdcurve("excellent", "female")
pdcurve("worldclass", "male")
```

## Zone systems for bin()

`ilevels`, `classicpower`, `classichr`, `frielhr`, `usachr`, `bcfhr`, `frielpace`, `pzipace`

## Full function reference

For the complete catalog of 80+ functions with syntax, parameters, and examples, read:
→ `references/expression-reference.md`

Categories: Conditional, Date, Logical, Mathematical, Power-Duration, Rounding, Selection, Smoothing, Sorting/Reshaping, Statistical, Training Levels, Trigonometric, Units.
