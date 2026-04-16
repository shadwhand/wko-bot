# WKO5 Reverse Engineering

**Date:** 2026-04-14 (updated 2026-04-16)
**Status:** Binary format cracked (WKO4 decoder <1% error vs FIT). PD model fitter matches WKO5 on Pmax, mFTP, and TTE within 2%; FRC and derived stamina remain off by ~25% due to a known FRC/tau decomposition degeneracy that a fresh sprint test would resolve.

## Summary

Reverse-engineered the WKO4/WKO5 proprietary binary file format by disassembling `PowerKitOSX.framework` (ARM64) from the WKO5 macOS app. Built a Python decoder for `.wko4` activity files and extracted model metrics from `.wko5athlete` profiles. Used the extracted ground truth to validate and improve our Peronnet-Thibault PD model.

No prior public work exists on this format — GoldenCheetah explicitly declined to attempt it.

## Binary Format

### Encoding

PKEncoder/PKDecoder — a custom serialization layer built on protobuf wire format conventions.

- **Tags:** `field_id << 3 | wire_type` (standard protobuf tag encoding)
- **Wire types:** 0=varint, 1=fixed64, 2=bytes (doubles: 8 raw bytes, NO length prefix), 3=start_group, 4=end_group, 5=vectorArchive
- **Signed integers:** zigzag encoding (same as protobuf sint32)
- **Discovered from:** disassembly of `PKEncoder::encode(uint, uint)` at 0x20fd94 — `lsl w1, w1, #3` confirms the `field_id << 3` tag format

### File Types

| Extension | Magic | Content |
|-----------|-------|---------|
| `.wko4` | `wko4` | Activity files — metadata + laps + peaks + time-series |
| `.wko5athlete` | `wko5athlete` | Athlete profile — model metrics, date ranges, settings |
| `.wko5cache` | `wko5cache` | Expression evaluation cache per workout |
| `.wko5chart` | `wko5chart` | Chart/panel definitions with expressions + layout |

### Time-Series Encoding (PKVectorStorageX)

Activities store second-by-second data (power, HR, cadence, speed, elevation) using `PKVectorStorageX`, identified by field IDs 111-122:

| Field | ID | Tag Bytes | Content |
|-------|----|-----------|---------|
| StorageType | 111 | `f8 06` | Enum: 0=INT32_DELTA, 1=DOUBLE, 2=FLOAT, 3=STRING |
| Count | 112 | `80 07` | Number of samples |
| Multiplier | 114 | `92 07` | Scale factor (default 1.0) |
| VectorData | 115 | `9d 07` | `size_varint + encoded_samples` |
| ChangeCount | 122 | `d0 07` | Modification counter |

**INT32_DELTA encoding (type 0):**
1. First value: zigzag-encoded varint (absolute)
2. Subsequent values: zigzag-encoded varint deltas (cumulative sum)
3. Sentinel: `abs(cumulative) > 10,000,000` → NULL/NA
4. Blob boundary: `data_start + blob_size` (reading past this causes overflow)

**Channel detection:** Find channel name bytes (e.g., `power`, `heartrate`) followed by `\xb4\x06` (F102 END_GROUP tag).

### Validation

Decoded power/HR/cadence validated against FIT file ground truth in `cycling_power.db`:

| Ride | Channel | WKO4 Decoded | FIT Truth | Error |
|------|---------|-------------|-----------|-------|
| Feb 9 VO2 | avg power | 159.6W | 160.3W | 0.4% |
| Jan 25 SS | avg power | 212.5W | 212.0W | 0.2% |
| Jan 25 SS | max power | 783W | 783W | 0.0% |
| Feb 9 VO2 | avg HR | 142.8 | 142.8 | 0.0% |
| Jan 25 SS | avg cadence | 80.2 | 80.0 | 0.2% |

Tested across 10 rides — all within 2% error.

## Athlete Model Metrics

Extracted from `.wko5athlete` binary file by finding metric name strings (`mftp`, `pmax`, `frc`, etc.) paired with sport names and nearby IEEE 754 doubles. Cross-referenced with WKO5 UI screenshots.

### Ground Truth (from WKO5 UI, 2026-04-14, date range 1/1/26–4/14/26)

| Metric | Value | Unit |
|--------|-------|------|
| Pmax | 1,302 | W |
| FRC | 10.8 | kJ |
| mFTP | 298 | W |
| TTE | 32:52 | min:sec |
| Stamina | 70 | % |
| VO2max | 4.40 | L/min |
| FVO2max | 356 | W |
| VLamax | 0.43 | mmol/L/sec |
| Phenotype | All-rounder | — |

Stored in `wko5/wko5_ground_truth.json`.

### WKO5 Test Targets (from UI)

WKO5 identifies undertested durations where the model predicts above MMP:

| Test | Duration | Target |
|------|----------|--------|
| Short | 1s | >1,302W |
| Medium | 34s | >523W |
| Long | 22:48 | >305W |

**Note:** these targets were used during interactive analysis to validate that our fitted curve matches WKO5's curve at those durations. They are **not** inputs to `fit_pd_model()` in the committed code — the fitter uses `ftp_prior` and `tte_prior` (from the `ftp_tests` table) plus heuristic Pmax/FRC estimates derived from the MMP curve shape. Treat the targets as a cross-check against WKO5, not as calibration anchors baked into the fitting procedure.

## PD Model Comparison

### WKO5's Fitting Approach

Key insights from screenshots and binary analysis:

1. **Theoretical ceiling:** The PD curve stays ABOVE the MMP envelope at most durations. WKO5 models what the athlete COULD do, not what they DID do. Undertested durations show the model above MMP (confirmed by residuals chart).

2. **Model form:** Peronnet-Thibault with post-TTE log-linear decline:
   ```
   P(t) = FRC*1000/t * (1-exp(-t/tau)) + mFTP * (1-exp(-t/tau2))           for t ≤ TTE
   P(t) = FRC*1000/t * (1-exp(-t/tau)) + mFTP * (1-exp(-t/tau2)) - a*ln(t/TTE)  for t > TTE
   ```
   Where `Pmax = FRC*1000/tau` (derived, not a free parameter).

3. **Aerobic/anaerobic decomposition** (from Image 2): The anaerobic (FRC) term drops steeply and is near zero by ~3 minutes. The aerobic (mFTP) term rises as a sigmoid, crossing 50% around 60-90s.

### Our Model vs WKO5 (with Sept 2025 FTP test prior)

| Param | WKO5 | Ours | Delta | Grade |
|-------|------|------|-------|-------|
| Pmax | 1,302W | 1,294W | -0.6% | ✓ |
| mFTP | 298W | 292W | -1.9% | ✓ |
| TTE | 32.9 min | 33.5 min | +1.8% | ✓ |
| FRC | 10.8 kJ | 13.4 kJ | +24% | ✗ |
| tau | 8.3s | 10.4s | +25% | ✗ |

The FRC/tau gap is a degeneracy: both decompositions produce the same PD curve (same Pmax = FRC*1000/tau ≈ 1295W). A fresh sprint test would pin Pmax directly and resolve the decomposition.

### Fitting Strategy (updated `pdcurve.py`)

Two-stage approach that works for any athlete:

1. **Estimate Pmax** from 1s MMP × 1.1 (extrapolation headroom)
2. **Fix Pmax** → constrains `tau = FRC*1000/Pmax`
3. **FRC estimate** from area between MMP and mFTP for t < 120s (scaled ×0.3)
4. **mFTP anchor** from FTP test (or estimated from long-duration MMP)
5. **TTE prior** from FTP test to exhaustion (breaks FRC/TTE degeneracy)
6. **Differential evolution** (global optimizer) fits remaining params with priors

Coach test protocol for best results:
- Sprint test (1-5s max) → pins Pmax
- 1min max effort → constrains FRC decay shape
- 3-5min max effort → constrains FVO2max
- FTP test to exhaustion → gives mFTP AND TTE directly

## WKO5 Expression Language

Extracted 18,406 unique expressions from 182 `.wko5chart` files and 170+ function implementations from the PowerKit binary (`PKExpressionParser` class).

### Key Functions (from `nm` symbol extraction)

**PD model:** `ftp()`, `frc()`, `pmax()`, `tte()`, `vo2max()`, `stamina()`, `phenotype()`, `dfrc()` (dynamic FRC), plus `_rolling` variants

**Time-series:** `meanmax()`, `ewma()`, `slr()`, `tl()` (training load/CTL/ATL), `levelfrom()`/`levelto()` (iLevels)

**Math/stats:** `avg()`, `sum()`, `max()`, `min()`, `count()`, `stddev()`, `greatest()`, `clamp()`, `gaussian()`

**Derived:** `s()` (slope), `dmax()`/`dmaxe()` (D-max inflection point), `pdcurve()`, `pdprofile()`

The expressions are stored as plain text strings inside the binary `.wko5chart` files, making extraction straightforward. A YAML-based chart format could replace the binary format for human-editable chart definitions.

## Files Created

### Committed tooling (reproducible)

| File | Purpose |
|------|---------|
| `tools/wko4_decoder.py` | Deterministic WKO4 activity file decoder (magic `wko4` only — rejects `wko5athlete`, `wko5cache`, `wko5chart`) |
| `wko5/pdcurve.py` | PD model fitter with two-stage Pmax-constrained fitting; accepts `ftp_prior` and `tte_prior` |
| `wko5/compare_models.py` | Comparison harness — default `--mode fit` runs `fit_pd_model` against MMP; `--mode posterior` reads Stan posterior samples (legacy) |

### Derived artifacts (one-off extraction)

| File | Purpose |
|------|---------|
| `wko5/wko5_ground_truth.json` | WKO5 metric values extracted from the athlete's `.wko5athlete` file + UI screenshots. Captured as a fixture; no checked-in extractor regenerates it. |

### Session-only analysis (not committed)

The following were performed interactively during the 2026-04-14 session and are **not** reproducible from committed tools:

- **`.wko5athlete` metric extraction** — ad-hoc Python scanning for metric names (`mftp`, `pmax`, etc.) + nearby IEEE 754 doubles. The JSON output was captured; the extractor was not.
- **`.wko5chart` expression corpus** — 18,406 expressions extracted from 182 chart files via one-off Python. The chart files themselves live in `~/Library/Application Support/WKO4/Cloud Library 5/` and are not committed. Repo-wide `find . -name '*.wko5chart'` returns 0 by design.
- **`PKExpressionParser` symbol enumeration** — `nm` dump of `PowerKitOSX.framework/PowerKitOSX`. The framework is proprietary and not in the repo; re-run against a local WKO5 install if needed.

Re-running any of the above requires a working WKO5 install on macOS and re-authoring the extraction scripts, which remain in the session transcript rather than in the repository.

## Next Steps

1. **Fresh test block** — sprint + 1min + 5min + FTP-to-exhaustion resolves FRC/tau decomposition
2. **Expression evaluator** — implement ~30 core functions to evaluate WKO5 chart expressions against our DB
3. **YAML chart format** — convert `.wko5chart` binary → human-editable YAML for training companion app
4. **Rolling PD profile** — use `rolling_pd_profile()` with the new fitting to track model params over time
5. **Stamina definition** — WKO5's stamina (70%) doesn't match P(60min)/mFTP; likely uses Dmax-based calculation from the `s()` and `dmax()` functions
