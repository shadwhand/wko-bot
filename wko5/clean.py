"""Data cleaning — spike removal, dropout handling, gap filling."""

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

SPIKE_THRESHOLD = 2000  # watts
MAX_FFILL_GAP = 5  # samples


def clean_power(power_series):
    """Clean a power series: remove spikes, handle dropouts.

    - Readings >2000W replaced with interpolated neighbors
    - NaN gaps <=5s forward-filled, longer gaps left as NaN
    - Zeros preserved (coasting)
    """
    s = power_series.copy().astype(float)

    # Spike removal: replace >2000W with NaN, then interpolate
    spike_mask = s > SPIKE_THRESHOLD
    if spike_mask.any():
        logger.info(f"Removing {spike_mask.sum()} power spikes >2000W")
        s[spike_mask] = np.nan
        s = s.interpolate(method="linear", limit_direction="both")

    # Dropout handling: forward-fill NaN gaps up to MAX_FFILL_GAP samples
    # Gaps longer than MAX_FFILL_GAP are left as NaN entirely
    if s.isna().any():
        # Label each NaN with its consecutive run length, then only fill short runs
        na_mask = s.isna()
        # Assign a group ID to each consecutive NaN run
        group = (na_mask != na_mask.shift()).cumsum()
        run_lengths = na_mask.groupby(group).transform("sum")
        # Only forward-fill within short gaps; leave long gaps as NaN
        short_gap_mask = na_mask & (run_lengths <= MAX_FFILL_GAP)
        s_filled = s.ffill(limit=MAX_FFILL_GAP)
        s = s.where(~short_gap_mask, s_filled)

    return s


def clean_records(records_df):
    """Clean a records DataFrame: apply power cleaning and fill timestamp gaps."""
    if records_df.empty:
        return records_df

    df = records_df.copy()

    if "power" in df.columns:
        df["power"] = clean_power(df["power"])

    # Timestamp gap handling: detect gaps >2s, fill <=5s with interpolation
    if "timestamp" in df.columns and len(df) > 1:
        try:
            ts = pd.to_datetime(df["timestamp"])
            gaps = ts.diff().dt.total_seconds()
            for idx in gaps.index:
                gap = gaps[idx]
                if gap is not None and 2 < gap <= 5:
                    for col in ["power", "heart_rate", "cadence", "speed"]:
                        if col in df.columns:
                            loc = df.index.get_loc(idx)
                            if loc > 0:
                                df.loc[idx, col] = (df[col].iloc[loc - 1] + df[col].iloc[loc]) / 2
        except Exception:
            pass  # timestamp parsing issues — skip gap handling

    return df
