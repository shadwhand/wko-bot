import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from wko5.config import get_config, set_config, init_config_table


def test_init_config_table():
    init_config_table()
    cfg = get_config()
    assert cfg is not None
    assert cfg["weight_kg"] == 78.0
    assert cfg["ftp_manual"] == 292
    assert cfg["bike_weight_kg"] == 9.0
    assert cfg["cda"] == 0.35
    assert cfg["crr"] == 0.005
    assert cfg["spike_threshold_watts"] == 2000


def test_get_config_returns_dict():
    cfg = get_config()
    assert isinstance(cfg, dict)
    assert "weight_kg" in cfg
    assert "pd_pmax_low" in cfg
    assert "ctl_time_constant" in cfg


def test_set_config():
    set_config("weight_kg", 80.0)
    cfg = get_config()
    assert cfg["weight_kg"] == 80.0
    set_config("weight_kg", 78.0)


def test_set_config_invalid_key():
    try:
        set_config("nonexistent_key", 999)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
