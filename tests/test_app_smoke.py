"""Smoke test for the web page: load app.py the way Streamlit would and check it does not crash.

    python3 -m pytest tests/ -q

Uses Streamlit's own test harness (AppTest), so no browser and no server. The page reads the
saved analyses in eval/fixtures (CT_FIXTURE_DIR) instead of calling the AI service.

No network or paid call can happen:
- the API key is a fake dummy value, so any real Anthropic call would be refused;
- the Anthropic base URL points at a closed local port, so a call could not leave this machine;
- ct.extract.extract (the only paid call on upload) is replaced with a stub that records the
  call, and the tests assert it was never used. Any slip would also show as an st.error on the
  page, which the tests assert is empty.
"""
from pathlib import Path

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from ct import extract

ROOT = Path(__file__).resolve().parent.parent
APP = str(ROOT / "app.py")
FIXTURES = str(ROOT / "eval" / "fixtures")
LAMBETH_PDF = ROOT / "21_04939_FUL--3474437.pdf"
DUMMY_KEY = "sk-ant-dummy-not-a-real-key"  # fake on purpose: a real call with it would fail
TIMEOUT = 60  # seconds per run; the full Lambeth notice renders a lot of panels


@pytest.fixture
def app(monkeypatch):
    """An AppTest for app.py with fixtures on, a dummy key and no saved-projects store."""
    monkeypatch.setenv("CT_FIXTURE_DIR", FIXTURES)
    # Set to empty rather than deleted, so a local .env cannot fill them in (load_dotenv does
    # not override variables that already exist). The key then comes from at.secrets below.
    for name in ("ANTHROPIC_API_KEY", "SUPABASE_URL", "SUPABASE_SERVICE_KEY",
                 "CT_LOCAL_STORE", "CT_DEV_USER"):
        monkeypatch.setenv(name, "")
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "http://127.0.0.1:9")  # closed port: nothing leaves

    calls = []

    def no_paid_call(*args, **kwargs):
        calls.append(args)
        raise AssertionError("The smoke test tried a real extraction call")

    monkeypatch.setattr(extract, "extract", no_paid_call)
    st.cache_resource.clear()  # get_store() is cached; start each test from a clean page

    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    # Dummy secrets before the first run (Streamlit: a missing secret may stop the app running).
    # https://docs.streamlit.io/develop/concepts/app-testing/beyond-the-basics
    at.secrets["ANTHROPIC_API_KEY"] = DUMMY_KEY
    at.extract_calls = calls
    return at


def page_text(at):
    return "\n".join(m.value for m in at.markdown)


def test_home_page_loads(app):
    app.run()
    assert not app.exception
    assert not app.error
    text = page_text(app)
    assert "UPLOAD DECISION NOTICES" in text
    assert "From planning permission to start on site." in text
    assert "not legal advice" in text  # the footer caveat is still on the page
    assert len(app.file_uploader) == 1
    assert app.extract_calls == []


def test_lambeth_notice_renders_from_fixture(app):
    # AppTest in the pinned Streamlit (1.58.0) can drive st.file_uploader, so this uploads the
    # real Lambeth PDF; the page finds eval/fixtures/21_04939_FUL--3474437.json by file name.
    app.run()
    app.file_uploader[0].set_value((LAMBETH_PDF.name, LAMBETH_PDF.read_bytes(), "application/pdf"))
    app.run()
    assert not app.exception
    assert not app.error
    assert app.extract_calls == []
    text = page_text(app)
    assert "38 planning conditions extracted from this notice" in text
    assert "21/04939/FUL" in text and "Havilland House" in text  # the notice title line
