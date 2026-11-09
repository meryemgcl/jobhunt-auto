import pytest
from services.notification_and_meta.notifier import _sanitize_header
from services.url_utils import canonicalize_url
from services.http_client import ResilientHttpClient


def test_sanitize_header_strips_crlf_injection():
    # Attempt email header injection (Bcc, Subject splitting)
    malicious = "attacker@example.com\r\nBcc: victim@example.com\nSubject: Injected"
    sanitized = _sanitize_header(malicious)
    assert "\r" not in sanitized
    assert "\n" not in sanitized
    assert "\t" not in sanitized
    assert "Bcc: victim@example.com" in sanitized  # Kept on a single line safely


def test_sanitize_header_handles_none_and_empty():
    assert _sanitize_header(None) == ""
    assert _sanitize_header("") == ""
    assert _sanitize_header("   hello \n world   ") == "hello world"


def test_url_canonicalization_blocks_malicious_schemes():
    # Only http and https are allowed
    assert canonicalize_url("javascript:alert(1)") == ""
    assert canonicalize_url("data:text/html,<script>alert(1)</script>") == ""
    assert canonicalize_url("file:///etc/passwd") == ""
    assert canonicalize_url("vbscript:msgbox(1)") == ""


def test_url_canonicalization_allows_legitimate_urls():
    url = "https://example.com/jobs/123?utm_source=twitter&ref=share#anchor"
    canonical = canonicalize_url(url)
    assert canonical == "https://example.com/jobs/123"


def test_http_client_ssl_verification_defaults_to_true(monkeypatch):
    monkeypatch.delenv("JOBHUNT_HTTP_VERIFY_SSL", raising=False)
    client = ResilientHttpClient()
    assert client.verify is True


def test_http_client_ssl_verification_can_be_disabled_via_env(monkeypatch):
    monkeypatch.setenv("JOBHUNT_HTTP_VERIFY_SSL", "false")
    client = ResilientHttpClient()
    assert client.verify is False
