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
    fitted_at TEXT NOT NULL DEFAULT (current_timestamp),
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
    result = conn.execute(
        "SELECT param_name, n_samples, samples FROM posterior_samples WHERE model_type = ?",
        [model_type]
    )
    rows = result.fetchall()
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
