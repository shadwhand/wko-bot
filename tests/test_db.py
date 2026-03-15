import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
from wko5.db import (
    get_connection, get_activities, get_records,
    WEIGHT_KG, FTP_DEFAULT, FTP_RANGE, DB_PATH,
)

def test_constants():
    assert WEIGHT_KG == 78.0
    assert FTP_DEFAULT == 292
    assert FTP_RANGE == (285, 299)
    assert "cycling_power.db" in DB_PATH

def test_get_connection():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM activities")
    count = cursor.fetchone()[0]
    assert count > 1000
    conn.close()

def test_get_activities_returns_dataframe():
    df = get_activities()
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 1000
    assert "start_time" in df.columns
    assert "avg_power" in df.columns

def test_get_activities_date_filter():
    df = get_activities(start="2025-01-01", end="2025-12-31")
    assert isinstance(df, pd.DataFrame)
    all_df = get_activities()
    assert len(df) < len(all_df)

def test_get_activities_sub_sport_filter():
    df = get_activities(sub_sport="virtual_activity")
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert all(df["sub_sport"] == "virtual_activity")

def test_get_activities_empty_returns_empty_df():
    df = get_activities(start="1999-01-01", end="1999-01-02")
    assert isinstance(df, pd.DataFrame)
    assert df.empty

def test_get_records():
    df = get_records(1)
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 100
    assert "power" in df.columns
    assert "heart_rate" in df.columns

def test_get_records_invalid_id():
    df = get_records(999999)
    assert isinstance(df, pd.DataFrame)
    assert df.empty
