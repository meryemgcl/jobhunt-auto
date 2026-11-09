import datetime as dt

from services.adapters import (
    ArbeitnowAdapter,
    AshbyAdapter,
    GitHubIssuesAdapter,
    GreenhouseAdapter,
    HackerNewsAdapter,
    HackerNewsJobsAdapter,
    LeverAdapter,
    RemotiveAdapter,
    StaticOpportunityAdapter,
)
from services.http_client import ResilientHttpClient
import services.job_collector as job_collector


def _recent_date(days_ago=2):
    return (dt.datetime.now(dt.UTC) - dt.timedelta(days=days_ago)).isoformat()


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
                        "publication_date": _recent_date(),
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
                        "created_at": int(
                            (dt.datetime.now(dt.UTC) - dt.timedelta(days=2)).timestamp()
                        ),
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


def test_github_adapter_forwards_configured_bearer_token(monkeypatch):
    class RecordingClient:
        headers = None

        def get_json(self, url, **kwargs):
            self.headers = kwargs["headers"]
            return {"items": []}

    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    client = RecordingClient()

    GitHubIssuesAdapter(client=client).fetch()

    assert client.headers["Authorization"] == "Bearer test-token"


def test_remotive_adapter_reports_invalid_payload():
    adapter = RemotiveAdapter(client=FakeClient({"unexpected": []}))

    assert adapter.fetch() == []
    assert adapter.last_error == "Invalid response payload: expected a jobs list."


def test_remotive_adapter_excludes_old_jobs_and_does_not_invent_dates():
    adapter = RemotiveAdapter(
        client=FakeClient(
            {
                "jobs": [
                    {
                        "title": "Old role",
                        "url": "https://example.com/old",
                        "publication_date": "2026-01-01T00:00:00",
                    },
                    {"title": "Undated role", "url": "https://example.com/unknown"},
                ]
            }
        )
    )

    [job] = adapter.fetch()

    assert job["title"] == "Undated role"
    assert job["published_at"] == ""


def test_greenhouse_adapter_filters_stale_jobs_and_keeps_partial_results():
    class BoardClient:
        def get_json(self, url):
            if "/missing/" in url:
                raise RuntimeError("board unavailable")
            return {
                "jobs": [
                    {
                        "title": "Junior Backend Engineer",
                        "company_name": "Example",
                        "absolute_url": "https://boards.greenhouse.io/example/jobs/1",
                        "location": {"name": "Remote - Turkey"},
                        "first_published": _recent_date(),
                        "departments": [{"name": "Engineering"}],
                    },
                    {
                        "title": "Old Engineer",
                        "absolute_url": "https://boards.greenhouse.io/example/jobs/2",
                        "first_published": "2025-01-01T00:00:00Z",
                    },
                ]
            }

    adapter = GreenhouseAdapter(boards=["example", "missing"], client=BoardClient())

    [job] = adapter.fetch()

    assert job["company"] == "Example"
    assert job["location"] == "Remote - Turkey"
    assert job["metadata"]["department"] == ["Engineering"]
    assert adapter.last_error == "1 of 2 Greenhouse board request(s) failed."


def test_hackernews_adapter_uses_original_publication_timestamp():
    current_timestamp = int(dt.datetime.now(dt.UTC).timestamp())

    class HackerNewsClient:
        def get_json(self, url):
            if url.endswith("topstories.json"):
                return [1]
            return {
                "title": "Fresh technology story",
                "url": "https://example.com/story",
                "time": current_timestamp,
            }

    [story] = HackerNewsAdapter(client=HackerNewsClient()).fetch()

    assert story["published_at"] == dt.datetime.fromtimestamp(
        current_timestamp, tz=dt.UTC
    ).date().isoformat()


def test_hackernews_jobs_adapter_keeps_job_posts_distinct_and_tracks_apply_link():
    current_timestamp = int(dt.datetime.now(dt.UTC).timestamp())

    class HackerNewsJobsClient:
        def get_json(self, url):
            if url.endswith("jobstories.json"):
                return [123]
            return {
                "title": "Example is hiring junior engineers",
                "url": "https://example.com/careers",
                "time": current_timestamp,
            }

    [job] = HackerNewsJobsAdapter(client=HackerNewsJobsClient()).fetch()

    assert job["category"] == "job"
    assert job["url"] == "https://news.ycombinator.com/item?id=123"
    assert job["metadata"]["application_url"] == "https://example.com/careers"


def test_job_collection_excludes_unverified_web_search_results(monkeypatch):
    adapter_names = []

    class FakeAdapter:
        def __init__(self, *args, **kwargs):
            adapter_names.append(type(self).__name__)
            self.last_error = None

        def fetch(self):
            return []

    class FakeRemotive(FakeAdapter):
        pass

    class FakeArbeitnow(FakeAdapter):
        pass

    class FakeGreenhouse(FakeAdapter):
        pass

    class FakeLever(FakeAdapter):
        pass

    class FakeAshby(FakeAdapter):
        pass

    class FakeHackerNewsHiring(FakeAdapter):
        pass

    monkeypatch.setattr(job_collector, "RemotiveAdapter", FakeRemotive)
    monkeypatch.setattr(job_collector, "ArbeitnowAdapter", FakeArbeitnow)
    monkeypatch.setattr(job_collector, "GreenhouseAdapter", FakeGreenhouse)
    monkeypatch.setattr(job_collector, "LeverAdapter", FakeLever)
    monkeypatch.setattr(job_collector, "AshbyAdapter", FakeAshby)
    monkeypatch.setattr(job_collector, "HackerNewsJobsAdapter", FakeHackerNewsHiring)

    assert job_collector.fetch_jobs() == []
    assert adapter_names == [
        "FakeRemotive",
        "FakeArbeitnow",
        "FakeGreenhouse",
        "FakeLever",
        "FakeAshby",
        "FakeHackerNewsHiring",
    ]


def test_lever_adapter_maps_turkish_board_postings_and_application_url():
    adapter = LeverAdapter(
        boards={"trendyol": "Trendyol"},
        client=FakeClient(
            [
                {
                    "text": "Software Engineering Intern",
                    "hostedUrl": "https://jobs.lever.co/trendyol/123",
                    "applyUrl": "https://jobs.lever.co/trendyol/123/apply",
                    "createdAt": int(
                        (dt.datetime.now(dt.UTC) - dt.timedelta(days=2)).timestamp() * 1000
                    ),
                    "country": "TR",
                    "workplaceType": "hybrid",
                    "categories": {
                        "location": "Istanbul",
                        "commitment": "Internship",
                        "department": "Engineering",
                    },
                }
            ]
        ),
    )

    [job] = adapter.fetch()

    assert job["company"] == "Trendyol"
    assert job["location"] == "Istanbul"
    assert job["metadata"]["country"] == "TR"
    assert job["metadata"]["application_url"].endswith("/apply")
    assert job["published_at"] == dt.datetime.fromtimestamp(
        int((dt.datetime.now(dt.UTC) - dt.timedelta(days=2)).timestamp()),
        tz=dt.UTC,
    ).date().isoformat()


def test_ashby_adapter_maps_remote_location_and_excludes_unlisted_jobs():
    adapter = AshbyAdapter(
        boards={"supabase": "Supabase"},
        client=FakeClient(
            {
                "jobs": [
                    {
                        "title": "Backend Engineer",
                        "jobUrl": "https://jobs.ashbyhq.com/supabase/123",
                        "applyUrl": "https://jobs.ashbyhq.com/supabase/123/application",
                        "publishedAt": _recent_date(),
                        "isListed": True,
                        "location": "Remote, Global",
                        "isRemote": True,
                        "employmentType": "FullTime",
                    },
                    {
                        "title": "Unlisted role",
                        "jobUrl": "https://jobs.ashbyhq.com/supabase/456",
                        "publishedAt": _recent_date(),
                        "isListed": False,
                    },
                ]
            }
        ),
    )

    [job] = adapter.fetch()

    assert job["company"] == "Supabase"
    assert job["location"] == "Remote, Global"
    assert job["metadata"]["is_remote"] is True
    assert job["metadata"]["application_url"].endswith("/application")
