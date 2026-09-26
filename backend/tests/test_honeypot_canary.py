from app.core.config import settings
from app.routers.honeypot import add_canary_lure, configured_canary_url


def test_canary_url_accepts_only_official_hosts(monkeypatch):
    monkeypatch.setattr(settings, "canarytoken_url", "https://example.com/tracker")
    assert configured_canary_url() is None

    monkeypatch.setattr(settings, "canarytoken_url", "https://canarytokens.com/example/token")
    assert configured_canary_url() == "https://canarytokens.com/example/token"


def test_canary_lure_is_opt_in_and_added_only_once(monkeypatch):
    monkeypatch.setattr(settings, "canarytoken_url", "https://canarytokens.com/example/token")
    intelligence = {"canary": {"armed": True, "proposed": False}}

    reply, intelligence, added = add_canary_lure("Please wait.", intelligence)
    assert added is True
    assert "https://canarytokens.com/example/token" in reply
    assert intelligence["canary"]["proposed"] is True

    second_reply, _, added_again = add_canary_lure("Still checking.", intelligence)
    assert added_again is False
    assert "canarytokens.com" not in second_reply


def test_canary_lure_stays_off_when_session_is_not_armed(monkeypatch):
    monkeypatch.setattr(settings, "canarytoken_url", "https://canarytokens.com/example/token")
    reply, _, added = add_canary_lure("Please wait.", {"canary": {"armed": False}})
    assert added is False
    assert reply == "Please wait."
