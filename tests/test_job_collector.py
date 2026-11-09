import pytest
from services.job_collector import (
    _collect_from_adapters,
    record_source_error,
    get_source_errors,
    reset_source_errors,
)


class SuccessfulAdapter:
    source_name = "SuccessSource"
    last_error = None

    def fetch(self):
        return [{"title": "Job 1", "source": "SuccessSource"}]


class FailingAdapter:
    source_name = "FailSource"
    last_error = "Connection refused"

    def fetch(self):
        raise RuntimeError("API network failure simulated")


class FaultyStatusAdapter:
    source_name = "FaultySource"
    last_error = "404 Not Found"

    def fetch(self):
        return [{"title": "Job 2", "source": "FaultySource"}]


def test_collect_from_adapters_isolates_adapter_failures():
    reset_source_errors()
    adapters = [SuccessfulAdapter(), FailingAdapter(), FaultyStatusAdapter()]

    # Even though FailingAdapter raises an exception, other adapters MUST succeed
    results = _collect_from_adapters(adapters, max_workers=2)

    titles = [item["title"] for item in results]
    assert "Job 1" in titles
    assert "Job 2" in titles

    errors = get_source_errors()
    assert "FailSource" in errors
    assert "FaultySource" in errors


def test_collect_from_adapters_empty_list():
    assert _collect_from_adapters([]) == []


def test_record_source_error_counter():
    reset_source_errors()
    record_source_error("TestSource")
    record_source_error("TestSource")
    record_source_error("OtherSource")

    errors = get_source_errors()
    assert errors["TestSource"] == 2
    assert errors["OtherSource"] == 1
