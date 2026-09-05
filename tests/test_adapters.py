from services.adapters import ArbeitnowAdapter, RemotiveAdapter, StaticOpportunityAdapter
from services.http_client import ResilientHttpClient


class FakeClient:
    def __init__(self, payload):
        self.payload = payload

    def get_json(self, url, **kwargs):
        return self.payload


def test_remotive_adapter_returns_common_opportunity_schema():
    adapter = RemotiveAdapter(
        client=FakeClient(
            {
                "jobs": [
                    {
                        "title": "Junior Python Engineer",
                        "company_name": "Example",
                        "url": "https://example.com/job?utm_campaign=x",
                        "candidate_required_location": "Remote",
                        "tags": ["Python"],
                        "description": "Build APIs",
                        "publication_date": "2026-09-05T00:00:00",
                    }
                ]
            }
        )
    )

    [job] = adapter.fetch()

    assert job["canonical_url"] == "https://example.com/job"
    assert job["category"] == "job"
    assert job["source_reliability"] == 90


def test_arbeitnow_adapter_returns_common_opportunity_schema():
    adapter = ArbeitnowAdapter(
        client=FakeClient(
            {
                "data": [
                    {
                        "title": "Junior Backend Intern",
                        "company_name": "Example",
                        "url": "https://example.com/intern",
                        "location": "Berlin Remote",
                        "tags": ["Python"],
                        "description": "Internship",
                        "created_at": 1788566400,
                    }
                ]
            }
        )
    )

    [job] = adapter.fetch()

    assert job["canonical_url"] == "https://example.com/intern"
    assert job["source"] == "Arbeitnow API"


def test_static_adapter_does_not_create_http_client():
    adapter = StaticOpportunityAdapter([{"title": "Camp", "url": "https://example.com/camp"}], category="bootcamp")

    assert adapter.client is None
    assert adapter.fetch()[0]["category"] == "bootcamp"


def test_http_client_sets_timeout_and_user_agent(monkeypatch):
    monkeypatch.setenv("JOBHUNT_HTTP_TIMEOUT", "7")
    monkeypatch.setenv("JOBHUNT_USER_AGENT", "JobHunt-Test/1.0")

    client = ResilientHttpClient()

    assert client.timeout == 7
    assert client.session.headers["User-Agent"] == "JobHunt-Test/1.0"
