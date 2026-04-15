#!/usr/bin/env python3
"""Compare our PD model output against WKO5 ground truth.

Loads WKO5's model metrics from wko5_ground_truth.json and compares
against our Bayesian PD model fitted parameters.

Usage:
    python3 wko5/compare_models.py
    python3 wko5/compare_models.py --category Other   # cycling aggregate
"""

import json
import struct
import sqlite3
import numpy as np
from pathlib import Path


def load_wko5_ground_truth():
    """Load WKO5 model metrics extracted from .wko5athlete file."""
    path = Path(__file__).parent / "wko5_ground_truth.json"
    with open(path) as f:
        return json.load(f)


def load_our_model(db_path=None):
    """Load our Bayesian PD model posterior samples."""
    if db_path is None:
        db_path = Path(__file__).parent / "cycling_power.db"

    conn = sqlite3.connect(str(db_path))

    # Athlete config
    cols = [d[0] for d in conn.execute("SELECT * FROM athlete_config LIMIT 1").description]
    row = conn.execute("SELECT * FROM athlete_config LIMIT 1").fetchone()
    config = dict(zip(cols, row))

    # Posterior samples from PD model (Peronnet-Thibault: Pmax, FRC, mFTP, tau)
    params = {}
    for row in conn.execute(
        "SELECT param_name, samples FROM posterior_samples "
        "WHERE model_type='pd_model' ORDER BY fitted_at DESC"
    ):
        pname, blob = row
        n = len(blob) // 8
        vals = [struct.unpack('<d', blob[i*8:(i+1)*8])[0] for i in range(n)]
        params[pname] = np.array(vals)

    conn.close()
    return config, params


def peronnet_thibault_power(t, pmax, mftp, frc, tau):
    """Peronnet-Thibault / WKO4 power-duration model.

    P(t) = pmax * exp(-t/tau) + mftp + frc/t * (1 - exp(-t/tau))

    For t in seconds, returns power in watts.
    """
    exp_term = np.exp(-t / tau)
    return pmax * exp_term + mftp + (frc / t) * (1 - exp_term)


def derive_metrics_from_posterior(params, weight_kg):
    """Derive WKO5-equivalent metrics from our model parameters.

    Our durability model uses params: a, b, c, sigma
    These map to the Peronnet-Thibault model differently depending
    on the parameterization.

    Returns dict with median and 90% CI for each metric.
    """
    # Check what parameters we have
    if not params:
        return None

    available = set(params.keys())
    print(f"  Available posterior params: {available}")

    # Map parameter names (DB may use uppercase from Stan model)
    param_map = {}
    for key in available:
        param_map[key.lower()] = params[key]

    if {'pmax', 'mftp', 'frc', 'tau'} <= set(param_map.keys()) or \
       {'Pmax', 'mFTP', 'FRC', 'tau'} <= available:
        pmax = param_map.get('pmax', params.get('Pmax'))
        mftp = param_map.get('mftp', params.get('mFTP'))
        frc = param_map.get('frc', params.get('FRC'))
        tau = param_map.get('tau', params.get('tau'))
    elif {'a', 'b', 'c'} <= set(param_map.keys()):
        # Our durability model parameterization
        # Need to know the mapping from a,b,c to pmax,mftp,frc,tau
        # This depends on our Stan model definition
        print("  Note: a,b,c params — need Stan model mapping")
        a = params['a']
        b = params['b']
        c = params['c']
        # TODO: implement the actual mapping from our Stan model
        # For now, report raw params
        return {
            'raw_params': {
                'a': (np.median(a), np.percentile(a, 5), np.percentile(a, 95)),
                'b': (np.median(b), np.percentile(b, 5), np.percentile(b, 95)),
                'c': (np.median(c), np.percentile(c, 5), np.percentile(c, 95)),
            }
        }
    else:
        print(f"  Unknown parameter set: {available}")
        return None

    # Derive WKO5-equivalent metrics
    metrics = {}

    # mFTP — directly from model
    metrics['mftp'] = (np.median(mftp), np.percentile(mftp, 5), np.percentile(mftp, 95))

    # Pmax — directly from model
    metrics['pmax'] = (np.median(pmax), np.percentile(pmax, 5), np.percentile(pmax, 95))

    # FRC — our Stan model stores in kJ, WKO5 stores in joules
    frc_j = frc * 1000  # kJ → J
    metrics['frc'] = (np.median(frc_j), np.percentile(frc_j, 5), np.percentile(frc_j, 95))

    # TTE — time to exhaustion at FTP
    # TTE = time where P(t) first drops to mFTP on the PD curve
    # Approximate: solve pmax*exp(-t/tau) + frc/t*(1-exp(-t/tau)) ≈ 0
    # In practice, TTE ≈ frc / (threshold_power - mftp) for W'-based models
    # Or compute numerically
    tte_samples = []
    for i in range(len(mftp)):
        t_range = np.arange(60, 7200, 1)
        power = peronnet_thibault_power(t_range, pmax[i], mftp[i], frc_j[i], tau[i])
        # TTE is where power first drops below mFTP
        below = np.where(power <= mftp[i])[0]
        tte_samples.append(t_range[below[0]] if len(below) > 0 else 7200)
    tte_arr = np.array(tte_samples)
    metrics['tte'] = (np.median(tte_arr), np.percentile(tte_arr, 5), np.percentile(tte_arr, 95))

    # Stamina — ratio of 60min power to FTP
    # stamina = P(3600) / mFTP
    stam = peronnet_thibault_power(3600, pmax, mftp, frc_j, tau) / mftp
    metrics['stamina'] = (np.median(stam), np.percentile(stam, 5), np.percentile(stam, 95))

    # VO2max — estimated from power
    # WKO5 formula: vo2max(meanmax(power)) / weight * 1000
    # Rough: VO2max ≈ (P_5min * 10.8 + 7 * weight) / weight
    # Or: VO2max ≈ P_5min / weight * some_factor
    p5min = peronnet_thibault_power(300, pmax, mftp, frc_j, tau)
    # Using Hawley & Noakes (1992): VO2max = 10.8 * P/W + 7
    vo2 = (10.8 * p5min / weight_kg + 7)
    metrics['vo2maxkg'] = (np.median(vo2), np.percentile(vo2, 5), np.percentile(vo2, 95))

    return metrics


def compare(category="Other"):
    """Run the comparison."""
    gt = load_wko5_ground_truth()
    config, params = load_our_model()

    wko5 = gt["categories"].get(category, {})
    if not wko5:
        print(f"No WKO5 data for category '{category}'")
        print(f"Available: {list(gt['categories'].keys())}")
        return

    print(f"Weight: {config['weight_kg']} kg")
    print(f"Manual FTP: {config['ftp_manual']} W")
    print()

    our = derive_metrics_from_posterior(params, config['weight_kg'])

    print()
    print("=" * 72)
    print(f"{'Metric':<12} {'WKO5':>12} {'Ours (median)':>14} {'Delta':>8} {'90% CI':>20}")
    print("=" * 72)

    if our and 'raw_params' in our:
        # Can't compare directly — different parameterization
        for metric in ['mftp', 'pmax', 'frc', 'stamina', 'tte', 'vo2maxkg']:
            wval = wko5.get(metric, 0)
            unit = 'W' if metric in ('mftp', 'pmax') else 'J' if metric == 'frc' else 's' if metric == 'tte' else ''
            print(f"  {metric:<10} {wval:>11.1f}{unit} {'—':>14} {'—':>8} {'need PT params':>20}")
        print()
        print("Raw model params (a, b, c parameterization):")
        for p, (med, lo, hi) in our['raw_params'].items():
            print(f"  {p}: {med:.4f} [{lo:.4f}, {hi:.4f}]")
        print()
        print("ACTION: Map a,b,c → Pmax,mFTP,FRC,tau to enable comparison.")
        print("Check wko5/stan_models/ for the parameterization.")
    elif our:
        for metric in ['mftp', 'pmax', 'frc', 'stamina', 'tte', 'vo2maxkg']:
            wval = wko5.get(metric, 0)
            if metric in our:
                med, lo, hi = our[metric]
                delta_pct = (med - wval) / wval * 100 if wval else 0
                unit = 'W' if metric in ('mftp', 'pmax') else 'J' if metric == 'frc' else 's' if metric == 'tte' else ''
                print(f"  {metric:<10} {wval:>11.1f}{unit} {med:>13.1f}{unit} {delta_pct:>+7.1f}% [{lo:.0f}-{hi:.0f}]")
            else:
                print(f"  {metric:<10} {wval:>11.1f} {'—':>14}")
    else:
        print("No model parameters found in DB.")
        print("Run the Stan PD model first, then re-run this comparison.")

    print("=" * 72)
    print(f"\nWKO5 category: '{category}' — {gt['notes'].get(category, '')}")


if __name__ == "__main__":
    import sys
    category = "Other"
    for arg in sys.argv[1:]:
        if arg.startswith("--category"):
            category = sys.argv[sys.argv.index(arg) + 1]
        elif not arg.startswith("--"):
            category = arg
    compare(category)
