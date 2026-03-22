# Phase 6: Bayesian Layer — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace point estimates with Bayesian posterior distributions using Stan (NUTS sampler) for the PD model, durability model, and training response — giving credible intervals, self-correcting estimates, and proper uncertainty propagation through gap analysis.

**Architecture:** Stan models in `.stan` files compiled via `cmdstanpy`. A Python wrapper `bayesian.py` handles model compilation, data preparation, sampling, posterior storage, and summary generation. Posteriors are stored as packed float arrays in a `posterior_samples` table. Gap analysis draws from stored posteriors instead of Gaussian perturbation. Auto-triggered after every Garmin sync.

**Tech Stack:** Stan (CmdStan 2.38.0), cmdstanpy, numpy, SQLite

**Existing:** `wko5/` with 168+ tests. Stan installed at `~/.cmdstan/cmdstan-2.38.0`. PD model Stan file tested and working (`wko5/stan/pd_model.stan` — mFTP=301W vs scipy's 240W, actual 292W). FTP test detection from TP data working (`ftp_test.py`).

**Python env:** `/tmp/fitenv/` — needs `cmdstanpy` installed (`pip install cmdstanpy`)

**Test command:** `source /tmp/fitenv/bin/activate && cd /Users/jshin/Documents/wko5-experiments && pytest tests/ -v`

**Key design decisions:**
- kJ for within-ride durability (not TSS)
- FTP prior from Kolie Moore test, SD widens with time since test (10W fresh → 40W stale)
- 2000 posterior samples per model fit
- Posterior summary for Claude: median, 95% CI, prior influence, what would reduce uncertainty
- Auto-refit after every Garmin sync

---

## File Structure

```
wko5/
  stan/
    pd_model.stan        # Already exists — PD curve with FTP prior
    durability.stan      # Decay model: a, b, c from long ride data
  bayesian.py            # Compile, sample, store, load posteriors + summaries
```

- `wko5/stan/pd_model.stan` — already tested and working
- `wko5/stan/durability.stan` — new Stan model for durability decay
- `wko5/bayesian.py` — orchestrates everything: model compilation, data prep, sampling, DB storage, summary generation, posterior loading

---

## Task 1: Bayesian engine (`bayesian.py`) + posterior storage

**Files:**
- Create: `wko5/bayesian.py`
- Create: `wko5/stan/durability.stan`
- Create: `tests/test_bayesian.py`

- [ ] **Step 1: Write the durability Stan model**

Create `wko5/stan/durability.stan`:

```stan
// Durability decay model — Bayesian estimation
//
// degradation = a * exp(-b * kJ / 1000) + (1-a) * exp(-c * hours)
//
// Fitted from windowed MMP ratios across long rides.

data {
  int<lower=1> N;
  array[N] real cum_kj;
  array[N] real elapsed_h;
  array[N] real ratio;       // MMP ratio: window power / first window power
}

parameters {
  real<lower=0.01, upper=0.99> a;
  real<lower=0.0001, upper=0.05> b;
  real<lower=0.001, upper=1.0> c;
  real<lower=0.01, upper=0.3> sigma;
}

model {
  a ~ beta(4, 4);
  b ~ lognormal(-5, 1.5);
  c ~ lognormal(-3, 1);
  sigma ~ exponential(10);

  for (i in 1:N) {
    real pred = a * exp(-b * cum_kj[i] / 1000) + (1 - a) * exp(-c * elapsed_h[i]);
    ratio[i] ~ normal(pred, sigma);
  }
}
```

- [ ] **Step 2: Write tests**

```python
# tests/test_bayesian.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from wko5.bayesian import (
    fit_pd_bayesian, fit_durability_bayesian, update_all_models,
    get_posterior_summary, load_posterior_samples, store_posterior,
)


def test_fit_pd_bayesian():
    """PD Bayesian fit should produce posterior samples."""
    result = fit_pd_bayesian(days=90)
    if result is None:
        return  # insufficient data

    assert "mFTP" in result
    assert "FRC" in result
    assert "Pmax" in result
    assert len(result["mFTP"]) >= 500  # at least 500 samples
    # mFTP should be in reasonable range
    median_ftp = float(np.median(result["mFTP"]))
    assert 150 < median_ftp < 400


def test_fit_pd_bayesian_with_ftp_prior():
    """FTP prior should pull mFTP toward tested value."""
    # With strong prior at 292W
    result_strong = fit_pd_bayesian(days=90, ftp_prior_mean=292, ftp_prior_sd=10)
    # With weak prior
    result_weak = fit_pd_bayesian(days=90, ftp_prior_mean=280, ftp_prior_sd=80)

    if result_strong is None or result_weak is None:
        return

    median_strong = float(np.median(result_strong["mFTP"]))
    median_weak = float(np.median(result_weak["mFTP"]))
    ci_strong = float(np.percentile(result_strong["mFTP"], 97.5) - np.percentile(result_strong["mFTP"], 2.5))
    ci_weak = float(np.percentile(result_weak["mFTP"], 97.5) - np.percentile(result_weak["mFTP"], 2.5))

    # Strong prior should produce narrower CI
    assert ci_strong < ci_weak


def test_fit_durability_bayesian():
    """Durability Bayesian fit should produce posterior samples."""
    result = fit_durability_bayesian(min_ride_hours=3, min_rides=5)
    if result is None:
        return

    assert "a" in result
    assert "b" in result
    assert "c" in result
    assert len(result["a"]) >= 500


def test_store_and_load_posterior():
    """Should store and load posterior samples from DB."""
    samples = {"mFTP": np.random.normal(290, 10, 1000).tolist(),
               "FRC": np.random.normal(20, 3, 1000).tolist()}
    store_posterior("test_model", samples)

    loaded = load_posterior_samples("test_model")
    assert loaded is not None
    assert "mFTP" in loaded
    assert len(loaded["mFTP"]) == 1000
    assert abs(np.mean(loaded["mFTP"]) - 290) < 5


def test_get_posterior_summary():
    """Summary should include median, CI, prior influence."""
    # First fit and store
    result = fit_pd_bayesian(days=90)
    if result is None:
        return
    store_posterior("pd_model", result)

    summary = get_posterior_summary("pd_model")
    assert "mFTP" in summary
    assert "median" in summary["mFTP"]
    assert "ci_95" in summary["mFTP"]
    assert "prior_influence" in summary["mFTP"]


def test_update_all_models():
    """Full update pipeline should complete without error."""
    update_all_models()
    # Verify posteriors exist
    pd = load_posterior_samples("pd_model")
    assert pd is not None
```

- [ ] **Step 3: Implement bayesian.py**

```python
# wko5/bayesian.py
"""Bayesian model fitting with Stan — PD model, durability, posterior storage."""

import json
import logging
import os
import struct
from pathlib import Path

import numpy as np
import cmdstanpy

from wko5.config import get_config
from wko5.db import get_connection
from wko5.pdcurve import compute_envelope_mmp
from wko5.durability import compute_windowed_mmp
from wko5.ftp_test import ftp_prior_strength, get_latest_ftp_test

logger = logging.getLogger(__name__)

STAN_DIR = Path(__file__).parent / "stan"

POSTERIOR_DDL = """
CREATE TABLE IF NOT EXISTS posterior_samples (
    model_type TEXT NOT NULL,
    fitted_at TEXT NOT NULL DEFAULT (datetime('now')),
    param_name TEXT NOT NULL,
    n_samples INTEGER,
    samples BLOB,
    PRIMARY KEY (model_type, param_name)
);
"""

# Compiled model cache
_compiled_models = {}


def _get_model(stan_file):
    """Get or compile a Stan model (cached)."""
    key = str(stan_file)
    if key not in _compiled_models:
        _compiled_models[key] = cmdstanpy.CmdStanModel(stan_file=str(stan_file))
    return _compiled_models[key]


def store_posterior(model_type, samples_dict):
    """Store posterior samples in the database.

    Args:
        model_type: 'pd_model' or 'durability'
        samples_dict: dict of {param_name: array_of_samples}
    """
    conn = get_connection()
    conn.execute(POSTERIOR_DDL)

    for param_name, samples in samples_dict.items():
        arr = np.array(samples, dtype=np.float64)
        blob = arr.tobytes()
        conn.execute("""
            INSERT OR REPLACE INTO posterior_samples
            (model_type, param_name, n_samples, samples)
            VALUES (?, ?, ?, ?)
        """, (model_type, param_name, len(arr), blob))

    conn.commit()
    conn.close()


def load_posterior_samples(model_type):
    """Load posterior samples from the database.

    Returns dict of {param_name: numpy_array} or None.
    """
    conn = get_connection()
    conn.execute(POSTERIOR_DDL)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT param_name, n_samples, samples FROM posterior_samples WHERE model_type = ?",
        (model_type,)
    )
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return None

    result = {}
    for param_name, n_samples, blob in rows:
        result[param_name] = np.frombuffer(blob, dtype=np.float64).copy()

    return result


def fit_pd_bayesian(days=90, ftp_prior_mean=None, ftp_prior_sd=None,
                    chains=2, iter_sampling=1000):
    """Fit the PD model using Stan NUTS sampler.

    Returns dict of {param_name: array_of_samples} or None.
    """
    mmp = compute_envelope_mmp(days=days)
    if len(mmp) < 60:
        logger.warning("Insufficient MMP data for Bayesian PD fit")
        return None

    # Downsample to key durations
    durations = [1, 2, 3, 5, 10, 15, 20, 30, 45, 60, 90, 120, 180, 240, 300,
                 360, 420, 480, 600, 720, 900, 1200, 1800, 2400, 3600]
    durations = [d for d in durations if d <= len(mmp)]
    powers = [float(mmp[d - 1]) for d in durations]

    # FTP prior
    if ftp_prior_mean is None or ftp_prior_sd is None:
        prior = ftp_prior_strength()
        if ftp_prior_mean is None:
            ftp_prior_mean = prior["ftp"] if prior["ftp"] else 280
        if ftp_prior_sd is None:
            ftp_prior_sd = prior["sd"]

    data = {
        "N": len(durations),
        "duration_s": durations,
        "observed_power": powers,
        "ftp_prior_mean": float(ftp_prior_mean),
        "ftp_prior_sd": float(max(ftp_prior_sd, 5)),  # floor at 5W
    }

    model = _get_model(STAN_DIR / "pd_model.stan")

    try:
        fit = model.sample(
            data=data, chains=chains, iter_sampling=iter_sampling,
            show_console=False, seed=42,
        )
    except Exception as e:
        logger.warning(f"Stan PD model sampling failed: {e}")
        return None

    return {
        "mFTP": fit.stan_variable("mFTP").tolist(),
        "FRC": fit.stan_variable("FRC").tolist(),
        "Pmax": fit.stan_variable("Pmax").tolist(),
        "tau": fit.stan_variable("tau").tolist(),
    }


def fit_durability_bayesian(min_ride_hours=3, min_rides=5,
                            chains=2, iter_sampling=1000):
    """Fit the durability model using Stan NUTS sampler.

    Returns dict of {param_name: array_of_samples} or None.
    """
    from wko5.db import get_activities, get_records

    activities = get_activities()
    long_rides = activities[activities["total_timer_time"] > min_ride_hours * 3600]

    if len(long_rides) < min_rides:
        return None

    all_kj = []
    all_hours = []
    all_ratios = []

    for _, ride in long_rides.iterrows():
        records = get_records(ride["id"])
        if records.empty or "power" not in records.columns:
            continue

        windows = compute_windowed_mmp(records["power"], window_hours=2)
        if len(windows) < 2:
            continue

        first_power = windows[0].get("mmp_300s")
        if first_power is None or first_power <= 0 or np.isnan(first_power):
            continue

        for w in windows[1:]:
            wp = w.get("mmp_300s")
            if wp is None or wp <= 0 or np.isnan(wp):
                continue
            ratio = wp / first_power
            if ratio > 1.2:
                continue
            all_kj.append(w["cumulative_kj"])
            all_hours.append(w["elapsed_hours"])
            all_ratios.append(ratio)

    if len(all_ratios) < 10:
        return None

    data = {
        "N": len(all_ratios),
        "cum_kj": all_kj,
        "elapsed_h": all_hours,
        "ratio": all_ratios,
    }

    model = _get_model(STAN_DIR / "durability.stan")

    try:
        fit = model.sample(
            data=data, chains=chains, iter_sampling=iter_sampling,
            show_console=False, seed=42,
        )
    except Exception as e:
        logger.warning(f"Stan durability model sampling failed: {e}")
        return None

    return {
        "a": fit.stan_variable("a").tolist(),
        "b": fit.stan_variable("b").tolist(),
        "c": fit.stan_variable("c").tolist(),
        "sigma": fit.stan_variable("sigma").tolist(),
    }


def get_posterior_summary(model_type):
    """Generate a summary of the posterior for Claude to interpret.

    Returns dict of {param_name: {median, ci_95, prior_influence, recommendation}}.
    """
    samples = load_posterior_samples(model_type)
    if samples is None:
        return {}

    summary = {}
    for param, values in samples.items():
        median = float(np.median(values))
        ci_low = float(np.percentile(values, 2.5))
        ci_high = float(np.percentile(values, 97.5))
        ci_width = ci_high - ci_low
        std = float(np.std(values))

        entry = {
            "median": round(median, 2),
            "ci_95": [round(ci_low, 2), round(ci_high, 2)],
            "std": round(std, 2),
            "ci_width": round(ci_width, 2),
        }

        # Prior influence estimation (for PD model mFTP)
        if model_type == "pd_model" and param == "mFTP":
            latest_test = get_latest_ftp_test()
            prior = ftp_prior_strength()
            if latest_test and prior["ftp"]:
                # How close is the posterior to the prior vs the data?
                # If posterior ≈ prior mean → prior-dominated
                # If posterior ≈ MMP-implied → data-dominated
                prior_dist = abs(median - prior["ftp"])
                prior_range = prior["sd"] * 2
                entry["prior_influence"] = round(max(0, 1 - prior_dist / prior_range), 2)
                entry["months_since_test"] = prior["months_since_test"]
                entry["last_test_ftp"] = prior["ftp"]

                if prior["months_since_test"] and prior["months_since_test"] > 4:
                    entry["recommendation"] = "FTP test would narrow CI significantly"
                elif ci_width > 30:
                    entry["recommendation"] = "More hard efforts needed to constrain the model"
                else:
                    entry["recommendation"] = "Model is well-constrained"

        summary[param] = entry

    return summary


def update_all_models():
    """Re-fit all Bayesian models with latest data. Call after Garmin sync.

    Pipeline: check FTP tests → fit PD model → fit durability → store posteriors.
    """
    logger.info("Updating Bayesian models...")

    # 1. Check for new FTP tests
    from wko5.ftp_test import detect_ftp_tests_from_tp
    try:
        new_tests = detect_ftp_tests_from_tp()
        if new_tests:
            logger.info(f"Found {len(new_tests)} new FTP tests")
    except Exception:
        pass

    # 2. Fit PD model
    logger.info("Fitting PD model (Stan)...")
    pd_samples = fit_pd_bayesian()
    if pd_samples:
        store_posterior("pd_model", pd_samples)
        summary = get_posterior_summary("pd_model")
        mftp = summary.get("mFTP", {})
        logger.info(f"PD model: mFTP={mftp.get('median')}W "
                    f"(95% CI: {mftp.get('ci_95')})")

    # 3. Fit durability model
    logger.info("Fitting durability model (Stan)...")
    dur_samples = fit_durability_bayesian()
    if dur_samples:
        store_posterior("durability", dur_samples)
        logger.info(f"Durability model: a={np.median(dur_samples['a']):.3f}")

    logger.info("Bayesian model update complete")
```

- [ ] **Step 4: Run tests**

Run: `source /tmp/fitenv/bin/activate && pytest tests/test_bayesian.py -v`
Expected: All tests PASS. Note: Stan compilation on first run adds ~4s. Sampling takes ~1-2s per model.

- [ ] **Step 5: Run full suite**

Run: `pytest tests/ -q`

- [ ] **Step 6: Commit**

```bash
git add wko5/bayesian.py wko5/stan/durability.stan tests/test_bayesian.py
git commit -m "feat: add Bayesian layer — Stan PD model + durability with posterior storage"
```

---

## Task 2: Wire gap analysis to use real posteriors

**Files:**
- Modify: `wko5/gap_analysis.py`
- Modify: `tests/test_gap_analysis.py`

- [ ] **Step 1: Update gap_analysis to use posteriors**

Replace the Gaussian perturbation hack in `run_monte_carlo` with posterior draws:

```python
# In gap_analysis.py, modify run_monte_carlo:

def run_monte_carlo(segments, pd_model, durability_params, n_draws=200, seed=42):
    from wko5.bayesian import load_posterior_samples

    rng = np.random.default_rng(seed)
    n_segments = len(segments)
    if n_segments == 0:
        return []

    # Try to use real posteriors
    pd_posterior = load_posterior_samples("pd_model")
    dur_posterior = load_posterior_samples("durability")

    completions = np.zeros(n_segments)
    demand_ratios_all = np.zeros((n_draws, n_segments))

    for draw in range(n_draws):
        if pd_posterior and dur_posterior:
            # Draw from real posteriors
            idx = rng.integers(0, len(pd_posterior["mFTP"]))
            pd_draw = {k: pd_posterior[k][idx] for k in pd_posterior}
            dur_idx = rng.integers(0, len(dur_posterior["a"]))
            dur_draw = {k: dur_posterior[k][dur_idx] for k in dur_posterior if k != "sigma"}
        else:
            # Fallback to Gaussian perturbation
            pd_draw = _perturb_pd_model(pd_model, rng)
            dur_draw = _perturb_durability(durability_params, rng)

        profile = build_demand_profile(segments, pd_draw, dur_draw)

        for i, seg in enumerate(profile):
            dr = seg.get("demand_ratio", 0)
            demand_ratios_all[draw, i] = dr
            if dr <= 1.0:
                completions[i] += 1

    # ... rest of function unchanged
```

- [ ] **Step 2: Add test**

```python
def test_monte_carlo_with_posteriors():
    """Monte Carlo should use posteriors when available."""
    from wko5.bayesian import fit_pd_bayesian, fit_durability_bayesian, store_posterior

    # Fit and store posteriors
    pd = fit_pd_bayesian(days=90)
    dur = fit_durability_bayesian()
    if pd: store_posterior("pd_model", pd)
    if dur: store_posterior("durability", dur)

    segments = [
        {"type": "flat", "distance_m": 5000, "duration_s": 600, "avg_grade": 0.0,
         "power_required": 180, "cumulative_kj_at_start": 0},
    ]
    pd_model = {"Pmax": 1100, "FRC": 20, "mFTP": 290, "TTE": 3600}
    dur_params = {"a": 0.5, "b": 0.001, "c": 0.05}

    result = run_monte_carlo(segments, pd_model, dur_params, n_draws=50)
    assert len(result) == 1
    assert "success_probability" in result[0]
```

- [ ] **Step 3: Run tests**

- [ ] **Step 4: Commit**

```bash
git add wko5/gap_analysis.py tests/test_gap_analysis.py
git commit -m "feat: gap analysis draws from Bayesian posteriors instead of Gaussian perturbation"
```

---

## Task 3: API endpoint + summary for Claude

**Files:**
- Modify: `wko5/api/routes.py`
- Modify: `wko5/__init__.py`

- [ ] **Step 1: Add posterior summary endpoint**

```python
from wko5.bayesian import get_posterior_summary, update_all_models

@router.get("/posterior-summary", dependencies=[Depends(verify_token)])
def posterior_summary():
    pd_summary = get_posterior_summary("pd_model")
    dur_summary = get_posterior_summary("durability")
    return _sanitize_nans({"pd_model": pd_summary, "durability": dur_summary})

@router.post("/update-models", dependencies=[Depends(verify_token)])
def update_models():
    update_all_models()
    return {"status": "updated"}
```

- [ ] **Step 2: Update exports**

```python
from wko5.bayesian import fit_pd_bayesian, fit_durability_bayesian, update_all_models, get_posterior_summary
```

- [ ] **Step 3: Update wko5-analyzer skill**

Add to Module Reference:
```
### Bayesian Models
from wko5.bayesian import update_all_models, get_posterior_summary, load_posterior_samples
update_all_models()  # re-fit after sync
summary = get_posterior_summary("pd_model")
# summary["mFTP"] = {median, ci_95, prior_influence, months_since_test, recommendation}
```

Add to Question mapping:
```
| How confident is my FTP estimate | get_posterior_summary("pd_model") |
| Update my models | update_all_models() |
```

- [ ] **Step 4: Run full suite + commit**

```bash
git add wko5/api/routes.py wko5/__init__.py
git commit -m "feat: add posterior summary API and exports"
```

---

## Task 4: Integration test — full pipeline

- [ ] **Step 1: End-to-end test**

```python
def test_full_bayesian_pipeline():
    """Full pipeline: fit models → store posteriors → gap analysis with posteriors."""
    from wko5.bayesian import update_all_models, get_posterior_summary, load_posterior_samples
    from wko5.segments import analyze_ride_segments
    from wko5.gap_analysis import gap_analysis

    # Update models
    update_all_models()

    # Check posteriors exist
    summary = get_posterior_summary("pd_model")
    assert "mFTP" in summary
    mftp = summary["mFTP"]
    assert 150 < mftp["median"] < 400
    assert mftp["ci_95"][0] < mftp["median"] < mftp["ci_95"][1]

    # Run gap analysis (should use posteriors)
    ride = analyze_ride_segments(1628)  # 300km ride
    if not ride["segments"]:
        return

    pd_model = {"mFTP": mftp["median"], "FRC": 20, "Pmax": 1100, "TTE": 3600}
    dur_samples = load_posterior_samples("durability")
    dur_params = {"a": 0.5, "b": 0.001, "c": 0.05}
    if dur_samples:
        dur_params = {k: float(np.median(v)) for k, v in dur_samples.items() if k != "sigma"}

    result = gap_analysis(ride["segments"], pd_model, dur_params, n_draws=50)
    assert "overall" in result
    assert isinstance(result["overall"]["probability_of_completion"], float)
```

- [ ] **Step 2: Run and commit**

```bash
pytest tests/test_bayesian.py -v
git add tests/test_bayesian.py
git commit -m "feat: add end-to-end Bayesian pipeline integration test"
git push origin main
```
