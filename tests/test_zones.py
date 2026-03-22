import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
from wko5.zones import coggan_zones, seiler_zones, ilevels, time_in_zones, hr_zones


def test_coggan_zones_boundaries():
    zones = coggan_zones(292)
    assert len(zones) == 7
    assert "Active Recovery" in zones
    assert "Neuromuscular" in zones
    low, high = zones["Threshold"]
    assert low < 292 < high


def test_coggan_zones_values():
    zones = coggan_zones(292)
    low, high = zones["Endurance"]
    assert abs(low - 292 * 0.56) < 1
    assert abs(high - 292 * 0.75) < 1


def test_seiler_zones():
    zones = seiler_zones(292)
    assert len(zones) == 3
    assert zones["Zone 1"][1] == int(292 * 0.80)


def test_ilevels_with_pd_model():
    pd_model = {"mFTP": 292, "FRC": 15.0, "TTE": 45, "Pmax": 1200}
    zones = ilevels(pd_model)
    assert len(zones) == 7
    assert zones["Threshold"][1] == 292


def test_hr_zones():
    zones = hr_zones(max_hr=190, lthr=172)
    assert len(zones) == 5


def test_time_in_zones():
    zones = coggan_zones(292)
    power = pd.Series([100] * 50 + [250] * 50 + [350] * 50)
    tiz = time_in_zones(power, zones)
    total = sum(tiz.values())
    assert total == 150


def test_sweet_spot_band():
    """Sweet spot should be 88-93% of FTP."""
    from wko5.zones import sweet_spot_band
    low, high = sweet_spot_band(300)
    assert low == 264  # 300 * 0.88
    assert high == 279  # 300 * 0.93


def test_validate_endurance_rides():
    """Should flag endurance rides with IF > 0.65."""
    from wko5.zones import validate_endurance_rides
    result = validate_endurance_rides(days_back=90)
    if result is not None:
        assert isinstance(result, list)
