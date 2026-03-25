"""Tests for /health endpoint data_version field."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from wko5.api.routes import _data_version, _invalidate_cache


def test_data_version_starts_at_one():
    from wko5.api import routes
    assert routes._data_version >= 1


def test_invalidate_cache_increments_version():
    from wko5.api import routes
    before = routes._data_version
    _invalidate_cache()
    assert routes._data_version == before + 1
