import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from wko5.profile import (
    power_profile, coggan_ranking, strengths_limiters,
    phenotype, profile_trend, fatigue_resistance,
)
from wko5.db import WEIGHT_KG


def test_power_profile_returns_watts_and_wkg():
    profile = power_profile(days=90)
    assert isinstance(profile, dict)
    if profile:
        assert "watts" in profile
        assert "wkg" in profile
        assert 60 in profile["watts"]
        assert 300 in profile["watts"]
        for d in profile["watts"]:
            if not np.isnan(profile["watts"][d]):
                expected_wkg = profile["watts"][d] / WEIGHT_KG
                assert abs(profile["wkg"][d] - expected_wkg) < 0.1


def test_coggan_ranking():
    profile = {"wkg": {5: 18.0, 60: 7.0, 300: 5.5, 1200: 4.5, 3600: 4.0}}
    ranking = coggan_ranking(profile)
    assert isinstance(ranking, dict)
    assert 5 in ranking
    assert ranking[5] in ["Untrained", "Fair", "Moderate", "Good", "Very Good", "Exceptional", "World Class"]


def test_strengths_limiters():
    profile = {"wkg": {5: 18.0, 60: 7.0, 300: 5.5, 1200: 4.5, 3600: 3.5}}
    result = strengths_limiters(profile)
    assert "strength" in result
    assert "limiter" in result


def test_phenotype_sprinter():
    model = {"Pmax": 1800, "mFTP": 280, "FRC": 25, "TTE": 40}
    result = phenotype(model)
    assert "Sprinter" in result


def test_phenotype_tter():
    model = {"Pmax": 1100, "mFTP": 290, "FRC": 12, "TTE": 55}
    result = phenotype(model)
    assert "TTer" in result


def test_profile_trend_returns_dataframe():
    import pandas as pd
    result = profile_trend(duration_s=300, window_days=90, step_days=30)
    assert isinstance(result, pd.DataFrame)
