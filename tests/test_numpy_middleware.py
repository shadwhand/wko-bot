"""Tests for numpy type conversion middleware."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import numpy as np
from wko5.api.routes import convert_numpy, _NanSafeEncoder


def test_numpy_bool():
    assert convert_numpy(np.bool_(True)) is True
    assert convert_numpy(np.bool_(False)) is False


def test_numpy_int():
    assert convert_numpy(np.int64(42)) == 42
    assert isinstance(convert_numpy(np.int64(42)), int)


def test_numpy_int_variants():
    assert isinstance(convert_numpy(np.int32(10)), int)
    assert isinstance(convert_numpy(np.int16(10)), int)
    assert isinstance(convert_numpy(np.uint8(10)), int)


def test_numpy_float():
    assert convert_numpy(np.float64(3.14)) == 3.14
    assert isinstance(convert_numpy(np.float64(3.14)), float)


def test_numpy_float_nan():
    assert convert_numpy(np.float64(float('nan'))) is None


def test_numpy_float_inf():
    assert convert_numpy(np.float64(float('inf'))) is None
    assert convert_numpy(np.float64(float('-inf'))) is None


def test_nested_dict():
    d = {"feasible": np.bool_(True), "values": [np.float64(1.0), np.int64(2)]}
    result = convert_numpy(d)
    assert result == {"feasible": True, "values": [1.0, 2]}
    assert isinstance(result["feasible"], bool)
    assert isinstance(result["values"][0], float)
    assert isinstance(result["values"][1], int)


def test_ndarray():
    arr = np.array([1.0, 2.0, 3.0])
    assert convert_numpy(arr) == [1.0, 2.0, 3.0]


def test_ndarray_nested():
    arr = np.array([[1, 2], [3, 4]])
    result = convert_numpy(arr)
    assert result == [[1, 2], [3, 4]]


def test_plain_python_passthrough():
    """Plain Python types should pass through unchanged."""
    assert convert_numpy(42) == 42
    assert convert_numpy(3.14) == 3.14
    assert convert_numpy("hello") == "hello"
    assert convert_numpy(None) is None
    assert convert_numpy(True) is True


def test_tuple_conversion():
    t = (np.int64(1), np.float64(2.0))
    result = convert_numpy(t)
    assert result == [1, 2.0]


def test_encoder_handles_numpy_bool():
    data = {"flag": np.bool_(True)}
    result = json.dumps(data, cls=_NanSafeEncoder)
    assert json.loads(result) == {"flag": True}


def test_encoder_handles_numpy_int():
    data = {"count": np.int64(42)}
    result = json.dumps(data, cls=_NanSafeEncoder)
    assert json.loads(result) == {"count": 42}


def test_encoder_handles_numpy_float():
    data = {"value": np.float64(3.14)}
    result = json.dumps(data, cls=_NanSafeEncoder)
    assert json.loads(result) == {"value": 3.14}


def test_encoder_handles_numpy_nan():
    data = {"value": np.float64(float('nan'))}
    result = json.dumps(data, cls=_NanSafeEncoder)
    assert json.loads(result) == {"value": None}


def test_encoder_handles_ndarray():
    data = {"arr": np.array([1, 2, 3])}
    result = json.dumps(data, cls=_NanSafeEncoder)
    assert json.loads(result) == {"arr": [1, 2, 3]}
