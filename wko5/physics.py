# wko5/physics.py
"""Cycling power equation and related physics calculations."""

import numpy as np
from scipy.optimize import brentq

# Standard gravitational acceleration
G = 9.81


def air_density(temperature_c=20, altitude_m=0, pressure_pa=None):
    """Calculate air density from temperature and altitude.

    Uses the barometric formula for standard atmosphere if pressure not provided.
    """
    if pressure_pa is None:
        # Standard atmosphere pressure at altitude
        # P = P0 * (1 - 0.0065 * h / 288.15) ^ 5.2559
        pressure_pa = 101325 * (1 - 0.0065 * altitude_m / 288.15) ** 5.2559

    # Ideal gas law: rho = P / (R_specific * T)
    R_specific = 287.058  # J/(kg·K) for dry air
    temperature_k = temperature_c + 273.15
    return pressure_pa / (R_specific * temperature_k)


def power_required(speed, grade, weight_rider, weight_bike, cda, crr,
                   rho=None, temperature_c=20, altitude_m=0, drivetrain_loss=0.03):
    """Calculate power required to maintain speed on a given grade.

    P = P_aero + P_rolling + P_gravity + P_drivetrain_loss

    Args:
        speed: velocity in m/s
        grade: decimal (0.05 = 5%)
        weight_rider: kg
        weight_bike: kg
        cda: drag area (m^2)
        crr: rolling resistance coefficient
        rho: air density kg/m^3 (computed from temp/altitude if None)
        temperature_c: ambient temperature
        altitude_m: altitude for air density
        drivetrain_loss: fraction of power lost in drivetrain (default 3%)

    Returns: power in watts
    """
    if rho is None:
        rho = air_density(temperature_c, altitude_m)

    m = weight_rider + weight_bike

    p_aero = 0.5 * cda * rho * speed ** 3
    p_rolling = crr * m * G * speed * np.cos(np.arctan(grade))
    p_gravity = m * G * speed * np.sin(np.arctan(grade))

    p_total = p_aero + p_rolling + p_gravity

    # Account for drivetrain loss (power at pedals > power at wheel)
    if p_total > 0:
        p_total = p_total / (1 - drivetrain_loss)

    return float(p_total)


def speed_from_power(power, grade, weight_rider, weight_bike, cda, crr,
                     rho=None, temperature_c=20, altitude_m=0, drivetrain_loss=0.03):
    """Calculate speed achievable at a given power on a given grade.

    Inverse of power_required. Uses root-finding (Brent's method).

    Returns: speed in m/s
    """
    if rho is None:
        rho = air_density(temperature_c, altitude_m)

    # Effective power at wheel after drivetrain loss
    p_wheel = power * (1 - drivetrain_loss)

    def residual(v):
        if v <= 0:
            return -p_wheel
        m = weight_rider + weight_bike
        p_aero = 0.5 * cda * rho * v ** 3
        p_rolling = crr * m * G * v * np.cos(np.arctan(grade))
        p_gravity = m * G * v * np.sin(np.arctan(grade))
        return p_aero + p_rolling + p_gravity - p_wheel

    # Find speed where power balance = 0
    try:
        v = brentq(residual, 0.1, 30.0)  # 0.36 to 108 km/h
    except ValueError:
        # If no root in range, return boundary
        if residual(0.1) > 0:
            return 0.1  # Can't go even 0.36 km/h at this power
        return 30.0  # Faster than 108 km/h

    return float(v)
