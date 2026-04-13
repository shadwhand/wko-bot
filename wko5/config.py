"""Athlete configuration — single-row config table replacing hardcoded constants."""

import logging
from wko5.db import get_connection

logger = logging.getLogger(__name__)

DEFAULTS = {
    "name": "default",
    "sex": "male",
    "weight_kg": 78.0,
    "max_hr": 186,
    "lthr": None,
    "ftp_manual": 292,
    "bike_weight_kg": 9.0,
    "cda": 0.35,
    "crr": 0.005,
    "pd_pmax_low": 800,
    "pd_pmax_high": 2500,
    "pd_mftp_low": 150,
    "pd_mftp_high": 400,
    "pd_frc_low": 5,
    "pd_frc_high": 30,
    "pd_tau_low": 5,
    "pd_tau_high": 30,
    "pd_t0_low": 1,
    "pd_t0_high": 15,
    "spike_threshold_watts": 2000,
    "resting_hr_baseline": None,
    "hrv_baseline": None,
    "resting_hr_alert_delta": 5,
    "ctl_ramp_rate_yellow": 7,
    "ctl_ramp_rate_red": 10,
    "tsb_floor_alert": -30,
    "collapse_kj_threshold": None,
    "intensity_ceiling_if": 0.70,
    "fueling_rate_g_hr": 75,
    "energy_deficit_alert_kcal": 3000,
    "ctl_time_constant": 42,
    "atl_time_constant": 7,
}

_config_cache = None


def init_config_table():
    conn = get_connection()
    columns = ", ".join(f"{k} REAL" if isinstance(v, (int, float)) and v is not None
                        else f"{k} TEXT" if isinstance(v, str)
                        else f"{k} REAL"
                        for k, v in DEFAULTS.items())
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS athlete_config (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            {columns}
        )
    """)
    result = conn.execute("SELECT COUNT(*) FROM athlete_config")
    if result.fetchone()[0] == 0:
        cols = ", ".join(DEFAULTS.keys())
        placeholders = ", ".join("?" for _ in DEFAULTS)
        conn.execute(
            f"INSERT INTO athlete_config (id, {cols}) VALUES (1, {placeholders})",
            list(DEFAULTS.values()),
        )
    conn.commit()
    conn.close()
    global _config_cache
    _config_cache = None


def get_config():
    global _config_cache
    if _config_cache is not None:
        return _config_cache.copy()

    conn = get_connection()
    try:
        result = conn.execute("SELECT * FROM athlete_config WHERE id = 1")
        row = result.fetchone()
        if row is None:
            conn.close()
            init_config_table()
            return get_config()
        columns = [d[0] for d in result.description]
        _config_cache = dict(zip(columns, row))
    except Exception:
        conn.close()
        init_config_table()
        return get_config()
    conn.close()
    return _config_cache.copy()


def set_config(key, value):
    if key not in DEFAULTS and key != "id":
        raise ValueError(f"Unknown config key: {key}")
    conn = get_connection()
    init_config_table()
    conn.execute(f"UPDATE athlete_config SET {key} = ? WHERE id = 1", (value,))
    conn.commit()
    conn.close()
    global _config_cache
    _config_cache = None
