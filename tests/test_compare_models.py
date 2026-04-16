"""Regression test for wko5/compare_models.py default fit-mode path.

Guards against the failure mode flagged in the 2026-04-16 review: the doc
claiming "<2% vs WKO5" while the harness pointed at a stale code path that
reported -60% deltas. This test verifies that the reproducible command

    python3 wko5/compare_models.py current_ui

actually produces the parameter-level agreement documented in
docs/research/wko5-reverse.md.

Determinism: fit_pd_model uses scipy.optimize.differential_evolution with
seed=42 (see wko5/pdcurve.py), so repeated runs on the same DB produce
identical results.
"""
import json
import sqlite3
import sys
import os

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from wko5.compare_models import (
    compare_fit_mode,
    derive_metrics_from_fit,
    load_athlete_config,
    load_latest_ftp_test,
    load_wko5_ground_truth,
)
from wko5.pdcurve import compute_envelope_mmp, fit_pd_model


# WKO5 screenshot range (from docs/research/wko5-reverse.md)
WKO5_START = "2026-01-01"
WKO5_END = "2026-04-14 23:59:59"


def _has_mmp_data():
    """Check if the test DB has enough activity data for the WKO5 window."""
    try:
        mmp = compute_envelope_mmp(start=WKO5_START, end=WKO5_END)
        return len(mmp) >= 3600
    except Exception:
        return False


needs_mmp = pytest.mark.skipif(
    not _has_mmp_data(),
    reason="No MMP data in DB for the WKO5 2026-01-01..2026-04-14 window",
)


def test_ftp_test_lookup_is_causal():
    """Historical windows must not be fit with future FTP test priors.

    Per the DB at time of writing, FTP tests exist on 2024-12-07, 2025-03-22,
    2025-07-07, and 2025-09-26. A window ending 2025-04-01 must not pull in
    the September 2025 test.
    """
    # Window ending before the Sept 2025 test — should pick the March 2025 test
    test = load_latest_ftp_test(as_of="2025-04-01")
    assert test is not None
    _ftp, _tte, date = test
    assert date <= "2025-04-01", (
        f"Causality violation: got FTP test dated {date} for as_of=2025-04-01"
    )

    # Window ending before any FTP test at all — returns None
    test = load_latest_ftp_test(as_of="2024-01-01")
    assert test is None


def test_ground_truth_json_has_current_ui_category():
    """The JSON fixture must expose the category used by the default harness run."""
    gt = load_wko5_ground_truth()
    assert "current_ui" in gt["categories"], (
        "wko5_ground_truth.json must expose 'current_ui' — this is the "
        "default category in compare_models.py"
    )
    ui = gt["categories"]["current_ui"]
    # Sanity-check the ground truth values haven't been mangled
    assert 1200 < ui["pmax"] < 1400
    assert 250 < ui["mftp"] < 350
    assert 1800 < ui["tte"] < 2200
    assert 8000 < ui["frc"] < 15000


@needs_mmp
def test_fit_mode_reproduces_wko5_agreement():
    """The default --mode fit path must match WKO5 within documented tolerances.

    Tolerances are loose enough to absorb small changes in the ride corpus but
    tight enough to catch regressions back to the -60% stale-posterior path.
    """
    gt = load_wko5_ground_truth()
    wko5 = gt["categories"]["current_ui"]

    config = load_athlete_config()
    test = load_latest_ftp_test(as_of=WKO5_END)
    assert test is not None, (
        "DB must contain at least one row in ftp_tests for this regression "
        "test to reproduce the documented fit. Seed with a known FTP test "
        "or mark this test xfail."
    )
    ftp_prior, tte_prior, _ = test

    mmp = compute_envelope_mmp(start=WKO5_START, end=WKO5_END)
    model = fit_pd_model(mmp, ftp_prior=ftp_prior, tte_prior=tte_prior)
    assert model is not None, "fit_pd_model returned None"

    ours = derive_metrics_from_fit(model, mmp, config["weight_kg"])

    def pct(o, w):
        return abs(o - w) / w * 100

    # Core parameter-level claims from the doc (within 5%)
    assert pct(ours["pmax"], wko5["pmax"]) < 5, (
        f"Pmax drift: ours={ours['pmax']:.0f} vs WKO5={wko5['pmax']:.0f} "
        f"({pct(ours['pmax'], wko5['pmax']):.1f}% off)"
    )
    assert pct(ours["mftp"], wko5["mftp"]) < 5, (
        f"mFTP drift: ours={ours['mftp']:.0f} vs WKO5={wko5['mftp']:.0f} "
        f"({pct(ours['mftp'], wko5['mftp']):.1f}% off)"
    )
    assert pct(ours["tte"], wko5["tte"]) < 10, (
        f"TTE drift: ours={ours['tte']:.0f} vs WKO5={wko5['tte']:.0f} "
        f"({pct(ours['tte'], wko5['tte']):.1f}% off)"
    )


@needs_mmp
def test_fit_mode_frc_gap_is_bounded():
    """FRC/stamina have a known degeneracy; guard that it stays within documented bounds.

    If this test starts passing with a much tighter tolerance, great — but then
    the doc needs updating. If it starts failing wider, something regressed in
    the fitter's Pmax/FRC handling.
    """
    gt = load_wko5_ground_truth()
    wko5 = gt["categories"]["current_ui"]

    config = load_athlete_config()
    ftp_prior, tte_prior, _ = load_latest_ftp_test(as_of=WKO5_END)

    mmp = compute_envelope_mmp(start=WKO5_START, end=WKO5_END)
    model = fit_pd_model(mmp, ftp_prior=ftp_prior, tte_prior=tte_prior)
    ours = derive_metrics_from_fit(model, mmp, config["weight_kg"])

    frc_pct = abs(ours["frc"] - wko5["frc"]) / wko5["frc"] * 100
    # Known ~25% gap; fail if it blows past 40% (something other than the
    # tau/FRC degeneracy is going on) or drops below 5% without doc update.
    assert 5 < frc_pct < 40, (
        f"FRC gap {frc_pct:.1f}% outside expected band. If much smaller, the "
        f"degeneracy resolved (update docs). If much larger, the fitter regressed."
    )
