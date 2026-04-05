import pytest
import py_eol.sync_data as sync_data_mod


def test_sync_data_success(monkeypatch):
    # Mock all steps to succeed
    monkeypatch.setattr(
        sync_data_mod,
        "fetch_py_eol_data",
        lambda: {"3.99": {"end_of_life": "2099-01-01", "status": "end-of-life"}},
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
        lambda: {"3.99": {"end_of_life": "2099-01-01", "status": "end-of-life"}},
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
            return {"3.99": {"end_of_life": "2099-01-01", "status": "end-of-life"}}

    monkeypatch.setattr(sync_data_mod.requests, "get", lambda url: MockResponse())
    result = sync_data_mod.fetch_py_eol_data()
    assert isinstance(result, dict)
    assert "3.99" in result


def test_fetch_py_eol_data_http_error(monkeypatch):
    class MockResponse:
        def raise_for_status(self):
            raise Exception("HTTP error")

    monkeypatch.setattr(sync_data_mod.requests, "get", lambda url: MockResponse())
    with pytest.raises(Exception):
        sync_data_mod.fetch_py_eol_data()


def test_generate_eol_data_content_valid():
    data = {"3.99": {"end_of_life": "2099-01-01", "status": "end-of-life"}}
    content = sync_data_mod.generate_eol_data_content(data)
    assert "3.99" in content
    assert "datetime.date(2099, 1, 1)" in content


def test_generate_eol_data_content_year_month_only():
    # end_of_life with year-month only should use last day of that month
    data = {"3.12": {"end_of_life": "2028-10", "status": "security"}}
    content = sync_data_mod.generate_eol_data_content(data)
    assert "3.12" in content
    assert "datetime.date(2028, 10, 31)" in content


def test_generate_eol_data_content_invalid_and_missing():
    # Should skip invalid date and missing end_of_life
    data = {
        "bad": {"end_of_life": "not-a-date", "status": "end-of-life"},
        "skip": {"end_of_life": None, "status": "end-of-life"},
        "ok": {"end_of_life": "2099-12-31", "status": "end-of-life"},
    }
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


def test_generate_eol_data_content_with_release_date():
    data = {"3.99": {"release": "2023-10-02", "end_of_life": "2028-10-31"}}
    content = sync_data_mod.generate_eol_data_content(data)
    assert "3.99" in content
    assert "release_date" in content
    assert "datetime.date(2023, 10, 2)" in content
    assert "eol_date" in content
    assert "datetime.date(2028, 10, 31)" in content


def test_generate_eol_data_content_missing_release_date():
    # release_date is optional; entry should still be generated with just eol_date
    data = {"3.99": {"end_of_life": "2099-01-01"}}
    content = sync_data_mod.generate_eol_data_content(data)
    assert "3.99" in content
    assert "eol_date" in content
    assert "datetime.date(2099, 1, 1)" in content


def test_generate_eol_data_content_generates_eol_dates_alias():
    data = {"3.99": {"end_of_life": "2099-01-01"}}
    content = sync_data_mod.generate_eol_data_content(data)
    assert "EOL_DATES" in content
    assert "PYTHON_VERSIONS" in content

