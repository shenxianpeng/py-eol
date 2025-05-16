import datetime
import pytest
from py_eol import is_eol, get_eol_date, supported_versions, eol_versions, latest_supported_version


def test_is_eol_known_version():
    assert is_eol("2.7") is True
    assert is_eol("3.7") is True
    assert isinstance(is_eol("3.12"), bool)


def test_is_eol_unknown_version():
    with pytest.raises(ValueError):
        is_eol("4.0")


def test_get_eol_date():
    date = get_eol_date("3.6")
    assert isinstance(date, datetime.date)


def test_supported_versions_not_empty():
    versions = supported_versions()
    assert isinstance(versions, list)
    assert all(isinstance(v, str) for v in versions)


def test_eol_versions_not_empty():
    versions = eol_versions()
    assert isinstance(versions, list)
    assert all(isinstance(v, str) for v in versions)


def test_latest_supported_version():
    version = latest_supported_version()
    assert isinstance(version, str)
