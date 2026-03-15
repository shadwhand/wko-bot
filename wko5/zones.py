"""Training zones — Coggan, iLevels, Seiler, HR zones, time-in-zone analysis."""

import logging
import pandas as pd
from wko5.db import get_connection, get_activities, get_records, FTP_DEFAULT

logger = logging.getLogger(__name__)


def coggan_zones(ftp):
    ftp = float(ftp)
    return {
        "Active Recovery": (0, int(ftp * 0.55)),
        "Endurance": (int(ftp * 0.56), int(ftp * 0.75)),
        "Tempo": (int(ftp * 0.76), int(ftp * 0.90)),
        "Threshold": (int(ftp * 0.91), int(ftp * 1.05)),
        "VO2max": (int(ftp * 1.06), int(ftp * 1.20)),
        "Anaerobic": (int(ftp * 1.21), int(ftp * 1.50)),
        "Neuromuscular": (int(ftp * 1.51), 9999),
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
        for name, (low, high) in zones.items():
            if low <= w <= high:
                result[name] += 1
                break
    return result


def ride_distribution(activity_id, zone_system="coggan", ftp=None):
    if ftp is None:
        ftp = FTP_DEFAULT
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
        ftp = FTP_DEFAULT
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
