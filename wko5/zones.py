"""Training zones — Coggan, iLevels, Seiler, HR zones, time-in-zone analysis."""

import logging
import pandas as pd
from wko5.db import get_connection, get_activities, get_records, FTP_DEFAULT
from wko5.config import get_config

logger = logging.getLogger(__name__)


def coggan_zones(ftp):
    ftp = float(ftp)
    return {
        "Active Recovery": {"power": (0, int(ftp * 0.55)), "rpe": "1-2/10"},
        "Endurance": {"power": (int(ftp * 0.56), int(ftp * 0.75)), "rpe": "2-3/10"},
        "Tempo": {"power": (int(ftp * 0.76), int(ftp * 0.90)), "rpe": "4-5/10"},
        "Threshold": {"power": (int(ftp * 0.91), int(ftp * 1.05)), "rpe": "7-8/10"},
        "VO2max": {"power": (int(ftp * 1.06), int(ftp * 1.20)), "rpe": "9-9.5/10"},
        "Anaerobic": {"power": (int(ftp * 1.21), int(ftp * 1.50)), "rpe": "10/10"},
        "Neuromuscular": {"power": (int(ftp * 1.51), 9999), "rpe": "max"},
    }


def ilevels(pd_model):
    mftp = pd_model["mFTP"]
    frc = pd_model["FRC"]
    frc_3min = frc * 1000 / 180
    frc_30s = frc * 1000 / 30
    return {
        "Recovery": (0, int(mftp * 0.55)),
        "Endurance": (int(mftp * 0.55), int(mftp * 0.76)),
        "Tempo": (int(mftp * 0.76), int(mftp * 0.90)),
        "Threshold": (int(mftp * 0.90), int(mftp)),
        "VO2max": (int(mftp), int(mftp + frc_3min * 0.15)),
        "Anaerobic": (int(mftp + frc_3min * 0.15), int(mftp + frc_30s * 0.50)),
        "Neuromuscular": (int(mftp + frc_30s * 0.50), 9999),
    }


def seiler_zones(ftp):
    ftp = float(ftp)
    return {
        "Zone 1": (0, int(ftp * 0.80)),
        "Zone 2": (int(ftp * 0.80) + 1, int(ftp)),
        "Zone 3": (int(ftp) + 1, 9999),
    }


def hr_zones(max_hr, lthr):
    return {
        "Zone 1": (0, int(max_hr * 0.68)),
        "Zone 2": (int(max_hr * 0.69), int(max_hr * 0.83)),
        "Zone 3": (int(max_hr * 0.84), int(max_hr * 0.94)),
        "Zone 4": (int(max_hr * 0.95), int(lthr * 1.05)),
        "Zone 5": (int(lthr * 1.05) + 1, 9999),
    }


def time_in_zones(power_series, zones):
    power = power_series.fillna(0).values
    result = {name: 0 for name in zones}
    for w in power:
        for name, data in zones.items():
            low, high = data["power"] if isinstance(data, dict) else data
            if low <= w <= high:
                result[name] += 1
                break
    return result


def ride_distribution(activity_id, zone_system="coggan", ftp=None):
    if ftp is None:
        ftp = get_config()["ftp_manual"]
    records = get_records(activity_id)
    if records.empty:
        return {}
    if zone_system == "coggan":
        zones = coggan_zones(ftp)
    elif zone_system == "seiler":
        zones = seiler_zones(ftp)
    else:
        zones = coggan_zones(ftp)
    return time_in_zones(records["power"], zones)


def period_distribution(start, end, zone_system="coggan", ftp=None):
    if ftp is None:
        ftp = get_config()["ftp_manual"]
    activities = get_activities(start=start, end=end)
    if activities.empty:
        return {}
    if zone_system == "coggan":
        zones = coggan_zones(ftp)
    elif zone_system == "seiler":
        zones = seiler_zones(ftp)
    else:
        zones = coggan_zones(ftp)
    total = {name: 0 for name in zones}
    for _, act in activities.iterrows():
        records = get_records(act["id"])
        if not records.empty:
            tiz = time_in_zones(records["power"], zones)
            for name in total:
                total[name] += tiz.get(name, 0)
    return total


def sweet_spot_band(ftp):
    """Return (low, high) power for sweet spot band (~88-93% FTP).

    Source: TMT-44 — sweet spot TTE is a key fitness marker.
    Ranges: untrained 40-60 min, trained 90-120 min, elite 180+ min.
    """
    return (int(ftp * 0.88), int(ftp * 0.93))


def validate_endurance_rides(days_back=90, ftp=None):
    """Check if endurance rides are actually easy enough.

    Flags rides >1.5h with IF > 0.65.
    Source: TMT-69 — endurance target IF 0.50-0.65.
    """
    if ftp is None:
        ftp = get_config().get("ftp") or FTP_DEFAULT

    activities = get_activities()
    cutoff = (pd.Timestamp.now() - pd.Timedelta(days=days_back)).strftime("%Y-%m-%d")
    recent = activities[
        (activities["start_time"] >= cutoff) &
        (activities["total_timer_time"] > 5400)  # > 1.5 hours
    ]

    flagged = []
    for _, act in recent.iterrows():
        np_val = act.get("normalized_power")
        if np_val and ftp > 0:
            ride_if = np_val / ftp
            if ride_if > 0.65:
                flagged.append({
                    "activity_id": act.get("id"),
                    "date": str(act.get("start_time", ""))[:10],
                    "if_value": round(ride_if, 3),
                    "duration_h": round(act.get("total_timer_time", 0) / 3600, 1),
                })

    return flagged if flagged else None
