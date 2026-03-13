# WKO5 Expression Reference — Complete Function Catalog

## Table of Contents
- [Conditional Functions](#conditional-functions)
- [Date Functions](#date-functions)
- [Logical Functions](#logical-functions)
- [Mathematical Functions](#mathematical-functions)
- [Power-Duration Functions](#power-duration-functions)
- [Rounding Functions](#rounding-functions)
- [Selection Functions](#selection-functions)
- [Smoothing Functions](#smoothing-functions)
- [Sorting and Reshaping Functions](#sorting-and-reshaping-functions)
- [Statistical Functions](#statistical-functions)
- [Training Levels Functions](#training-levels-functions)
- [Variables](#variables)

---

## Conditional Functions

### has(string, substring)
Check if a string contains the substring (case-insensitive).
Returns 1 if found, 0 if not.
```
has(title, "vo2max")    → returns 1 if workout title contains "vo2max"
```

### hastag(string)
Check if a workout has the specified tag (case-insensitive, must match entire tag).
Returns 1 if tag exists, 0 otherwise.
```
hastag("edge800")       → 1 if workout has EDGE800 tag
hastag("race")          → use with if() to filter race workouts
```

### if(condition, truevalue)
Returns truevalue when condition is true, "--" (na) otherwise.
```
if(cadence > 0 and cadence < 50, cadence)    → cadence values in range only
if(hastag("race"), tss)                       → TSS only for race workouts
```

### if(condition, truevalue, falsevalue)
Returns truevalue when true, falsevalue when false.
```
if(date < today, tss, plannedtss)    → completed TSS for past, planned for future
if(power > bikeftp, power, 0)        → power above FTP, else 0
```

### isvalid(numbers)
Returns 1 if valid number, 0 if missing/na.
```
isvalid(na)    → 0
isvalid(0)     → 1
isvalid(3.14)  → 1
```

---

## Date Functions

### date(value)
Converts a weekvalue, monthvalue, or yearvalue to a date.
```
date(trunc(weekval(today)) + 1)          → first day of next week
date(trunc(monthval(today)) + 1) - 1     → last day of current month
```

### date(year, month, day)
Creates a date from components. Year is 4-digit, month 1-12, day 1-31.
```
date(2016, 4, 7)           → April 7, 2016
date({2015:2017}, 12, 31)  → Dec 31 for each year 2015-2017
```

### date(year, month, day, hour, minute)
Creates a date+time value. Hour 0-23, minute 0-59.

### day(datevalues)
Day of month (1-31).
```
day(today)    → current day of month
```

### dayofweek(date)
Day of week as offset (0-6) from first day per Preferences.
```
dayofweek(date(2016, 4, 7))    → 3 if first day is Monday (Thursday)
```

### formatdate(datevalues, format)
Format specifiers: yy, yyyy, M, MM, MMM, MMMM, d, dd, EEE, EEEE, h, hh, H, HH, m, mm, s, ss, a
```
formatdate(today, "EEEE, MMMM dd, yyyy")      → "Saturday, August 13, 2016"
formatdate(date, "yyyy-MM-dd HH:mm:ss")        → "2016-08-12 13:21:06"
```

### month(datevalues)
Month number (1-12).

### monthval(datevalues)
Converts date to fractional months since Jan 1, 1901. Useful for grouping by month.
```
monthval(date(2015, 11, 3))    → displays as "November 2015" with month units
```

### startofmonth(datevalues)
First day of the month containing the date.

### startofweek(datevalues)
First day of the week containing the date.

### startofyear(datevalues)
January 1st of the year containing the date.

### week(datevalues)
ISO-8601 week number (1-53).

### weekval(datevalues)
Converts date to fractional weeks since Jan 1, 1901. Useful for grouping by week.

### year(datevalues)
Four-digit year number.

### yearval(datevalues)
Converts date to fractional years since Jan 1, 1901. Useful for grouping by year.

---

## Logical Functions

### logicaland(lhs, rhs)
Same as `and` / `&&`. Returns 1 if both nonzero, 0 otherwise.
```
logicaland(date > today, plannedtss > 100)
```

### logicalor(lhs, rhs)
Same as `or` / `||`. Returns 1 if either nonzero, 0 otherwise.
```
logicalor(hastag("race"), has(title, "race"))
```

---

## Mathematical Functions

### abs(numbers)
Absolute value.
```
abs(-3)                    → 3
abs({1, -1, 0, 3, -3})    → {1, 1, 0, 3, 3}
```

### add(lhs, rhs)
Addition. Same as `+`.
```
add({1,2,3}, {4,5,6})    → {5, 7, 9}
```

### divide(lhs, rhs)
Division. Same as `/`.
```
divide({2,10,50}, {2,2,5})    → {1, 5, 10}
```

### ln(numbers)
Natural logarithm.
```
ln(e^5)    → 5
```

### log(numbers, base)
Logarithm with specified base.
```
log(64, 2)    → 6
```

### log10(numbers)
Base-10 logarithm.
```
log10(1000)    → 3
```

### multiply(lhs, rhs)
Multiplication. Same as `*`.

### power(lhs, rhs)
Exponentiation. Same as `^`.
```
power(2, 4)      → 16
power(64, 1/3)   → 4
```

### sign(numbers)
Returns 1 for positive, -1 for negative, 0 for zero.

### sqrt(numbers)
Square root.
```
sqrt({9, 64, 16})    → {3, 8, 4}
```

### subtract(lhs, rhs)
Subtraction. Same as `-`.

---

## Power-Duration Functions

All power-duration functions take `meanmax(power)` or `meanmax(power/weight)` as their primary argument. Most have a rolling lookback variant for daily tracking.

### ftp(meanmaxcurve)
Modeled Functional Threshold Power in W (or W/kg if using power/weight).
```
ftp(meanmax(power))           → FTP in watts
ftp(meanmax(power/weight))    → FTP in W/kg
```

### ftp(meanmaxcurve, lookback)
Daily rolling FTP.
```
ftp(meanmax(power), 90)    → daily FTP from 90-day rolling windows
```

### ftpe(meanmaxcurve)
Estimated error in FTP calculation (+/- watts).

### ftpcurve(meanmaxcurve)
Power-duration curve showing only the FTP component.

### frc(meanmaxcurve)
Functional Reserve Capacity in kJ (or kJ/kg).
```
frc(meanmax(power))           → FRC in kJ
frc(meanmax(power/weight))    → FRC in kJ/kg
```

### frc(meanmaxcurve, lookback)
Daily rolling FRC.
```
frc(meanmax(power/weight), 90)    → daily FRC normalized to body weight
```

### frce(meanmaxcurve)
Estimated error in FRC calculation.

### frccurve(meanmaxcurve)
Power-duration curve showing only the FRC component.

### pmax(meanmaxcurve)
Maximum instantaneous power (neuromuscular peak).
```
pmax(meanmax(power))    → Pmax in watts
```

### pmax(meanmaxcurve, lookback)
Daily rolling Pmax.

### pmaxe(meanmaxcurve)
Estimated error in Pmax calculation.

### vo2max(meanmaxcurve)
Estimated VO2max in L/min.
```
vo2max(meanmax(power)) * 1000 / weight    → VO2max in mL/min/kg
```

### vo2max(meanmaxcurve, lookback)
Daily rolling VO2max.
```
vo2max(meanmax(power), 90) * 1000 / weight    → daily VO2max in mL/min/kg
```

### tte(meanmaxcurve)
Time to Exhaustion at FTP, in seconds.

### tte(meanmaxcurve, lookback)
Daily rolling TTE.

### fibertype(meanmaxcurve)
Estimated % type I (slow-twitch) muscle fiber area.
```
fibertype(meanmax(power))       → fiber type %
fibertype(meanmax(power), 90)   → daily rolling fiber type
```

### pdcurve(meanmaxcurve)
Full modeled power-duration curve.
```
pdcurve(meanmax(power))    → complete PD curve
```

### pdcurve(standardindex, gender)
Standards-based PD curve for comparison.
Standard indices: "untrained", "fair", "moderate", "good", "verygood", "excellent", "exceptional", "worldclass" (or 0-7).
Gender: "male" or "female".
```
pdcurve("excellent", "female")    → excellent female standards curve
```

### pdprofile(meanmaxcurve)
Power-duration profile curve (typically used with power/weight).
```
pdprofile(meanmax(power/weight))
```

### phenotype(meanmaxcurve)
Rider classification: "Sprinter", "Pursuiter", "TTer", or "All-rounder".

### sumsqr(meanmaxcurve)
Sum of squares error of model fit. Lower = better fit.

### meanmax(channel)
Builds a mean-maximal curve from a time-series channel. This is the foundational function for all power-duration analysis.
```
meanmax(power)           → mean-max power curve
meanmax(power/weight)    → mean-max power/weight curve
meanmax(heartrate)       → mean-max heart rate curve
```

---

## Rounding Functions

### ceil(numbers)
Ceiling (smallest integer >= value).
```
ceil(3.1)                        → 4
ceil({-3.3, 0, -7.8, 5.9})      → {-3, 0, -7, 6}
```

### floor(numbers)
Floor (largest integer <= value).
```
floor(3.1)                       → 3
floor({-3.3, 0, -7.8, 5.9})     → {-4, 0, -8, 5}
```

### frac(numbers)
Fractional part only.
```
frac(3.1)                        → 0.1
frac({-3.3, 0, -7.8, 5.9})      → {-0.3, 0, -0.8, 0.9}
```

### round(numbers)
Round to nearest integer.
```
round(3.5)    → 4
```

### round(numbers, places)
Round to specified precision. Negative places = right of decimal.
```
round(pi, -1)       → 3.1
round(pi, -3)       → 3.142
round(1234.567, 2)  → 1200
```

### trunc(numbers)
Truncate (remove fractional part, toward zero).
```
trunc(3.9)     → 3
trunc(-3.9)    → -3
```

---

## Selection Functions

### athleterange(fromdate, todate, expression)
Override the date range for athlete-level expressions.
```
athleterange(date(2017,2,23), date(2017,3,17), avg(tss))    → avg TSS for that range
athleterange(today - 30, today, sum(distance))               → total distance last 30 days
```

### workoutrange(fromtime, totime, expression)
Override the time range within a workout.
```
workoutrange(begintime + duration/2, endtime, avg(power))    → avg power second half
```

### clamp(values, min, max)
Constrain values to [min, max].
```
clamp({5,7,3,2,4,9,8}, 4, 8)    → {5,7,4,4,4,8,8}
```

### first(values, count)
First N values.
```
first({5,7,3,2,4,9,8}, 3)    → {5, 7, 3}
```

### last(values, count)
Last N values.
```
last({5,7,3,2,4,9,8}, 3)    → {4, 9, 8}
```

### greatest(values, count)
N largest values (preserves original order).
```
greatest({5,7,3,2,4,9,8}, 3)    → {7, 9, 8}
sortd(greatest(tss, 5))          → top 5 TSS sorted descending
```

### least(values, count)
N smallest values (preserves original order).
```
least({5,7,3,2,4,9,8}, 3)    → {3, 2, 4}
```

### max(values)
Greatest single value. Returns as horizontal line for channels.
```
max(power)    → maximum power as horizontal line
```

### max(values, groupby)
Maximum grouped by identifier.
```
max(distance, dayofweek(date))    → max distance per day of week
```

### min(values)
Least single value.

### min(values, groupby)
Minimum grouped by identifier.

---

## Smoothing Functions

### ewma(numbers, factor)
Exponential Weighted Moving Average.
```
ewma(power, 30)    → smoothed power
```

### tl(numbers, constant)
Training load calculation using exponential decay.
```
tl(tss, ctlconstant)    → CTL (Chronic Training Load / fitness)
tl(tss, atlconstant)    → ATL (Acute Training Load / fatigue)
```

### filter(numbers, kernel, sides)
Apply convolution filter with specified kernel.

### gaussian(sigma, length)
Generate a Gaussian kernel for use with filter().

### isef(factor, length)
Generate an exponential smoothing kernel.

---

## Sorting and Reshaping Functions

### sort(values)
Ascending sort. Works with numbers, strings, and pairs (sorts by Y).
```
sort({5,3,8,0,na,7})        → {0,1,2,3,4,5,6,7,8,--}
sort((power, cadence))       → scatter sorted by cadence ascending
```

### sortd(values)
Descending sort.
```
sortd(greatest(tss, 5))    → top 5 TSS greatest to least
```

### sortx(pairs)
Sort pairs by X value ascending.
```
sortx((power, cadence))    → scatter sorted by power ascending
```

### sortxd(pairs)
Sort pairs by X value descending.

### rev(values)
Reverse order.
```
rev({3,5,7,9})    → {9,7,5,3}
```

### delta(numbers)
Difference between consecutive values. First value is na.
```
delta({3,5,7,11,13})         → {na, 2, 2, 4, 2}
sum(delta(frontgear > 0))    → count of front gear changes
```

### noinvalid(numbers)
Remove all na values.
```
noinvalid({13, 0, 7, na, 0, 21})    → {13, 0, 7, 0, 21}
```

### nozero(numbers)
Replace zeros with na (useful for averages excluding stopped time).
```
avg(nozero(cadence))    → average cadence excluding zeros
nozero({13, 0, 7})      → {13, na, 7}
```

### resample(values, newrate)
Resample time-series data to a new rate.

### shift(numbers, positions)
Shift values by N positions.

### string(values)
Convert numbers to strings.
```
sort(unique(string(frontgear) + "x" + string(reargear)))    → all gear combos
```

### unique(values)
Remove duplicates.
```
sort(unique(tags))    → all tags used in selected range
```

### cross(values, values)
Deprecated. Use `(X, Y)` pair notation instead.

### xx(pairs)
Copy X to Y: `(X,Y)` → `(X,X)`.

### yx(pairs)
Swap X and Y: `(X,Y)` → `(Y,X)`.

---

## Statistical Functions

### avg(numbers)
Average/mean.
```
avg(power)                         → average power
avg(distance, dayofweek(date))     → avg distance by day of week
```

### avg(numbers, groupby)
Average grouped by identifier.

### sum(numbers)
Sum of all values.

### sum(numbers, groupby)
Sum grouped by identifier.

### count(values)
Count of valid, non-zero values.
```
count({3, 6, 0, 9, na, 12})    → 4
count(heartrate)                 → count of non-zero HR values
```

### count(values, groupby)
Count grouped by period. Period: "day", "week", "month", "year".
```
count(tss, "month")    → monthly workout count
```

### length(values)
Count of ALL values including zeros and na.
```
length({3, 6, 0, 9, na, 12})    → 6
heartrate[length(heartrate)-1]   → last heart rate value
```

### cumsum(numbers)
Running cumulative sum.
```
cumsum({1,2,3,4,5})                  → {1, 3, 6, 10, 15}
cumsum(power * deltatime) / 1000     → cumulative work in kJ
```

### bin(values, binsize)
Histogram with uniform bin width.
```
bin(cadence, 10)    → cadence in 10 rpm bins
```

### bin(values, binvalues)
Histogram with custom cut points.
```
bin(cadence, {85, 95})             → 3 bins: <85, 85-95, >=95
bin(power, {162, 184, 206, 228})   → custom power bins
```

### bin(values, levelsname)
Histogram using named training level system.
Systems: "ilevels", "classicpower", "classichr", "frielhr", "usachr", "bcfhr", "frielpace", "pzipace"
```
bin(power, "ilevels")    → power distributed across iLevel zones
```

### median(numbers)
Median value.

### percentile(numbers, pct)
Value at specified percentile.

### stdev(numbers)
Standard deviation.

### li(pairs, numbers)
Linear interpolation — find Y for given X values.
```
li(elapseddistance, 0:10:00)                        → distance at 10 min
li(pdcurve(meanmax(power)), {60, 300, 1200})         → power at 1, 5, 20 min
```

### lookup(pairs, numbers)
Find Y values for given X values (exact match).

---

## Training Levels Functions

### levelfrom(levelsname, index)
Get the "from" (lower bound) value for a training level.

### levelto(levelsname, index)
Get the "to" (upper bound) value for a training level.

### levelname(levelsname, index)
Get the name of a training level.

Supported level systems: ilevels, classicpower, classichr, frielhr, usachr, bcfhr, frielpace, pzipace

---

## Variables

### Athlete Variables (one value per workout)
- `date` — workout date
- `tss` — Training Stress Score
- `plannedtss` — planned TSS
- `distance` — total distance
- `if` — Intensity Factor
- `weight` — athlete weight

### Channel Variables (time-series, one value per second)
- `power` — power in watts
- `heartrate` — heart rate in bpm
- `cadence` — cadence in rpm
- `speed` — speed
- `elevation` — elevation/altitude
- `deltatime` — time delta between samples
- `frontgear`, `reargear` — gear data
- `elapseddistance` — cumulative distance

### Range Variables
- `today` — current date
- `date` — workout date (in range context)
- `title` — workout title string
- `tags` — workout tags

### Workout Variables
- `begintime` — start time of selected range
- `endtime` — end time of selected range
- `duration` — duration of selected range
- `bikeftp` — FTP set on the bike computer

### Constants
- `na` — not available / missing value
- `pi` — 3.14159...
- `e` — 2.71828...
- `ctlconstant` — decay constant for CTL calculation
- `atlconstant` — decay constant for ATL calculation

### Metrics Variables
- Various pre-calculated metrics accessible as variables
