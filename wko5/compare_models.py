#!/usr/bin/env python3
"""Compare our PD model output against WKO5 ground truth.

Default mode (--mode fit, the reproducible path):
    Runs wko5.pdcurve.fit_pd_model() against an envelope MMP computed from
    the athlete's ride history for the date range WKO5 used. If an FTP test
    is present in the `ftp_tests` table, its ftp_watts and tte_minutes are
    passed as priors (breaks the FRC/TTE degeneracy).

Legacy mode (--mode posterior):
    Reads pre-computed posterior samples from the `posterior_samples` table.
    Only works if a Stan PD model has been fit and stored there.

Usage:
    python3 wko5/compare_models.py                    # default: fit mode, 'current_ui' category
    python3 wko5/compare_models.py current_ui
    python3 wko5/compare_models.py Other --mode posterior
    python3 wko5/compare_models.py current_ui --start 2026-01-01 --end 2026-04-14

Database layout (not currently overridable — see the note on DB paths below):
    wko5/cycling_power.duckdb  -> rides/records, used by compute_envelope_mmp
    wko5/cycling_power.db      -> athlete_config + ftp_tests (SQLite)
Both are expected to be in sync. The CLI does not currently accept an
alternate DB path because the DuckDB + SQLite split would require threading
overrides through wko5.db as well.

FTP-prior causality:
    For historical comparisons (--start/--end before today), the harness
    uses only the most recent FTP test whose test_date is <= end, so a
    2025-03 window is not fit with a September 2025 test result.
"""

import argparse
import json
import os
import struct
import sqlite3
import sys
from pathlib import Path

import numpy as np

# Allow running as a script: add repo root to path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from wko5.pdcurve import compute_envelope_mmp, fit_pd_model, _pd_model  # noqa: E402


# Category → (start_date, end_date) used by WKO5 to compute ground-truth values.
# 'current_ui' matches the UI screenshots taken 2026-04-14.
CATEGORY_DATE_RANGES = {
    "current_ui": ("2026-01-01", "2026-04-14 23:59:59"),
    "Other": ("2026-01-01", "2026-04-14 23:59:59"),
    "All Run": ("2026-01-01", "2026-04-14 23:59:59"),
    "Day Off": ("2026-01-01", "2026-04-14 23:59:59"),
}


def load_wko5_ground_truth():
    """Load WKO5 model metrics extracted from .wko5athlete + UI screenshots."""
    path = Path(__file__).parent / "wko5_ground_truth.json"
    with open(path) as f:
        return json.load(f)


def _default_sqlite_path():
    """Return the canonical SQLite DB path (athlete_config + ftp_tests)."""
    return str(Path(__file__).parent / "cycling_power.db")


def load_athlete_config(db_path=None):
    """Load athlete config (weight, ftp, etc.) from the SQLite companion DB."""
    db_path = db_path or _default_sqlite_path()
    conn = sqlite3.connect(str(db_path))
    cols = [d[0] for d in conn.execute("SELECT * FROM athlete_config LIMIT 1").description]
    row = conn.execute("SELECT * FROM athlete_config LIMIT 1").fetchone()
    conn.close()
    return dict(zip(cols, row))


def load_latest_ftp_test(db_path=None, as_of=None):
    """Return (ftp_watts, tte_minutes, test_date) from the most recent FTP test.

    If `as_of` (ISO date string or date-time) is provided, restricts to tests
    with test_date <= as_of. This prevents leaking future priors into
    historical comparisons.
    """
    db_path = db_path or _default_sqlite_path()
    conn = sqlite3.connect(str(db_path))
    if as_of:
        as_of_date = str(as_of)[:10]  # truncate to YYYY-MM-DD
        row = conn.execute(
            "SELECT ftp_watts, tte_minutes, test_date FROM ftp_tests "
            "WHERE test_date <= ? "
            "ORDER BY test_date DESC LIMIT 1",
            (as_of_date,),
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT ftp_watts, tte_minutes, test_date FROM ftp_tests "
            "ORDER BY test_date DESC LIMIT 1"
        ).fetchone()
    conn.close()
    if row and row[0]:
        return float(row[0]), float(row[1]) if row[1] else None, row[2]
    return None


def load_pd_posterior_samples(db_path=None):
    """Load posterior samples from the Stan pd_model (legacy comparison path)."""
    db_path = db_path or _default_sqlite_path()
    conn = sqlite3.connect(str(db_path))
    params = {}
    for row in conn.execute(
        "SELECT param_name, samples FROM posterior_samples "
        "WHERE model_type='pd_model' ORDER BY fitted_at DESC"
    ):
        pname, blob = row
        n = len(blob) // 8
        vals = [struct.unpack('<d', blob[i*8:(i+1)*8])[0] for i in range(n)]
        params[pname.lower()] = np.array(vals)
    conn.close()
    return params


def derive_metrics_from_fit(model, mmp, weight_kg):
    """Convert fit_pd_model() output dict into WKO5-comparable metric values.

    fit_pd_model returns {Pmax, FRC (kJ), mFTP, TTE (min), tau, tau2, a, ...}.
    WKO5 stores FRC in joules and TTE in seconds, so we convert.
    """
    frc_kj = model["FRC"]
    mftp = model["mFTP"]
    tau = model["tau"]
    tau2 = model["tau2"]
    tte_s = model["TTE"] * 60.0
    a = model["a"]

    p3600 = float(_pd_model(3600.0, frc_kj, mftp, tau, tau2, tte_s, a))
    p300 = float(_pd_model(300.0, frc_kj, mftp, tau, tau2, tte_s, a))

    return {
        "pmax": model["Pmax"],
        "mftp": mftp,
        "frc": frc_kj * 1000.0,       # kJ → J
        "tte": tte_s,                  # min → s
        "stamina": p3600 / mftp,
        "vo2maxkg": model.get("mVO2max_ml_min_kg", 10.8 * p300 / weight_kg + 7),
        "fvo2max": p300,
    }


def derive_metrics_from_posterior(params, weight_kg):
    """Legacy: derive metrics from Stan posterior samples (pd_model)."""
    required = {"pmax", "mftp", "frc", "tau"}
    if not required <= set(params.keys()):
        return None

    pmax = params["pmax"]
    mftp = params["mftp"]
    frc_kj = params["frc"]
    tau = params["tau"]

    # Simple PT model (no tau2/TTE/decline) — legacy path, less accurate
    def pt(t, pm, mf, fj, tu):
        return pm * np.exp(-t / tu) + mf + (fj * 1000 / t) * (1 - np.exp(-t / tu))

    p3600 = pt(3600, pmax, mftp, frc_kj, tau)
    p300 = pt(300, pmax, mftp, frc_kj, tau)

    return {
        "pmax": (np.median(pmax), np.percentile(pmax, 5), np.percentile(pmax, 95)),
        "mftp": (np.median(mftp), np.percentile(mftp, 5), np.percentile(mftp, 95)),
        "frc": (np.median(frc_kj * 1000), np.percentile(frc_kj * 1000, 5), np.percentile(frc_kj * 1000, 95)),
        "stamina": (np.median(p3600 / mftp), np.percentile(p3600 / mftp, 5), np.percentile(p3600 / mftp, 95)),
        "fvo2max": (np.median(p300), np.percentile(p300, 5), np.percentile(p300, 95)),
        "vo2maxkg": (np.median(10.8 * p300 / weight_kg + 7),) * 3,
    }


def print_comparison(category, wko5_vals, our_vals, mode):
    """Render the side-by-side comparison table."""
    print("=" * 70)
    print(f"Mode: {mode}    Category: {category}")
    print("=" * 70)
    print(f"{'Metric':<12} {'WKO5':>12} {'Ours':>14} {'Delta':>8} {'Grade':>6}")
    print("-" * 55)

    for metric in ["pmax", "mftp", "frc", "tte", "fvo2max", "stamina", "vo2maxkg"]:
        if metric not in wko5_vals or metric not in our_vals:
            continue

        w = wko5_vals[metric]

        # Posterior mode returns tuples (median, lo, hi); fit mode returns scalars
        if isinstance(our_vals[metric], tuple):
            o = our_vals[metric][0]
        else:
            o = our_vals[metric]

        unit = ""
        if metric in ("pmax", "mftp", "fvo2max"):
            unit = "W"
        elif metric == "frc":
            unit = "J"
        elif metric == "tte":
            unit = "s"
        elif metric == "vo2maxkg":
            unit = ""

        delta_pct = (o - w) / w * 100 if w else 0
        grade = "✓" if abs(delta_pct) < 5 else "~" if abs(delta_pct) < 15 else "✗"
        print(f"  {metric:<10} {w:>11.1f}{unit} {o:>13.1f}{unit} {delta_pct:>+7.1f}% {grade:>6}")

    print("=" * 70)


def compare_fit_mode(category, start, end):
    """Primary reproducible path: fit PD model from MMP and compare with WKO5."""
    gt = load_wko5_ground_truth()
    wko5 = gt["categories"].get(category)
    if not wko5:
        print(f"No WKO5 ground truth for category '{category}'")
        print(f"Available: {list(gt['categories'].keys())}")
        return

    config = load_athlete_config()
    weight_kg = config["weight_kg"]
    ftp_manual = config.get("ftp_manual")

    # Causal FTP prior: only use tests whose date <= end of comparison window.
    # Prevents leaking future FTP/TTE into historical backtests.
    test = load_latest_ftp_test(as_of=end)
    if test:
        ftp_prior, tte_prior, test_date = test
        print(f"Using FTP test from {test_date} (as_of {end[:10]}): "
              f"FTP={ftp_prior}W, TTE={tte_prior}min")
    else:
        ftp_prior = ftp_manual
        tte_prior = None
        print(f"No FTP test on or before {end[:10]}; "
              f"using ftp_manual={ftp_prior}W (no TTE prior)")

    print(f"Athlete: weight={weight_kg}kg")
    print(f"MMP envelope: {start} to {end}")

    mmp = compute_envelope_mmp(start=start, end=end)
    if len(mmp) < 60:
        print(f"Insufficient MMP data ({len(mmp)}s) — need at least 60 seconds.")
        return

    print(f"MMP: {len(mmp)} durations, 1s={mmp[0]:.0f}W, 60min={mmp[3599] if len(mmp) >= 3600 else 'N/A'}")

    model = fit_pd_model(mmp, ftp_prior=ftp_prior, tte_prior=tte_prior)
    if model is None:
        print("PD model fit failed.")
        return

    print(f"\nFitted: Pmax={model['Pmax']:.0f}W FRC={model['FRC']:.1f}kJ "
          f"mFTP={model['mFTP']:.0f}W tau={model['tau']:.1f}s "
          f"tau2={model['tau2']:.0f}s TTE={model['TTE']:.1f}min a={model['a']:.1f}")

    our_vals = derive_metrics_from_fit(model, mmp, weight_kg)
    print()
    print_comparison(category, wko5, our_vals, mode="fit")

    print(f"\nNotes for category '{category}': {gt['notes'].get(category, '—')}")


def compare_posterior_mode(category):
    """Legacy path: compare against stored Stan posterior samples."""
    gt = load_wko5_ground_truth()
    wko5 = gt["categories"].get(category)
    if not wko5:
        print(f"No WKO5 ground truth for category '{category}'")
        return

    config = load_athlete_config()
    params = load_pd_posterior_samples()

    if not params:
        print("No pd_model posterior samples in DB.")
        print("Hint: fit the Stan pd_model first, or use the default --mode fit.")
        return

    our_vals = derive_metrics_from_posterior(params, config["weight_kg"])
    if our_vals is None:
        print(f"Posterior samples missing required params. Found: {list(params.keys())}")
        return

    print_comparison(category, wko5, our_vals, mode="posterior (legacy)")


def main():
    parser = argparse.ArgumentParser(description="Compare our PD model output against WKO5.")
    parser.add_argument("category", nargs="?", default="current_ui",
                        help="Ground-truth category (default: current_ui)")
    parser.add_argument("--mode", choices=["fit", "posterior"], default="fit",
                        help="fit (default): run fit_pd_model on MMP. "
                             "posterior: read Stan posterior samples (legacy).")
    parser.add_argument("--start", default=None, help="MMP envelope start date (YYYY-MM-DD)")
    parser.add_argument("--end", default=None, help="MMP envelope end date")
    args = parser.parse_args()

    # NOTE: --db was considered but removed. The rides DB (DuckDB) and the
    # config DB (SQLite) live in separate files under wko5/, and threading
    # an override through both paths (compute_envelope_mmp -> wko5.db +
    # load_athlete_config/load_latest_ftp_test) is more surgery than this
    # harness warrants. Both files are expected at their canonical paths.

    if args.mode == "fit":
        start = args.start
        end = args.end
        if not start or not end:
            rng = CATEGORY_DATE_RANGES.get(args.category)
            if rng is None:
                print(f"No default date range for category '{args.category}'. "
                      f"Provide --start and --end.")
                sys.exit(1)
            start, end = rng
        compare_fit_mode(args.category, start, end)
    else:
        compare_posterior_mode(args.category)


if __name__ == "__main__":
    main()
