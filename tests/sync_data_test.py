import pytest
import py_eol.sync_data as sync_data_mod


def test_sync_data_success(monkeypatch):
    # Mock all steps to succeed
    monkeypatch.setattr(
        sync_data_mod,
        "fetch_py_eol_data",
        lambda: [{"cycle": "3.99", "eol": "2099-01-01"}],
    )
    monkeypatch.setattr(
        sync_data_mod, "generate_eol_data_content", lambda data: "test content"
    )
    monkeypatch.setattr(sync_data_mod, "save_eol_data", lambda content: None)
    assert sync_data_mod.sync_data() is True


def test_sync_data_api_failure(monkeypatch):
    def fail_fetch():
        raise Exception("API error")

    monkeypatch.setattr(sync_data_mod, "fetch_py_eol_data", fail_fetch)
    assert sync_data_mod.sync_data() is False


def test_sync_data_file_write_failure(monkeypatch):
    monkeypatch.setattr(
        sync_data_mod,
        "fetch_py_eol_data",
        lambda: [{"cycle": "3.99", "eol": "2099-01-01"}],
    )
    monkeypatch.setattr(
        sync_data_mod, "generate_eol_data_content", lambda data: "test content"
    )

    def fail_save(content):
        raise Exception("Write error")

    monkeypatch.setattr(sync_data_mod, "save_eol_data", fail_save)
    assert sync_data_mod.sync_data() is False


def test_fetch_py_eol_data_success(monkeypatch):
    class MockResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return [{"cycle": "3.99", "eol": "2099-01-01"}]

    monkeypatch.setattr(sync_data_mod.requests, "get", lambda url, **kwargs: MockResponse())
    result = sync_data_mod.fetch_py_eol_data()
    assert isinstance(result, list)
    assert result[0]["cycle"] == "3.99"


def test_fetch_py_eol_data_http_error(monkeypatch):
    class MockResponse:
        def raise_for_status(self):
            raise Exception("HTTP error")

    monkeypatch.setattr(sync_data_mod.requests, "get", lambda url, **kwargs: MockResponse())
    with pytest.raises(Exception):
        sync_data_mod.fetch_py_eol_data()


def test_generate_eol_data_content_valid():
    data = [{"cycle": "3.99", "eol": "2099-01-01"}]
    content = sync_data_mod.generate_eol_data_content(data)
    assert "3.99" in content
    assert "datetime.date(2099, 1, 1)" in content


def test_generate_eol_data_content_invalid_and_missing():
    # Should skip invalid date and missing eol
    data = [
        {"cycle": "bad", "eol": "not-a-date"},
        {"cycle": "skip", "eol": None},
        {"cycle": "ok", "eol": "2099-12-31"},
    ]
    content = sync_data_mod.generate_eol_data_content(data)
    assert "ok" in content
    assert "skip" not in content
    assert "bad" not in content


def test_save_eol_data(tmp_path, capsys):
    file_path = tmp_path / "_eol_data.py"
    content = "# test file\n"
    # Patch OUTPUT_FILE to our temp file
    orig_file = sync_data_mod.OUTPUT_FILE
    sync_data_mod.OUTPUT_FILE = file_path
    try:
        sync_data_mod.save_eol_data(content)
        assert file_path.read_text(encoding="utf-8") == content
        out = capsys.readouterr().out
        assert "Updated" in out
    finally:
        sync_data_mod.OUTPUT_FILE = orig_file


def test_normalize_pep_data():
    # Test PEP API format with "version" and "end_of_life" fields
    pep_data = [
        {"version": "3.13", "end_of_life": "2029-10-31"},
        {"version": "3.12", "end_of_life": "2028-10-31"},
    ]
    result = sync_data_mod.normalize_pep_data(pep_data)
    assert len(result) == 2
    assert result[0]["cycle"] == "3.13"
    assert result[0]["eol"] == "2029-10-31"


def test_normalize_pep_data_with_cycle_field():
    # Test with "cycle" field (endoflife.date format)
    data = [
        {"cycle": "3.99", "eol": "2099-01-01"},
    ]
    result = sync_data_mod.normalize_pep_data(data)
    assert len(result) == 1
    assert result[0]["cycle"] == "3.99"
    assert result[0]["eol"] == "2099-01-01"


def test_normalize_pep_data_missing_fields():
    # Test with missing fields - should skip incomplete entries
    data = [
        {"version": "3.13"},  # missing end_of_life
        {"end_of_life": "2029-10-31"},  # missing version
        {"version": "3.12", "end_of_life": "2028-10-31"},  # complete
    ]
    result = sync_data_mod.normalize_pep_data(data)
    assert len(result) == 1
    assert result[0]["cycle"] == "3.12"


def test_fetch_py_eol_data_pep_api_success(monkeypatch):
    # Test successful fetch from PEP API
    class MockPEPResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return [{"version": "3.13", "end_of_life": "2029-10-31"}]

    call_count = {"count": 0}

    def mock_get(url, **kwargs):
        call_count["count"] += 1
        if sync_data_mod.PEP_API_URL in url:
            return MockPEPResponse()
        # Should not reach EOL API
        raise Exception("Should use PEP API")

    monkeypatch.setattr(sync_data_mod.requests, "get", mock_get)
    result = sync_data_mod.fetch_py_eol_data()
    assert isinstance(result, list)
    assert result[0]["cycle"] == "3.13"
    assert call_count["count"] == 1  # Only PEP API was called


def test_fetch_py_eol_data_fallback_to_endoflife(monkeypatch):
    # Test fallback to endoflife.date API when PEP API fails
    class MockEOLResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return [{"cycle": "3.99", "eol": "2099-01-01"}]

    call_count = {"count": 0}

    def mock_get(url, **kwargs):
        call_count["count"] += 1
        if sync_data_mod.PEP_API_URL in url:
            raise Exception("PEP API error")
        # Fall back to EOL API
        return MockEOLResponse()

    monkeypatch.setattr(sync_data_mod.requests, "get", mock_get)
    result = sync_data_mod.fetch_py_eol_data()
    assert isinstance(result, list)
    assert result[0]["cycle"] == "3.99"
    assert call_count["count"] == 2  # Both APIs were attempted
