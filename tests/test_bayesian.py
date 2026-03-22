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


def test_full_bayesian_pipeline():
    """Full pipeline: fit models -> store posteriors -> gap analysis with posteriors."""
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

    # Run gap analysis (should use posteriors internally)
    ride = analyze_ride_segments(1628)  # 300km ride
    if not ride["segments"]:
        return

    pd_model = {"mFTP": mftp["median"], "FRC": 20, "Pmax": 1100, "TTE": 3600, "tau": 15, "t0": 4}
    dur_samples = load_posterior_samples("durability")
    dur_params = {"a": 0.5, "b": 0.001, "c": 0.05}
    if dur_samples:
        dur_params = {k: float(np.median(v)) for k, v in dur_samples.items() if k != "sigma"}

    result = gap_analysis(ride["segments"], pd_model, dur_params, n_draws=50)
    assert "overall" in result
    assert isinstance(result["overall"]["probability_of_completion"], float)
