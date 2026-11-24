"""Headless smoke test: the app loads with no secrets file and no network."""
import pathlib
import socket

import pytest
from streamlit.testing.v1 import AppTest

APP = str(pathlib.Path(__file__).resolve().parents[1] / "app.py")


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def blocked(*a, **k):
        raise OSError("network disabled in tests")
    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    for k in ("GOOGLE_API_KEY", "GEMINI_API_KEY"):
        monkeypatch.delenv(k, raising=False)


def test_app_loads_without_secrets():
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert not at.exception


def test_key_not_in_url_and_output_escaped():
    src = pathlib.Path(APP).read_text()
    assert "?key=" not in src
    assert "html.escape(" in src
