# tests/test_physics.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from wko5.physics import power_required, speed_from_power, air_density


def test_power_flat_no_wind():
    """Power on flat at 30 km/h should be ~150-200W for a road cyclist."""
    v = 30 / 3.6  # m/s
    p = power_required(speed=v, grade=0, weight_rider=78, weight_bike=9, cda=0.35, crr=0.005)
    assert 100 < p < 250, f"Power={p:.0f}W on flat at 30km/h outside expected range"


def test_power_climbing():
    """Power climbing 8% at 10 km/h should be ~250-350W."""
    v = 10 / 3.6
    p = power_required(speed=v, grade=0.08, weight_rider=78, weight_bike=9, cda=0.35, crr=0.005)
    assert 200 < p < 400, f"Power={p:.0f}W climbing 8% at 10km/h outside expected range"


def test_power_descending_negative():
    """Descending steep grade at speed should require near-zero or negative power."""
    v = 50 / 3.6
    p = power_required(speed=v, grade=-0.08, weight_rider=78, weight_bike=9, cda=0.35, crr=0.005)
    assert p < 50, f"Power={p:.0f}W descending 8% should be near zero"


def test_power_increases_with_speed():
    """Power should increase with speed on flat (cubic relationship)."""
    p1 = power_required(speed=20/3.6, grade=0, weight_rider=78, weight_bike=9, cda=0.35, crr=0.005)
    p2 = power_required(speed=40/3.6, grade=0, weight_rider=78, weight_bike=9, cda=0.35, crr=0.005)
    assert p2 > p1 * 3, "Power at 40km/h should be >3x power at 20km/h (cubic)"


def test_power_increases_with_grade():
    """Power should increase linearly with grade at low speed."""
    p1 = power_required(speed=15/3.6, grade=0.04, weight_rider=78, weight_bike=9, cda=0.35, crr=0.005)
    p2 = power_required(speed=15/3.6, grade=0.08, weight_rider=78, weight_bike=9, cda=0.35, crr=0.005)
    assert p2 > p1 * 1.5, "Power at 8% should be significantly more than at 4%"


def test_speed_from_power_roundtrip():
    """speed_from_power should be inverse of power_required on flat."""
    target_power = 200
    v = speed_from_power(power=target_power, grade=0, weight_rider=78, weight_bike=9, cda=0.35, crr=0.005)
    p_check = power_required(speed=v, grade=0, weight_rider=78, weight_bike=9, cda=0.35, crr=0.005)
    assert abs(p_check - target_power) < 1.0, f"Roundtrip error: {p_check:.1f} vs {target_power}"


def test_speed_from_power_climbing():
    """Speed from power on a climb should be reasonable."""
    v = speed_from_power(power=280, grade=0.06, weight_rider=78, weight_bike=9, cda=0.35, crr=0.005)
    v_kmh = v * 3.6
    assert 10 < v_kmh < 20, f"Speed={v_kmh:.1f}km/h on 6% at 280W outside expected range"


def test_air_density_sea_level():
    """Air density at sea level, 20C should be ~1.2 kg/m3."""
    rho = air_density(temperature_c=20, altitude_m=0)
    assert 1.15 < rho < 1.25


def test_air_density_altitude():
    """Air density decreases with altitude."""
    rho_sea = air_density(temperature_c=20, altitude_m=0)
    rho_high = air_density(temperature_c=20, altitude_m=2000)
    assert rho_high < rho_sea * 0.85
