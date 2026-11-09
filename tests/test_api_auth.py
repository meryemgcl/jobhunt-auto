import pytest
from fastapi import HTTPException

import api


def test_api_protected_routes_fail_closed_without_configured_token(monkeypatch):
    monkeypatch.delenv("JOBHUNT_API_TOKEN", raising=False)

    with pytest.raises(HTTPException) as error:
        api._verify_api_token(None)

    assert error.value.status_code == 503


def test_api_token_comparison_rejects_missing_or_invalid_token(monkeypatch):
    monkeypatch.setenv("JOBHUNT_API_TOKEN", "configured-token")

    for token in (None, "wrong-token"):
        with pytest.raises(HTTPException) as error:
            api._verify_api_token(token)
        assert error.value.status_code == 401

    api._verify_api_token("configured-token")


def test_engine_trigger_is_post_only():
    trigger_route = next(route for route in api.app.routes if route.path == "/trigger-engine")

    assert trigger_route.methods == {"POST"}
